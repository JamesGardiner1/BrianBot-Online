import discord
from discord import app_commands, FFmpegPCMAudio
from discord.ext import commands
import discord.app_commands
from io import BytesIO
import json
import time
import tempfile
import asyncio
import aiohttp
from datetime import datetime
import os

GLOBAL_SYNC = True

API_ROOT = 'https://api.uberduck.ai'

guild_to_voice_client = dict()

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


async def get_or_create_voice_client(interaction: discord.Interaction):
    #if users guild id is in voice_client dictionary
    if interaction.guild.id in guild_to_voice_client:
        #set variables to the guild id
        voice_client, _ = guild_to_voice_client[interaction.guild.id]
    else:
        #else set vc to users voice channel if the user has one
        voice_channel = context_to_voice_channel(interaction)
        #if user has no voice channel then voice client is set to None
        if voice_channel is None:
            voice_client = None
        else:
            #If it is not none we connect Brian to the channel and set joined to True
            voice_client = await voice_channel.connect()
    #return the voice client and bool
    return (voice_client)

def context_to_voice_channel(interaction: discord.Interaction):
    #return users voice channel if the user is connected to a voice channel. Else returns None
    return interaction.user.voice.channel if interaction.user.voice else None

class QuackTTS(commands.GroupCog, name="quack"):
    def __init__(self, bot: commands.Bot) -> None:
        self.cwd = os.getcwd()
        self.bot = bot
        self.is_available = True
        super().__init__()
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"QuackTTS cog is now ready. Synced Globally: {GLOBAL_SYNC}")
    
    @app_commands.command(name="join", description="Get TTS Brian to join the call.")
    async def join_vc(self, interaction: discord.Interaction) -> None:
        #create and set voice client to voice channel user is connected to
        voice_client = await get_or_create_voice_client(interaction)
        #if None we send message informing user
        if voice_client is None:
            embed = discord.Embed(title=f"You're not currently connected to a voice channel", colour=discord.Color.from_rgb(255, 0, 0))
            await interaction.response.send_message(embed=embed, ephemeral=True)
        
        #voice clients channel id doesnt match the users voice channel id
        if voice_client.channel.id != interaction.user.voice.channel.id:
            #store the connected voice channels name
            old_channel_name = voice_client.channel.name
            #disconnect the voice client
            await voice_client.disconnect()
            #set up new voice client and connect to the users current voice channel
            voice_client = await interaction.user.voice.channel.connect()
            #store new voice clients channel name
            new_channel_name = voice_client.channel.name
            #add the users guild(server) to dictionary with the voice client and current time
            guild_to_voice_client[interaction.guild.id] = (voice_client, datetime.utcnow())
            await interaction.response.send_message(f"Switched from #{old_channel_name} to #{new_channel_name}")
        else:
            #send message add the users guild(server) to dictionary with the voice client and current time
            await interaction.response.send_message("Connected to a voice channel")
            guild_to_voice_client[interaction.guild.id] = (voice_client, datetime.utcnow)


    @app_commands.command(name="leave", description="Get TTS Brian to leave the call.")
    async def kick_vc(self, interaction: discord.Interaction) -> None:
        #if users guild(server) id is in dictionary
        if interaction.guild.id in guild_to_voice_client:
            #remove guild from dictionary, disconnect Brian and send message
            voice_client, _ = guild_to_voice_client.pop(interaction.guild.id)
            await voice_client.disconnect()
            embed = discord.Embed(title=f"Disconnected from the voice channel", colour=discord.Color.from_rgb(0, 255, 0))
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(title=f"Brian is not connected to a voice channel", colour=discord.Color.from_rgb(255, 0, 0))
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="tts", description="Make Brian say whatever you want in a variety of voices")
    async def tts_command(self, interaction: discord.Interaction, voices: str, speech: str) -> None:
            voice_client, _ = await get_or_create_voice_client(interaction)
            
            if self.is_available is True:
                self.is_available = False
                try:
                    if voice_client:
                        guild_to_voice_client[interaction.guild.id] = (voice_client, datetime.utcnow())
                        await interaction.response.defer(thinking=True)
                        audio_data = await query_uberduck(speech, voices)
                        self.is_generating = True
                        with tempfile.NamedTemporaryFile(suffix=".wav", dir=self.cwd, delete=False) as wav_f:
                            #write audio data to wav_f file
                            wav_f.write(audio_data.getvalue())
                            wav_f.flush()
                            #assign source to play
                            source = FFmpegPCMAudio(wav_f.name)
                            #turn of is_generating
                            self.is_generating = False
                            #send message to show generation is complete
                            embed = discord.Embed(title=f"Speech generation complete. Playing audio now", color=discord.Color.from_rgb(0, 255, 0))
                            await interaction.followup.send(embed=embed, ephemeral=True)
                        try:
                            #try clause to catch any errors
                            #play the source with current voice_client
                            voice_client.play(source, after=None)
                            #Delay continueing while Brian is playing
                            while voice_client.is_playing():
                                await asyncio.sleep(0.5)
                        except Exception as e:
                            embed = discord.Embed(title=f"Encountered Error", description=f"error: `{e}`")
                            await interaction.followup.send(embed=embed, ephemeral=True)
                        finally:
                            #proceeds when audio stops and makes Brian available again
                            self.is_available = True
                            #remove previously generated file
                            os.remove(wav_f.name)
                            #disconnects Brian automatically
                            voice_client, _ = guild_to_voice_client.pop(interaction.guild.id)
                            await voice_client.disconnect()
                    else:
                        embed = discord.Embed(title=f"You're not in a voice channel. Please join a voice channel to use Quack TTS", color=discord.Color.from_rgb(255, 0, 0))
                        await interaction.followup.send(embed=embed, ephemeral=True)
                        self.is_available = True
                except Exception as e:
                    embed = discord.Embed(title=f"Encountered Error", description=f"error: `{e}`")
                    await interaction.followup.send(embed=embed)
                    self.is_available = True
            else:
                embed = discord.Embed(title=f"Brians TTS is currently in use.", color=discord.Color.from_rgb(255, 0, 0))
                await interaction.response.send_message(embed=embed, ephemeral=True)


    @app_commands.command(name="help", description="List all TTS voices")
    async def help_command(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(title=f"UbderDuck Quack Help", color=discord.Color.from_rgb(0, 255, 0))
        embed.add_field(name=f"UberDuck AI Help", value="Visit [UberDuck Help Page](https://app.uberduck.ai/quack-help) for a list of voices and how to use them.")
        embed.set_thumbnail(url="https://app.uberduck.ai/_ipx/w_640,q_75/%2Fuberduck-neon.jpg?url=%2Fuberduck-neon.jpg&w=640&q=75")
        embed.set_footer(text="If you encounter any issues use /quack kick and /quack join to restart Brian.")
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot) -> None:
    if GLOBAL_SYNC:
        # Global Sync
        await bot.add_cog(QuackTTS(bot))
    else:
        # Private Sync
        await bot.add_cog(QuackTTS(bot), guilds=[discord.Object(id=os.environ["DEVELOPMENT_SERVER_ID"])])