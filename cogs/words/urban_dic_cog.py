import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
import re
import requests
from bs4 import BeautifulSoup
import os

class UrbanDic(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="urban_define", description="Grab the definition of a word or phrase from urbandictionary")
    async def urban_define_command(self, interaction: discord.Interaction, search: Optional[str], random: Optional[bool] = False) -> None:
        #Variables used for searching
        main_url = "https://www.urbandictionary.com/"
        search_command = "define.php?term="

        if random is True:
            url = "https://www.urbandictionary.com/random.php"
        else:
            # Modify user search into usable web address
            search = re.sub('\ \ +', ' ', search)
            search = search.replace(' ', '%20')
            url = main_url + search_command + search

        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')

        word = soup.find("a", {"class": "word text-denim font-bold font-serif dark:text-fluorescent break-words text-3xl md:text-[2.75rem] md:leading-10"}).get_text()
        definitions = soup.find("div", {"class": "meaning mb-4"}).get_text()
        example = soup.find("div", {"class": "example italic mb-4"}).get_text()
        author = soup.find("div", {"class": "contributor font-bold"}).get_text()

        embed = discord.Embed(title=word)
        embed.add_field(name="Definition", value=f"```{definitions}```", inline=False)
        embed.add_field(name="Example", value=f"```{example}```", inline=False)
        embed.add_field(name="Uploaded By", value=f"```{author}```")
        embed.set_thumbnail(url="https://upload.wikimedia.org/wikipedia/commons/thumb/f/f0/Urban_Dictionary_logo.svg/512px-Urban_Dictionary_logo.svg.png?20180302232617")
        await interaction.response.send_message(embed=embed)



async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(UrbanDic(bot), guilds=[discord.Object(id=os.environ("DEVELOPMENT_SERVER_ID"))])