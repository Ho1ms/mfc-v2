from fastapi import APIRouter, Depends
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ...core.errors import not_found
from ...db.session import get_db
from ...models.kb import KbDocument
from ...schemas.kb import KbBulkIn, KbDocumentIn, KbDocumentOut, KbDocumentPatch
from ..deps import CurrentPrincipal, require_admin
from ...services.ai import lemmatize
router = APIRouter()


@router.get("/documents", response_model=list[KbDocumentOut])
def list_documents(
    db: Session = Depends(get_db),
    _: CurrentPrincipal = Depends(require_admin),
) -> list[KbDocument]:
    return list(
        db.execute(select(KbDocument).order_by(KbDocument.created_at.desc())).scalars()
    )

@router.post("/documents", response_model=list[KbDocumentOut])
def upload_documents(
    payload: KbBulkIn,
    db: Session = Depends(get_db),
    p: CurrentPrincipal = Depends(require_admin),
) -> list[KbDocument]:
    """Bulk-загрузка. Если replace=true — затирает существующие документы."""
    if payload.replace:
        db.execute(delete(KbDocument))

    created: list[KbDocument] = []
    for doc in payload.documents:
        d = KbDocument(
            topic=doc.topic,
            content=doc.content,
            tags=doc.tags,
            is_active=doc.is_active,
            uploaded_by=p.admin_id,
        )
        db.add(d)
        created.append(d)
    db.commit()
    for d in created:
        db.refresh(d)
    return created


@router.post("/documents/one", response_model=KbDocumentOut, status_code=201)
def create_document(
    payload: KbDocumentIn,
    db: Session = Depends(get_db),
    p: CurrentPrincipal = Depends(require_admin),
) -> KbDocument:

    tags_lemmas = tuple(lemmatize(" ".join(payload.tags or [])))

    d = KbDocument(
        topic=payload.topic,
        content=payload.content,
        tags=tags_lemmas,
        is_active=payload.is_active,
        uploaded_by=p.admin_id,
    )
    db.add(d)
    db.commit()
    db.refresh(d)

    return d


@router.patch("/documents/{document_id}", response_model=KbDocumentOut)
def patch_document(
    document_id: int,
    payload: KbDocumentPatch,
    db: Session = Depends(get_db),
    _: CurrentPrincipal = Depends(require_admin),
) -> KbDocument:
    d = db.get(KbDocument, document_id)
    if d is None:
        raise not_found("Документ не найден")
    for k, v in payload.model_dump(exclude_unset=True).items():
        if k == "tags" and v is not None:
            v = tuple(lemmatize(" ".join(v)))
        setattr(d, k, v)
    db.commit()
    db.refresh(d)

    return d


@router.delete("/documents/{document_id}", status_code=204)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    _: CurrentPrincipal = Depends(require_admin),
):
    d = db.get(KbDocument, document_id)
    if d is None:
        raise not_found("Документ не найден")
    db.delete(d)
    db.commit()
