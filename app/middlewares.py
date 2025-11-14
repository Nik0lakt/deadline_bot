from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .config import Config


class ConfigMiddleware(BaseMiddleware):
    """Инжектит Config в data для всех хендлеров."""
    def __init__(self, config: Config) -> None:
        super().__init__()
        self._config = config

    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: Dict[str, Any],
    ) -> Any:
        data["config"] = self._config
        return await handler(event, data)


class DbSessionMiddleware(BaseMiddleware):
    """Создаёт AsyncSession на время обработки апдейта."""
    def __init__(self, session_maker: async_sessionmaker[AsyncSession]) -> None:
        super().__init__()
        self._session_maker = session_maker

    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: Dict[str, Any],
    ) -> Any:
        async with self._session_maker() as session:
            data["session"] = session
            return await handler(event, data)
