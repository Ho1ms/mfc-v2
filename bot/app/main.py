from __future__ import annotations

import asyncio
import logging
import os
import sys
from typing import Any

from .backend import BackendClient
from .config import settings
from .push import consume as push_consume
from maxapi.enums.format import Format
from maxapi.enums.update import UpdateType

log = logging.getLogger(__name__)


def _default_start_text(lang: str) -> str:
    if lang == "ru":
        return (
            "Здравствуйте! Это бот МФЦ РУТ МИИТ.\n"
            "Откройте мини-приложение, чтобы заказать справку или посмотреть статус заявки."
        )
    return (
        "Hello! This is the RUT MIIT MFC bot.\n"
        "Open the mini-app to request a certificate or track your application."
    )


async def _get_start_text(backend: BackendClient, lang: str) -> str:
    key = "bot_start_message_ru" if lang == "ru" else "bot_start_message_en"
    text = await backend.get_setting(key)
    return text or _default_start_text(lang)


async def _run_mock() -> None:
    log.warning("BOT_MODE=mock — only push consumer is running (no MAX polling)")

    class _NoopBot:
        async def send_message(self, **kwargs: Any) -> None:
            log.info("[push mock] %s", kwargs)

    await push_consume(_NoopBot())


def _extract_attachments(body: Any) -> list[dict[str, Any]] | None:
   
    if body is None:
        return None
    raw = getattr(body, "attachments", None) or []
    out: list[dict[str, Any]] = []
    for att in raw:
        t = getattr(att, "type", None)
        t = t.value if hasattr(t, "value") else t
        item: dict[str, Any] = {"type": t}
        payload = getattr(att, "payload", None)

        if t == "image" and payload is not None:
            item["url"] = getattr(payload, "url", None)
            item["mime"] = "image/jpeg"
        elif t == "video":
            urls = getattr(att, "urls", None)
            # Берём mp4_720 если есть, иначе любой доступный.
            if urls is not None:
                for k in ("mp4_720", "mp4_480", "mp4_1080", "mp4_360", "mp4_240", "mp4_144", "hls"):
                    v = getattr(urls, k, None)
                    if v:
                        item["url"] = v
                        break
            item["mime"] = "video/mp4"
        elif t == "audio" and payload is not None:
            item["url"] = getattr(payload, "url", None)
            item["mime"] = "audio/mpeg"
            transcription = getattr(att, "transcription", None)
            if transcription:
                item["transcription"] = transcription
        elif t == "file":
            if payload is not None:
                item["url"] = getattr(payload, "url", None)
            item["name"] = getattr(att, "filename", None)
            size = getattr(att, "size", None)
            if size:
                item["size"] = size
            item["mime"] = "application/octet-stream"
        elif t == "sticker" and payload is not None:
            item["url"] = getattr(payload, "url", None)
            item["mime"] = "image/webp"
        else:
            continue

        if item.get("url"):
            out.append(item)
    return out or None


async def run_polling(bot, dp):
    await dp.start_polling(bot)

async def run_webhook(bot, dp):
    await bot.subscribe_webhook(
        url='https://demo.bot.wish-edu.ru/', 
        update_types=[UpdateType.MESSAGE_CREATED, UpdateType.MESSAGE_CALLBACK, UpdateType.BOT_STARTED], 
        secret="ASDgdfsag3q4534523"
    )
    await dp.handle_webhook(bot, host='0.0.0.0', port=8080)
    await bot.unsubscribe_webhook(url="https://demo.bot.wish-edu.ru/")

