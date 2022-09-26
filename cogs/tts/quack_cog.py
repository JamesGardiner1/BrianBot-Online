import discord
from discord import app_commands, FFmpegPCMAudio, errors
from discord.ext import commands
from discord.app_commands import Choice
from io import BytesIO
import json
import time
import tempfile
import asyncio
import aiohttp
from datetime import datetime, timedelta
import os

API_ROOT = 'https://api.uberduck.ai'

guild_to_voice_client = dict()
generating = False

async def query_uberduck(text, voice):
    max_time = 60
    async with aiohttp.ClientSession() as session:
        url = f"{API_ROOT}/speak"
        data = json.dumps(
            {
                "speech": text,
                "voice": voice,
            }
        )

        start = time.time()
        async with session.post(url, data=data, auth=aiohttp.BasicAuth(os.environ["UBERDUCK_API_KEY"], os.environ["UBERDUCK_API_SECRET"])) as r:
            if r.status != 200:
                raise Exception("Error synthesizing speech", await r.json())
            uuid = (await r.json())["uuid"]
        while True:
            if time.time() - start > max_time:
                raise Exception("Request timed out!")
            await asyncio.sleep(1)
            status_url = f"{API_ROOT}/speak-status"
            async with session.get(status_url, params={"uuid": uuid}) as r:
                if r.status != 200:
                    continue
                response = await r.json()
                if response["path"]:
                    async with session.get(response["path"]) as r:
                        return BytesIO(await r.read())

async def terminate_stale_voice_connections():
    while True:
        await asyncio.sleep(5)
        for k in list(guild_to_voice_client.keys()):
            v = guild_to_voice_client[k]
            voice_client, last_used = v
            if datetime.utcnow() - last_used > timedelta(minutes=10):
                await voice_client.disconnect()
                guild_to_voice_client.pop(k)

async def _get_or_create_voice_client(ctx: discord.Interaction):
    joined = False
    if ctx.guild.id in guild_to_voice_client:
        voice_client, _ = guild_to_voice_client[ctx.guild.id]
    else:
        voice_channel = _context_to_voice_channel(ctx)
        if voice_channel is None:
            voice_client = None
        else:
            voice_client = await voice_channel.connect()
            joined = True
    return (voice_client, joined)

def _context_to_voice_channel(interaction: discord.Interaction):
    return interaction.user.voice.channel if interaction.user.voice else None

async def _send_help(interaction: discord.Interaction):
    await interaction.response.send_message("See https://uberduck.ai/quack-help for instructions on using the bot commands. Make sure you enter a voice that exactly matches one of the listed voices.")


class QuackTTS(commands.GroupCog, name="quack"):
    def __init__(self, bot: commands.Bot) -> None:
        self.cwd = os.getcwd()
        self.bot = bot
        self.is_available = True
        super().__init__()
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("QuackTTS cog is now ready.")

    @app_commands.command(name="tts", description="Make Brian say whatever you want in a variety of voices")
    async def tts_command(self, interaction: discord.Interaction, voices: str, speech: str) -> None:
            voice_client, _ = await _get_or_create_voice_client(interaction)
            if self.is_available is True:
                self.is_available = False
                try:
                    if voice_client:
                        guild_to_voice_client[interaction.guild.id] = (voice_client, datetime.utcnow())
                        await interaction.response.defer(thinking=True)
                        audio_data = await query_uberduck(speech, voices)
                        self.is_generating = True
                        with tempfile.NamedTemporaryFile(suffix=".wav", dir=self.cwd, delete=False) as wav_f:
                            wav_f.write(audio_data.getvalue())
                            wav_f.flush()
                            print(wav_f.name)
                            source = FFmpegPCMAudio(wav_f.name)
                            self.is_generating = False
                            await interaction.followup.send("Speech generated. Playing now.")

                        try:
                            voice_client.play(source, after=None)
                            while voice_client.is_playing():
                                print("Playing..")
                                await asyncio.sleep(0.5)
                        finally:
                            print("Stopped.")
                            self.is_available = True
                            os.remove(wav_f.name)
                            voice_client, _ = guild_to_voice_client.pop(interaction.guild.id)
                            await voice_client.disconnect()

                    else:
                        await interaction.followup.send("You're not in a voice channel. Join a voice channel to invite the bot!", ephemeral=True)
                        self.is_available = True
                except Exception as e:
                    await interaction.followup.send(f"Encountered Error. {e}")
                    self.is_available = True
            else:
                await interaction.response.send_message("Brians TTS is currently in use.")

    @app_commands.command(name="help", description="List all TTS voices")
    async def help_command(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(title=f"UbderDuck Quack Help", color=discord.Color.from_rgb(0, 255, 0))
        embed.add_field(name=f"UberDuck AI Help", value="Visit [UberDuck Help Page](https://app.uberduck.ai/quack-help) for a list of voices and how to use them.")
        embed.set_thumbnail(url="https://app.uberduck.ai/_ipx/w_640,q_75/%2Fuberduck-neon.jpg?url=%2Fuberduck-neon.jpg&w=640&q=75")
        embed.set_footer(text="If you encounter any issues use /quack kick and /quack join to restart Brian.")
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot) -> None:
    # Global Sync
    #await bot.add_cog(QuackTTS(bot))
    # Private Sync
    await bot.add_cog(QuackTTS(bot), guilds=[discord.Object(id=os.environ["DEVELOPMENT_SERVER_ID"])])