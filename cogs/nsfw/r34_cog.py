import discord
from discord import app_commands
from discord.ext import commands
import re
import requests
from bs4 import BeautifulSoup
import random
import os
from config import GLOBAL_SYNC

commandExamples = dict()
commandExamples = {
    "r34" : "/nsfw r34 <search>",
    "help" : "/nsfw help"
}

class Nsfw(commands.GroupCog, name="nsfw"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"NSFW cog is now ready. Synced Globally: {GLOBAL_SYNC}")

    @app_commands.command(name="r34", description="Returns a random Rule 34 image")
    async def r34_command(self, interaction: discord.Interaction, *, search: str):
        if not interaction.channel.is_nsfw():
            embed = discord.Embed(title="This command can only be used in NSFW/18+ channels", color=discord.Color.from_rgb(255, 0, 0))
            return await interaction.response.send_message(embed=embed)

        #Variables used for searching
        results = []
        main_url = "https://rule34.xxx/"
        search_command = "index.php?page=post&s=list&tags="

        # Modify user search into usable web address
        new_search = search.replace(' ', '_')
        new_search = re.sub('\_\_+', '_', new_search)
        new_search = new_search.lstrip('_')
        url = main_url + search_command + new_search
        header = {'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148'}
        response = requests.get(url, headers=header)

        # store webpage content
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find image-list class and search for all <a> elements within class
        # Store all href instances within <a> elements
        try:
            content_div = soup.find("div", {"class": "image-list"})
            for href in content_div.find_all('a'):
                temp = href.get('href')
                results.append(temp)
        
            # Generate random pick from results
            results_count = len(results)
            image_link = main_url + results[random.randint(0, results_count)]

            # Repeat similar but on the thumbnail image we just found
            # Final src is the full scaled image
            response = requests.get(image_link, headers=header)
            soup = BeautifulSoup(response.content, 'html.parser')
            content_div = soup.find("div", {"class": "flexi"})
            for src in content_div.find_all('img'):
                final_img = src.get('src')

            await interaction.response.send_message(final_img)
        except AttributeError:
            await interaction.response.send_message(f"No results for: {search}")
        
    @app_commands.command(name="help", description="Get help with Bot Brians nsfw commands")
    async def nsfw_help_command(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(title="NSFW Commands", description="List of all Bot Brians nsfw commands with examples", color=discord.Color.from_rgb(0, 255, 0))

        cog = self.bot.get_cog("nsfw")
        group = cog.app_command
        for command in group.commands:
            embed.add_field(name=command.name, value=f"`{command.description}`\n`{commandExamples.get(command.name)}`", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot) -> None:
    if GLOBAL_SYNC:
        # Global Sync
        await bot.add_cog(Nsfw(bot))
    else:
        # Private Sync
        await bot.add_cog(Nsfw(bot), guilds=[discord.Object(id=os.environ["DEVELOPMENT_SERVER_ID"])])