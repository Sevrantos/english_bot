from aiogram import Bot, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InputMediaPhoto, Message

from bot.fsm.student import Quiz
from bot.keyboards.inline_keyboard import AnswerCB, QuizCB, cancel_kb, question_kb
from bot.services.database.repositories.quizzes import QuizRepository
from bot.utils.config import FAIL_PHOTO, MIN_PASS_SCORE, SUCCESS_PHOTO

router = Router()


@router.callback_query(QuizCB.filter())
async def get_quiz(
    callback: CallbackQuery, callback_data: QuizCB, state: FSMContext, db
):
    quiz_repo = QuizRepository(db)

    question = await quiz_repo.get_question(callback_data.topic_id, 0)

    await state.set_state(Quiz.answer)
    await state.update_data(
        message_id=callback.message.message_id,
        correct_answer=question.correct_answer,
        totoal_questions=1,
        correct_questions=0,
        topic_id=callback_data.topic_id,
    )

    await callback.message.edit_text(
        "Розпочався модульний тест.\n"
        "Це фінальна перевірка знань з теми. Бажаємо успіху!",
        reply_markup=cancel_kb,
    )
    await callback.message.pin()

    await callback.message.answer(
        f"Питання: {question.question}",
        reply_markup=await question_kb(answers=question.options),
    )


@router.callback_query(Quiz.answer, AnswerCB.filter())
async def answer_question(
    callback: CallbackQuery, callback_data: AnswerCB, state: FSMContext, bot: Bot, db
):
    quiz_repo = QuizRepository(db)

    data = await state.get_data()
    correct_questions = data.get("correct_questions") + (
        data.get("correct_answer") == callback_data.idx
    )
    totoal_questions = data.get("totoal_questions")
    topic_id = data.get("topic_id")

    question = await quiz_repo.get_question(
        topic_id=topic_id, question_index=totoal_questions
    )

    if not question:
        score = round((correct_questions / totoal_questions) * 100)
        if score >= MIN_PASS_SCORE:
            await quiz_repo.save_student_score(
                student_id=callback.from_user.id, topic_id=topic_id, score=score
            )

            text = f"""
🎉 Вітаємо! Ви успішно склали модульний тест!
📊 Ваш результат: {score}% ({correct_questions}/{totoal_questions} правильних відповідей)

Ви можете перейти до вивчення наступної теми!"""
            await callback.message.edit_media(
                media=InputMediaPhoto(media=SUCCESS_PHOTO, caption=text),
                reply_markup=None,
            )

        else:
            text = f"""
❌ На жаль, модульний тест не складено
📊 Ваш результат: {score}% ({correct_questions}/{totoal_questions} правильних відповідей)
ℹ️ Для успішного проходження потрібно набрати мінімум {MIN_PASS_SCORE}%

💡 Рекомендуємо повторити матеріал теми та спробувати ще раз!"""
            await callback.message.edit_media(
                media=InputMediaPhoto(media=FAIL_PHOTO, caption=text), reply_markup=None
            )

        await state.clear()
        await bot.edit_message_reply_markup(
            chat_id=callback.from_user.id,
            message_id=data.get("message_id"),
            reply_markup=None,
        )
        await bot.unpin_all_chat_messages(chat_id=callback.from_user.id)
        return

    await state.update_data(
        correct_answer=question.correct_answer,
        correct_questions=correct_questions,
        totoal_questions=totoal_questions + 1,
    )

    await callback.message.edit_text(
        f"Питання: {question.question}",
        reply_markup=await question_kb(answers=question.options),
    )


@router.message(Quiz.answer)
async def except_quiz(message: Message):
    await message.answer("Спочатку закінчіть модульний тест")
