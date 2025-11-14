import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties

from app.config import load_config
from app.db.session import build_session_maker
from app.services.notifications import send_daily_digests
from app.utils.logging import setup_logging


async def digest_job(session_maker, bot: Bot):
    async with session_maker() as session:
        await send_daily_digests(session, bot)

async def main():
    config = load_config()
    setup_logging(config.log_level)
    logging.info("Запуск планировщика дайджестов")

    session_maker = build_session_maker(config.database_url)
    bot = Bot(token=config.bot_token, default=DefaultBotProperties(parse_mode="HTML"))

    scheduler = AsyncIOScheduler()
    trigger = CronTrigger(hour=config.daily_digest_hour, minute=0)
    scheduler.add_job(digest_job, trigger=trigger, args=[session_maker, bot], name="daily_digest")
    scheduler.start()

    # Блокируемся, пока работает scheduler
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
