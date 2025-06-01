import enum
from typing import List

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.services.database.models import Lesson, TestQuestion, Topic
from bot.utils.class_range import class_range

use_full_name_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📛 Взяти ім’я з Telegram", callback_data="use_tg_name"
            )
        ]
    ]
)

support_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🪲Повідомити про баг", callback_data="support")]
    ]
)

cancel_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🛑Зупинитись", callback_data="cancel")]
    ]
)


class ProgramCB(CallbackData, prefix="program"):
    start_class: int
    end_class: int


program_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🏫 1-4 класи (Молодша школа)",
                callback_data=ProgramCB(start_class=1, end_class=4).pack(),
            )
        ],
        [
            InlineKeyboardButton(
                text="🏫 5-9 класи (Середня школа)",
                callback_data=ProgramCB(start_class=5, end_class=9).pack(),
            )
        ],
        [
            InlineKeyboardButton(
                text="🏫 10-11 класи (Старша школа)",
                callback_data=ProgramCB(start_class=10, end_class=11).pack(),
            )
        ],
    ]
)


class ClassCB(CallbackData, prefix="class"):
    class_number: int
    admin: bool


async def class_kb_generator(start_class: int, end_class: int, admin: bool = False):
    keyboard = InlineKeyboardBuilder()
    for i in range(start_class, end_class + 1):
        keyboard.add(
            InlineKeyboardButton(
                text=f"{i} Клас",
                callback_data=ClassCB(class_number=i, admin=admin).pack(),
            )
        )

    if admin is False:
        keyboard.add(InlineKeyboardButton(text=f"🔙", callback_data="programs"))

    return keyboard.adjust(1).as_markup()


class ListComands(enum.Enum):
    open = 1
    add = 2
    cancel = 3
    delete = 4
    edit = 5
    add_test = 6
    get_test = 7
    add_quiz = 8
    get_quiz = 9
    get_materials = 10


class TopicCB(CallbackData, prefix="topics"):
    topic_id: int
    cmd: int
    admin: bool
    class_number: int


async def topics_kb_generator(
    topics: List[Topic], class_number: int, cmd: ListComands, admin: bool = False
):
    keyboard = InlineKeyboardBuilder()
    for topic in topics:
        keyboard.add(
            InlineKeyboardButton(
                text=f"📚 {topic.title}",
                callback_data=TopicCB(
                    topic_id=topic.id, cmd=cmd, admin=admin, class_number=class_number
                ).pack(),
            )
        )

    if admin:
        if cmd is ListComands.open:
            keyboard.add(
                InlineKeyboardButton(
                    text="➕ Додати нову тему",
                    callback_data=TopicCB(
                        topic_id=0,
                        cmd=ListComands.add,
                        admin=True,
                        class_number=class_number,
                    ).pack(),
                )
            )
            if len(topics) > 0:
                keyboard.add(
                    InlineKeyboardButton(
                        text="🗑 Видалити тему",
                        callback_data=TopicCB(
                            topic_id=0,
                            cmd=ListComands.delete,
                            admin=True,
                            class_number=class_number,
                        ).pack(),
                    )
                )
            keyboard.add(
                InlineKeyboardButton(text="🔙 Назад", callback_data="admin_classes")
            )
        else:
            keyboard.add(
                InlineKeyboardButton(
                    text="❌ Відмінити",
                    callback_data=TopicCB(
                        topic_id=0,
                        cmd=ListComands.cancel,
                        admin=True,
                        class_number=class_number,
                    ).pack(),
                )
            )
    else:
        start_class, end_class = class_range(class_number)
        keyboard.add(
            InlineKeyboardButton(
                text="🔙",
                callback_data=ProgramCB(
                    start_class=start_class, end_class=end_class
                ).pack(),
            )
        )

    return keyboard.adjust(1).as_markup()


class LessonCB(CallbackData, prefix="lessons"):
    lesson_id: int
    cmd: int
    admin: bool
    topic_id: int


