from discord.ext import commands

from some_func import return_goods
from config import USER_ID


class StartSearching(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='search')
    async def search_goods(self, ctx):
        user = await self.bot.fetch_user(USER_ID)
        find = await return_goods(user=user)
        if not find:
            await ctx.author.send("No new adverts found.")



async def setup(bot):
    await bot.add_cog(StartSearching(bot))
