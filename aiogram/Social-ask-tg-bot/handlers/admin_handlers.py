from aiogram import Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import redis_client
from handlers.common import command_start_handler
from keyboards.inline import admin_builder
from some_func import correct_input
from states.admin_states import AdminState


# Show admin menu
async def admin(callback: CallbackQuery) -> None:
    if not await is_admin(callback):
        return
    await callback.message.answer("Оберіть наступний крок:", reply_markup=admin_builder.as_markup())


# Add admin
async def add_admin(callback: CallbackQuery, state: FSMContext) -> None:
    if not await is_admin(callback):
        return
    await callback.message.answer("Введіть: <Призначуване ім'я> <Унікальне ім'я користувача (saw_TheMoon)>",
                                  parse_mode=None)
    await state.set_state(AdminState.waiting_for_admin_name)


# Аdd admin processing
async def process_admin_name(message: Message, state: FSMContext) -> None:
    result = await correct_input(message)
    if result is None:
        return
    admin_name, admin_nickname = result
    if await redis_client.exists(f"admin:{admin_nickname}"):
        await message.answer(
            f"Адміністартор з ім'ям користувача «{admin_nickname}» уже існує. Повторіть спробу.")
        return

    await redis_client.hset(f"admin:{admin_nickname}", mapping={
        "id": "",
        "name": admin_name,
        "user_name": admin_nickname,
        "full_name": ""
    })

    await redis_client.sadd("admins", admin_nickname)

    await state.clear()

    await message.answer(f"Адміністратора «{admin_name}» з userID {admin_nickname} було додано.")
    await message.answer("Оберіть наступний крок:", reply_markup=admin_builder.as_markup())


# Show all admins
async def list_admins(callback_query: CallbackQuery) -> None:
    if not await is_admin(callback_query):
        return
    admins = await redis_client.smembers("admins")

    if not admins:
        await callback_query.message.answer("Адміністраторів не знайдено.")
        return

    admin_list = []
    for admin in admins:
        admin_id, admin_name, admin_tg_name, admin_nickname = await redis_client.hmget(f"admin:{admin.decode()}",
                                                                                       "id", "name", "user_name",
                                                                                       "full_name")
        admin_list.append(
            f"ID: {'NODATA' if not admin_id or admin_id.decode() == '' else admin_id.decode()}, "
            f"Ім'я: {'NODATA' if not admin_name else admin_name.decode()}, "
            f"Посилання: {'NODATA' if not admin_tg_name else '@' + admin_tg_name.decode()}, "
            f"Псевдонім: {'NODATA' if not admin_nickname or admin_nickname.decode() == '' else admin_nickname.decode()}"
        )

    await callback_query.message.answer("\n".join(admin_list))
    await callback_query.message.answer("Оберіть наступний крок:", reply_markup=admin_builder.as_markup())


# Change admin name
async def edit_admin(callback: CallbackQuery, state: FSMContext) -> None:
    if not await is_admin(callback):
        return
    await callback.message.answer(
        "Введіть: <нове ім'я> <Унікальне ім'я користувача (saw_TheMoon)>", parse_mode=None)
    await state.set_state(AdminState.waiting_for_admin_new_name)


# Change admin name processing
async def process_admin_new_name(message: Message) -> None:
    try:
        admin_new_name, admin_nickname = await correct_input(message)
    except TypeError:
        return

    if not await redis_client.exists(f"admin:{admin_nickname}"):
        await message.answer(
            f'Адміністратора з ім\'ям користувача телеграм «{admin_nickname}» не знайдено. Спробуйте знову!')
        return

    await redis_client.hset(f"admin:{admin_nickname}", "name", admin_new_name)
    await message.answer(
        f'Ім\'я адміністратора з назвою користувача телеграм «{admin_nickname}» оновлено на «{admin_new_name}»')
    await message.answer("Оберіть наступний крок:", reply_markup=admin_builder.as_markup())


