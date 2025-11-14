from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Iterable, List, Optional, Tuple

from aiogram.types import Chat as TgChat, User as TgUser
from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User, Chat, Task


# --- Вспомогательные функции по пользователям/чатам ---

async def upsert_user_from_tg(session: AsyncSession, tg_user: TgUser) -> User:
    """Найти пользователя по tg_id или создать/обновить его профиль."""
    q = await session.execute(select(User).where(User.tg_id == tg_user.id))
    user = q.scalar_one_or_none()
    if user is None:
        user = User(
            tg_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name,
        )
        session.add(user)
        await session.flush()
    else:
        # Обновим основные поля, если изменились
        user.username = tg_user.username
        user.first_name = tg_user.first_name
        user.last_name = tg_user.last_name
        await session.flush()
    return user


async def get_or_create_chat(session: AsyncSession, tg_chat: TgChat) -> Chat:
    q = await session.execute(select(Chat).where(Chat.tg_chat_id == tg_chat.id))
    chat = q.scalar_one_or_none()
    if chat is None:
        chat = Chat(
            tg_chat_id=tg_chat.id,
            title=getattr(tg_chat, "title", None),
            type=tg_chat.type,
        )
        session.add(chat)
        await session.flush()
    else:
        chat.title = getattr(tg_chat, "title", chat.title)
        chat.type = tg_chat.type or chat.type
        await session.flush()
    return chat


async def get_or_stub_user_by_username(session: AsyncSession, username: str) -> User:
    """Получить исполнителя по username, создать заглушку если нет (tg_id=None)."""
    username = username.lower()
    q = await session.execute(select(User).where(User.username.ilike(username)))
    user = q.scalar_one_or_none()
    if user is None:
        user = User(
            tg_id=None,
            username=username,
            first_name=None,
            last_name=None,
        )
        session.add(user)
        await session.flush()
    return user


# --- Операции над задачами ---

async def create_task(
    session: AsyncSession,
    *,
    chat: Chat,
    creator: User,
    assignee: User,
    title: str,
    deadline: date,
    origin_message_id: Optional[int] = None,
    description: Optional[str] = None,
) -> Task:
    task = Task(
        chat_id=chat.id,
        creator_id=creator.id,
        assignee_id=assignee.id,
        title=title,
        description=description,
        deadline=deadline,
        status="open",
        origin_message_id=origin_message_id,
    )
    session.add(task)
    await session.flush()
    return task


async def fetch_open_tasks_for_user(session: AsyncSession, user: User) -> List[Task]:
    q = await session.execute(
        select(Task)
        .where(Task.assignee_id == user.id, Task.status == "open")
        .order_by(Task.deadline.asc(), Task.id.asc())
        .limit(200)
    )
    return list(q.scalars().all())


async def fetch_tasks_today(session: AsyncSession, user: User, today: date) -> List[Task]:
    q = await session.execute(
        select(Task)
        .where(Task.assignee_id == user.id, Task.status == "open", Task.deadline == today)
        .order_by(Task.deadline.asc(), Task.id.asc())
    )
    return list(q.scalars().all())


async def fetch_tasks_week(session: AsyncSession, user: User, today: date) -> List[Task]:
    end = today + timedelta(days=7)
    q = await session.execute(
        select(Task)
        .where(Task.assignee_id == user.id, Task.status == "open", Task.deadline >= today, Task.deadline <= end)
        .order_by(Task.deadline.asc(), Task.id.asc())
    )
    return list(q.scalars().all())


async def fetch_tasks_overdue(session: AsyncSession, user: User, today: date) -> List[Task]:
    q = await session.execute(
        select(Task)
        .where(Task.assignee_id == user.id, Task.status == "open", Task.deadline < today)
        .order_by(Task.deadline.asc(), Task.id.asc())
    )
    return list(q.scalars().all())


async def mark_task_done(
    session: AsyncSession,
    *,
    task_id: int,
    closer: User,
    allow_creator_close: bool = True,
) -> Tuple[Optional[Task], str]:
    """Отмечает задачу выполненной, если closer — исполнитель или (опционально) создатель."""
    q = await session.execute(select(Task).where(Task.id == task_id))
    task = q.scalar_one_or_none()
    if task is None:
        return None, "Задача с таким ID не найдена."

    if task.status != "open":
        return task, f"Задача уже имеет статус '{task.status}'."

    can_close = closer.id == task.assignee_id or (allow_creator_close and closer.id == task.creator_id)
    if not can_close:
        return None, "У вас нет прав закрывать эту задачу."

    task.status = "done"
    task.closed_at = datetime.now(timezone.utc)
    await session.flush()
    return task, "ok"


# --- Выборки для дайджестов ---

async def users_with_open_tasks(session: AsyncSession) -> List[User]:
    # все пользователи, у которых есть открытые задачи и есть tg_id
    q = await session.execute(
        select(User).where(
            User.tg_id.is_not(None)
        ).where(
            User.id.in_(select(Task.assignee_id).where(Task.status == "open"))
        )
    )
    return list(q.scalars().all())
