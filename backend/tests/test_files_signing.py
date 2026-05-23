"""Тесты подписанных URL для вложений."""

import time

import pytest

from app.core.errors import ApiError
from app.services import files as files_svc


def test_verify_ok_for_valid_signature():
    url = files_svc.make_signed_url(42, ttl_seconds=60)
    # Извлекаем exp и sig
    qs = url.split("?", 1)[1]
    params = dict(p.split("=", 1) for p in qs.split("&"))
    files_svc.verify_signed(42, int(params["exp"]), params["sig"])  # не должно бросать


def test_verify_rejects_expired():
    sig = files_svc._sign(42, int(time.time()) - 10)  # уже истёк
    with pytest.raises(ApiError) as ei:
        files_svc.verify_signed(42, int(time.time()) - 10, sig)
    assert ei.value.detail["code"] == "link_expired"


def test_verify_rejects_wrong_signature():
    with pytest.raises(ApiError) as ei:
        files_svc.verify_signed(42, int(time.time()) + 60, "deadbeef")
    assert ei.value.detail["code"] == "bad_signature"


def test_verify_rejects_wrong_id():
    """Подпись от id=42 не должна валидироваться для id=43."""
    url = files_svc.make_signed_url(42, ttl_seconds=60)
    qs = url.split("?", 1)[1]
    params = dict(p.split("=", 1) for p in qs.split("&"))
    with pytest.raises(ApiError) as ei:
        files_svc.verify_signed(43, int(params["exp"]), params["sig"])
    assert ei.value.detail["code"] == "bad_signature"
