import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from config import GLOBAL_SYNC
import asyncio

user_ids = [
    147651412774486016,
    293835259265548289,
    153945414683328513,
    162957028535435266,
    147802163572113408,
    501444082426576896,
    668531400676212777,
    147395879962148864,
    147439193323208704,
    227850389079326720
]

class GPT(commands.GroupCog, name="GPT"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"GPT cog is now ready. Synced Globally: {GLOBAL_SYNC}")

    @app_commands.command(name="history", description="Brian retrieves message history")
    async def define(self, interaction: discord.Interaction, amount: int) -> None:
        if interaction.user.id not in user_ids:
            return await interaction.response.send_message("User cannot use this command")

        messages = [message async for message in interaction.channel.history(limit=amount)]

        await interaction.response.send_message(f"Successfully traced back {amount} messages. List size: {len(messages)}\n\n {messages}")

