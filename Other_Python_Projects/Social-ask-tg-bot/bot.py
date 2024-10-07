import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

from config import TOKEN, redis_client
from handlers.admin_handlers import register_admin_handlers
from handlers.common import register_common_handlers
from handlers.poll_handlers import register_poll_handlers
from handlers.result_handlers import register_result_handlers
from handlers.user_handlers import register_user_handlers


async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    storage = RedisStorage(redis=redis_client)
    dp = Dispatcher(storage=storage)

    register_common_handlers(dp)
    register_admin_handlers(dp)
    register_poll_handlers(dp)
    register_user_handlers(dp)
    register_result_handlers(dp)

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