async def lessons_kb_generator(
    lessons: List[Lesson],
    class_number: int,
    topic_id: int,
    cmd: ListComands,
    admin: bool = False,
):
    keyboard = InlineKeyboardBuilder()
    for lesson in lessons:
        keyboard.add(
            InlineKeyboardButton(
                text=f"{lesson.title}",
                callback_data=LessonCB(
                    lesson_id=lesson.id, cmd=cmd, admin=admin, topic_id=topic_id
                ).pack(),
            )
        )

    if admin:
        if cmd is ListComands.open:
            keyboard.add(
                InlineKeyboardButton(
                    text="➕ Додати урок",
                    callback_data=LessonCB(
                        lesson_id=0, cmd=ListComands.add, admin=True, topic_id=topic_id
                    ).pack(),
                )
            )
            keyboard.add(
                InlineKeyboardButton(
                    text="📝 Додати модульний тест",
                    callback_data=TopicCB(
                        topic_id=topic_id,
                        cmd=ListComands.add_quiz,
                        admin=True,
                        class_number=class_number,
                    ).pack(),
                )
            )
            keyboard.add(
                InlineKeyboardButton(
                    text="📋 Дістати модульний тест",
                    callback_data=TopicCB(
                        topic_id=topic_id,
                        cmd=ListComands.get_quiz,
                        admin=True,
                        class_number=class_number,
                    ).pack(),
                )
            )
            keyboard.add(
                InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data=ClassCB(class_number=class_number, admin=True).pack(),
                )
            )
        else:
            keyboard.add(
                InlineKeyboardButton(
                    text="❌ Відмінити",
                    callback_data=LessonCB(
                        lesson_id=0,
                        cmd=ListComands.cancel,
                        admin=True,
                        topic_id=topic_id,
                    ).pack(),
                )
            )
    else:
        keyboard.add(
            InlineKeyboardButton(
                text="🔙",
                callback_data=ClassCB(class_number=class_number, admin=False).pack(),
            )
        )

    return keyboard.adjust(1).as_markup()


async def admin_lesson_kb_generator(lesson: Lesson, class_number: int):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(
            text="📝 Оновити матеріали",
            callback_data=LessonCB(
                lesson_id=lesson.id,
                cmd=ListComands.edit,
                admin=True,
                topic_id=lesson.topic_id,
            ).pack(),
        )
    )
    keyboard.add(
        InlineKeyboardButton(
            text="✍️ Додати тест",
            callback_data=LessonCB(
                lesson_id=lesson.id,
                cmd=ListComands.add_test,
                admin=True,
                topic_id=lesson.topic_id,
            ).pack(),
        )
    )
    keyboard.add(
        InlineKeyboardButton(
            text="📋 Переглянути тест",
            callback_data=LessonCB(
                lesson_id=lesson.id,
                cmd=ListComands.get_test,
                admin=True,
                topic_id=lesson.topic_id,
            ).pack(),
        )
    )
    keyboard.add(
        InlineKeyboardButton(
            text="🗑 Видалити урок",
            callback_data=LessonCB(
                lesson_id=lesson.id,
                cmd=ListComands.delete,
                admin=True,
                topic_id=lesson.topic_id,
            ).pack(),
        )
    )
    keyboard.add(
        InlineKeyboardButton(
            text="🔙",
            callback_data=TopicCB(
                topic_id=lesson.topic_id,
                cmd=ListComands.open,
                admin=True,
                class_number=class_number,
            ).pack(),
        )
    )
    return keyboard.adjust(2).as_markup()


async def lesson_kb_generator(lesson: Lesson, class_number: int):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(
            text="📚 Отримати навчальні матеріали",
            callback_data=LessonCB(
                lesson_id=lesson.id,
                cmd=ListComands.get_materials,
                admin=False,
                topic_id=lesson.topic_id,
            ).pack(),
        )
    )
    keyboard.add(
        InlineKeyboardButton(
            text="✍️ Пройти тестування",
            callback_data=LessonCB(
                lesson_id=lesson.id,
                cmd=ListComands.get_test,
                admin=False,
                topic_id=lesson.topic_id,
            ).pack(),
        )
    )
    keyboard.add(
        InlineKeyboardButton(
            text="🔙",
            callback_data=TopicCB(
                topic_id=lesson.topic_id,
                cmd=ListComands.open,
                admin=False,
                class_number=class_number,
            ).pack(),
        )
    )
    return keyboard.adjust(2).as_markup()


class AnswerCB(CallbackData, prefix="answer"):
    idx: int


async def question_kb(answers: List[str]):
    keyboard = InlineKeyboardBuilder()
    for idx, answer in enumerate(answers):
        keyboard.add(
            InlineKeyboardButton(
                text=f"{answer}", callback_data=AnswerCB(idx=idx).pack()
            )
        )
    return keyboard.adjust(1).as_markup()


class QuizCB(CallbackData, prefix="quiz"):
    topic_id: int


async def quizzes_kb(topics: List[Topic]):
    keyboard = InlineKeyboardBuilder()
    for topic in topics:
        keyboard.add(
            InlineKeyboardButton(
                text=f"{topic.title}", callback_data=QuizCB(topic_id=topic.id).pack()
            )
        )
    return keyboard.adjust(1).as_markup()
