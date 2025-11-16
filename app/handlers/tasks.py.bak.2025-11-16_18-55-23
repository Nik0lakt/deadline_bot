from __future__ import annotations

from datetime import date, timedelta
from typing import List

from aiogram import Router, types, F
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import Config
from app.db.models import Task, Chat
from app.services.tasks import (
    upsert_user_from_tg,
    get_or_create_chat,
    get_or_stub_user_by_username,
    create_task,
    fetch_open_tasks_for_user,
    fetch_tasks_today,
    fetch_tasks_week,
    fetch_tasks_overdue,
    mark_task_done,
)
from app.utils.parsing import parse_task_command, ParseError

router = Router(name="tasks")

def _fmt_task_line(task: Task, chat_title: str | None) -> str:
    d = task.deadline.strftime("%d.%m.%Y")
    chat_part = f", чат: {chat_title}" if chat_title else ""
    return f"#{task.id} — {task.title} (до {d}{chat_part})"


@router.message(Command("task"), F.chat.type.in_({"group", "supergroup"}))
async def task_create_group(message: types.Message, session: AsyncSession, config: Config):
    """Создание задачи из группового чата."""
    raw = message.text or message.caption or ""
    try:
        data = parse_task_command(raw)
    except ParseError as e:
        return await message.reply(
            f"❌ {e}\nПример: `/task сделать лендинг до 20.11 @username`",
            parse_mode="HTML",
        )

    # Создатель и чат
    creator = await upsert_user_from_tg(session, message.from_user)
    chat = await get_or_create_chat(session, message.chat)
    # Исполнитель (по username, возможно заглушка)
    assignee = await get_or_stub_user_by_username(session, data.assignee_username)

    # Создаём задачу
    task = await create_task(
        session,
        chat=chat,
        creator=creator,
        assignee=assignee,
        title=data.title,
        deadline=data.deadline,
        origin_message_id=message.message_id,
    )
    await session.commit()

    # Ответ в чат
    deadline_str = data.deadline.strftime("%d.%m.%Y")
    resp = (
        f"✅ Задача #{task.id} создана\n"
        f"*Что:* {task.title}\n"
        f"*Кому:* @{assignee.username if assignee.username else 'unknown'}\n"
        f"*Дедлайн:* {deadline_str}"
    )
    await message.reply(resp, parse_mode="HTML")

    # ЛС исполнителю (если он писал /start и у нас есть tg_id)
    if assignee.tg_id:
        try:
            await message.bot.send_message(
                assignee.tg_id,
                f"Тебе назначена задача #{task.id}: «{task.title}» к {deadline_str}.",
            )
        except Exception:
            # Например, бот в бане у пользователя — не фейлимся
            pass


# --- Личные команды просмотра ---

async def _ensure_user(session: AsyncSession, tg_user: types.User):
    """Гарантируем, что пользователь есть в БД."""
    user = await upsert_user_from_tg(session, tg_user)
    await session.commit()
    return user


@router.message(Command("my"), F.chat.type == "private")
async def my_tasks(message: types.Message, session: AsyncSession):
    user = await _ensure_user(session, message.from_user)
    tasks = await fetch_open_tasks_for_user(session, user)

    if not tasks:
        return await message.answer("У тебя нет открытых задач.")

    # Подтягиваем названия чатов
    chat_ids = sorted({t.chat_id for t in tasks})
    from sqlalchemy import select
    q = await session.execute(select(Chat).where(Chat.id.in_(chat_ids)))
    chats_map = {c.id: c.title for c in q.scalars().all()}

    lines = ["Твои задачи:"]
    for t in tasks:
        lines.append(_fmt_task_line(t, chats_map.get(t.chat_id)))
    await message.answer("\n".join(lines))


@router.message(Command("today"), F.chat.type == "private")
async def today_tasks(message: types.Message, session: AsyncSession):
    user = await _ensure_user(session, message.from_user)
    tasks = await fetch_tasks_today(session, user, date.today())
    if not tasks:
        return await message.answer("На сегодня задач нет.")
    chat_ids = sorted({t.chat_id for t in tasks})
    q = await session.execute(select(Chat).where(Chat.id.in_(chat_ids)))
    chats_map = {c.id: c.title for c in q.scalars().all()}

    lines = ["Задачи на сегодня:"]
    for t in tasks:
        lines.append(_fmt_task_line(t, chats_map.get(t.chat_id)))
    await message.answer("\n".join(lines))


@router.message(Command("week"), F.chat.type == "private")
async def week_tasks(message: types.Message, session: AsyncSession):
    user = await _ensure_user(session, message.from_user)
    tasks = await fetch_tasks_week(session, user, date.today())
    if not tasks:
        return await message.answer("На ближайшую неделю задач нет.")
    chat_ids = sorted({t.chat_id for t in tasks})
    q = await session.execute(select(Chat).where(Chat.id.in_(chat_ids)))
    chats_map = {c.id: c.title for c in q.scalars().all()}

    lines = ["Задачи на неделю:"]
    for t in tasks:
        lines.append(_fmt_task_line(t, chats_map.get(t.chat_id)))
    await message.answer("\n".join(lines))


@router.message(Command("overdue"), F.chat.type == "private")
async def overdue_tasks(message: types.Message, session: AsyncSession):
    user = await _ensure_user(session, message.from_user)
    tasks = await fetch_tasks_overdue(session, user, date.today())
    if not tasks:
        return await message.answer("Просроченных задач нет 🎉")
    chat_ids = sorted({t.chat_id for t in tasks})
    q = await session.execute(select(Chat).where(Chat.id.in_(chat_ids)))
    chats_map = {c.id: c.title for c in q.scalars().all()}

    lines = ["Просроченные задачи:"]
    for t in tasks:
        d = t.deadline.strftime("%d.%m.%Y")
        lines.append(f"#{t.id} — {t.title} (дедлайн: {d}, чат: {chats_map.get(t.chat_id)})")
    await message.answer("\n".join(lines))


# --- Закрытие задачи ---

@router.message(Command("done"))
async def done_cmd(message: types.Message, session: AsyncSession, config: Config):
    raw = (message.text or "").strip()
    parts = raw.split(maxsplit=1)
    if len(parts) < 2:
        return await message.reply("Использование: `/done <id>`", parse_mode="HTML")
    try:
        task_id = int(parts[1].strip())
    except ValueError:
        return await message.reply("ID должен быть числом.", parse_mode="HTML")

    closer = await upsert_user_from_tg(session, message.from_user)
    task, result = await mark_task_done(session, task_id=task_id, closer=closer, allow_creator_close=True)
    if result != "ok":
        await session.rollback()
        return await message.reply(f"❌ {result}")

    await session.commit()
    await message.reply(f"✅ Задача #{task.id} отмечена как выполненная")

    # Уведомление в исходный чат (опционально)
    if config.notify_done_in_chat and task and task.chat:
        try:
            await message.bot.send_message(
                task.chat.tg_chat_id,
                f"✅ Задача #{task.id} выполнена @{closer.username or closer.tg_id}",
            )
        except Exception:
            pass
