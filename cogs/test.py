import discord
from discord import app_commands
from discord.ext import commands
import os
from main import GLOBAL_SYNC

class Test(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Test cog is now ready. Synced Globally: {GLOBAL_SYNC}")

    @app_commands.command(name="introduce", description="Introduce yourself!")
    async def introduce(self, interaction: discord.Interaction, name: str, age: int) -> None:
        await interaction.response.send_message(f"My name is: {name} and my age is: {age}")

async def setup(bot: commands.Bot) -> None:
    if GLOBAL_SYNC:
        # Global Sync
        await bot.add_cog(Test(bot))
    else:
        # Private Sync
        await bot.add_cog(Test(bot), guilds=[discord.Object(id=os.environ["DEVELOPMENT_SERVER_ID"])])