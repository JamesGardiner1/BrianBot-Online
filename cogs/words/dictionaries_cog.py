from unicodedata import name
import discord
from discord import app_commands
from discord.ext import commands
import requests
from bs4 import BeautifulSoup
import os
from typing import Optional
import re

class Dictionaries(commands.GroupCog, name="dictionaries"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Dictionaries cog is now ready.")

    @app_commands.command(name="define", description="Brian returns the definition for your word")
    async def define(self, interaction: discord.Interaction, word: str) -> None:
        main_url = "https://www.dictionary.com/"
        search_command = "browse/"
        url = main_url + search_command + word
        response = requests.get(url)

        # store webpage content
        soup = BeautifulSoup(response.content, 'html.parser')

        #different ways of displaying information. Some words arent split, some are. To do with website HTML
        try:
            main_section = soup.find("div", {"class": "css-1avshm7 e16867sm0"})
            phonetic = main_section.find("span", {"class": "pron-spell-content css-7iphl0 evh0tcl1"}).get_text()

            embed = discord.Embed(title=word, description=phonetic, color=discord.Color.from_rgb(0, 255, 0))
            embed.set_thumbnail(url="https://www.dictionary.com/e/wp-content/uploads/2021/12/dictionary-logo.png")

            sections = main_section.findChildren('section', recursive=False)
            num_sections = len(sections)
            for section in range(1, num_sections):
                type = sections[section].find("div", {"class": "css-69s207 e1hk9ate3"}).get_text()
                definitions_list = sections[section].find("div", {"class": "css-10n3ydx e1hk9ate0"})
                definitions = definitions_list.findChildren('div', recursive=False)
                definition_string = ""

                counter = 1
                for definition in definitions:
                    definition_string += f"{counter}. {definition.get_text()}\n\n"
                    counter += 1
                embed.add_field(name=type, value=f"```{definition_string}```", inline=False)
            
            await interaction.response.send_message(embed=embed)
        except AttributeError:
            embed = discord.Embed(description=f"`{word}` not found on [dictionary.com](https://www.dictionary.com/)", color=discord.Color.from_rgb(255, 0, 0))
            await interaction.response.send_message(embed=embed)

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

        word = soup.find("a", {"class": "word text-denim font-bold font-serif dark:text-fluorescent break-all text-3xl md:text-[2.75rem] md:leading-10"}).get_text()
        definitions = soup.find("div", {"class": "break-words meaning mb-4"}).get_text()
        example = soup.find("div", {"class": "break-words example italic mb-4"}).get_text()
        author = soup.find("div", {"class": "contributor font-bold"}).get_text()

        embed = discord.Embed(title=word)
        embed.add_field(name="Definition", value=f"```{definitions}```", inline=False)
        embed.add_field(name="Example", value=f"```{example}```", inline=False)
        embed.add_field(name="Uploaded By", value=f"```{author}```")
        embed.set_thumbnail(url="https://upload.wikimedia.org/wikipedia/commons/thumb/f/f0/Urban_Dictionary_logo.svg/512px-Urban_Dictionary_logo.svg.png?20180302232617")
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot) -> None:
    # Global Sync
    await bot.add_cog(Dictionaries(bot))
    # Private Sync
    #await bot.add_cog(Dictionaries(bot), guilds=[discord.Object(id=os.environ["DEVELOPMENT_SERVER_ID"])])