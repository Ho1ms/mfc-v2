"""Заполнение БД демо-данными.

Запускается через `make seed` (`python -m app.db.seed` внутри контейнера backend).
Идемпотентно: повторный запуск не создаёт дубликаты (проверка по уникальным полям).
"""

from __future__ import annotations

import logging
import os
from datetime import date, datetime, timezone

from sqlalchemy import select

from ..models.admin import Admin
from ..models.enums import (
    AdminRoleEnum,
    FieldTypeEnum,
    SubmissionStatusEnum,
    SystemEnum,
)
from ..models.form import FormField, FormTemplate
from ..models.kb import KbDocument, KbFaq
from ..models.settings import AppSetting
from ..models.submission import FormSubmission, SubmissionStatusHistory
from ..models.user import User
from .session import SessionLocal

log = logging.getLogger(__name__)


def _ensure_admin(db, *, max_user_id: str, full_name: str, role: AdminRoleEnum) -> Admin:
    admin = db.execute(select(Admin).where(Admin.max_user_id == max_user_id)).scalar_one_or_none()
    if admin:
        return admin
    admin = Admin(max_user_id=max_user_id, full_name=full_name, role=role, is_active=True)
    db.add(admin)
    db.flush()
    return admin


def _ensure_form(db, *, name: str, description: str, order: int) -> FormTemplate:
    f = db.execute(select(FormTemplate).where(FormTemplate.name == name)).scalar_one_or_none()
    if f:
        return f
    f = FormTemplate(name=name, description=description, is_active=True, order=order)
    db.add(f)
    db.flush()
    return f


def _ensure_field(
    db,
    *,
    form_id: int,
    label: str,
    type: FieldTypeEnum,
    order: int,
    is_required: bool = False,
    regexp: str | None = None,
    min_value: str | None = None,
    max_value: str | None = None,
    default_value: str | None = None,
    profile_key: str | None = None,
) -> FormField:
    existing = db.execute(
        select(FormField).where(FormField.form_template_id == form_id, FormField.label == label)
    ).scalar_one_or_none()
    if existing:
        return existing
    f = FormField(
        form_template_id=form_id,
        label=label,
        type=type,
        order=order,
        is_required=is_required,
        regexp=regexp,
        min_value=min_value,
        max_value=max_value,
        default_value=default_value,
        profile_key=profile_key,
        is_active=True,
    )
    db.add(f)
    db.flush()
    return f


def _ensure_user(db, *, user_id: str, system: SystemEnum, **kwargs) -> User:
    u = db.execute(
        select(User).where(User.user_id == user_id, User.system == system)
    ).scalar_one_or_none()
    if u:
        return u
    u = User(user_id=user_id, system=system, **kwargs)
    db.add(u)
    db.flush()
    return u


def _ensure_faq(db, *, question: str, answer: str, order: int, **kwargs) -> KbFaq:
    existing = db.execute(select(KbFaq).where(KbFaq.question == question)).scalar_one_or_none()
    if existing:
        return existing
    item = KbFaq(question=question, answer=answer, order=order, **kwargs)
    db.add(item)
    db.flush()
    return item


def _ensure_kb(db, *, topic: str, content: str, tags: list[str]) -> KbDocument:
    existing = db.execute(select(KbDocument).where(KbDocument.topic == topic)).scalar_one_or_none()
    if existing:
        return existing
    doc = KbDocument(topic=topic, content=content, tags=tags, is_active=True)
    db.add(doc)
    db.flush()
    return doc


def _ensure_setting(db, *, key: str, value: str) -> AppSetting:
    s = db.get(AppSetting, key)
    if s:
        return s
    s = AppSetting(key=key, value=value)
    db.add(s)
    db.flush()
    return s


