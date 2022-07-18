import discord
from discord import app_commands
from discord.ext import commands
import requests
from bs4 import BeautifulSoup
import os

class define(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

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


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(define(bot), guilds=[discord.Object(id=os.environ("DEVELOPMENT_SERVER_ID"))])