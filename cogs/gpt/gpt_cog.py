import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from config import GLOBAL_SYNC
import asyncio
import os
import re

url_regex = re.compile("(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))")

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

known_junk = [
    '~play',
    '~stop',
    '~rule34',
    '~skip'
]

async def process_data() -> None:
    return


class GPT(commands.GroupCog, name="gpt"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()


    @commands.Cog.listener()
    async def on_ready(self):
        print(f"GPT cog is now ready. Synced Globally: {GLOBAL_SYNC}")

    @app_commands.command(name="create_corpus", description="Brian retrieves message history")
    async def create_corpus(self, interaction: discord.Interaction, user: discord.User,  amount: int) -> None:
        if interaction.user.id not in user_ids:
            return await interaction.response.send_message("User cannot use this command")
        
        await interaction.response.defer(thinking=True, ephemeral=True)

        messages = []
        async for message in interaction.channel.history(limit=amount):
            #if message is not by the person we want then skip
            if re.search(url_regex, message.content) is None:         
                messages.append(message.content)

        for message in messages:
            print(message)

        return await interaction.followup.send(f"Successfully traced back {amount} messages. Corpus Sentence Size: {len(messages)}", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    if GLOBAL_SYNC:
        # Global Sync
        await bot.add_cog(GPT(bot))
    else:
        # Private Sync
        await bot.add_cog(GPT(bot), guilds=[discord.Object(id=os.environ["DEVELOPMENT_SERVER_ID"])])

