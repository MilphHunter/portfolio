from discord.ext import commands


class HelpCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='bot-help')
    async def show_keywords(self, ctx):
        commands_list = (
            "/add - Add keywords.\n"
            "/show - Show saved keywords.\n"
            "/del - Remove keywords.\n"
            "/search - Forced search\n"
            "/help - See this message."
        )
        await ctx.send(f"Here's a list of available commands:\n{commands_list}")


async def setup(bot):
    await bot.add_cog(HelpCommand(bot))
