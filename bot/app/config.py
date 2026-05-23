from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict
from os import getenv


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    
    MAX_BOT_TOKEN: str = getenv("MAX_BOT_TOKEN")
    MAX_BOT_USERNAME: str = getenv("MAX_BOT_USERNAME", "rut_mfc_test_bot")

    PUBLIC_MINIAPP_URL: str = "http://localhost:5174"
    PUBLIC_API_URL: str = "http://localhost:8000"

    BOT_MODE: Literal["mock", "live"] = "live"
    BOT_INTERNAL_API_URL: str = "http://backend:8000"
    BOT_INTERNAL_API_TOKEN: str = ""

    REDIS_URL: str = "redis://redis:6379/0"
    APP_LOG_LEVEL: str = "INFO"
    USE_WEBHOOK: bool = False


settings = Settings()
