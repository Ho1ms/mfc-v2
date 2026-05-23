from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...core.errors import not_found
from ...db.session import get_db
from ...models.user import User
from ...schemas.user import ProfileOut, ProfilePatchIn, RutLinkOut
from ...services.rate_limit import rate_limit
from ..deps import CurrentPrincipal, require_student

router = APIRouter()

_profile_rl = rate_limit("profile_update", limit=30, window_seconds=60)


@router.get("", response_model=ProfileOut)
def get_profile(
    db: Session = Depends(get_db),
    p: CurrentPrincipal = Depends(require_student),
) -> User:
    user = db.get(User, p.user_id)
    if user is None:
        raise not_found("Профиль не найден")
    return user


@router.put("", response_model=ProfileOut, dependencies=[Depends(_profile_rl)])
def update_profile(
    payload: ProfilePatchIn,
    db: Session = Depends(get_db),
    p: CurrentPrincipal = Depends(require_student),
) -> User:
    user = db.get(User, p.user_id)
    if user is None:
        raise not_found("Профиль не найден")

    for k, v in payload.model_dump(exclude_unset=True).items():
        if isinstance(v, str):
            v = v.strip() or None
        setattr(user, k, v)

    db.commit()
    db.refresh(user)
    return user


@router.post("/rut/link", response_model=RutLinkOut)
def link_rut(_: CurrentPrincipal = Depends(require_student)) -> RutLinkOut:
    """Заглушка табельного номера РУТ (МИИТ) — функция «в разработке» (§9.6)."""
    return RutLinkOut()
