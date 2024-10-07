from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import redis_client


async def correct_input(message):
    if len(message.text.split()) != 2:
        await message.answer("Неправильне введення даних, спробуйте знову.")
        return

    admin_new_name, admin_nickname = message.text.split()
    admin_nickname = admin_nickname[1:] if admin_nickname.startswith("@") else admin_nickname
    admin_nickname = admin_nickname[13:] if admin_nickname.startswith("https://t.me/") else admin_nickname
    return admin_new_name, admin_nickname


async def add_poll_to_bd(message, poll_id, question_num):
    poll_question = message.poll.question
    poll_options = [option.text for option in message.poll.options]
    allows_multiple_answers = message.poll.allows_multiple_answers

    await redis_client.hset(f"poll:{poll_id}:questions", question_num, poll_question)

    await redis_client.hset(f"poll:{poll_id}:options:{question_num}", mapping={
        str(i + 1): option for i, option in enumerate(poll_options)
    })
    await redis_client.hset(f"poll:{poll_id}:multiple_answers", question_num, int(allows_multiple_answers))
    return poll_question


async def add_questions_to_message(poll_times, poll_questions, question_buttons, poll_id):
    questions_with_time = [
        (question_num, question_text.decode(), poll_times.get(question_num).decode())
        for question_num, question_text in poll_questions.items()
    ]
    questions_with_time.sort(key=lambda x: x[2])

    for question_num, question_text, question_time in questions_with_time:
        question_buttons.button(
            text=f"{question_text}",
            callback_data=f"edit_poll_question:{poll_id}:{question_num.decode()}"
        )

    question_buttons.button(text="Додати запитання", callback_data=f"edit_poll_question:{poll_id}:add")
    question_buttons.button(text="Назад", callback_data="edit_poll")
    question_buttons.adjust(2)


async def get_polls(message: Message = None, user_id: int = None):
    # Получаем все опросы
    polls = await redis_client.smembers("polls")

    if not polls:
        await message.answer("Опитувань для проходження немає.")
        return []

    poll_list = []

    for poll_id in polls:
        poll_id = poll_id.decode()
        poll_data = await redis_client.hgetall(f"poll:{poll_id}")
        poll_title = poll_data.get(b'name').decode()
        created_at = poll_data.get(b'created_at').decode()
        if user_id:
            user_completed = await redis_client.sismember(f"poll:{poll_id}:user_complete", user_id)

            if not user_completed:
                poll_list.append((poll_id, poll_title, created_at))
        else:
            poll_list.append((poll_id, poll_title, created_at))

    poll_list.sort(key=lambda x: x[2])
    return poll_list


async def create_poll_button_list(text_true: str, text_false: str, btn_txt: str, message: Message, user_id: int = None):
    poll_list = await get_polls(message=message, user_id=user_id if user_id else None)

    poll_list_builder = InlineKeyboardBuilder()
    if poll_list:
        for poll_id, poll_title, _ in poll_list:
            poll_list_builder.button(text=poll_title, callback_data=f"{btn_txt}:{poll_id}")

        if not user_id:
            poll_list_builder.button(text="Назад", callback_data="poll")
        poll_list_builder.adjust(2)
        await message.answer(text_true, reply_markup=poll_list_builder.as_markup())
    else:
        await message.answer(text_false)


async def get_poll_desc_and_set_id_to_state(callback: CallbackQuery, state: FSMContext):
    poll_id = callback.data.split(":")[1]

    poll_data = await redis_client.hgetall(f"poll:{poll_id}")
    current_desc = poll_data.get(b'description').decode() if poll_data.get(b'description') else "Описание отсутствует."

    await state.clear()
    await state.update_data(poll_id=poll_id)

    return current_desc
