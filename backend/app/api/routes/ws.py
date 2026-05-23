"""WebSocket-чат (§8.3 ТЗ). Подписки на комнаты:

- staff — все сотрудники (новые тикеты, бейдж счётчика)
- user:<id> — конкретный разговор (студент + сотрудник)
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from ...core.security import decode_token
from ...db.session import SessionLocal
from ...models.user import User
from ...services.ws_hub import hub, staff_room, user_room

log = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/chat")
async def ws_chat(
    websocket: WebSocket,
    token: str = Query(...),
    user_pk: int | None = Query(default=None),
) -> None:
  
    try:
        payload = decode_token(token)
    except Exception:  # noqa: BLE001
        await websocket.close(code=4401)
        return

    role = payload.get("role")
    student_pk = payload.get("user_pk")
    rooms: list[str] = []

    if role == "student":
        if not student_pk:
            await websocket.close(code=4401)
            return
        with SessionLocal() as db:
            user = db.get(User, int(student_pk))
            if user and user.ban_app:
                await websocket.close(code=4403)
                return
        print("ADD ROOM", student_pk)
        rooms.append(user_room(int(student_pk)))
    elif role in ("admin", "employee"):
        rooms.append(staff_room())
        if user_pk:
            rooms.append(user_room(int(user_pk)))
    else:
        await websocket.close(code=4401)
        return

    await websocket.accept()
    for r in rooms:
        await hub.join(r, websocket)
    try:
        await websocket.send_json({"type": "ready", "rooms": rooms})
        while True:
            # Сейчас сервер не принимает входящие — отправка идёт через REST.
            # Просто держим соединение, отбрасывая входящие.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        for r in rooms:
            await hub.leave(r, websocket)
