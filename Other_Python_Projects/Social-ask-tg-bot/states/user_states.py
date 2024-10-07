from aiogram.fsm.state import State, StatesGroup


class UserStates(StatesGroup):
    waiting_for_user_answer = State()
