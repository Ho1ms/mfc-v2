from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ...core.errors import not_found
from ...db.session import get_db
from ...models.form import FormField, FormTemplate
from ...schemas.form import (
    FormFieldIn,
    FormFieldOut,
    FormFieldPatch,
    FormTemplateDetailed,
    FormTemplateIn,
    FormTemplateOut,
    FormTemplatePatch,
)
from ...services.ws_hub import hub, staff_room
from ..deps import CurrentPrincipal, get_current_principal, require_admin

router = APIRouter()


async def _broadcast_forms_changed() -> None:
    await hub.broadcast(staff_room(), {"type": "forms_changed"})


@router.get("", response_model=list[FormTemplateOut])
def list_forms(
    db: Session = Depends(get_db),
    p: CurrentPrincipal = Depends(get_current_principal),
) -> list[FormTemplate]:
    """Студент видит только активные, админ/сотрудник — все."""
    q = select(FormTemplate).order_by(FormTemplate.order, FormTemplate.id)
    if p.role == "student":
        q = q.where(FormTemplate.is_active.is_(True))
    return list(db.execute(q).scalars())


@router.get("/{form_id}", response_model=FormTemplateDetailed)
def get_form(
    form_id: int,
    db: Session = Depends(get_db),
    p: CurrentPrincipal = Depends(get_current_principal),
) -> FormTemplate:
    q = (
        select(FormTemplate)
        .options(selectinload(FormTemplate.fields))
        .where(FormTemplate.id == form_id)
    )
    tpl = db.execute(q).scalar_one_or_none()
    if tpl is None:
        raise not_found("Форма не найдена")
    if p.role == "student" and not tpl.is_active:
        raise not_found("Форма не найдена")
    return tpl


@router.get("/{form_id}/fields", response_model=list[FormFieldOut])
def list_form_fields(
    form_id: int,
    db: Session = Depends(get_db),
    p: CurrentPrincipal = Depends(get_current_principal),
) -> list[FormField]:
    tpl = db.get(FormTemplate, form_id)
    if tpl is None:
        raise not_found("Форма не найдена")

    q = select(FormField).where(FormField.form_template_id == form_id).order_by(
        FormField.order, FormField.id
    )
    if p.role == "student":
        q = q.where(FormField.is_active.is_(True))
    return list(db.execute(q).scalars())


@router.post("", response_model=FormTemplateOut, status_code=201)
async def create_form(
    payload: FormTemplateIn,
    db: Session = Depends(get_db),
    admin: CurrentPrincipal = Depends(require_admin),
) -> FormTemplate:
    tpl = FormTemplate(
        name=payload.name,
        description=payload.description,
        is_active=payload.is_active,
        order=payload.order,
        reply_on_accept=payload.reply_on_accept,
        created_by=admin.admin_id,
    )
    db.add(tpl)
    db.commit()
    db.refresh(tpl)
    await _broadcast_forms_changed()
    return tpl


@router.patch("/{form_id}", response_model=FormTemplateOut)
async def patch_form(
    form_id: int,
    payload: FormTemplatePatch,
    db: Session = Depends(get_db),
    _: CurrentPrincipal = Depends(require_admin),
) -> FormTemplate:
    tpl = db.get(FormTemplate, form_id)
    if tpl is None:
        raise not_found("Форма не найдена")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(tpl, k, v)
    db.commit()
    db.refresh(tpl)
    await _broadcast_forms_changed()
    return tpl


@router.delete("/{form_id}", status_code=204)
async def delete_form(
    form_id: int,
    db: Session = Depends(get_db),
    _: CurrentPrincipal = Depends(require_admin),
):
    tpl = db.get(FormTemplate, form_id)
    if tpl is None:
        raise not_found("Форма не найдена")
    db.delete(tpl)
    db.commit()
    await _broadcast_forms_changed()


# ───────── Админ: CRUD полей ─────────


@router.post("/{form_id}/fields", response_model=FormFieldOut, status_code=201)
async def create_field(
    form_id: int,
    payload: FormFieldIn,
    db: Session = Depends(get_db),
    _: CurrentPrincipal = Depends(require_admin),
) -> FormField:
    tpl = db.get(FormTemplate, form_id)
    if tpl is None:
        raise not_found("Форма не найдена")
    f = FormField(form_template_id=form_id, **payload.model_dump())
    db.add(f)
    db.commit()
    db.refresh(f)
    await _broadcast_forms_changed()
    return f


@router.patch("/{form_id}/fields/{field_id}", response_model=FormFieldOut)
async def patch_field(
    form_id: int,
    field_id: int,
    payload: FormFieldPatch,
    db: Session = Depends(get_db),
    _: CurrentPrincipal = Depends(require_admin),
) -> FormField:
    f = db.get(FormField, field_id)
    if f is None or f.form_template_id != form_id:
        raise not_found("Поле не найдено")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(f, k, v)
    db.commit()
    db.refresh(f)
    await _broadcast_forms_changed()
    return f


@router.delete("/{form_id}/fields/{field_id}", status_code=204)
async def delete_field(
    form_id: int,
    field_id: int,
    db: Session = Depends(get_db),
    _: CurrentPrincipal = Depends(require_admin),
):
    f = db.get(FormField, field_id)
    if f is None or f.form_template_id != form_id:
        raise not_found("Поле не найдено")
    db.delete(f)
    db.commit()
    await _broadcast_forms_changed()
