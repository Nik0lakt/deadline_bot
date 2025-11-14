from __future__ import annotations

from aiogram import Router, types, F
from aiogram.filters import CommandStart, Command

from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards import main_menu_kb
from app.services.tasks import upsert_user_from_tg, get_or_create_chat

router = Router(name="common")

@router.message(CommandStart(), F.chat.type == "private")
async def start_private(message: types.Message, session: AsyncSession):
    """Регистрация пользователя и краткая инструкция."""
    await upsert_user_from_tg(session, message.from_user)
    await session.commit()

    text = (
        "Привет! Я — *Мастер дедлайнов*.\n\n"
        "Я помогаю создавать задачи с дедлайнами прямо в чатах и следить за ними.\n\n"
        "➕ Создать задачу в группе:\n"
        "`/task сделать лендинг до 20.11 @username`\n"
        "`/task настроить оплату до 2025-11-20 @username`\n\n"
        "📋 Смотреть задачи (в ЛС):\n"
        "`/my` — все открытые\n"
        "`/today` — на сегодня\n"
        "`/week` — на 7 дней вперёд\n"
        "`/overdue` — просроченные\n\n"
        "✅ Отметить выполненной: `/done 123`\n\n"
        "_Важно_: напишите мне `/start`, чтобы я мог присылать личные уведомления."
    )
    await message.answer(text, reply_markup=main_menu_kb(), parse_mode="Markdown")

@router.message(CommandStart(), F.chat.type.in_({"group", "supergroup"}))
async def start_group(message: types.Message, session: AsyncSession):
    """Регистрация группового чата."""
    await get_or_create_chat(session, message.chat)
    await session.commit()
    text = (
        "Привет! Я здесь, чтобы помогать со сроками.\n\n"
        "Создайте задачу так:\n"
        "`/task сделать лендинг до 20.11 @username`\n\n"
        "Чтобы получать личные уведомления — участники должны написать мне `/start` в ЛС."
    )
    await message.reply(text, parse_mode="Markdown")

@router.message(Command("help"))
async def help_cmd(message: types.Message):
    await message.answer(
        "Справка по командам:\n"
        "/task <что> до <дата> @username — создать задачу в чате\n"
        "/my, /today, /week, /overdue — смотреть задачи (в ЛС)\n"
        "/done <id> — отметить задачу выполненной",
        parse_mode="Markdown",
    )
