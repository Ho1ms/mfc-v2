from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_ENV: Literal["development", "staging", "production"] = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    APP_LOG_LEVEL: str = "INFO"
    APP_ROLE: Literal["api", "worker"] = "api"

    JWT_SECRET: str = "change-me"
    JWT_ALG: str = "HS256"
    JWT_EXPIRES_MIN: int = 720

    CORS_ORIGINS: str = ""

    DATABASE_URL: str = "postgresql+psycopg://mfc:mfc@db:5432/mfc"
    REDIS_URL: str = "redis://redis:6379/0"

    # MAX
    MAX_BOT_TOKEN: str = ""
    BEAVERS_BOT_TOKEN: str = ""
    MAX_BOT_USERNAME: str = ""

    PUBLIC_API_URL: str = "http://localhost:8000"
    PUBLIC_MINIAPP_URL: str = "http://localhost:5174"
    PUBLIC_ADMIN_URL: str = "http://localhost:5173"

    TRANSLATION_PROVIDER: Literal["noop"] = "noop"
    AI_PROVIDER: Literal["kb_local"] = "kb_local"

    GOOGLE_SHEETS_MODE: Literal["mock", "live"] = "mock"
    GOOGLE_SHEETS_MOCK_FILE: str = "/app/seed/google_sheets_mock.json"
    GOOGLE_SHEETS_ID: str = ""
    GOOGLE_SHEETS_RANGE: str = "B:C"
    GOOGLE_SHEETS_CREDENTIALS_FILE: str = ""
    MONITORING_INTERVAL_SECONDS: int = 300

    BOT_MODE: Literal["mock", "live"] = "mock"
    BOT_INTERNAL_API_URL: str = "http://backend:8000"
    BOT_INTERNAL_API_TOKEN: str = ""

    DEV_BYPASS_INITDATA: bool = False

    UPLOADS_DIR: str = "/app/uploads"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    def bot_token_for(self, system: str) -> str | None:
        match system:
            case "max":
                return self.MAX_BOT_TOKEN
            case "beavers":
                return self.BEAVERS_BOT_TOKEN
            case _:
                return None
            
    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


_WEAK_SECRET_MARKERS = ("change-me", "example", "secret", "todo", "please")
_WEAK_INTERNAL_TOKEN_DEFAULT = "internal-bot-token-change-me"


class ConfigurationError(RuntimeError):
    """Стартовая ошибка конфигурации — несовместимая для прода настройка."""


def _validate_production(settings: "Settings") -> None:
    errors: list[str] = []

    s = (settings.JWT_SECRET or "").strip()
    if len(s) < 32:
        errors.append("JWT_SECRET слишком короткий (нужно ≥32 символа случайных байт).")
    if any(m in s.lower() for m in _WEAK_SECRET_MARKERS):
        errors.append("JWT_SECRET содержит маркер дефолтного значения — выпустить новый.")

    if settings.DEV_BYPASS_INITDATA:
        errors.append("DEV_BYPASS_INITDATA=true запрещён в production (обход MAX-подписи).")

    if settings.BOT_MODE == "live" and not settings.MAX_BOT_TOKEN.strip():
        errors.append("BOT_MODE=live, но MAX_BOT_TOKEN пуст.")

    internal = (settings.BOT_INTERNAL_API_TOKEN or "").strip()
    if not internal:
        errors.append("BOT_INTERNAL_API_TOKEN пуст — бот сможет писать ingress без аутентификации.")
    elif internal == _WEAK_INTERNAL_TOKEN_DEFAULT or len(internal) < 16:
        errors.append("BOT_INTERNAL_API_TOKEN слишком слабый или равен дефолту.")

    pg = (settings.DATABASE_URL or "")

    if ":mfc@" in pg or ":postgres@" in pg or ":password@" in pg:
        errors.append("DATABASE_URL содержит дефолтный пароль — заменить.")

    if not settings.cors_origins_list:
        errors.append("CORS_ORIGINS пуст в production (фронт не сможет ходить в API).")
    elif any("localhost" in o or "127.0.0.1" in o for o in settings.cors_origins_list):
        errors.append("CORS_ORIGINS содержит localhost — выпилить для production.")

    if errors:
        msg = "Production configuration is unsafe:\n  - " + "\n  - ".join(errors)
        raise ConfigurationError(msg)


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    if s.is_production:
        _validate_production(s)
    return s


settings = get_settings()
