from aiogram.fsm.state import State, StatesGroup


class AddTopic(StatesGroup):
    title = State()
    description = State()


class AddLesson(StatesGroup):
    title = State()
    description = State()
    add_test = State()


class AddMaterials(StatesGroup):
    add = State()


class AddQuiz(StatesGroup):
    add = State()


class AddTest(StatesGroup):
    add = State()
