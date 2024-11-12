import asyncio

from discord.ext import commands

from config import redis_client


class TimerCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='timer')
    async def set_timer(self, ctx):
        await ctx.send("Please enter the timer duration in seconds:")

        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel

        try:
            timer_message = await self.bot.wait_for('message', check=check, timeout=60)
            timer_duration = int(timer_message.content)

            redis_client.set(f"timer:{ctx.author.id}", timer_duration)

            await ctx.send(f"Timer set for {timer_duration} seconds.")

        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond!")
        except ValueError:
            await ctx.send("Please enter a valid number of seconds.")


async def setup(bot):
    await bot.add_cog(TimerCommand(bot))
