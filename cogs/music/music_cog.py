import discord
from discord import InteractionResponded, NotFound, app_commands, errors
from discord.ext import commands
import asyncio
from typing import Optional
import wavelink
import datetime
import os

class Music(commands.GroupCog, name="music"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        bot.loop.create_task(self.create_nodes())
        super().__init__()
    
    async def create_nodes(self):
        await self.bot.wait_until_ready()
        await wavelink.NodePool.create_node(bot=self.bot, host="lavalink.oops.wtf", port=443, password="www.freelavalink.ga", https=True)

    @commands.Cog.listener()
    async def on_ready(self):
        print("Music cog is now ready.")

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        print(f"Wavelink node ready.\n Node <{node.identifier}>")

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, player: wavelink.Player, track: wavelink.YouTubeTrack, reason):
        try:
            interaction = player.interaction
            vc = player.client.voice_clients[0]

            if vc.loop:
                return await vc.play(track)
            
            next_song = await vc.queue.get_wait()

            await vc.play(next_song)
            embed = discord.Embed(  title=f"Now playing: {next_song}",
                                    description=f"[{next_song.author} - {next_song.title}]({next_song.uri})\n`00:00:00 - {str(datetime.timedelta(seconds=next_song.duration))}`",
                                    color=discord.Color.from_rgb(255, 255, 255))
            embed.set_thumbnail(url=next_song.thumbnail)
            await interaction.followup.send(embed=embed)
        except AttributeError:
            pass

    @app_commands.command(name="join", description="Get Brian to join your current voice channel")
    async def join_command(self, interaction: discord.Interaction, channel: Optional[discord.VoiceChannel]):
        node = wavelink.NodePool.get_node()
        player = node.get_player(interaction.user.guild)

        if channel is None:
            channel = interaction.user.voice.channel

        if player is not None and player.is_connected():
            embed = discord.Embed(title="I'm already connected to a voice channel", color=discord.Color.from_rgb(255, 0, 0))
            return await interaction.response.send_message(embed=embed)

        await channel.connect(cls=wavelink.Player)
        embed = discord.Embed(title=f"Connected to {channel.name}", color=discord.Color.from_rgb(255, 255, 255))
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leave", description="Get Brian to leave his current voice channel")
    async def leave_command(self, interaction: discord.Interaction):
        node = wavelink.NodePool.get_node()
        player = node.get_player(interaction.user.guild)

        if player is None:
            embed = discord.Embed(title="I'm not connected to a voice channel", color=discord.Color.from_rgb(255, 0, 0))
            return await interaction.response.send_message(embed=embed)

        await player.disconnect()
        embed = discord.Embed(title="Disconnected", color=discord.Color.from_rgb(255, 255, 255))
        return await interaction.response.send_message(embed=embed)

    @app_commands.command(name="play", description="Get Brian to search and play something in the voice channel")
    async def play_command(self, interaction: discord.Interaction, *, search: str):
        """Plays the first YouTube result from a given search.

        __**Command:**__
        ```=play <search>```
        __**Examples:**__
        ```=play Minecraft Wet Hands Vibrato```
        """
        if interaction.user.voice is None:
            embed = discord.Embed(title="Please connect to a voice channel to use this command.", color=discord.Color.from_rgb(255, 0, 0))
            return await interaction.response.send_message(embed=embed)

        search = await wavelink.YouTubeTrack.search(query=search, return_first=True)
        await self.manage_song(interaction, search)

    @staticmethod
    async def manage_song(interaction: discord.Interaction, song: wavelink.YouTubeTrack):
        if not interaction.client.voice_clients:
            vc: wavelink.Player = await interaction.user.voice.channel.connect(cls=wavelink.Player)
        else:
            vc: wavelink.Player = interaction.client.voice_clients[0]

        if vc.queue.is_empty:
            if vc.is_playing():
                await vc.queue.put_wait(song)
                embed = discord.Embed( title=f"Added to queue: {song}",
                                        description=f"[{song.author} - {song.title}]({song.uri})\n`00:00:00 - {str(datetime.timedelta(seconds=song.duration))}`",
                                        color=discord.Color.from_rgb(255, 255, 255))
                embed.set_thumbnail(url=song.thumbnail)
                
                return await interaction.followup.send(embed=embed)
            else:
                await vc.play(song)
                embed = discord.Embed(  title=f"Now playing: {song}",
                                        description=f"[{song.author} - {song.title}]({song.uri})\n`00:00:00 - {str(datetime.timedelta(seconds=song.duration))}`",
                                        color=discord.Color.from_rgb(255, 255, 255))
                embed.set_thumbnail(url=song.thumbnail)
                await interaction.response.defer()
                return await interaction.followup.send(embed=embed)
        else:
            await vc.queue.put_wait(song)
            embed = discord.Embed( title=f"Added to queue: {song}",
                                    description=f"[{song.author} - {song.title}]({song.uri})\n`00:00:00 - {str(datetime.timedelta(seconds=song.duration))}`",
                                    color=discord.Color.from_rgb(255, 255, 255))
            embed.set_thumbnail(url=song.thumbnail)
            await interaction.response.defer()
            await interaction.followup.send(embed=embed)
        
        vc.interaction = interaction
        setattr(vc, "loop", False)

    @app_commands.command(name="stop", description="Stop Brian playing any tracks")
    async def stop_command(self, interaction: discord.Interaction):
        """Stops Brian singing completely.

        __**Command:**__
        ```=stop```
        """
        if interaction.user.voice is None:
            embed = discord.Embed(title="Please connect to a voice channel to use this command.", color=discord.Color.from_rgb(255, 0, 0))
            return await interaction.response.send_message(embed=embed)

        node = wavelink.NodePool.get_node()
        player = node.get_player(interaction.user.guild)

        if player is None:
            embed = discord.Embed(title="I'm not connected to a voice channel", color=discord.Color.from_rgb(255, 0, 0))
            return await interaction.response.send_message(embed=embed)

        if player.is_playing():
            await player.stop()
            embed = discord.Embed(title="Singing stopped", color=discord.Color.from_rgb(0, 255, 0))
            return await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(title="I'm not singing atm", color=discord.Color.from_rgb(0, 255, 0))
            return await interaction.response.send_message(embed=embed)

    @app_commands.command(name="pause", description="Pause Brian at current point in the track")
    async def pause_command(self, interaction: discord.Interaction):
        """Pauses Brian's singing.

        __**Command:**__
        ```=pause```
        """
        if interaction.user.voice is None:
            embed = discord.Embed(title="Please connect to a voice channel to use this command.", color=discord.Color.from_rgb(255, 0, 0))
            return await interaction.response.send_message(embed=embed)

        node = wavelink.NodePool.get_node()
        player = node.get_player(interaction.user.guild)

        if player is None:
            embed = discord.Embed(title="I'm not connected to a voice channel", color=discord.Color.from_rgb(255, 0, 0))
            return await interaction.response.send_message(embed=embed)

        if not player.is_paused():
            if player.is_playing():
                await player.pause()
                embed = discord.Embed(title="Singing paused", color=discord.Color.from_rgb(0, 255, 0))
                return await interaction.response.send_message(embed=embed)
            else:
                embed = discord.Embed(title="No track currently playing", color=discord.Color.from_rgb(255, 0, 0))
                return await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(title="Singing is already paused", color=discord.Color.from_rgb(255, 0, 0))
            return await interaction.response.send_message(embed=embed)
 
    @app_commands.command(name="resume", description="Resume Brian from previous pause point")
    async def resume_command(self, interaction: discord.Interaction):
        """Resumes Brian's singing.

        __**Command:**__
        ```=resume```
        """
        if interaction.user.voice is None:
            embed = discord.Embed(title="Please connect to a voice channel to use this command.", color=discord.Color.from_rgb(255, 0, 0))
            return await interaction.response.send_message(embed=embed)

        node = wavelink.NodePool.get_node()
        player = node.get_player(interaction.user.guild)

        if player is None:
            embed = discord.Embed(title="I'm not connected to a voice channel", color=discord.Color.from_rgb(255, 0, 0))
            return await interaction.response.send_message(embed=embed)

        if player.is_paused:
            await player.resume()
            embed = discord.Embed(title="Singing resumed", color=discord.Color.from_rgb(0, 255, 0))
            return await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(title="Singing isn't paused", color=discord.Color.from_rgb(0, 255, 0))
            return await interaction.response.send_message(embed=embed)

    @app_commands.command(name="volume", description="Change Brians playback volume")
    async def volume_command(self, interaction: discord.Interaction, volume: int):
        """Changes volume of Brian's singing.

        __**Command:**__
        ```=volume [number]```
        __**Example:**__
        ```=volume 75```
        """
        if interaction.user.voice is None:
            embed = discord.Embed(title="Please connect to a voice channel to use this command.", color=discord.Color.from_rgb(255, 0, 0))
            return await interaction.response.send_message(embed=embed)

        vScaled = round((volume - 1) * (5 - 0.1) / (100 - 1) + 0.1, 1)

        if volume > 100 or volume < 0:
            embed = discord.Embed(title="Volume should be between 0 and 100", color=discord.Color.from_rgb(255, 0, 0))
            return await interaction.response.send_message(embed=embed)

        node = wavelink.NodePool.get_node()
        player = node.get_player(interaction.user.guild)

        if volume == 0:
            await player.set_volume(vScaled)
            embed = discord.Embed(title=f"Volume muted", color=discord.Color.from_rgb(0, 255, 0))
            return await interaction.response.send_message(embed=embed)
        else:
            await player.set_volume(vScaled)
            embed = discord.Embed(title=f"Volume changed to {volume}", color=discord.Color.from_rgb(0, 255, 0))
            return await interaction.response.send_message(embed=embed)

    @app_commands.command(name="search", description="Search for a return multiple YouTube tracks to pick and play")
    async def search_command(self, interaction: discord.Interaction, amount: Optional[int] = 5, *, search: str):
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
        if interaction.user.voice is None:
            embed = discord.Embed(title="Please connect to a voice channel to use this command.", color=discord.Color.from_rgb(255, 0, 0))
            return await interaction.response.send_message(embed=embed)

        if amount > 10:
            amount = 10
            embed = discord.Embed(title="Search amount cannot be greater than 10.", color=discord.Color.from_rgb(0, 255, 0))
            return await interaction.response.send_message(embed=embed)

        search = await wavelink.YouTubeTrack.search(query=search, return_first=False)
        emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟', '❌']

        embed = discord.Embed(title=f"Query Results:\n",
                            color=discord.Color.from_rgb(0, 255, 0))

        for x in range(amount):
            embed.add_field(name=f"{x + 1}. {search.__getitem__(x).title}",
                        value=f"{search.__getitem__(x).author} `{str(datetime.timedelta(seconds=search.__getitem__(x).duration))}`\n",
                        inline=False)

        await interaction.response.defer()
        message = await interaction.followup.send(embed=embed)
        for i in range(amount):
            await message.add_reaction(emojis[i])

        await message.add_reaction(emojis[len(emojis) - 1])

        def check(response, user):
            return user == interaction.user and response.emoji in ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟', '❌']

        try:
            reaction = await self.bot.wait_for('reaction_add', timeout=20.0, check=check)
        except asyncio.TimeoutError:
            embed = discord.Embed(title=f"{interaction.user.name} Didn't react in time",
                                color=discord.Color.from_rgb(255, 0, 0))
            return await interaction.followup.send(embed=embed)
        else:
            for x in range(amount):
                if reaction[0].emoji == emojis[x]:
                    embed = discord.Embed(title=f"Track {x + 1} picked: {search.__getitem__(x).title}",
                                        color=discord.Color.from_rgb(0, 255, 0))
                    await interaction.followup.send(embed=embed)
                    await self.manage_song(interaction, search.__getitem__(x))


            if reaction[0].emoji == emojis[len(emojis) - 1]:
                embed = discord.Embed(title=f"Selection Cancelled.", color=discord.Color.from_rgb(255, 0, 0))
                return await interaction.followup.send(embed=embed)

    @app_commands.command(name="seek", description="Jump to a specific point in the track. Format: hh:mm:ss")
    async def seek_command(self, interaction: discord.Interaction, timestamp: Optional[str], current: Optional[bool]):
        """Skips to a timestamp within the current track.

        Supported formats:
        `HH:MM:SS` `MM:SS` `SS`
        If only seconds supplied any number can be entered and will be converted to `HH:MM:SS`

        __**Examples:**__
        ```=seek 80
        =seek 2:45
        =seek 1:20:24```
        """
        if interaction.user.voice is None:
            embed = discord.Embed(title="Please connect to a voice channel to use this command.", color=discord.Color.from_rgb(255, 0, 0))
            return await interaction.response.send_message(embed=embed)
    
        node = wavelink.NodePool.get_node()
        player = node.get_player(interaction.user.guild)

        if player.track is None:
            embed = discord.Embed(title="No track currently playing", color=discord.Color.from_rgb(255, 0, 0))
            return await interaction.response.send_message(embed=embed)

        hours = 0
        minutes = 0
        seconds = 0

        if current is True:
            embed = discord.Embed(title=f"Current time stamp is: `{str(datetime.timedelta(seconds=(int(player.position))))}`", 
                                    color=discord.Color.from_rgb(0, 255, 0))
            return await interaction.response.send_message(embed=embed)

        timestamp = timestamp.split(":")

        if len(timestamp) == 1:
            seconds = int(timestamp[0]) % (24 * 3600)
            hours = seconds // 3600
            seconds %= 3600
            minutes = seconds // 60
            seconds %= 60
        elif len(timestamp) == 2:
            minutes = int(timestamp[0])
            seconds = int(timestamp[1])
            hours = 0
        elif len(timestamp) == 3:
            hours = int(timestamp[0])
            minutes = int(timestamp[1])
            seconds = int(timestamp[2])

        if hours is not None and hours < 0:
            embed = discord.Embed(name=f"Hours should be above 0", 
                                    color=discord.Color.from_rgb(255, 0, 0))
            return await interaction.response.send_message(embed=embed)
        if minutes is not None and minutes < 0 or minutes > 59:
            embed = discord.Embed(name=f"Minutes should be between 0 - 59", 
                                    color=discord.Color.from_rgb(255, 0, 0))
            return await interaction.response.send_message(embed=embed)
        if seconds < 0:
            embed = discord.Embed(name=f"Seconds should be at least 0", 
                                    color=discord.Color.from_rgb(255, 0, 0))
            return await interaction.response.send_message(embed=embed)

        totalSeconds = (seconds + (minutes * 60) + ((hours * 60) * 60)) * 1000

        await player.seek(totalSeconds)
        embed = discord.Embed(title=f"Skipped to {hours}h {minutes}m and {seconds}s", 
                                color=discord.Color.from_rgb(0, 255, 0))
        return await interaction.response.send_message(embed=embed)

    @app_commands.command(name="loop")
    async def loop_command(self, interaction: discord.Interaction):
        """Toggles track looping on current playing track.

        __**Command:**__
        ```=looping```
        """
        if interaction.user.voice is None:
            embed = discord.Embed(title="Please connect to a voice channel to use this command.", color=discord.Color.from_rgb(255, 0, 0))
            return await interaction.response.send_message(embed=embed)

        if not interaction.client.voice_clients:
            vc: wavelink.Player = await interaction.user.voice.channel.connect(cls=wavelink.Player)
        else:
            vc: wavelink.Player = interaction.client.voice_clients[0]
        
        try:
            vc.loop ^= True
        except Exception:
            setattr(vc, "loop", False)
        
        if vc.loop:
            embed = discord.Embed(title=f"Looping is now enabled",
                                color=discord.Color.from_rgb(0, 255, 0))
            return await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(title=f"Looping is now disabled",
                                color=discord.Color.from_rgb(0, 255, 0))
            return await interaction.response.send_message(embed=embed)

    @app_commands.command(name="queue")
    async def queue_command(self, interaction: discord.Interaction):
        """Displays all tracks in the queue.

        __**Command:**__
        ```=queue```
        """
        if not interaction.client.voice_clients:
            return print("not playing so no queue")
        else:
            vc: wavelink.Player = interaction.client.voice_clients[0]
        
        if vc.queue.is_empty:
            embed = discord.Embed(title=f"Queue is empty.",
                                color=discord.Color.from_rgb(255, 255, 255))
            return await interaction.response.send_message(embed=embed)
        
        embed = discord.Embed(title="Current Queue", 
                                color=discord.Color.from_rgb(255, 255, 255))
        queue = vc.queue.copy()
        song_count = 0
        for song in queue:
            song_count += 1
            embed.add_field(name=f"{song_count}. {song.title}", value=f"{song.author}", inline=False)
        
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
        if interaction.user.voice is None:
            embed = discord.Embed(title="Please connect to a voice channel to use this command.", color=discord.Color.from_rgb(255, 0, 0))
            return await interaction.response.send_message(embed=embed)

        node = wavelink.NodePool.get_node()
        player = node.get_player(interaction.user.guild)

        if not interaction.client.voice_clients:
            return print("Not playing so cant skip")
        else:
            vc: wavelink.Player = interaction.client.voice_clients[0]
        
        if vc.queue.is_empty:
            embed = discord.Embed(title=f"Queue is empty.",
                                color=discord.Color.from_rgb(255, 255, 255))
            return await interaction.response.send_message(embed=embed)
        
        if all == "all":
            vc.queue.clear()
            embed = discord.Embed(title=f"Queue Cleared!",
                            color=discord.Color.from_rgb(255, 255, 255))
            return await interaction.response.send_message(embed=embed)
        else:
            queue = vc.queue.copy()
            next_song = queue.get()

            await player.stop()
            embed = discord.Embed(title=f"Song Skipped! now playing: {next_song}",
                            color=discord.Color.from_rgb(255, 255, 255))
            return await interaction.response.send_message(embed=embed)
        
    def get_player(self, obj):
        if isinstance(obj, commands.Context):
            return self.bot.wavelink.get_player(obj.guild.id, cls=wavelink.Player, context=obj)
        elif isinstance(obj, discord.Guild):
            return self.bot.wavelink.get_player(obj.id, cls=wavelink.Player)
    
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
            print("Message has already been responded too, couldnt send last part to discord channel")

async def setup(bot: commands.Bot) -> None:
    # Global Sync
    await bot.add_cog(Music(bot))
    # Private Sync
    #await bot.add_cog(Music(bot), guilds=[discord.Object(id=os.environ["DEVELOPMENT_SERVER_ID"])])