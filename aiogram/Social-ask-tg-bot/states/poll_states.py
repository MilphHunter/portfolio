from aiogram.fsm.state import State, StatesGroup


class CreatePollState(StatesGroup):
    waiting_for_poll_title = State()
    waiting_for_poll_title_edit = State()
    waiting_for_poll_desc = State()
    waiting_for_poll_desc_edit = State()
    waiting_for_poll_questions = State()
    waiting_for_poll_question_edit = State()
