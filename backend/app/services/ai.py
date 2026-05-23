
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
import pymorphy3

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.config import settings
from ..models.kb import KbDocument

log = logging.getLogger(__name__)
morph = pymorphy3.MorphAnalyzer()

STOPWORDS = {
    "и", "в", "на", "с", "по", "для", "не", "что", "как", "это",
    "из", "от", "до", "за", "при", "под", "над", "или", "но", "а",
    "то", "же", "бы", "ли", "уже", "еще", "ещё", "будет", "быть", "из-за"
}

ACTION_LEMMAS = {
    "помочь", "хотеть", "нужный", "надо", "попросить",
    "записать", "связать", "соединить", "позвонить", "написать",
    "передать", "сотрудник", "менеджер", "специалист", "человек"
}

def lemmatize(text: str) -> set[str]:
    """Токенизация + лемматизация + фильтр стоп-слов."""
    words = re.findall(r"[а-яёa-z]+", text.lower())
    result = set()
    for word in words:
        if word in STOPWORDS:
            continue
        lemma = morph.parse(word)[0].normal_form
        result.add(lemma)
    return result


@dataclass
class KbHit:
    document_id: int
    topic: str
    answer: str
    score: float


def find_answer(db: Session, text: str) -> KbHit | None:
    if not text or settings.AI_PROVIDER != "kb_local":
        return None

    user_lemmas = lemmatize(text)

    if not user_lemmas:
        return None

    if user_lemmas & ACTION_LEMMAS:
        return None
    
    best: KbHit | None = None

    for doc in db.execute(
        select(KbDocument).where(KbDocument.is_active.is_(True))
    ).scalars():
        
        tag_lemmas = {
            lemma
            for t in (doc.tags or [])
            for lemma in lemmatize(t)
        }
        topic_lemmas = lemmatize(doc.topic)
        candidate_lemmas = tag_lemmas | topic_lemmas

        overlap = user_lemmas & candidate_lemmas
        if not overlap:
            continue

        score = (2 * len(overlap)) / (len(user_lemmas) + len(candidate_lemmas))
        print(f"Document {doc.id} overlap: {overlap}, score: {score:.2f}")
        if best is None or score > best.score:
            best = KbHit(
                document_id=doc.id,
                topic=doc.topic,
                answer=doc.content,
                score=score,
            )

    if best and best.score >= 0.15:  
        return best
    return None

def classify(text: str) -> str:
    """Очень грубая классификация для UI/аналитики."""
    if not text:
        return "empty"
    t = text.lower()
    if any(k in t for k in ("справк", "документ", "certificate")):
        return "certificate"
    if any(k in t for k in ("стипенди", "оплат", "плат", "scholarship")):
        return "payment"
    if any(k in t for k in ("общежит", "dorm")):
        return "dorm"
    return "general"
