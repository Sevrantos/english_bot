from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InputMediaPhoto, Message

from bot.fsm.student import Test
from bot.keyboards.inline_keyboard import (
    AnswerCB,
    LessonCB,
    ListComands,
    cancel_kb,
    question_kb,
)
from bot.services.database.repositories.tests import TestRepository
from bot.services.database.repositories.topics import TopicRepository
from bot.utils.config import FAIL_PHOTO, MIN_PASS_SCORE, SUCCESS_PHOTO

router = Router()


@router.callback_query(LessonCB.filter(F.cmd == ListComands.get_test.value))
async def get_test(
    callback: CallbackQuery, callback_data: LessonCB, state: FSMContext, db
):
    test_repo = TestRepository(db)

    question = await test_repo.get_question(callback_data.lesson_id, 0)

    if not question:
        await callback.answer("На жаль, тест ще не доступний", show_alert=True)
        return

    await state.set_state(Test.answer)
    await state.update_data(
        message_id=callback.message.message_id,
        correct_answer=question.correct_answer,
        totoal_questions=1,
        correct_questions=0,
        lesson_id=callback_data.lesson_id,
        topic_id=callback_data.topic_id,
    )

    await callback.message.edit_text(
        "Розпочався тест з уроку.\nБудь ласка, уважно читайте питання та обирайте правильну відповідь.",
        reply_markup=cancel_kb,
    )
    await callback.message.pin()

    await callback.message.answer(
        f"Питання: {question.question}",
        reply_markup=await question_kb(answers=question.options),
    )


@router.callback_query(Test.answer, AnswerCB.filter())
async def answer_question(
    callback: CallbackQuery, callback_data: AnswerCB, state: FSMContext, bot: Bot, db
):
    test_repo = TestRepository(db)
    topic_repo = TopicRepository(db)

    data = await state.get_data()
    correct_questions = data.get("correct_questions") + (
        data.get("correct_answer") == callback_data.idx
    )
    totoal_questions = data.get("totoal_questions")
    lesson_id = data.get("lesson_id")

    question = await test_repo.get_question(lesson_id, totoal_questions)

    # No more questions
    if not question:
        score = round((correct_questions / totoal_questions) * 100)
        if score >= MIN_PASS_SCORE:
            await test_repo.save_student_score(
                student_id=callback.from_user.id, lesson_id=lesson_id, score=score
            )

            text = f"""
✅ Вітаємо! Ви успішно склали тест!
📊 Ваш результат: {score}% ({correct_questions}/{totoal_questions} правильних відповідей)

Продовжуйте навчання та відкривайте нові можливості!"""
            await callback.message.edit_media(
                media=InputMediaPhoto(media=SUCCESS_PHOTO, caption=text),
                reply_markup=None,
            )

            if await topic_repo.is_quiz_open(
                student_id=callback.from_user.id,
                topic_id=data.get("topic_id"),
                min_lesson_score=MIN_PASS_SCORE,
            ):
                await callback.message.answer(
                    "🎉 Вітаємо! Ви відкрили модульний тест з теми!\n"
                    "Перейдіть у розділ 'Модульні тести' щоб пройти його."
                )

        else:
            text = f"""
❌ На жаль, тест не складено
📊 Ваш результат: {score}% ({correct_questions}/{totoal_questions} правильних відповідей)
ℹ️ Для успішного проходження потрібно набрати мінімум {MIN_PASS_SCORE}%

💡 Рекомендуємо повторити матеріал уроку та спробувати ще раз!"""
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


@router.message(Test.answer)
async def except_test(message: Message):
    await message.answer("Спочатку закінчіть тест")
