from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="👨‍🎓Навчання")],
        [KeyboardButton(text="📝Модульні тести")],
        [KeyboardButton(text="🙋‍♂️Допомога")],
    ],
    is_persistent=True,
    resize_keyboard=True,
)
