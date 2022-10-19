import discord
from discord.ext import commands
import aiohttp
import os
from config import GLOBAL_SYNC

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='=',
                            intents=discord.Intents.all(),
                            application_id=999392379272441876)
        
    async def setup_hook(self):
        self.session = aiohttp.ClientSession()
        await self.load_extension(f"cogs.words.dictionaries_cog")
        await self.load_extension(f"cogs.music.music_cog")
        await self.load_extension(f"cogs.nsfw.r34_cog")
        await self.load_extension(f"cogs.ai_images.ai_image_gen")
        await self.load_extension(f"cogs.tts.quack_cog")
        if GLOBAL_SYNC:
            await bot.tree.sync()
        else:
            await bot.tree.sync(guild=discord.Object(id=os.environ["DEVELOPMENT_SERVER_ID"]))
        #
    async def on_ready(self):
        print(f"{self.user} has conected to Discord! Synced Globally: {GLOBAL_SYNC}")

bot = MyBot()

bot.run(os.environ["DISCORD_TOKEN"])

# WHEN TO SYNC
# When you add a new command.
# When you remove a command.
# When a command's name or description changes.
# When the callback's parameters change.
#       This includes parameter names, types or descriptions.
#       Also when you add or remove a parameter.
# If you change a global to a guild command, or vice versa.
#       If you do this, you will need to sync both global and to that guild to reflect the change.