import asyncio

import discord
from discord.ext import commands

from config import redis_client


class RemoveKeywords(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='del')
    async def remove_keywords(self, ctx):
        await ctx.author.send("Please send me the keywords you want to remove (comma-separated):")

        def check(msg):
            return msg.author == ctx.author and msg.channel.type == discord.ChannelType.private

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=60)
            keywords_to_remove = [keyword.strip() for keyword in msg.content.split(',')]

            existing_keywords = await redis_client.get(f"keywords:{ctx.author.id}")

            if existing_keywords:
                existing_keywords = existing_keywords.decode('utf-8').split(',')
                updated_keywords = [keyword for keyword in existing_keywords if keyword not in keywords_to_remove]

                if updated_keywords:
                    await redis_client.set(f"keywords:{ctx.author.id}", ','.join(updated_keywords))
                    await ctx.author.send("Keywords removed!")
                else:
                    await redis_client.delete(f"keywords:{ctx.author.id}")
                    await ctx.author.send("All your keywords have been removed!")
            else:
                await ctx.author.send("You don't have any keywords saved.")
        except asyncio.TimeoutError:
            await ctx.author.send("You took too long to respond!")


async def setup(bot):
    await bot.add_cog(RemoveKeywords(bot))
