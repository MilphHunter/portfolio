from random import randint

from aiogram import Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, PollAnswer

from config import redis_client
from handlers.common import command_start_handler
from keyboards.inline import show_desc_builder
from some_func import get_poll_desc_and_set_id_to_state
from states.user_states import UserStates


# Checking is user ready to start
async def poll_start(callback: CallbackQuery, state: FSMContext):
    current_desc = await get_poll_desc_and_set_id_to_state(callback, state)
    await state.update_data(user_id=callback.from_user.id)
    await callback.message.answer(text=current_desc, reply_markup=show_desc_builder.as_markup())


# Consistently provide the user with questions
async def create_questions_list(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    poll_id = data.get('poll_id')

    if not poll_id:
        await callback.message.answer("Опитування не знайдено.")
        return

    poll_questions = await redis_client.hgetall(f"poll:{poll_id}:questions")

    if not poll_questions:
        await callback.message.answer("Опитування не містить запитань.")
        return

    questions_list = [(key.decode(), value.decode()) for key, value in poll_questions.items()]

    user_id = callback.from_user.id
    progress = await redis_client.hget(f"user:{user_id}:poll:{poll_id}:progress", "current_question_index")

    if progress:
        current_question_index = int(progress.decode())
    else:
        current_question_index = 0

    await state.update_data(user_id=user_id, questions_list=questions_list,
                            current_question_index=current_question_index)

    await ask_next_question(callback.message, state)


# Function for sending an embedded survey to the user
async def ask_next_question(message: Message, state: FSMContext):
    data = await state.get_data()
    questions_list = data.get('questions_list')
    current_question_index = data.get('current_question_index')

    if current_question_index >= len(questions_list):
        await message.answer("Опитування завершено! Дякуємо за відповіді.")
        await get_reward(message)

        user_id = message.from_user.id
        poll_id = data.get('poll_id')

        await redis_client.sadd(f"poll:{poll_id}:user_complete", user_id)
        await redis_client.hdel(f"user:{user_id}:poll:{poll_id}:progress", "current_question_index")
        await state.clear()

        await state.update_data(user_id=user_id)
        await go_back_to_start_user(message=message, state=state)
        return

    question_id, question_text = questions_list[current_question_index]
    await state.update_data(current_question_id=question_id)

    poll_options = await redis_client.hgetall(f"poll:{data['poll_id']}:options:{question_id}")

    if not poll_options or len(poll_options) < 2:
        await message.answer(f"Питання {current_question_index + 1}: {question_text}")
        await state.set_state(UserStates.waiting_for_user_answer)
    else:
        sorted_options = sorted(poll_options.items(), key=lambda x: int(x[0]))
        poll_options = [option.decode() for _, option in sorted_options]

        allows_multiple_answers = await redis_client.hget(f"poll:{data['poll_id']}:multiple_answers", question_id)
        allows_multiple_answers = bool(int(allows_multiple_answers))

        poll_message = await message.bot.send_poll(
            chat_id=message.chat.id,
            question=question_text,
            options=poll_options,
            allows_multiple_answers=allows_multiple_answers,
            is_anonymous=False
        )

        await state.update_data(current_message_id=poll_message.message_id, chat_id=poll_message.chat.id)
    await state.update_data(current_question_index=current_question_index + 1)

    user_id = data.get('user_id')
    poll_id = data.get('poll_id')
    await redis_client.hset(f"user:{user_id}:poll:{poll_id}:progress", "current_question_index",
                            current_question_index)


# Function for processing the user's response to an inbuilt survey
async def handle_poll_answer(poll_answer: PollAnswer, state: FSMContext):
    user_id = poll_answer.user.id

    data = await state.get_data()
    poll_id = data.get('poll_id')
    question_id = data.get('current_question_id')

    selected_options = poll_answer.option_ids
    selected_options_text = [
        await redis_client.hget(f"poll:{poll_id}:options:{question_id}", str(option_id + 1))
        for option_id in selected_options
    ]

    await redis_client.hset(
        f"user:{user_id}:poll:{poll_id}:answers",
        question_id,
        ','.join([option.decode() for option in selected_options_text])
    )

    chat_id = data.get('chat_id')

    if chat_id:
        class FakeMessage:
            def __init__(self, bot, chat):
                self.bot = bot
                self.chat = type("Chat", (object,), {"id": chat})
                self.from_user = type("User", (object,), {"id": user_id})

            async def answer(self, text, reply_markup=None):
                return await self.bot.send_message(chat_id=self.chat.id, text=text, reply_markup=reply_markup)

        fake_message = FakeMessage(bot=poll_answer.bot, chat=chat_id)

        await ask_next_question(fake_message, state)


# Saving user answer
async def handle_user_answer(message: Message, state: FSMContext):
    data = await state.get_data()
    poll_id = data.get('poll_id')
    question_id = data.get('current_question_id')

    if not poll_id or not question_id:
        await message.answer("Не вдалося отримати дані запитання або опитування.")
        return

    user_id = message.from_user.id
    user_answer = message.text

    await redis_client.hset(f"user:{user_id}:poll:{poll_id}:answers", question_id, user_answer)

    await ask_next_question(message, state)


# Get reward to user after poll complete
async def get_reward(message: Message):
    count_of_sticker_packs = await redis_client.get("reward:id_counter")
    reward = randint(1, int(count_of_sticker_packs.decode()))
    sticker_pack = await redis_client.hget("reward:sticker_pack", str(reward))
    await message.answer(text=f"Ваша нагорода за допомогу: {sticker_pack.decode()}")


# Go back to start after finishing with poll
async def go_back_to_start_user(callback: CallbackQuery = None, message: Message = None,
                                state: FSMContext = None) -> None:
    await state.update_data(returning_from_back_user=True)
    await command_start_handler(callback.message, state) if callback else await command_start_handler(message, state)


# Function for registering user handlers
def register_user_handlers(dp: Dispatcher):
    dp.callback_query.register(create_questions_list, lambda c: c.data == "start_poll")
    dp.callback_query.register(go_back_to_start_user, lambda c: c.data == "go_back_to_start_user")
    dp.callback_query.register(poll_start, lambda c: c.data.startswith('show_poll:'))

    dp.message.register(handle_user_answer, UserStates.waiting_for_user_answer)

    dp.poll_answer.register(handle_poll_answer)
