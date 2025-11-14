from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv

def _env_bool(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "y", "on"}

@dataclass(frozen=True)
class Config:
    bot_token: str
    database_url: str
    log_level: str = "INFO"
    daily_digest_hour: int = 9
    notify_done_in_chat: bool = True

def load_config() -> Config:
    # Загружаем .env из текущей рабочей директории (для systemd важен WorkingDirectory)
    load_dotenv()
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not bot_token:
        raise RuntimeError("BOT_TOKEN не задан в окружении / .env")
    if not database_url:
        raise RuntimeError("DATABASE_URL не задан в окружении / .env")

    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    daily_digest_hour = int(os.getenv("DAILY_DIGEST_HOUR", "9"))
    notify_done_in_chat = _env_bool("NOTIFY_DONE_IN_CHAT", True)

    return Config(
        bot_token=bot_token,
        database_url=database_url,
        log_level=log_level,
        daily_digest_hour=daily_digest_hour,
        notify_done_in_chat=notify_done_in_chat,
    )
