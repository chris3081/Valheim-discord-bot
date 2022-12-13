import os
import sys
import discord
import emoji
import requests
import logging
from discord.ext import tasks
from config import server_name, server_address, server_port, channel_name, bot_token

root = logging.getLogger()
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)


class ValheimBot(discord.Client):
    def __init__(self, server_name, server_address, server_port, channel_name, **kwargs):
        super().__init__(intents=discord.Intents.all())
        self._server_name = server_name
        self._server_address = server_address
        self._server_port = server_port
        self._channel_name = channel_name
        self._player_count = 0
        self._player_names_list = []
        self._command_prefix = '!'
        self._logger = logging.getLogger("ValheimBot")
        self._valheim_online = False
        _handler = logging.StreamHandler(sys.stdout)
        _handler.setLevel(logging.INFO)
        _formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        _handler.setFormatter(_formatter)
        self._logger.addHandler(_handler)
        self._logger.setLevel(logging.DEBUG)

    async def update_server_state(self, value):
        discord_service = list(self.guilds).pop()
        channel = discord.utils.get(discord_service.channels, name=self._channel_name)
        if self._valheim_online == value:
            return

        if value:
            self._logger.info("Valheim Server online")
            await channel.send(f"{emoji.emojize(':white_check_mark:')} Server Online")
            self._valheim_online = True
        else:
            self._logger.error("Valheim Server offine")
            await channel.send(f"{emoji.emojize(':cross_mark:')} Server Offline")
            self._valheim_online = False

    async def get_data(self):
        resp = requests.get(f"http://{self._server_address}:{self._server_port}/status.json")
        if resp.status_code != 200:
            await self.update_server_state(False)
            return None
        await self.update_server_state(True)
        return resp.json()

    async def on_ready(self):
        self._logger.info(f'Bot connected as {self.user}')
        discord_service = list(self.guilds).pop()
        channel = discord.utils.get(discord_service.channels, name=self._channel_name)
        await channel.send(f"Bot ready\nuse {self._command_prefix}help for commands")
        await self.get_data()

    async def on_message(self, message):
        msg = message.content
        member_id = "{}#{}".format(message.author.name, message.author.discriminator)
        # ignore if I'm the author
        if member_id == "{}#{}".format(self.user.name, self.user.discriminator):
            return

        if msg.startswith('{}help'.format(self._command_prefix)):
            await self.help_ctx(message)
        elif msg.startswith('{}players'.format(self._command_prefix)):
            await self.player_list(message)

    async def help_ctx(self, ctx):
        help_embed = discord.Embed(
            description="[**Valheim Discord Bot**](https://github.com/ckbaudio/valheim-discord-bot)",
            color=0x33a163, )
        help_embed.add_field(name="{}players".format(self._command_prefix),
                             value="Shows a list of active players".format(self._command_prefix), inline=True)
        help_embed.set_footer(text="Valbot v0.42")
        await ctx.channel.send(embed=help_embed)

    async def player_list(self, ctx):
        resp = await self.get_data()
        self._player_names_list = resp['players']
        plist = ""
        for p in [x.name for x in self._player_names_list if 'name' in x]:
            plist += "{}\n".format(p)
        if not plist:
            plist = "None"
        player_embed = discord.Embed(
            description="[**Valheim Discord Bot**](https://github.com/ckbaudio/valheim-discord-bot)",
            color=0x33a163)
        player_embed.add_field(name="Player List", value=f"{plist}", inline=True)
        await ctx.channel.send(embed=player_embed)

    @tasks.loop(seconds=30)
    async def server_stats_update(self):
        resp = await self.get_data()
        if resp:
            self._player_names_list = resp['players']
            self._player_count = resp['player_count']
        self._logger.info("Server update loop finished")


settings = {}
settings['server_address'] = os.environ.get("SERVER_ADDRESS", server_address)
settings['server_port'] = int(os.environ.get("SERVER_PORT", server_port))
settings['server_name'] = os.environ.get("SERVER_NAME", server_name)
settings['channel_name'] = os.environ.get("CHANNEL_NAME", channel_name)

client = ValheimBot(**settings)
client.run(os.environ.get("BOT_TOKEN", bot_token))
