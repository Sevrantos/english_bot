from aiogram.fsm.state import State, StatesGroup


class Register(StatesGroup):
    name = State()


class Test(StatesGroup):
    answer = State()


class Quiz(StatesGroup):
    answer = State()


class Support(StatesGroup):
    send = State()
