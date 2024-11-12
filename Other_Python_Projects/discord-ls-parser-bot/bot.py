import asyncio
import os

import discord
from discord.ext import commands

from config import TOKEN, USER_ID, redis_client
from some_func import return_goods

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)


# Function for sending recurring messages
async def send_periodic_messages(user):
    try:
        commands_list = (
            "/add - Add keywords.\n"
            "/show - Show saved keywords.\n"
            "/del - Remove keywords.\n"
            "/search - Forced search\n"
            "/timer - Change the frequency of checks (in seconds)\n"
            "/bot-help - See this message."
        )
        await user.send(f"Hi! Here's a list of available commands:\n{commands_list}")
        print("Message sent")
    except discord.Forbidden:
        print("Bot can't send message")
    else:
        while True:
            await return_goods(user)
            timer_value = redis_client.get(f"timer:{user.id}")
            if timer_value:
                await asyncio.sleep(int(timer_value))
            else:
                await asyncio.sleep(3600)


async def load_commands():
    for filename in os.listdir('commands'):
        if filename.endswith('.py'):
            await bot.load_extension(f'commands.{filename[:-3]}')


@bot.event
async def on_ready():
    print(f'Bot came in as {bot.user}')
    await load_commands()
    user = await bot.fetch_user(USER_ID)
    await send_periodic_messages(user)


@bot.event
async def on_message(message):
    await bot.process_commands(message)


bot.run(TOKEN)
