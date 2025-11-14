from __future__ import annotations

from datetime import date
from typing import List

from aiogram import Bot

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Task, Chat, User
from app.services.tasks import (
    users_with_open_tasks,
    fetch_tasks_today,
    fetch_tasks_overdue,
)


def _fmt_task_line(t: Task, chat: Chat | None = None) -> str:
    d = t.deadline.strftime("%d.%m.%Y")
    chat_part = f", чат: {chat.title}" if chat and chat.title else ""
    return f"#{t.id} — {t.title} (до {d}{chat_part})"


async def _load_chats_for_tasks(session: AsyncSession, tasks: List[Task]) -> dict[int, Chat]:
    # Сопоставим chat_id -> chat одним запросом
    if not tasks:
        return {}
    chat_ids = sorted({t.chat_id for t in tasks})
    from sqlalchemy import select
    q = await session.execute(select(Chat).where(Chat.id.in_(chat_ids)))
    return {c.id: c for c in q.scalars().all()}


async def send_daily_digests(session: AsyncSession, bot: Bot) -> None:
    """Формирует и отправляет пользователям дайджесты задач на сегодня и просроченных."""
    today = date.today()
    users = await users_with_open_tasks(session)

    for user in users:
        if not user.tg_id:
            continue

        tasks_today = await fetch_tasks_today(session, user, today)
        tasks_overdue = await fetch_tasks_overdue(session, user, today)

        chats_map = await _load_chats_for_tasks(session, tasks_today + tasks_overdue)

        lines = []
        if tasks_today:
            lines.append("🎯 Твои задачи на сегодня:")
            for t in tasks_today:
                lines.append(f"{_fmt_task_line(t, chats_map.get(t.chat_id))}")
        if tasks_overdue:
            if lines:
                lines.append("")  # пустая строка-разделитель
            lines.append("⏰ Просрочены:")
            for t in tasks_overdue:
                d = t.deadline.strftime("%d.%m.%Y")
                chat_part = f", чат: {chats_map.get(t.chat_id).title}" if chats_map.get(t.chat_id) else ""
                lines.append(f"#{t.id} — {t.title} (дедлайн: {d}{chat_part})")

        if not lines:
            # Ничего важного — можно не слать сообщение
            continue

        text = "\n".join(lines)
        try:
            await bot.send_message(user.tg_id, text)
        except Exception as e:
            # Например, юзер не писал /start — Forbidden
            import logging
            logging.getLogger(__name__).warning("Не удалось отправить дайджест пользователю %s: %s", user.username, e)
