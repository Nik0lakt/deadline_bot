import asyncio
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import load_config
from app.db.base import Base
# ВАЖНО: импортируем модели, чтобы они зарегистрировались в metadata
from app.db import models  # noqa: F401

async def main():
    cfg = load_config()
    engine = create_async_engine(cfg.database_url, echo=False, pool_pre_ping=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print("Таблицы успешно созданы.")

if __name__ == "__main__":
    asyncio.run(main())
