from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from app.config import load_config
from app.db.session import build_session_maker
from app.handlers import setup_routers
from app.middlewares import ConfigMiddleware, DbSessionMiddleware
from app.utils.logging import setup_logging


async def main() -> None:
    config = load_config()
    setup_logging(config.log_level)

    logging.getLogger(__name__).info("Старт бота 'Мастер дедлайнов'")

    session_maker = build_session_maker(config.database_url)

    bot = Bot(token=config.bot_token, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()

    # Подключаем роутеры
    setup_routers(dp)

    # Миддлвары для всех апдейтов
    dp.update.middleware(ConfigMiddleware(config))
    dp.update.middleware(DbSessionMiddleware(session_maker))

    # Запускаем polling
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
