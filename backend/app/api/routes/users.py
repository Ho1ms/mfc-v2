from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from ...core.errors import forbidden, not_found
from ...db.session import get_db
from ...models.admin import Admin
from ...models.enums import SystemEnum
from ...models.message import Message
from ...models.submission import FormSubmission
from ...models.user import User
from ...schemas.message import MessageOut
from ...schemas.submission import SubmissionOut
from ...schemas.user import BanPatchIn, UserSummary
from ...services.rate_limit import rate_limit
from ..deps import CurrentPrincipal, require_admin, require_staff

router = APIRouter()

_ban_rl = rate_limit("user_ban", limit=30, window_seconds=60)

# История переписки в карточке пользователя — окно последних N сообщений.
_USER_MESSAGES_LIMIT = 200


@router.get("", response_model=list[UserSummary])
def list_users(
    query: str | None = Query(default=None, description="Поиск по имени/username"),
    system: SystemEnum | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: CurrentPrincipal = Depends(require_staff),
) -> list[User]:
    q = select(User).order_by(User.created_at.desc()).limit(limit).offset(offset)
    if system:
        q = q.where(User.system == system)
    if query:
        like = f"%{query}%"
        q = q.where(
            or_(
                User.first_name.ilike(like),
                User.last_name.ilike(like),
                User.patronymic.ilike(like),
                User.username.ilike(like),
                User.phone.ilike(like),
                User.email.ilike(like),
                User.user_id.ilike(like),
                User.study_group.ilike(like),
            )
        )
    return list(db.execute(q).scalars())


@router.get("/{user_pk}")
def get_user(
    user_pk: int,
    db: Session = Depends(get_db),
    _: CurrentPrincipal = Depends(require_staff),
) -> dict:
    """Карточка пользователя: профиль + история чата + история заявок (§8.5)."""
    user = db.get(User, user_pk)
    if user is None:
        raise not_found("Пользователь не найден")

    # joinedload по relationship Message.replied_by_admin — чтобы не было N+1
    # при сериализации MessageOut.replied_by_admin_name.
    messages = list(
        db.execute(
            select(Message)
            .options(selectinload(Message.replied_by_admin))
            .where(Message.user_id == user.id)
            .order_by(Message.created_at.desc())
            .limit(_USER_MESSAGES_LIMIT)
        ).scalars()
    )
    messages.reverse()  # отдаём по возрастанию created_at

    submissions = list(
        db.execute(
            select(FormSubmission)
            .where(FormSubmission.user_id == user.id)
            .order_by(FormSubmission.created_at.desc())
        ).scalars()
    )

    return {
        "user": UserSummary.model_validate(user, from_attributes=True).model_dump(mode="json"),
        "messages": [
            MessageOut.model_validate(m, from_attributes=True).model_dump(mode="json")
            for m in messages
        ],
        "submissions": [
            SubmissionOut.model_validate(s, from_attributes=True).model_dump(mode="json")
            for s in submissions
        ],
    }


def _user_belongs_to_admin(db: Session, user: User, admin_id: int | None) -> bool:
    """True, если этот user — «теневой» аккаунт текущего админа (тот же max_user_id).

    Пользователи (User) и сотрудники (Admin) — разные таблицы. Но если админ
    зашёл когда-то и как студент, у него есть и тот, и другой профиль с одинаковым
    max_user_id. Защитимся от случайного локаута администратора через эту запись.
    """
    if admin_id is None:
        return False
    admin = db.get(Admin, admin_id)
    if admin is None:
        return False
    return user.user_id == admin.max_user_id


@router.patch(
    "/{user_pk}/ban",
    response_model=UserSummary,
    dependencies=[Depends(_ban_rl)],
)
def patch_ban(
    user_pk: int,
    payload: BanPatchIn,
    db: Session = Depends(get_db),
    p: CurrentPrincipal = Depends(require_admin),
) -> User:
    """Управление блокировками пользователя (только админ).

    Можно ставить/снимать любую комбинацию из ban_chat / ban_forms / ban_app
    и опционально задавать причину для каждой. Поля, не переданные в теле,
    остаются без изменений.

    Защиты:
      - админ не может банить «свой» user-аккаунт (тот же max_user_id);
      - в Pydantic-схеме BanPatchIn нет посторонних полей (защита от set чужих полей).
    """
    user = db.get(User, user_pk)
    if user is None:
        raise not_found("Пользователь не найден")

    if _user_belongs_to_admin(db, user, p.admin_id):
        raise forbidden(
            "Нельзя выставлять блокировку на собственный аккаунт",
            code="self_ban_forbidden",
        )

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(user, k, v)

    db.commit()
    db.refresh(user)
    return user
