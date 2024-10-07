import uuid
from datetime import datetime

from aiogram import Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import redis_client
from handlers.admin_handlers import is_admin
from keyboards.inline import poll_builder
from some_func import add_poll_to_bd, add_questions_to_message, get_polls, get_poll_desc_and_set_id_to_state
from states.poll_states import CreatePollState


# Poll Menu
async def poll(callback: CallbackQuery) -> None:
    if not await is_admin(callback):
        return
    await callback.message.answer("Оберіть наступний крок:", reply_markup=poll_builder.as_markup())


# Add poll
async def add_poll(callback: CallbackQuery, state: FSMContext) -> None:
    if not await is_admin(callback):
        return
    await callback.message.answer("Введіть назву для опитування:")
    await state.set_state(CreatePollState.waiting_for_poll_title)


# Saving poll title
async def process_poll_title(message: Message, state: FSMContext) -> None:
    await state.clear()
    poll_title = message.text

    if await redis_client.exists(f"poll:{poll_title}"):
        await message.answer(
            f'Опитування з назвою «{poll_title}» вже існує. Будь ласка, введіть іншу назву.')
        return

    poll_id = str(uuid.uuid4())[:8]
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    await state.update_data(poll_id=poll_id, poll_title=poll_title)

    await redis_client.hset(f"poll:{poll_id}", mapping={
        "id": poll_id,
        "created_by": message.from_user.id,
        "name": poll_title,
        "description": "",
        "created_at": created_at
    })

    await redis_client.sadd("polls", poll_id)

    await message.answer('Введіть опис для опитування або «blank», для пропуску:')
    await state.set_state(CreatePollState.waiting_for_poll_desc)


# Add poll description
async def process_poll_desc(message: Message, state: FSMContext) -> None:
    poll_desc = message.text
    data = await state.get_data()
    poll_id = data.get('poll_id')

    if poll_desc.lower() != "blank":
        await redis_client.hset(f"poll:{poll_id}", "description", poll_desc)
        await message.answer("Опис збережено.")

    await message.answer("Питання №1:")
    await state.set_state(CreatePollState.waiting_for_poll_questions)
    await state.update_data(current_question_num=1)


