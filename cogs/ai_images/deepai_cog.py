from code import interact
import discord
from discord import app_commands
from discord.ext import commands
import requests
import os

TEEF2_SERVER = 749955516398305363

class deepai(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.id_list = []

    @app_commands.command(name="deepai", description="Generate an AI image from text prompt with DeepAI")
    async def deepai(self, interaction: discord.Interaction, prompt: str) -> None:
        if interaction.user.id in self.id_list:
            embed = discord.Embed(title="Please wait for your current DALL-E image to complete", color=discord.Color.from_rgb(255, 0, 0))
            return await interaction.response.send_message(embed=embed)
            
        self.id_list.append(interaction.user.id)

        loading_emoji = self.bot.get_emoji(997263536076107827)
        
        await interaction.response.defer()
        embed = discord.Embed(title=f"Generating DeepAI Image now! {loading_emoji}", description=f"Prompt: {prompt}", color=discord.Color.from_rgb(0, 255, 0))
        embed.set_thumbnail(url="https://6lli539m39y3hpkelqsm3c2fg-wpengine.netdna-ssl.com/wp-content/uploads/2020/10/DeepAi-Logo.png")
        embed.set_footer(text="Please allow for up to 2 minutes.")
        # Get last sent message id so we can edit/delete when generation complete
        msg = await interaction.followup.send(embed=embed)

        try:
            r = requests.post("https://api.deepai.org/api/text2img",
                data={'text': prompt},
                headers={'api-key': os.environ["DEEPAI_API_KEY"]})

            content = r.json()
            print(content)
            image_url = content["output_url"]
        except KeyError:
            return await interaction.followup.send("Could not complete request, please try again.")


        embed = discord.Embed(title=f"{interaction.user.name}'s DeepAI Search Finished!", description=f"Prompt: {prompt}", color=discord.Color.from_rgb(0, 255, 0))
        embed.set_footer(text="Website Link: https://www.craiyon.com")
        embed.set_image(url=image_url)
        await interaction.followup.send(embed=embed)
        self.id_list.remove(interaction.user.id)
        embed = discord.Embed(title="Images Generated", color=discord.Color.from_rgb(255, 255, 255))
        await msg.edit(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(deepai(bot), guilds=[discord.Object(id=TEEF2_SERVER)])