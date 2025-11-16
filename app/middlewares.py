from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from app.config import Config

class ConfigMiddleware(BaseMiddleware):
    def __init__(self, config: Config) -> None:
        super().__init__()
        self._config = config

    async def __call__(self, handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]], event: Any, data: Dict[str, Any]) -> Any:
        # Пробрасываем конфиг во все хендлеры
        data["config"] = self._config
        return await handler(event, data)


class DbSessionMiddleware(BaseMiddleware):
    """
    Открывает async-сессию на время обработки апдейта.
    Делает commit при успехе и rollback при ошибке.
    """
    def __init__(self, session_maker: async_sessionmaker[AsyncSession]) -> None:
        super().__init__()
        self._session_maker = session_maker

    async def __call__(self, handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]], event: Any, data: Dict[str, Any]) -> Any:
        async with self._session_maker() as session:
            data["session"] = session
            try:
                result = await handler(event, data)
                await session.commit()   # ✅ коммитим все изменения
                return result
            except Exception:
                await session.rollback() # 🔁 откатываем в случае ошибки
                raise
