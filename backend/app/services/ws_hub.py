"""Простой in-memory hub для WebSocket-чата сотрудников и mini-app (§8.3 ТЗ).

Сообщения broadcast'ятся:
- staff-каналу (всем подключённым сотрудникам)
- комнате конкретного пользователя `user:<id>` (студент + сотрудник, открывшие диалог)
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict

from fastapi import WebSocket

log = logging.getLogger(__name__)


class WsHub:
    def __init__(self) -> None:
        self._rooms: dict[str, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def join(self, room: str, ws: WebSocket) -> None:
        async with self._lock:
            self._rooms[room].add(ws)

    async def leave(self, room: str, ws: WebSocket) -> None:
        async with self._lock:
            self._rooms[room].discard(ws)
            if not self._rooms[room]:
                self._rooms.pop(room, None)

    async def broadcast(self, room: str, event: dict) -> None:
        sockets: list[WebSocket]
        async with self._lock:
            sockets = list(self._rooms.get(room, ()))
        for ws in sockets:
            try:
                await ws.send_json(event)
            except Exception as e:  # noqa: BLE001
                log.debug("ws send failed: %s", e)


hub = WsHub()


def staff_room() -> str:
    return "staff"


def user_room(user_pk: int) -> str:
    return f"user:{user_pk}"
