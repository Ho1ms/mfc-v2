from __future__ import annotations

import logging
from typing import Any

import httpx

from .config import settings

log = logging.getLogger(__name__)


class BackendClient:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=settings.BOT_INTERNAL_API_URL,
            timeout=20.0,
            headers={"X-Bot-Token": settings.BOT_INTERNAL_API_TOKEN},
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def ingress_message(
        self,
        *,
        user_id: str,
        system: str,
        text: str | None,
        external_id: str | None = None,
        language_code: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        username: str | None = None,
        attachments: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        payload = {
            "user_id": user_id,
            "system": system,
            "text": text,
            "external_id": external_id,
            "language_code": language_code,
            "first_name": first_name,
            "last_name": last_name,
            "username": username,
            "attachments": attachments,
        }
        try:
            r = await self._client.post("/api/messages/ingress", json=payload)
            r.raise_for_status()
            return r.json()
        except httpx.HTTPError as e:
            log.warning("backend ingress failed: %s", e)
            return {}

    async def get_setting(self, key: str) -> str | None:
        try:
            r = await self._client.get(f"/api/settings/{key}")
            r.raise_for_status()
            data = r.json() or {}
            value = data.get("value")
            return value if isinstance(value, str) and value else None
        except httpx.HTTPError as e:
            log.warning("get_setting(%s) failed: %s", key, e)
            return None

    async def fetch_bytes(self, url: str) -> tuple[bytes, str] | None:
       
        try:
            
            r = await self._client.get(url)
            r.raise_for_status()
            return r.content, r.headers.get("content-type", "application/octet-stream")
        except httpx.HTTPError as e:
            log.warning("fetch_bytes(%s) failed: %s", url, e)
            return None
