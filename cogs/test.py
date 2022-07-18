import discord
from discord import app_commands
from discord.ext import commands

TEEF2_SERVER = 749955516398305363

class test(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="introduce", description="Introduce yourself!")
    async def introduce(self, interaction: discord.Interaction, name: str, age: int) -> None:
        await interaction.response.send_message(f"My name is: {name} and my age is: {age}")

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(test(bot), guild=discord.Object(id=TEEF2_SERVER))