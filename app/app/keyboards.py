from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="/my"), KeyboardButton(text="/today")],
            [KeyboardButton(text="/week"), KeyboardButton(text="/overdue")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Быстрые команды",
    )
