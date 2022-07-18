import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, Set

TEEF2_SERVER = 749955516398305363

class MyHelpCommand(commands.MinimalHelpCommand):
    def get_command_signature(self, command):
        return f"{self.clean_prefix}{command.qualified_name} {command.signature}"

    async def help_embed(self, title: str, description: Optional[str] = None, mapping: Optional[dict] = None,
        command_set: Optional[Set[commands.Command]] = None):
        embed = discord.Embed(title=title)
        if description:
            embed.description = description
        if command_set:
            filtered = await self.filter_commands(command_set, sort=True)
            for command in filtered:
                embed.add_field(name=self.get_command_signature(command), value=command.short_doc or "...",
                                inline=False)
        if mapping:
            for cog, command_set in mapping.items():
                filtered = await self.filter_commands(command_set, sort=True)
                if not filtered:
                    continue
                name = cog.qualified_name if cog else "No category"

                cmd_list = "\u2002".join(f"`{self.clean_prefix}{cmd.name}`" for cmd in filtered)
                value = (f"{cog.description}\n{cmd_list}"
                        if cog and cog.description
                        else cmd_list
                        )
                embed.add_field(name=name, value=value, inline=False)

        return embed

    async def send_bot_help(self, mapping: dict):
        embed = await self.help_embed(title="Bot Commands",
                                      description=self.context.bot.description,
                                      mapping=mapping)

        embed.add_field(name="__Command Info__",
                        value=f"`<...>` _Required argument_\n`[...]` _Optional argument_",
                        inline=False)

        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command: commands.Command):
        embed = await self.help_embed(
            title=f"={command.qualified_name}",
            description=command.help,
            command_set=command.commands if isinstance(command, commands.Group) else None
        )

        await self.get_destination().send(embed=embed)

    async def send_cog_help(self, cog: commands.Cog):
        embed = await self.help_embed(
            title=cog.qualified_name,
            description=cog.description,
            command_set=cog.get_commands()
        )

        await self.get_destination().send(embed=embed)

    send_group_help = send_command_help

class help(commands.Cog, name="Help"):
    """Shows help info about commands"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._original_help_command = bot.help_command
        bot.help_command = MyHelpCommand()
        bot.help_command.cog = self

    def cog_unload(self):
        self.bot.help_command = self._original_help_command

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(help(bot), guilds=[discord.Object(id=TEEF2_SERVER)])