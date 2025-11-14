import asyncio

from app.config import load_config
from app.db.base import Base
from app.db.session import build_session_maker

async def _run():
    config = load_config()
    session_maker = build_session_maker(config.database_url)
    async with session_maker() as session:
        # Создаём таблицы через соединение движка
        engine = session.get_bind()
        assert engine is not None
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    print("Таблицы успешно созданы.")

if __name__ == "__main__":
    asyncio.run(_run())
