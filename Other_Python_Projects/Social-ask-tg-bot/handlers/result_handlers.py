from aiogram import Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import redis_client
from some_func import create_poll_button_list


# Shows available surveys as buttons for further interaction
async def select_poll_to_see_result(callback_query: CallbackQuery):
    await create_poll_button_list(text_true="Виберіть тест, результати якого бажаєте переглянути:",
                                  text_false="Тестів для перегляду результатів не існує.", btn_txt="result",
                                  message=callback_query.message)


# Choose question to see users answers
async def result_poll_questions(callback_query: CallbackQuery, state: FSMContext = None) -> None:
    poll_id = callback_query.data.split(":")[1]

    poll_questions = await redis_client.hgetall(f"poll:{poll_id}:questions")

    if not poll_questions:
        await callback_query.message.answer("У цьому опитуванні немає запитань.")
        return

    question_buttons = InlineKeyboardBuilder()

    for question_num, question_text in poll_questions.items():
        question_text = question_text.decode()
        question_buttons.button(text=f"Вопрос {question_num.decode()}: {question_text}",
                                callback_data=f"view_poll_result:{poll_id}:{question_num.decode()}")

    question_buttons.adjust(1)

    poll_data = await redis_client.hgetall(f"poll:{poll_id}")
    poll_title = poll_data.get(b'name').decode()

    await callback_query.message.answer(f"Оберіть питання для перегляду результатів у «{poll_title}»:",
                                        reply_markup=question_buttons.as_markup())

    await state.update_data(poll_id=poll_id)


# Show users answers process
async def show_question_results(callback_query: CallbackQuery):
    _, poll_id, question_num = callback_query.data.split(":")

    poll_options = await redis_client.hgetall(f"poll:{poll_id}:options:{question_num}")
    user_answers = await get_user_answers_for_question(poll_id, question_num)

    if not poll_options:
        await callback_query.message.answer("Немає даних щодо варіантів відповідей.")
        return

    total_responses = len(user_answers)
    answer_counts = {option_num.decode(): 0 for option_num in poll_options}

    for _, user_answer in user_answers:
        user_answer_list = user_answer.split(",")

        for user_choice in user_answer_list:
            user_choice = user_choice.strip()
            for option_num, option_text in poll_options.items():
                option_text = option_text.decode()
                if user_choice == option_text:
                    answer_counts[option_num.decode()] += 1

    sorted_poll_options = sorted(poll_options.items(), key=lambda item: int(item[0].decode()))

    result_text = f"Відповіді на запитання {question_num}:\n\n"
    for option_num, option_text in sorted_poll_options:
        option_text = option_text.decode()
        count = answer_counts.get(option_num.decode(), 0)
        percentage = (count / total_responses * 100) if total_responses > 0 else 0
        result_text += f"{option_text}: {percentage:.2f}% ({count}/{total_responses})\n"

    result_text += "\nВідповіді користувачів:\n"
    if user_answers:
        for username, answer in user_answers:
            result_text += f"\n@{username}: {answer}\n"
    else:
        result_text += "Немає відповідей від користувачів."

    await callback_query.message.answer(result_text)
    await result_poll_questions(callback_query)


# Getting answers to the selected question
async def get_user_answers_for_question(poll_id: str, question_num: str):
    user_ids = await redis_client.smembers(f"poll:{poll_id}:user_complete")

    if not user_ids:
        return []

    user_answers = []
    for user_id in user_ids:
        user_id = user_id.decode()
        user_answer = await redis_client.hget(f"user:{user_id}:poll:{poll_id}:answers", question_num)
        if user_answer:
            user_answer = user_answer.decode()

            user_data = await redis_client.hgetall(f"user:{user_id}")
            username = user_data.get(b'username', b'unknown_user').decode()

            user_answers.append((username, user_answer))

    return user_answers


# Function for registering result handlers
def register_result_handlers(dp: Dispatcher):
    dp.callback_query.register(select_poll_to_see_result, lambda c: c.data == "results")
    dp.callback_query.register(result_poll_questions, lambda c: c.data.startswith("result:"))
    dp.callback_query.register(show_question_results, lambda c: c.data.startswith("view_poll_result:"))
