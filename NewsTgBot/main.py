import asyncio  # Хуйня для ассинхронного взаимодействия с ботом
import logging  # Ещё какая-то хуйня
import sys  # Системная хуйня
import main_news  # Импорт функций из файла
import find  # Импорт функций из файла
import requests  # Хуйня для парсинга(пиздим инфу) сайтов
import os  # Системная хуйня
from config import TOKEN_API, start_message  # Из моего файла config импортируем(пиздим) 2е переменные
from aiogram import Bot, Dispatcher, types  # aiogram - сторонняя библиотека, с которой мы воруем всякую хуйню
from aiogram.enums import ParseMode
from aiogram.types import FSInputFile
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

TOKEN = TOKEN_API  # Присваиваем переменной TOKEN то, что мы спиздили из файла config
dp = Dispatcher()  # Хуйня, с помощью которой бот распознаёт команды пользователя
bot1 = Bot(TOKEN)  # Создаём переменную, с помощью которой мы отдаём боту команды

start_buts = InlineKeyboardBuilder()
more_news_buts = InlineKeyboardBuilder()
start_buts_texts = ["Технології", "ІТ-бізнес", "Пристрої", "Софт", "Пошук"]
more_news_buts_texts = ["Далі", "Минула новина"]  # Хуня по которой нажимают хуйня(кнопка)
for text in start_buts_texts:
    start_buts.button(text=text, callback_data=f"button_{text}")
for text in more_news_buts_texts:
    more_news_buts.button(text=text, callback_data=f"button_{text}")
start_buts.adjust(2, 2, 1)
more_news_buts.adjust(2)

j = 1  # Переменная для того, что бы выводить новости в определённом порядке


@dp.message(CommandStart())  # Штука которая обрабатывает команды /start
async def cmd_start(message: types.Message):  # def = ФУНКЦИЯ
    await message.answer(text=start_message, parse_mode='HTML', reply_markup=start_buts.as_markup())  # ANSWER = ОТВЕТ
    # reply_markup = Штука которая создаёт кнопки. MARKUP = кнопка


news_message_id = None  # переменная КОТОРАЯ СОДЕРЖИТ В СЕБЕ  айди новости
buttons_message_id = None  # переменная КОТОРАЯ СОДЕРЖИТ В СЕБЕ  айди сообщения
forum_name = None  # Хуйня которая содержит в себе 5 основных кнопок


@dp.callback_query(
    lambda callback_query: callback_query.data.startswith('button_'))  # Диспетчер, который реагирует на нажите кнопки
async def on_button_click(callback_query: types.CallbackQuery):
    global j, news_message_id, buttons_message_id, forum_name  # Объявление глобальных переменных
    button_text = callback_query.data.split('_')[1]  # Переменная которая содержитв себе текст кнопки

    if (button_text == "Технології" or button_text == "ІТ-бізес" or button_text == "Пристрої"
            or button_text == "Софт" or button_text == "Пошук"):
        forum_name = callback_query.data.split('_')[1]
        j = 1

    user_id = callback_query.from_user.id
    if forum_name == "Технології":
        url = 'https://itc.ua/ua/tehnologiyi/'
        folder = 'technologies'
        await news_posting(user_id, button_text, url, folder, 0)
    elif forum_name == "ІТ-бізес":
        url = 'https://itc.ua/ua/biznes-ua/'
        folder = 'it-buziness'
        await news_posting(user_id, button_text, url, folder, 0)
    elif forum_name == "Пристрої":
        url = 'https://itc.ua/ua/pristroyi/'
        folder = 'gadgets'
        await news_posting(user_id, button_text, url, folder, 0)
    elif forum_name == "Софт":
        url = 'https://itc.ua/ua/soft/'
        folder = 'soft'
        await news_posting(user_id, button_text, url, folder, 0)
    elif forum_name == "Пошук":
        global search_message  # SEARCH = поиск
        search_message = await bot1.send_message(chat_id=user_id, text="Введіть тему яка вас цікавить:")

        async def handle_user_input(message: types.Message):  # Реагирует на введёный пользователем текст
            global search_message, forum_name  # Добавляем ключевое слово global
            user_text = message.text
            user_id = message.from_user.id
            try:
                await bot1.delete_message(chat_id=user_id, message_id=search_message.message_id)
                await bot1.delete_message(chat_id=user_id,
                                          message_id=message.message_id)  # Удаляем сообщение пользователя
            except:
                pass
            folder = 'search'  # folder = ПАПКА
            await news_posting(user_id, button_text, user_text, folder, 1)

        await dp.message.register(handle_user_input)
        await dp.message.unregistered(handle_user_input)  # Вызываем обработчик сообщений
        search_message = None  # Обнуляем локальную переменную
        forum_name = None  # Обнуляем локальную переменную


async def news_posting(user_id, button_text, url, folder, move):
    global j, news_message_id, buttons_message_id
    if news_message_id is not None:
        await bot1.delete_message(chat_id=user_id, message_id=news_message_id)
    if buttons_message_id is not None:  # Попытка удалить новость и кнопку после неё
        await bot1.delete_message(chat_id=user_id, message_id=buttons_message_id)
    news_message_id = None
    buttons_message_id = None

    if button_text == "Далі":
        j += 1
    elif button_text == "Минула новина" and j > 1:
        j -= 1
    if move == 0:
        result = await main_news.main(url)  # Блять кароче вызываем функцию, которая лежит в файле main_news
        title, time, description, link, photo = result
    else:
        result = await find.find_news(url)
        if result == ([], [], []):
            sent_message = await bot1.send_message(chat_id=user_id, text="Результатів не знайдено.")
            await asyncio.sleep(2)
            await bot1.delete_message(chat_id=user_id, message_id=sent_message.message_id)
        else:
            title, link, photo = result

    for i in range(min(j, len(title))):
        i = j - 1
        response = requests.get(url=photo[i])
        folder_path = f"NewsTgBot/img's/{folder}/"
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        photo_path = f"NewsTgBot/img's/{folder}/{i}_{user_id}_req_img.jpg"  # Шобла-йобла с фоткой
        if photo_path:
            with open(photo_path, 'wb') as file:
                file.write(response.content)
        if move == 0:
            caption_text = f"<a href='{link[i]}'><b>{title[i]}</b></a>\nКоротко: {description[i]}\nДень публікації: {time[i]}"
        else:
            caption_text = f"<a href='{link[i]}'><b>{title[i]}</b></a>"
        photo = FSInputFile(photo_path)
        news_message = await bot1.send_photo(user_id, photo=photo, caption=caption_text,
                                             parse_mode='HTML')  # caption =  описание
        if move == 0:
            buttons_message = await bot1.send_message(chat_id=user_id, text="Продовжуємо?",
                                                      reply_markup=more_news_buts.as_markup())
        news_message_id = news_message.message_id
        if buttons_message is not None:
            buttons_message_id = buttons_message.message_id


# Хуйня для запуска программы
async def main() -> None:
    bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
