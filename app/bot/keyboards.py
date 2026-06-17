from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_keyboard() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text=" Мой список")],
        [KeyboardButton(text=" Помощь"), KeyboardButton(text="🗑 Удалить игру")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)