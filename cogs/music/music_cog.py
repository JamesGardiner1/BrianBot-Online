import discord
from discord import InteractionResponded, NotFound, app_commands
from discord.ext import commands
import asyncio
from typing import Optional
import wavelink
import datetime
import os
from config import GLOBAL_SYNC

commandExamples = dict()
commandExamples = {
    "join": "/music join OPTIONAL<channel name>",
    "leave": "/music leave",
    "play": "/music play <query>",
    "stop": "/music stop",
    "pause": "/music pause",
    "resume": "/music resume",
    "volume": "/music volume <number 0 - 100>",
    "search": "/music search <query> OPTIONAL<results 1 - 10>",
    "seek": "/music seek <hours> <minutes> <seconds> OR /seek <current>",
    "loop": "/music loop",
    "queue": "/music queue",
    "skip": "/music skip OPTIONAL<all>",
    "help": "/music help",
}


class Music(commands.GroupCog, name="music"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        bot.loop.create_task(self.create_nodes())
        super().__init__()

    current_channel = -1

    # Create wavelink nodes for track playing
    async def create_nodes(self):
        await self.bot.wait_until_ready()

        node: wavelink.Node = wavelink.Node(
            uri="212.192.29.91:25529", password="reedrouxv4lavalink"
        )
        await wavelink.NodePool.connect(client=self.bot, nodes=[node])

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Music cog is now ready. Synced Globally: {GLOBAL_SYNC}")

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        print(f"Wavelink node ready.\n Node <{node}>")

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackEventPayload):
        current_song = payload.track

        channel = payload.player.client.get_channel(self.current_channel)
        embed = discord.Embed(
            title=f"Now playing: {current_song}",
            description=f"[{current_song.author} - {current_song.title}]({current_song.uri})\n`{convert_from_millis(current_song.duration)}`",
            color=discord.Color.from_rgb(255, 255, 255),
        )

        await channel.send(embed=embed)

    @app_commands.command(
        name="connect", description="Get Brian to join your current voice channel"
    )
    async def connect_command(
        self,
        interaction: discord.Interaction,
        *,
        channel: discord.VoiceChannel | None = None,
    ):
        try:
            channel = channel or interaction.user.voice.channel
        except AttributeError:
            embed = discord.Embed(
                title=f"No voice channel to connect to. Please either join one or provide me one to join",
                color=discord.Color.from_rgb(255, 0, 0),
            )
            return await interaction.response.send_message(embed=embed)

        await channel.connect(cls=wavelink.Player)

        embed = discord.Embed(
            title=f"Connected to {channel}",
            color=discord.Color.from_rgb(0, 255, 0),
        )
        return await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="disconnect", description="Get Brian to leave his current voice channel"
    )
    async def disconnect_command(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client

        if vc is None:
            embed = discord.Embed(
                title="I'm not connected to a voice channel",
                color=discord.Color.from_rgb(255, 0, 0),
            )
            return await interaction.response.send_message(embed=embed)

        await vc.disconnect()
        embed = discord.Embed(
            title="Disconnected", color=discord.Color.from_rgb(255, 255, 255)
        )
        return await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="play",
        description="Get Brian to search and play something in the voice channel",
    )
    async def play_command(self, interaction: discord.Interaction, *, search: str):
        """Plays the first YouTube result from a given search.

        __**Command:**__
        ```=play <search>```
        __**Examples:**__
        ```=play Minecraft Wet Hands Vibrato```
        """
        self.current_channel = interaction.channel_id
        vc: wavelink.Playable = interaction.guild.voice_client

        if not vc:
            channel = interaction.user.voice.channel
            vc: wavelink.Player = await channel.connect(cls=wavelink.Player)

        vc.autoplay = True

        results = await wavelink.YouTubeTrack.search(search)

        await interaction.response.defer()
        return await self.manage_song(interaction, results[0], vc)

    @staticmethod
    async def manage_song(
        interaction: discord.Interaction,
        song: wavelink.YouTubeTrack,
        vc: wavelink.Player,
    ):
        # if we're playing, put song in queue
        if vc.is_playing():
            embed = discord.Embed(
                title=f"Added to queue: {song}",
                description=f"[{song.author} - {song.title}]({song.uri})\n`{convert_from_millis(song.duration)}`",
                color=discord.Color.from_rgb(255, 255, 255),
            )
            embed.set_thumbnail(url=song.thumbnail)
            await interaction.followup.send(embed=embed)
            return await vc.queue(song)
        else:
            embed = discord.Embed(
                title=f"Attempting to play {song}",
                color=discord.Color.from_rgb(0, 255, 0),
            )
            await interaction.followup.send(embed=embed)
            return await vc.play(song)

    @app_commands.command(name="stop", description="Stop Brian playing any tracks")
    async def stop_command(self, interaction: discord.Interaction):
        """Stops Brian singing completely.

        __**Command:**__
        ```=stop```
        """
        self.current_channel = interaction.channel_id
        if interaction.user.voice is None:
            embed = discord.Embed(
                title="Please connect to a voice channel to use this command.",
                color=discord.Color.from_rgb(255, 0, 0),
            )
            return await interaction.response.send_message(embed=embed)

        vc = interaction.guild.voice_client

        if vc is None:
            embed = discord.Embed(
                title="I'm not connected to a voice channel",
                color=discord.Color.from_rgb(255, 0, 0),
            )
            return await interaction.response.send_message(embed=embed)

        if vc.is_playing():
            await vc.stop()
            await vc.disconnect()
            embed = discord.Embed(
                title="Singing stopped", color=discord.Color.from_rgb(0, 255, 0)
            )
            return await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(
                title="I'm not singing atm", color=discord.Color.from_rgb(255, 255, 255)
            )
            return await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="pause", description="Pause Brian at current point in the track"
    )
    async def pause_command(self, interaction: discord.Interaction):
        """Pauses Brian's singing.

        __**Command:**__
        ```=pause```
        """
        self.current_channel = interaction.channel_id
        if interaction.user.voice is None:
            embed = discord.Embed(
                title="Please connect to a voice channel to use this command.",
                color=discord.Color.from_rgb(255, 0, 0),
            )
            return await interaction.response.send_message(embed=embed)

        vc = interaction.guild.voice_client

        if vc is None:
            embed = discord.Embed(
                title="I'm not connected to a voice channel. Either use /connect or /play to get me to join.",
                color=discord.Color.from_rgb(255, 0, 0),
            )
            return await interaction.response.send_message(embed=embed)

        if not vc.is_paused():
            if vc.is_playing():
                await vc.pause()
                embed = discord.Embed(
                    title="Singing paused", color=discord.Color.from_rgb(0, 255, 0)
                )
                return await interaction.response.send_message(embed=embed)
            else:
                embed = discord.Embed(
                    title="No track currently playing",
                    color=discord.Color.from_rgb(255, 0, 0),
                )
                return await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(
                title="Singing is already paused",
                color=discord.Color.from_rgb(255, 0, 0),
            )
            return await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="resume", description="Resume Brian from previous pause point"
    )
    async def resume_command(self, interaction: discord.Interaction):
        """Resumes Brian's singing.

        __**Command:**__
        ```=resume```
        """
        self.current_channel = interaction.channel_id
        if interaction.user.voice is None:
            embed = discord.Embed(
                title="Please connect to a voice channel to use this command.",
                color=discord.Color.from_rgb(255, 0, 0),
            )
            return await interaction.response.send_message(embed=embed)

        vc = interaction.guild.voice_client

        if vc is None:
            embed = discord.Embed(
                title="I'm not connected to a voice channel",
                color=discord.Color.from_rgb(255, 0, 0),
            )
            return await interaction.response.send_message(embed=embed)

        if vc.is_paused():
            await vc.resume()
            embed = discord.Embed(
                title="Singing resumed", color=discord.Color.from_rgb(0, 255, 0)
            )
            return await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(
                title="Singing isn't paused", color=discord.Color.from_rgb(0, 255, 0)
            )
            return await interaction.response.send_message(embed=embed)

    @app_commands.command(name="volume", description="Change Brians playback volume")
    async def volume_command(self, interaction: discord.Interaction, volume: int):
        """Changes volume of Brian's singing.

        __**Command:**__
        ```=volume [number]```
        __**Example:**__
        ```=volume 75```
        """
        self.current_channel = interaction.channel_id
        if interaction.user.voice is None:
            embed = discord.Embed(
                title="Please connect to a voice channel to use this command.",
                color=discord.Color.from_rgb(255, 0, 0),
            )
            return await interaction.response.send_message(embed=embed)

        if volume > 1000 or volume < 0:
            embed = discord.Embed(
                title="Volume should be between 0 and 1000",
                color=discord.Color.from_rgb(255, 0, 0),
            )
            return await interaction.response.send_message(embed=embed)

        vc = interaction.guild.voice_client
        await vc.set_volume(volume)

        if volume == 0:
            embed = discord.Embed(
                title=f"Volume muted", color=discord.Color.from_rgb(0, 255, 0)
            )
            return await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(
                title=f"Volume changed to {volume}",
                color=discord.Color.from_rgb(0, 255, 0),
            )
            return await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="search",
        description="Search for a return multiple YouTube tracks to pick and play",
    )
    async def search_command(
        self,
        interaction: discord.Interaction,
        amount: Optional[int] = 5,
        *,
        search: str,
    ):
        """Returns a list of YouTube results from a given search.

        __**Command:**__
        ```
        =search [number] <search>
        ```
        `[number]` argument optional. If not specified the command will return 5 results

        __**Examples:**__
        ```=search niggamode
        =search 3 wet hands```
        """
        self.current_channel = interaction.channel_id
        if interaction.user.voice is None:
            embed = discord.Embed(
                title="Please connect to a voice channel to use this command.",
                color=discord.Color.from_rgb(255, 0, 0),
            )
            return await interaction.response.send_message(embed=embed)

        vc: wavelink.Playable = interaction.guild.voice_client

        if not vc:
            channel = interaction.user.voice.channel
            vc: wavelink.Player = await channel.connect(cls=wavelink.Player)

        if amount > 10:
            amount = 10
            embed = discord.Embed(
                title="Search amount cannot be greater than 10.",
                color=discord.Color.from_rgb(0, 255, 0),
            )
            return await interaction.response.send_message(embed=embed)

        search = await wavelink.YouTubeTrack.search(search)
        emojis = [
            "1️⃣",
            "2️⃣",
            "3️⃣",
            "4️⃣",
            "5️⃣",
            "6️⃣",
            "7️⃣",
            "8️⃣",
            "9️⃣",
            "🔟",
            "❌",
        ]

        embed = discord.Embed(
            title=f"Query Results:\n", color=discord.Color.from_rgb(0, 255, 0)
        )

        for x in range(amount):
            embed.add_field(
                name=f"{x + 1}. {search[x].title}",
                value=f"{search[x].author} `{convert_from_millis(search[x].duration)}`\n",
                inline=False,
            )

        await interaction.response.defer()
        message = await interaction.followup.send(embed=embed)
        for i in range(amount):
            await message.add_reaction(emojis[i])

        await message.add_reaction(emojis[len(emojis) - 1])

        def check(response, user):
            return user == interaction.user and response.emoji in [
                "1️⃣",
                "2️⃣",
                "3️⃣",
                "4️⃣",
                "5️⃣",
                "6️⃣",
                "7️⃣",
                "8️⃣",
                "9️⃣",
                "🔟",
                "❌",
            ]

        try:
            reaction = await self.bot.wait_for(
                "reaction_add", timeout=30.0, check=check
            )
        except asyncio.TimeoutError:
            embed = discord.Embed(
                title=f"{interaction.user.name} Didn't react in time",
                color=discord.Color.from_rgb(255, 0, 0),
            )
            return await interaction.followup.send(embed=embed)
        else:
            for x in range(amount):
                if reaction[0].emoji == emojis[x]:
                    embed = discord.Embed(
                        title=f"Track {x + 1} picked: {search[x].title}",
                        color=discord.Color.from_rgb(0, 255, 0),
                    )
                    await interaction.followup.send(embed=embed)
                    await self.manage_song(interaction, search[x], vc)

            if reaction[0].emoji == emojis[len(emojis) - 1]:
                embed = discord.Embed(
                    title=f"Selection Cancelled.",
                    color=discord.Color.from_rgb(255, 0, 0),
                )
                return await interaction.followup.send(embed=embed)

    @app_commands.command(
        name="timestamp",
        description="Return the current timestamp of a track being played.",
    )
    async def timestamp_command(self, interaction: discord.Interaction):
        self.current_channel = interaction.channel_id
        vc = interaction.guild.voice_client

        if vc.is_playing():
            embed = discord.Embed(
                title=f"Current time stamp is: `{convert_from_millis(vc.position)}`",
                color=discord.Color.from_rgb(0, 255, 0),
            )
            return await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(
                title=f"No track currently playing",
                color=discord.Color.from_rgb(255, 0, 0),
            )
            return await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="seek",
        description="Jump to a specific point in the track. Format: hh:mm:ss",
    )
    async def seek_command(
        self,
        interaction: discord.Interaction,
        hour: int,
        minute: int,
        second: int,
    ):
        """Skips to a timestamp within the current track.

        Supported formats:
        `HH:MM:SS` `MM:SS` `SS`
        If only seconds supplied any number can be entered and will be converted to `HH:MM:SS`

        __**Examples:**__
        ```=seek 80
        =seek 2:45
        =seek 1:20:24```
        """
        self.current_channel = interaction.channel_id
        if interaction.user.voice is None:
            embed = discord.Embed(
                title="Please connect to a voice channel to use this command.",
                color=discord.Color.from_rgb(255, 0, 0),
            )
            return await interaction.response.send_message(embed=embed)

        vc = interaction.guild.voice_client

        if not vc.is_playing():
            embed = discord.Embed(
                title="No track currently playing ",
                color=discord.Color.from_rgb(255, 0, 0),
            )
            return await interaction.response.send_message(embed=embed)

        hours = hour
        minutes = minute
        seconds = second

        if hours is not None and hours < 0:
            embed = discord.Embed(
                name=f"Hours should be above 0", color=discord.Color.from_rgb(255, 0, 0)
            )
            return await interaction.response.send_message(embed=embed)
        if minutes is not None and minutes < 0 or minutes > 59:
            embed = discord.Embed(
                name=f"Minutes should be between 0 - 59",
                color=discord.Color.from_rgb(255, 0, 0),
            )
            return await interaction.response.send_message(embed=embed)
        if seconds < 0:
            embed = discord.Embed(
                name=f"Seconds should be at least 0",
                color=discord.Color.from_rgb(255, 0, 0),
            )
            return await interaction.response.send_message(embed=embed)

        totalMillis = (seconds + (minutes * 60) + ((hours * 60) * 60)) * 1000

        await vc.seek(totalMillis)
        embed = discord.Embed(
            title=f"Skipped to {hours}h {minutes}m and {seconds}s",
            color=discord.Color.from_rgb(0, 255, 0),
        )
        return await interaction.response.send_message(embed=embed)

    @app_commands.command(name="queue")
    async def queue_command(self, interaction: discord.Interaction):
        """Displays all tracks in the queue.

        __**Command:**__
        ```=queue```
        """
        vc: wavelink.Player = interaction.guild.voice_client

        if vc.queue.is_empty:
            embed = discord.Embed(
                title=f"Queue is empty.", color=discord.Color.from_rgb(255, 255, 255)
            )
            return await interaction.response.send_message(embed=embed)

        embed = discord.Embed(
            title="Current Queue", color=discord.Color.from_rgb(255, 255, 255)
        )

        embed.add_field(name="", value="Up Next...", inline=False)

        embed.add_field(
            name=vc.queue[0].title,
            value=f"{vc.queue[0].author}. `{convert_from_millis(vc.queue[0].duration)}`",
            inline=False,
        )

        if vc.queue.count > 1:
            embed.add_field(
                name="",
                value="Later on...",
                inline=False,
            )
            for x in range(1, vc.queue.count):
                embed.add_field(
                    name=f"{x + 1}. {vc.queue[x].title}",
                    value=f"{vc.queue[x].author}. `{convert_from_millis(vc.queue[x].duration)}`",
                    inline=False,
                )

        return await interaction.response.send_message(embed=embed)

    @app_commands.command(name="skip")
    async def skip_command(self, interaction: discord.Interaction, all: Optional[bool]):
        """Skips to the next track in the queue.

        Command:
        ```=skip <all>```
        `[all]` argument optional. If written the whole queue will be cleared.

        __**Examples:**__
        ```=skip
        =skip all```
        """
        self.current_channel = interaction.channel_id
        if interaction.user.voice is None:
            embed = discord.Embed(
                title="Please connect to a voice channel to use this command.",
                color=discord.Color.from_rgb(255, 0, 0),
            )
            return await interaction.response.send_message(embed=embed)

        vc: wavelink.Player = interaction.guild.voice_client

        if vc.queue.is_empty:
            embed = discord.Embed(
                title=f"Queue is empty.", color=discord.Color.from_rgb(255, 255, 255)
            )
            return await interaction.response.send_message(embed=embed)

        if all == True:
            vc.queue.clear()
            embed = discord.Embed(
                title=f"Queue Cleared!", color=discord.Color.from_rgb(255, 255, 255)
            )
            return await interaction.response.send_message(embed=embed)

        next_song = await vc.queue.get_wait()
        await vc.play(next_song)

        embed = discord.Embed(
            title=f"Song Skipped!",
            color=discord.Color.from_rgb(255, 255, 255),
        )
        return await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="help", description="Get help with Bot Brians music commands"
    )
    async def music_help_command(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(
            title="Music Commands",
            description="List of all Bot Brians music commands with examples",
            color=discord.Color.from_rgb(0, 255, 0),
        )

        cog = self.bot.get_cog("music")
        group = cog.app_command
        for command in group.commands:
            embed.add_field(
                name=command.name,
                value=f"`{command.description}`\n`{commandExamples.get(command.name)}`",
                inline=False,
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # Error Handling
    @play_command.error
    async def play_command_error(self, interaction: discord.Interaction, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await interaction.response.send_message("Missing `Search` Parameter")
        if isinstance(error, NotFound):
            print("could not complete command on time, please try again")

    @volume_command.error
    async def volume_command_error(self, interaction: discord.Interaction, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await interaction.response.send_message("Missing `Volume` Parameter")

    @search_command.error
    async def search_command_error(self, interaction: discord.Interaction, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await interaction.response.send_message("Missing `Search` Parameter")
        if isinstance(error, InteractionResponded):
            print(
                "Message has already been responded too, couldnt send last part to discord channel"
            )


def convert_from_millis(millis: int) -> str:
    seconds = (millis / 1000) % 60
    seconds = int(seconds)
    minutes = (millis / (1000 * 60)) % 60
    minutes = int(minutes)
    hours = (millis / (1000 * 60 * 60)) % 24

    return "%02d:%02d:%02d" % (hours, minutes, seconds)


async def setup(bot: commands.Bot) -> None:
    if GLOBAL_SYNC:
        # Global Sync
        await bot.add_cog(Music(bot))
    else:
        # Private Sync
        await bot.add_cog(
            Music(bot), guilds=[discord.Object(id=os.environ["DEVELOPMENT_SERVER_ID"])]
        )
