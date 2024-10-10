from aiogram import Dispatcher
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from config import redis_client
from keyboards.inline import main_menu_builder
from some_func import create_poll_button_list


# Start command for admins and users
async def command_start_handler(message: Message, state: FSMContext = None) -> None:
    user_data = await state.get_data()
    returning_from_back_admin = user_data.get("returning_from_back_admin", False)
    returning_from_back_user = user_data.get("returning_from_back_user", False)

    username = getattr(message.from_user, 'username', "unknown_user")

    if await redis_client.exists(
            f"admin:{username}") or returning_from_back_admin:
        await message.answer("Меню:", reply_markup=main_menu_builder.as_markup())
        current_id = await redis_client.hget(f"admin:{message.from_user.username}", "id")
        if current_id == b'':
            await redis_client.hset(f"admin:{message.from_user.username}",
                                    mapping={"id": message.from_user.id, "full_name": message.from_user.full_name})
        full_name = await redis_client.hget(f"admin:{message.from_user.username}", "full_name")
        if str(full_name) != message.from_user.full_name:
            await redis_client.hset(f"admin:{message.from_user.username}", "full_name", message.from_user.full_name)
    else:

        user_id = user_data.get('user_id') if returning_from_back_user else message.from_user.id
        user_key = f"user:{user_id}"
        user_exists = await redis_client.exists(user_key)
        if username != "unknown_user":
            if user_exists:
                user_data = await redis_client.hgetall(user_key)
                stored_full_name = user_data.get(b'full_name').decode()
                stored_username = user_data.get(b'username').decode()

                if stored_full_name != message.from_user.full_name or stored_username != message.from_user.username:
                    await redis_client.hset(user_key, mapping={
                        "username": message.from_user.username,
                        "full_name": message.from_user.full_name,
                    })
            else:
                await redis_client.hset(user_key, mapping={
                    "username": message.from_user.username,
                    "full_name": message.from_user.full_name,
                })
                await redis_client.sadd("users", message.from_user.id)
        await create_poll_button_list(text_true="Оберіть тест для проходження:",
                                      text_false="Усі доступні тести вже пройдено!", btn_txt="show_poll",
                                      message=message, user_id=user_id)


# Empty message check
async def echo_handler(message: Message) -> None:
    try:
        await message.send_copy(chat_id=message.chat.id)
    except TypeError:
        await message.answer("Nice try!")


# Main handlers
def register_common_handlers(dp: Dispatcher):
    dp.message(echo_handler)
    dp.message.register(command_start_handler, CommandStart())
