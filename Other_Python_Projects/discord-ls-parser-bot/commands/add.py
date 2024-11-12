import asyncio

import discord
from discord.ext import commands

from config import redis_client


class AddKeywords(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='add')
    async def add_keywords(self, ctx):
        await ctx.author.send("Please send me your keywords (comma-separated):")

        def check(msg):
            return msg.author == ctx.author and msg.channel.type == discord.ChannelType.private

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=60)
            new_keywords = [keyword.strip() for keyword in msg.content.split(',')]

            existing_keywords = await redis_client.get(f"keywords:{ctx.author.id}")

            if existing_keywords:
                existing_keywords = existing_keywords.decode('utf-8').split(',')
                combined_keywords = list(set(existing_keywords + new_keywords))  # Убираем дубликаты
                await redis_client.set(f"keywords:{ctx.author.id}", ','.join(combined_keywords))
            else:
                await redis_client.set(f"keywords:{ctx.author.id}", ','.join(new_keywords))

            await ctx.author.send("Keywords saved!")
        except asyncio.TimeoutError:
            await ctx.author.send("You took too long to respond!")


async def setup(bot):
    await bot.add_cog(AddKeywords(bot))