# Delete admin
async def delete_admin(callback: CallbackQuery, state: FSMContext) -> None:
    if not await is_admin(callback):
        return
    await callback.message.answer(
        "Введіть: <Унікальне ім'я користувача (saw_TheMoon) для видалення>",
        parse_mode=None)
    await state.set_state(AdminState.waiting_for_admin_name_for_delete)


# Delete admin processing
async def process_admin_name_for_delete(message: Message, state: FSMContext) -> None:
    if len(message.text.split()) != 1:
        await message.answer("Неправильне введення даних, спробуйте ще раз.")
        return

    admin_nickname = message.text
    admin_nickname = admin_nickname[1:] if admin_nickname.startswith("@") else admin_nickname
    admin_nickname = admin_nickname[13:] if admin_nickname.startswith("https://t.me/") else admin_nickname

    if not await redis_client.exists(f"admin:{admin_nickname}"):
        await message.answer(
            f'Адміністратора з ім\'ям користувача телеграм «{admin_nickname}» не знайдено. Спробуйте знову!')
        return

    await redis_client.delete(f"admin:{admin_nickname}")

    await redis_client.srem("admins", admin_nickname)

    await state.clear()

    await message.answer(f"Адміністратора з ім'ям користувача телеграм «{admin_nickname}» було успішно видалено.")
    await message.answer("Оберіть наступний крок:", reply_markup=admin_builder.as_markup())


# Add sticker reward for complete poll
async def add_reward(callback: CallbackQuery, state: FSMContext) -> None:
    if not await is_admin(callback):
        return
    await callback.message.answer("Надішліть стікер, щоб додати стікерпак у нагороди.")
    await state.set_state(AdminState.waiting_for_sticker_reward)


# Process reward creating
async def process_create_reward(message: Message):
    if not message.sticker:
        await message.reply("Будь ласка, надішліть стікер.")
        return

    sticker_set_name = message.sticker.set_name

    if not sticker_set_name:
        await message.reply("Не вдалося отримати інформацію про стікерпак.")
        return

    redis_link = f"https://t.me/addstickers/{sticker_set_name}"

    all_sticker_packs = await redis_client.hgetall("reward:sticker_pack")

    if redis_link.encode() in all_sticker_packs.values():
        await message.reply("Стікерпак уже було додано.")
        await message.answer("Оберіть наступний крок:", reply_markup=admin_builder.as_markup())
        return

    next_sticker_pack_id = await redis_client.incr("reward:id_counter")

    await redis_client.hset("reward:sticker_pack", next_sticker_pack_id, redis_link)

    await message.reply(f"Стікерпак збережено: {redis_link}")
    await message.answer("Оберіть наступний крок:", reply_markup=admin_builder.as_markup())


# Go back to main menu
async def go_back_to_start(callback_query: CallbackQuery, state: FSMContext):
    await state.update_data(returning_from_back_admin=True)
    await command_start_handler(callback_query.message, state)


# Check: is user admin?
async def is_admin(callback) -> bool:
    if not await redis_client.exists(f"admin:{callback.from_user.username}"):
        await command_start_handler(callback.message)
        return False
    return True


# Function for registering administrator handlers
def register_admin_handlers(dp: Dispatcher):
    dp.callback_query.register(admin, lambda c: c.data == "admin")
    dp.callback_query.register(add_admin, lambda c: c.data == "add_admin")
    dp.callback_query.register(list_admins, lambda c: c.data == "show_admin")
    dp.callback_query.register(edit_admin, lambda c: c.data == "edit_admin")
    dp.callback_query.register(delete_admin, lambda c: c.data == "delete_admin")
    dp.callback_query.register(go_back_to_start, lambda c: c.data == "go_back_to_start")
    dp.callback_query.register(add_reward, lambda c: c.data == "reward")

    dp.message.register(process_admin_name, AdminState.waiting_for_admin_name)
    dp.message.register(process_admin_new_name, AdminState.waiting_for_admin_new_name)
    dp.message.register(process_admin_name_for_delete, AdminState.waiting_for_admin_name_for_delete)
    dp.message.register(process_create_reward, AdminState.waiting_for_sticker_reward)
