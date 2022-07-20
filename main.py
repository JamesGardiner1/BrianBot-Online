import discord
from discord.ext import commands
import aiohttp
import os

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='=',
                            intents=discord.Intents.all(),
                            application_id=987829603118759936)
        
    async def setup_hook(self):
        self.session = aiohttp.ClientSession()
        await self.load_extension(f"cogs.test")
        #await self.load_extension(f"cogs.words.dictionaries_cog")
        #await self.load_extension(f"cogs.music.music_cog")
        #await self.load_extension(f"cogs.nsfw.r34_cog")
        #await self.load_extension(f"cogs.ai_images.ai_image_gen")
    
    async def on_ready(self):
        print(f"{self.user} has conected to Discord!")

bot = MyBot()

@bot.command(name="globalcmdsync")
async def global_sync_command(ctx: commands.Context):
    if not ctx.author.id == 153945414683328513:
        return await ctx.reply("You do not have permission to use this command.")
    guild = ctx.guild
    await bot.tree.copy_global_to(guild=guild)
    print("All commands synced globally")


@bot.command(name="privatecmdsync")
async def private_sync_command(ctx: commands.Context):
    if not ctx.author.id == 153945414683328513:
        return await ctx.reply("You do not have permission to use this command.")
    await bot.tree.sync(guild=discord.Object(id=os.environ["DEVELOPMENT_SERVER_ID"]))
    print("Private commands synces")

@bot.command(name="removeallcmds")
async def remove_all_commands(ctx: commands.Context):
    if not ctx.author.id == 153945414683328513:
        return await ctx.reply("You do not have permission to use this command.")
    bot.tree.sync(guild=discord.Object(id=os.environ["DEVELOPMENT_SERVER_ID"]))
    print("Synced")
    await bot.tree.remove_command("join")
    await bot.tree.remove_command("leave")
    await bot.tree.remove_command("play")
    await bot.tree.remove_command("stop")
    await bot.tree.remove_command("pause")
    await bot.tree.remove_command("resume")
    await bot.tree.remove_command("volume")
    await bot.tree.remove_command("search")
    await bot.tree.remove_command("seek")
    await bot.tree.remove_command("loop")
    await bot.tree.remove_command("queue")
    await bot.tree.remove_command("skip")
    await bot.tree.remove_command("introduce")
    await bot.tree.remove_command("define")
    await bot.tree.remove_command("urban_define")
    await bot.tree.remove_command("r34")
    await bot.tree.remove_command("dalle")
    await bot.tree.remove_command("deepai")
    print("All commands removed.")

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