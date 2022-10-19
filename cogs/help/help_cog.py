from unicodedata import name
import discord
from discord import app_commands
from discord.ext import commands
import re
import requests
from bs4 import BeautifulSoup
import random
import os
from config import GLOBAL_SYNC

class Brian(commands.GroupCog, name="brian"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Brian cog is now ready. Synced Globally: {GLOBAL_SYNC}")

    @app_commands.command(name="help", description="Get help with Brians commands")
    async def help_command(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Bot Brian Help", description="", color=discord.Color.from_rgb(0, 255, 0))
        for c in self.bot.cogs:
            cog = self.bot.get_cog(c)
            group = cog.app_command
            embed.add_field(name=group.name.upper(), value=f"".join(f"`{command.name}`: {command.description}\n" for command in group.commands), inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
            


async def setup(bot: commands.Bot) -> None:
    if GLOBAL_SYNC:
        # Global Sync
        await bot.add_cog(Brian(bot))
    else:
        # Private Sync
        await bot.add_cog(Brian(bot), guilds=[discord.Object(id=os.environ["DEVELOPMENT_SERVER_ID"])])