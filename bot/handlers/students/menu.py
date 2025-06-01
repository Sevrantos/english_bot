from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from bot.keyboards.inline_keyboard import (
    ClassCB,
    ListComands,
    ProgramCB,
    TopicCB,
    class_kb_generator,
    lessons_kb_generator,
    program_kb,
    quizzes_kb,
    support_kb,
    topics_kb_generator,
)
from bot.services.database.repositories.lessons import LessonRepository
from bot.services.database.repositories.quizzes import QuizRepository
from bot.services.database.repositories.topics import TopicRepository
from bot.utils.config import MIN_PASS_SCORE

router = Router()


@router.message(F.text == "👨‍🎓Навчання")
async def show_programs(message: Message):
    await message.answer(
        """📚 Вітаємо у розділі навчання!

Оберіть навчальну програму для початку:
• 5-6 класи - базовий рівень
• 7-9 класи - середній рівень
• 10-11 класи - поглиблений рівень""",
        reply_markup=program_kb,
    )


@router.callback_query(F.data == "programs")
async def back_programs(callback: CallbackQuery):
    await callback.message.edit_text(
        """📚 Вітаємо у розділі навчання!

Оберіть навчальну програму для початку:
• 5-6 класи - базовий рівень
• 7-9 класи - середній рівень
• 10-11 класи - поглиблений рівень""",
        reply_markup=program_kb,
    )


@router.callback_query(ProgramCB.filter())
async def show_classes(callback: CallbackQuery, callback_data: ProgramCB):
    await callback.message.edit_text(
        f"""📚 Оберіть клас для навчання

🎯 Програма: {callback_data.start_class}-{callback_data.end_class} класи
ℹ️ Кожен клас містить:
• Тематичні розділи
• Детальні уроки
• Практичні завдання
• Модульні тести""",
        reply_markup=await class_kb_generator(
            callback_data.start_class, callback_data.end_class
        ),
    )


@router.callback_query(ClassCB.filter())
async def show_topics(callback: CallbackQuery, callback_data: ClassCB, db):
    topic_repo = TopicRepository(db)

    topics = await topic_repo.get_topics_by_class(callback_data.class_number)

    text = f"""📚 {callback_data.class_number}-й клас

Оберіть тему для вивчення. Кожна тема містить декілька уроків та завершується модульним тестом."""

    await callback.message.edit_text(
        text,
        reply_markup=await topics_kb_generator(
            topics=topics, class_number=callback_data.class_number, cmd=ListComands.open
        ),
    )


@router.callback_query(TopicCB.filter())
async def show_lessons(callback: CallbackQuery, callback_data: TopicCB, db):
    lesson_repo = LessonRepository(db)
    topic_repo = TopicRepository(db)

    lessons = await lesson_repo.get_lessons_by_topic(callback_data.topic_id)
    topic = await topic_repo.get_topic(callback_data.topic_id)

    text = f"""📘 Тема: {topic.title}
📝 Опис: {topic.description}

Оберіть урок для вивчення:"""

    await callback.message.edit_text(
        text,
        reply_markup=await lessons_kb_generator(
            lessons=lessons,
            class_number=callback_data.class_number,
            topic_id=callback_data.topic_id,
            cmd=ListComands.open,
        ),
    )


@router.message(F.text == "📝Модульні тести")
async def show_quizzes(message: Message, db):
    quiz_repo = QuizRepository(db)

    topics = await quiz_repo.get_eligible_topics(message.from_user.id, MIN_PASS_SCORE)

    if not topics:
        await message.answer("В тебе немає доступних модульних тестів")
        return

    await message.answer(
        "Список модульних тестів", reply_markup=await quizzes_kb(topics=topics)
    )


@router.message(F.text == "🙋‍♂️Допомога")
async def show_faq(message: Message, db):
    text = f"""
📚 Часті запитання (FAQ)

❓ Як працює навчання?
- Оберіть навчальну програму та клас
- Вивчайте уроки по темах
- Проходьте тести після кожного уроку
- Відкривайте модульні тести, успішно склавши всі тести з теми

❓ Що таке модульний тест?
- Це підсумковий тест з усієї теми
- Відкривається після успішного складання всіх тестів з уроків теми (мінімум 60%)
- Допомагає перевірити загальне розуміння матеріалу

❓ Які прохідні бали?
- Тести з уроків: мінімум {MIN_PASS_SCORE}%
- Модульні тести: мінімум {MIN_PASS_SCORE}%

❓ Що робити, якщо виникла помилка?
- Натисніть кнопку "Повідомити про помилку"
- Опишіть проблему
- Адміністратори розглянуть її якнайшвидше

💡 Додаткові питання можна задати через форму зворотного зв'язку нижче
"""
    await message.answer(text=text, reply_markup=support_kb)
