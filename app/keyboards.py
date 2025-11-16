from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu_kb() -> ReplyKeyboardMarkup:
    # Небольшая «клава» с быстрыми командами
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="/my"), KeyboardButton(text="/today")],
            [KeyboardButton(text="/week"), KeyboardButton(text="/overdue")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Быстрые команды",
    )
