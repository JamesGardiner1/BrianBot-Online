import discord
from discord.ext import commands
import aiohttp
import os

TEEF2_SERVER = 749955516398305363

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='=',
                            intents=discord.Intents.all(),
                            application_id=987829603118759936)
        
    async def setup_hook(self):
        self.session = aiohttp.ClientSession()
        await self.load_extension(f"cogs.test")
        await self.load_extension(f"cogs.words.define_cog")
        await self.load_extension(f"cogs.words.urban_dic_cog")
        await self.load_extension(f"cogs.music.music_cog")
        await self.load_extension(f"cogs.nsfw.r34_cog")
        await self.load_extension(f"cogs.ai_images.deepai_cog")
        await self.load_extension(f"cogs.ai_images.dalle_cog")
        await bot.tree.sync(guild=discord.Object(id=TEEF2_SERVER))
    
    async def on_ready(self):
        print(f"{self.user} has conected to Discord!")

bot = MyBot()
bot.run(os.environ["DISCORD_TOKEN"])