# Add questions
async def process_poll_questions(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    poll_id = data.get('poll_id')
    question_num = data.get('current_question_num', 1)
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if message.poll:
        await add_poll_to_bd(message, poll_id, question_num)
        await redis_client.hset(f"poll:{poll_id}:question_time", question_num, created_at)

        await state.update_data(current_question_num=question_num + 1)

        await message.answer(f"Вбудоване опитування №{question_num} збережено. Введіть наступне питання, "
                             f'або «end» для завершення.')

    else:
        poll_question = message.text

        if poll_question.lower() == "end":
            await message.answer("Запитання для опитування збережено.")
            await state.clear()
            await message.answer("Оберіть наступний крок:", reply_markup=poll_builder.as_markup())
            return

        await redis_client.hset(f"poll:{poll_id}:questions", question_num, poll_question)
        await redis_client.hset(f"poll:{poll_id}:question_time", question_num, created_at)

        await state.update_data(current_question_num=question_num + 1)

        await message.answer(
            f'Запитання №{question_num + 1}. Введіть наступне питання, або «end» для завершення.')


# Poll editor menu
async def edit_poll(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    if not await is_admin(callback):
        return

    poll_list = await get_polls(callback.message)

    edit_poll_builder = InlineKeyboardBuilder()

    for poll_id, poll_title, _ in poll_list:
        edit_poll_builder.button(text=poll_title, callback_data=f"edit_poll:{poll_id}")
    edit_poll_builder.button(text="Назад", callback_data="poll")
    edit_poll_builder.adjust(4, 3)

    await callback.message.answer("Оберіть опитування для редагування:", reply_markup=edit_poll_builder.as_markup())


# What admin want to edit?
async def handle_poll_edit(callback: CallbackQuery) -> None:
    poll_id = callback.data.split(":")[1]

    edit_poll_builder = InlineKeyboardBuilder()
    edit_poll_builder.button(text="Назва", callback_data=f"edit_poll_title:{poll_id}")
    edit_poll_builder.button(text="Опис", callback_data=f"edit_poll_desc:{poll_id}")
    edit_poll_builder.button(text="Питання", callback_data=f"edit_poll_questions:{poll_id}")
    edit_poll_builder.button(text="Видалити", callback_data=f"delete_poll:{poll_id}")
    edit_poll_builder.button(text="Назад", callback_data=f"edit_poll")
    edit_poll_builder.adjust(4, 1)

    poll_data = await redis_client.hgetall(f"poll:{poll_id}")
    poll_title = poll_data.get(b'name').decode()

    await callback.message.answer(f'Що ви хочете змінити в «{poll_title}»?',
                                  reply_markup=edit_poll_builder.as_markup())


# Poll title edit
async def edit_poll_title(callback: CallbackQuery, state: FSMContext) -> None:
    poll_id = callback.data.split(":")[1]

    await state.clear()
    await state.update_data(poll_id=poll_id)

    await callback.message.answer("Введіть нову назву для опитування:")
    await state.set_state(CreatePollState.waiting_for_poll_title_edit)


async def process_poll_title_edit(message: Message, state: FSMContext) -> None:
    poll_new_title = message.text
    data = await state.get_data()
    poll_id = data.get('poll_id')

    if await redis_client.exists(f"poll:{poll_new_title}") and poll_new_title != poll_id:
        await message.answer(f'Опитування з назвою «{poll_new_title}» вже існує. Введіть іншу назву.')
        return

    await redis_client.hset(f"poll:{poll_id}", "name", poll_new_title)
    await message.answer(f'Назву опитування змінено на «{poll_new_title}».')
    await state.clear()
    await message.answer("Оберіть наступний крок:", reply_markup=poll_builder.as_markup())


# Poll description edit
async def edit_poll_desc(callback: CallbackQuery, state: FSMContext) -> None:
    current_desc = await get_poll_desc_and_set_id_to_state(callback, state)

    await callback.message.answer(
        f'Поточний опис: «{current_desc}»\nВведіть новий опис для опитування або «blank», щоб зробити його порожнім:'
    )

    await state.set_state(CreatePollState.waiting_for_poll_desc_edit)


async def process_poll_desc_edit(message: Message, state: FSMContext) -> None:
    poll_new_desc = message.text
    data = await state.get_data()
    poll_id = data.get('poll_id')

    if poll_new_desc.lower() != "blank":
        await redis_client.hset(f"poll:{poll_id}", "description", poll_new_desc)
    else:
        await redis_client.hset(f"poll:{poll_id}", "description", "")

    await message.answer("Опис опитування змінено.")
    await state.clear()
    await message.answer("Оберіть наступний крок:", reply_markup=poll_builder.as_markup())


# Poll questions edit
async def edit_poll_questions(callback: CallbackQuery = None, message: Message = None, poll_id: str = None,
                              state: FSMContext = None) -> None:
    if callback:
        await callback_questions_btn(callback, state)
    elif message:
        poll_questions = await redis_client.hgetall(f"poll:{poll_id}:questions")
        poll_times = await redis_client.hgetall(f"poll:{poll_id}:question_time")

        question_buttons = InlineKeyboardBuilder()

        if not poll_questions:
            question_buttons.button(text="Додати перше запитання", callback_data=f"edit_poll_question:{poll_id}:add")
            question_buttons.button(text="Назад", callback_data="edit_poll")
            question_buttons.adjust(2)
            await message.answer("В опитуванні немає запитань.",
                                 reply_markup=question_buttons.as_markup())
            return

        await add_questions_to_message(poll_times, poll_questions, question_buttons, poll_id)

        poll_data = await redis_client.hgetall(f"poll:{poll_id}")
        poll_title = poll_data.get(b'name').decode()

        await message.answer(f"Виберіть питання для редагування в «{poll_title}»:",
                             reply_markup=question_buttons.as_markup())

        await state.clear()


# Display available questions for editing in the survey as buttons for further interaction with them
async def callback_questions_btn(callback: CallbackQuery, state: FSMContext) -> None:
    poll_id = callback.data.split(":")[1]
    poll_questions = await redis_client.hgetall(f"poll:{poll_id}:questions")
    poll_times = await redis_client.hgetall(f"poll:{poll_id}:question_time")

    question_buttons = InlineKeyboardBuilder()

    if not poll_questions:
        question_buttons.button(text="Додати перше запитання", callback_data=f"edit_poll_question:{poll_id}:add")
        question_buttons.button(text="Назад", callback_data="edit_poll")
        question_buttons.adjust(2)
        await callback.message.answer("В опитуванні немає запитань. Додайте перше запитання:",
                                      reply_markup=question_buttons.as_markup())
        return

    await add_questions_to_message(poll_times, poll_questions, question_buttons, poll_id)

    poll_data = await redis_client.hgetall(f"poll:{poll_id}")
    poll_title = poll_data.get(b'name').decode()

    await callback.message.answer(f"Виберіть питання для редагування в «{poll_title}»:",
                                  reply_markup=question_buttons.as_markup())

    await state.clear()


# Requesting a new question or deleting an existing
async def edit_poll_question(callback: CallbackQuery, state: FSMContext) -> None:
    poll_id = callback.data.split(":")[1]
    poll_question_num = callback.data.split(":")[2]

    await state.clear()
    await state.update_data(poll_id=poll_id, question_num=poll_question_num)

    if poll_question_num == "add":
        await callback.message.answer('Введіть нове запитання:')
        await state.set_state(CreatePollState.waiting_for_poll_question_edit)
    else:
        await callback.message.answer('Введіть новий текст для запитання, або «delete», щоб його видалити:')
        await state.set_state(CreatePollState.waiting_for_poll_question_edit)


# Question editing process
async def process_edit_poll_question(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    poll_id = data.get('poll_id')
    question_num = data.get('question_num')
    is_new = False

    if question_num == "add":
        poll_questions = await redis_client.hgetall(f"poll:{poll_id}:questions")
        next_question_num = str(len(poll_questions) + 1)
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M")

        await state.update_data(question_num=next_question_num)
        question_num = next_question_num

        await redis_client.hset(f"poll:{poll_id}:question_time", next_question_num, created_at)

        is_new = True

    if message.poll:
        poll_question = await add_poll_to_bd(message, poll_id, question_num)

        await message.answer(f'Питання №{question_num} змінено на вбудоване опитування: «{poll_question}»')
        await state.clear()

    else:
        if message.text.lower() == "delete":
            await redis_client.hdel(f"poll:{poll_id}:questions", question_num)
            await redis_client.delete(f"poll:{poll_id}:options:{question_num}")
            await redis_client.hdel(f"poll:{poll_id}:multiple_answers", question_num)

            await message.answer(f"Питання №{question_num} видалено.")
            await state.clear()
            return

        new_question_text = message.text

        await redis_client.hset(f"poll:{poll_id}:questions", question_num, new_question_text)
        if is_new:
            await message.answer(f'Запитання №{question_num} було додано: «{new_question_text}».')
        else:
            await message.answer(f"Питання №{question_num} змінено на: «{new_question_text}».")

        await state.clear()
    await edit_poll_questions(message=message, poll_id=poll_id, state=state)


# Delete poll process
async def delete_poll(callback: CallbackQuery, state: FSMContext) -> None:
    poll_id = callback.data.split(":")[1]

    poll_name = await redis_client.hget(f"poll:{poll_id}", "name")

    if not await redis_client.exists(f"poll:{poll_id}"):
        await callback.message.answer("Опитування не знайдено.")
        return

    await redis_client.delete(f"poll:{poll_id}")

    poll_questions = await redis_client.hkeys(f"poll:{poll_id}:questions")
    for question_num in poll_questions:
        await redis_client.delete(f"poll:{poll_id}:options:{question_num.decode()}")
        await redis_client.hdel(f"poll:{poll_id}:multiple_answers", question_num.decode())

    await redis_client.delete(f"poll:{poll_id}:questions")
    await redis_client.delete(f"poll:{poll_id}:question_time")

    await redis_client.srem("polls", poll_id)

    await callback.message.answer(f'Опитування «{poll_name.decode()}» успішно видалено.')

    await state.clear()


# Function for registering poll handlers
def register_poll_handlers(dp: Dispatcher):
    dp.callback_query.register(poll, lambda c: c.data == "poll")
    dp.callback_query.register(add_poll, lambda c: c.data == "create_poll")
    dp.callback_query.register(edit_poll, lambda c: c.data == "edit_poll")
    dp.callback_query.register(handle_poll_edit, lambda c: c.data.startswith("edit_poll:"))
    dp.callback_query.register(edit_poll_title, lambda c: c.data.startswith("edit_poll_title"))
    dp.callback_query.register(edit_poll_desc, lambda c: c.data.startswith("edit_poll_desc"))
    dp.callback_query.register(edit_poll_questions, lambda c: c.data.startswith("edit_poll_questions"))
    dp.callback_query.register(edit_poll_question, lambda c: c.data.startswith("edit_poll_question"))
    dp.callback_query.register(delete_poll, lambda c: c.data and c.data.startswith("delete_poll"))

    dp.message.register(process_poll_title, CreatePollState.waiting_for_poll_title)
    dp.message.register(process_poll_desc, CreatePollState.waiting_for_poll_desc)
    dp.message.register(process_poll_questions, CreatePollState.waiting_for_poll_questions)
    dp.message.register(process_poll_title_edit, CreatePollState.waiting_for_poll_title_edit)
    dp.message.register(process_poll_desc_edit, CreatePollState.waiting_for_poll_desc_edit)
    dp.message.register(process_edit_poll_question, CreatePollState.waiting_for_poll_question_edit)
