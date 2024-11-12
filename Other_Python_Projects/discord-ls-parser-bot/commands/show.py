from discord.ext import commands

from config import redis_client


class ShowKeywords(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='show')
    async def show_keywords(self, ctx):
        keywords = await redis_client.get(f"keywords:{ctx.author.id}")
        if keywords:
            keywords_list = keywords.decode('utf-8').split(',')
            keywords_list.reverse()
            await ctx.send(f"Your keywords: {', '.join(keywords_list)}")
        else:
            await ctx.send("You don't have any keywords saved.")


async def setup(bot):
    await bot.add_cog(ShowKeywords(bot))
