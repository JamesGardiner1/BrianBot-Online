import discord
from discord.ext import commands
import aiohttp
import BrianBotConfig as config

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='=',
                            intents=discord.Intents.all(),
                            application_id=987829603118759936)
        
    async def setup_hook(self):
        self.session = aiohttp.ClientSession()
        await self.load_extension(f"cogs.test")
        await self.load_extension(f"cogs.ai_images.dalle_cog")
        await self.load_extension(f"cogs.music.music_cog")
        #await self.load_extension(f"cogs.help.help_cog")
        await self.load_extension(f"cogs.nsfw.r34_cog")
        await bot.tree.sync(guild=discord.Object(id=config.TEEF2_SERVER))
    
    async def on_ready(self):
        print(f"{self.user} has conected to Discord!")

bot = MyBot()
bot.run(config.TOKEN)