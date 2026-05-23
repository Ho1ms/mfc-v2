from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...core.errors import not_found
from ...db.session import get_db
from ...models.kb import KbFaq
from ...schemas.kb import FaqIn, FaqOut, FaqPatch
from ..deps import CurrentPrincipal, get_current_principal, require_admin

router = APIRouter()


@router.get("", response_model=list[FaqOut])
def list_faq(
    db: Session = Depends(get_db),
    p: CurrentPrincipal = Depends(get_current_principal),
) -> list[KbFaq]:
    q = select(KbFaq).order_by(KbFaq.order, KbFaq.id)
    if p.role == "student":
        q = q.where(KbFaq.is_active.is_(True))
    return list(db.execute(q).scalars())


@router.post("", response_model=FaqOut, status_code=201)
def create_faq(
    payload: FaqIn,
    db: Session = Depends(get_db),
    _: CurrentPrincipal = Depends(require_admin),
) -> KbFaq:
    faq = KbFaq(**payload.model_dump())
    db.add(faq)
    db.commit()
    db.refresh(faq)
    return faq


@router.patch("/{faq_id}", response_model=FaqOut)
def patch_faq(
    faq_id: int,
    payload: FaqPatch,
    db: Session = Depends(get_db),
    _: CurrentPrincipal = Depends(require_admin),
) -> KbFaq:
    f = db.get(KbFaq, faq_id)
    if f is None:
        raise not_found("FAQ не найден")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(f, k, v)
    db.commit()
    db.refresh(f)
    return f


@router.delete("/{faq_id}", status_code=204)
def delete_faq(
    faq_id: int,
    db: Session = Depends(get_db),
    _: CurrentPrincipal = Depends(require_admin),
):
    f = db.get(KbFaq, faq_id)
    if f is None:
        raise not_found("FAQ не найден")
    db.delete(f)
    db.commit()