def run() -> None:
    with SessionLocal() as db:
        admin = _ensure_admin(
            db,
            max_user_id=os.getenv("SEED_ADMIN_MAX_USER_ID", "admin-1"),
            full_name="Екатерина Карпова",
            role=AdminRoleEnum.admin,
        )
        _ensure_admin(
            db,
            max_user_id=os.getenv("SEED_EMPLOYEE_MAX_USER_ID", "employee-1"),
            full_name="Иван Соколов",
            role=AdminRoleEnum.employee,
        )

        # Формы
        f_certificate = _ensure_form(
            db,
            name="Справка об обучении",
            description="Стандартная справка о факте обучения",
            order=1,
        )
        _ensure_field(
            db, form_id=f_certificate.id, label="Фамилия", type=FieldTypeEnum.string, order=1,
            is_required=True, profile_key="last_name", regexp=r"^[А-Яа-яA-Za-zЁё\- ]{1,80}$",
        )
        _ensure_field(
            db, form_id=f_certificate.id, label="Имя", type=FieldTypeEnum.string, order=2,
            is_required=True, profile_key="first_name",
        )
        _ensure_field(
            db, form_id=f_certificate.id, label="Отчество", type=FieldTypeEnum.string, order=3,
            is_required=False, profile_key="patronymic",
        )
        _ensure_field(
            db, form_id=f_certificate.id, label="Группа", type=FieldTypeEnum.string, order=4,
            is_required=True, profile_key="study_group",
        )
        _ensure_field(
            db, form_id=f_certificate.id, label="Дата рождения", type=FieldTypeEnum.date,
            order=5, is_required=True, profile_key="birth_date",
            min_value="1950-01-01", max_value=date.today().isoformat(),
        )
        _ensure_field(
            db, form_id=f_certificate.id, label="Количество экземпляров", type=FieldTypeEnum.number,
            order=6, is_required=True, min_value="1", max_value="5", default_value="1",
        )
        _ensure_field(
            db, form_id=f_certificate.id, label="Нужен электронный экземпляр", type=FieldTypeEnum.checkbox,
            order=7, default_value="false",
        )

        f_dorm = _ensure_form(db, name="Справка для общежития", description="Для предоставления в общежитие", order=2)
        _ensure_field(
            db, form_id=f_dorm.id, label="Фамилия", type=FieldTypeEnum.string, order=1,
            is_required=True, profile_key="last_name",
        )
        _ensure_field(
            db, form_id=f_dorm.id, label="Имя", type=FieldTypeEnum.string, order=2,
            is_required=True, profile_key="first_name",
        )
        _ensure_field(
            db, form_id=f_dorm.id, label="Группа", type=FieldTypeEnum.string, order=3,
            is_required=True, profile_key="study_group",
        )

        # FAQ
        _ensure_faq(
            db,
            question="Как заказать справку об обучении?",
            answer="Откройте раздел «Подать заявку» в мини-приложении, выберите «Справка об обучении» и заполните форму.",
            order=1,
        )
        _ensure_faq(
            db,
            question="Сколько ждать готовности справки?",
            answer="Обычно справка готова в течение 3 рабочих дней. Точный статус — в разделе «История заявок».",
            order=2,
        )
        _ensure_faq(
            db,
            question="Как привязать аккаунт МИИТ?",
            answer="Функция привязки табельного номера РУТ (МИИТ) пока в разработке. Заполните данные вручную в профиле.",
            order=3,
        )

        # KB документы для AI-ответов
        _ensure_kb(
            db,
            topic="Срок изготовления справки",
            content="Справка об обучении готовится в течение 3 рабочих дней с момента подачи заявки.",
            tags=["справка", "срок", "когда", "готова"],
        )
        _ensure_kb(
            db,
            topic="Какие нужны документы",
            content="Для оформления справки нужен только заполненный профиль (ФИО, группа, дата рождения).",
            tags=["документы", "паспорт", "что нужно"],
        )

        # Тексты бота
        _ensure_setting(
            db,
            key="bot_start_message_ru",
            value=(
                "Привет! Это бот МФЦ РУТ МИИТ. Через мини-приложение вы можете заказать справку, "
                "посмотреть статус заявки или задать вопрос."
            ),
        )
        _ensure_setting(
            db,
            key="bot_start_message_en",
            value=(
                "Hello! This is the RUT MIIT MFC bot. Through the mini-app you can request a certificate, "
                "check the status of your application, or ask a question."
            ),
        )

        # Демо-студент + одна заявка для дашборда
        student = _ensure_user(
            db,
            user_id="demo-student-1",
            system=SystemEnum.max,
            first_name="Алина",
            last_name="Морозова",
            patronymic="Сергеевна",
            username="alina",
            language_code="ru",
            study_group="ТЭСУ-211",
            birth_date=date(2003, 9, 15),
        )

        existing_sub = db.execute(
            select(FormSubmission)
            .where(FormSubmission.user_id == student.id)
            .limit(1)
        ).scalar_one_or_none()
        if existing_sub is None:
            cert_fields = list(
                db.execute(
                    select(FormField)
                    .where(FormField.form_template_id == f_certificate.id)
                    .order_by(FormField.order, FormField.id)
                ).scalars()
            )
            cert_by_label = {f.label: f for f in cert_fields}
            values_map = {
                str(cert_by_label["Фамилия"].id): "Морозова",
                str(cert_by_label["Имя"].id): "Алина",
                str(cert_by_label["Группа"].id): "ТЭСУ-211",
                str(cert_by_label["Дата рождения"].id): "2003-09-15",
                str(cert_by_label["Количество экземпляров"].id): 1.0,
                str(cert_by_label["Нужен электронный экземпляр"].id): False,
            }
            sub = FormSubmission(
                form_template_id=f_certificate.id,
                user_id=student.id,
                values=values_map,
                field_labels={str(f.id): f.label for f in cert_fields if str(f.id) in values_map},
                status=SubmissionStatusEnum.new,
            )
            db.add(sub)
            db.flush()
            db.add(
                SubmissionStatusHistory(
                    submission_id=sub.id,
                    from_status=None,
                    to_status=SubmissionStatusEnum.new,
                    changed_by=None,
                    changed_at=datetime.now(tz=timezone.utc),
                    comment="Демо-заявка из seed",
                )
            )

        db.commit()
        log.info("seed complete: admin=%s student=%s", admin.id, student.id)


if __name__ == "__main__":
    logging.basicConfig(level="INFO", format="%(asctime)s %(levelname)s %(message)s")
    run()
