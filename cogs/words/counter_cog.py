import discord
from discord import app_commands
from discord.ext import commands
import difflib
import random
import asyncio
import time
import os
from config import GLOBAL_SYNC

SIMILARITY_THRESHHOLD = 0.8


class Counter(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        """
        define init
        """
        self.bot = bot

    @app_commands.command(
        name="counter",
        description="Brian returns the amount of times someone has said one or multiple words (seperated with a ,).",
    )
    async def counter_command(
        self,
        interaction: discord.Interaction,
        words: str,
        user: discord.User | None = None,
        history: int | None = 100,
    ) -> None:
        """
        define command
        """
        try:
            user: discord.User = user or interaction.user
        except AttributeError as e:
            return print(f"Error occured: {e}")

        if interaction.user.id == 147439193323208704:
            return await handle_john(interaction)

        seperated_words: list[str] = split_user_input(words)
        normalized_words = normalize_words(seperated_words)

        await interaction.response.defer()
        embed: discord.Embed = create_embed(
            title=f"Collecting {user}'s messages. This may take some time depending on how far back you're searching.",
            description=None,
            rgb_colour=(0, 255, 0),
        )
        await interaction.followup.send(embed=embed)

        normalized_words = await calculate_word_occurances(
            interaction=interaction,
            history=history,
            user=user,
            normalized_words=normalized_words,
        )

        embed = create_embed(
            title="Completed!",
            description=f"Checked {normalized_words['total'][0]} messages from {user}",
            rgb_colour=(0, 255, 0),
        )

        for key in normalized_words:
            if key != "total" and key != "links":
                embed.add_field(
                    name=key,
                    value=f"{normalized_words[key][0]}",
                    inline=True,
                )

        # embed.add_field(
        #     name="Jump to messages",
        #     value=normalized_words["links"],
        #     inline=False,
        # )
        return await interaction.followup.send(embed=embed)


# check 2 words to see if they're similar enough to be counted
def similar(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio()


# Splits the users input into seperate words
def split_user_input(words: str):
    return words.split(",")


# Normalize seperated user input words and create dictionary with words as key
def normalize_words(seperated_words: list[str]):
    normalized_words: dict[str, list()] = {}
    normalized_words.setdefault("total", []).append(0)
    normalized_words.setdefault("links", [])
    for word in seperated_words:
        normalized_words.setdefault(word.lower().strip(), []).append(0)
    return normalized_words


# Normalize text by converting to lower case and stripping excess whitespaces
def normalize_text(text: str):
    return text.lower().strip()


# Calculates word occurances of each word in the dictionary to the chat history we're checking
async def calculate_word_occurances(
    interaction: discord.Interaction,
    history: int,
    user: discord.User,
    normalized_words: dict[str, list()],
) -> dict:
    async for message in interaction.channel.history(limit=history):
        if message.author == user:
            normalized_words["total"][0] += 1
            message_content = [normalize_text(w) for w in message.content.split()]

            for word_in_message in message_content:
                # if normalized_words.get(word):
                #     normalized_words[word][0] += 1

                for word in normalized_words:
                    if similar(word, word_in_message) >= SIMILARITY_THRESHHOLD:
                        normalized_words[word][0] += 1
                        # normalized_words["links"].append(
                        #     f"[{word}]({message.jump_url})"
                        # )

    return normalized_words


# Creates and returns discord Embed
def create_embed(
    title: str,
    description: str,
    rgb_colour: list[int],
) -> discord.Embed:
    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.from_rgb(rgb_colour[0], rgb_colour[1], rgb_colour[2]),
    )

    return embed


async def handle_john(interaction: discord.Interaction):
    gifs = [
        "https://media.tenor.com/i3aq-NVdOM0AAAAC/blah-talk.gif",
        "https://media.tenor.com/IqcTgySAAboAAAAd/roblox-dance-roberto.gif",
        "https://media.tenor.com/umAhsC4GHloAAAAC/james-soycat.gif",
        "https://media.tenor.com/VkkGArCza9gAAAAd/danmorris-boxing.gif",
        "https://tenor.com/view/among-ass-among-us-amongar-hi-mia-amongal-gif-20120616",
    ]
    channels = interaction.guild.voice_channels

    annoy_method = random.randint(1, 7)

    match annoy_method:
        # Move him to a random channel
        case 1:
            moved = False
            while moved == False:
                voice_channel = random.choice(channels)
                if voice_channel != interaction.user.voice.channel:
                    await interaction.user.move_to(random.choice(channels))
                    await interaction.response.send_message(random.choice(gifs))
                    moved = True

                await asyncio.sleep(0.5)
        # Move him to a random channel with Brian if Brian is connected
        case 2:
            current_users = interaction.user.voice.channel.members
            for user in current_users:
                if user.id == 227850389079326720:
                    channel = random.choice(channels)
                    await interaction.user.move_to(channel)
                    await user.move_to(channel)
                    return await interaction.response.send_message(random.choice(gifs))
            dm_channel = await interaction.user.create_dm()
            await dm_channel.send("kys?")
        case 3:
            await interaction.user.kick()
            return await interaction.response.send_message(random.choice(gifs))
        case 4:
            await interaction.user.edit(mute=True)

        case 5:
            await interaction.user.edit(deafen=True)
        case 6:
            await interaction.user.edit(mute=True)
            await interaction.user.edit(deafen=True)
        case 7:
            x = 0
            while x <= 5:
                sleep_timer = random.randint(3, 20)
                await interaction.user.move_to(random.choice(channels))
                await asyncio.sleep(sleep_timer)
                x += 1


async def setup(bot: commands.Bot) -> None:
    if GLOBAL_SYNC:
        # Global Sync
        await bot.add_cog(Counter(bot))
    else:
        # Private Sync
        await bot.add_cog(
            Counter(bot),
            guilds=[discord.Object(id=os.environ["DEVELOPMENT_SERVER_ID"])],
        )
