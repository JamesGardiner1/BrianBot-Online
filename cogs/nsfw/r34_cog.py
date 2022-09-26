import discord
from discord import app_commands
from discord.ext import commands
import re
import requests
from bs4 import BeautifulSoup
import random
import os

class Nsfw(commands.GroupCog, name="nsfw"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Nsfw cog is now ready.")

    @app_commands.command(name="r34", description="Returns a random Rule 34 image")
    async def r34_command(self, interaction: discord.Interaction, *, search: str):
        """Returns a random image from r34 website.

        __**Command:**__
        ```=r34 <search>```

        __**Example:**__
        ```=r34 spongebob squarepants```
        """
        #Variables used for searching
        results = []
        main_url = "https://rule34.xxx/"
        search_command = "index.php?page=post&s=list&tags="

        # Modify user search into usable web address
        new_search = search.replace(' ', '_')
        new_search = re.sub('\_\_+', '_', new_search)
        new_search = new_search.lstrip('_')
        url = main_url + search_command + new_search
        response = requests.get(url)

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
            response = requests.get(image_link)
            soup = BeautifulSoup(response.content, 'html.parser')
            content_div = soup.find("div", {"class": "flexi"})
            for src in content_div.find_all('img'):
                final_img = src.get('src')


            await interaction.response.send_message(final_img)
        except AttributeError:
            await interaction.response.send_message(f"No results for: {search}")

async def setup(bot: commands.Bot) -> None:
    # Global Sync
    #await bot.add_cog(Nsfw(bot))
    # Private Sync
    await bot.add_cog(Nsfw(bot), guilds=[discord.Object(id=os.environ["DEVELOPMENT_SERVER_ID"])])