async def _run_live() -> None:
    try:
        from maxapi import Bot, Dispatcher  
        from maxapi.types import ( 
            BotStarted,
            Command,
            CommandStart,
            MessageCreated,
            OpenAppButton,
        )
        from maxapi.utils.inline_keyboard import InlineKeyboardBuilder  
    except ImportError as e:
        log.error("maxapi not installed (%s) — falling back to mock", e)
        await _run_mock()
        return

    backend = BackendClient()
    bot = Bot(settings.MAX_BOT_TOKEN)
    dp = Dispatcher()

    try:
        me = await bot.get_me()  
        log.info("MAX bot connected: @%s (id=%s)", getattr(me, "username", "?"), getattr(me, "user_id", "?"))
    except Exception as e:  # noqa: BLE001
        log.warning("get_me failed: %s", e)

    def _build_miniapp_keyboard(lang: str) -> list[Any]:
        builder = InlineKeyboardBuilder()
        text = "Открыть мини-приложение" if lang == "ru" else "Open the mini-app"
        builder.row(
            OpenAppButton(
                text=text,
                web_app=bot.me.username,  
                contact_id=bot.me.user_id, 
            ),
        )
        return [builder.as_markup()]

    @dp.bot_started()
    async def on_bot_started(event: BotStarted) -> None: 

        lang = getattr(event, "user_locale", "ru")
        text = await _get_start_text(backend, lang)
        try:
            await event.bot.send_message(
                chat_id=event.chat_id,
                text=text,
                attachments=_build_miniapp_keyboard(lang),
                format=Format.HTML
            )
        except Exception as e:  
            log.warning("on_bot_started send failed: %s", e)

    @dp.message_created(CommandStart())  
    async def on_start(event: MessageCreated) -> None:  
        lang = getattr(event, "user_locale", "ru")
        print(lang)
        text = await _get_start_text(backend, lang)
        try:
            await event.message.answer(
                text=text,
                attachments=_build_miniapp_keyboard(lang),
            )
        except Exception as e: 
            log.warning("/start answer failed: %s", e)

    @dp.message_created(Command("miniapp"))  
    async def on_miniapp(event: MessageCreated) -> None: 
        lang = getattr(event, "user_locale", "ru")
        try:
            await event.message.answer(
                text=("Откройте мини-приложение:" if lang == "ru" else "Open the mini-app:"),
                attachments=_build_miniapp_keyboard(lang),
            )
        except Exception as e:  
            log.warning("/miniapp answer failed: %s", e)

    @dp.message_created(Command("id"))  
    async def on_id(event: MessageCreated) -> None: 
        user_id = getattr(event.from_user, "user_id", None) or "—"
        try:
            await event.message.answer(
                text=(
                    f"Ваш MAX user_id: `{user_id}`\n"
                ),
            )
        except Exception as e:  
            log.warning("/id answer failed: %s", e)

    @dp.message_created()  
    async def on_message(event: MessageCreated) -> None: 
        user = event.from_user
        message = event.message

        text = getattr(message, "text", None) or getattr(getattr(message, "body", None), "text", None)
        external_id = None
        body = getattr(message, "body", None)
        if body is not None:
            external_id = str(getattr(body, "mid", "") or "") or None

        if not user or not getattr(user, "user_id", None):
            return

        attachments_out = _extract_attachments(body)

        res = await backend.ingress_message(
            user_id=str(user.user_id),
            system="max",
            text=text,
            external_id=external_id,
            language_code=getattr(user, "language_code", None),
            first_name=getattr(user, "first_name", None),
            last_name=getattr(user, "last_name", None),
            username=getattr(user, "username", None),
            attachments=attachments_out,
        )

        ai_answer = (res or {}).get("ai_answer")
        if ai_answer:
            try:
                await event.message.answer(ai_answer, format=Format.HTML)
            except Exception as e:  
                log.warning("ai answer send failed: %s", e)

    push_task = asyncio.create_task(push_consume(bot))
    try:
        if settings.USE_WEBHOOK:
            await run_webhook(bot, dp)
        else:             
            await run_polling(bot, dp)
    finally:
        push_task.cancel()
        try:
            await push_task
        except asyncio.CancelledError:
            pass
        except Exception as e:  
            log.debug("push task ended with: %s", e)
        await backend.aclose()




def main() -> None:
    logging.basicConfig(
        level=os.getenv("APP_LOG_LEVEL", settings.APP_LOG_LEVEL),
        format="%(asctime)s %(levelname)-7s %(name)s :: %(message)s",
        stream=sys.stdout,
    )
    
    if settings.BOT_MODE == "live" and settings.MAX_BOT_TOKEN:
        asyncio.run(_run_live())
    else:
        if settings.BOT_MODE == "live":
            log.warning("BOT_MODE=live, но MAX_BOT_TOKEN пустой — переключаюсь в mock")
        asyncio.run(_run_mock())


if __name__ == "__main__":
    main()
