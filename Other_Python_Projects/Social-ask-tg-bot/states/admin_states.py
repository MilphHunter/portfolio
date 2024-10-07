from aiogram.fsm.state import State, StatesGroup


class AdminState(StatesGroup):
    waiting_for_admin_name = State()
    waiting_for_admin_new_name = State()
    waiting_for_admin_name_for_delete = State()
    waiting_for_sticker_reward = State()
