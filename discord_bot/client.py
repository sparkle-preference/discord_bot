import asyncio
import logging

from aiohttp import web_exceptions as aiohttp_exc
from discord.ext import commands

import cfg

from discord_bot.stream import stream

LOG = logging.getLogger('debug')


class Bot(commands.Bot):

    def __init__(self):

        self.stream_manager = stream.StreamManager(self, filename='channels')
        self.stream_manager.init()

        # Chat Bot
        super(Bot, self).__init__(command_prefix=cfg.COMMAND_PREFIX)

    async def start(self):
        """ Start the bot, if it disconnects, try to reconnect every 3s """
        try:
            await super(Bot, self).start(cfg.DISCORD_BOT_TOKEN)
        except aiohttp_exc.HTTPException:
            LOG.error('Bot is disconnected, reconnection...')
            await asyncio.sleep(3)
            await self.start()

    # BOT EVENTS #

    async def on_ready(self):
        LOG.debug("Bot is connected | user id: {bot_id} | username: {bot_name}".format(bot_id=self.user.id,
                                                                                       bot_name=self.user))
        self.load_extension('discord_bot.stream.commands')

    async def on_error(self, event, *args, **kwargs):
        LOG.exception('An error has occurred: {event}'.format(event=str(event)))

    async def on_guild_channel_delete(self, channel):
        LOG.debug("The channel '{guild_name:channel_name}' has been deleted".format(guild_name=channel.guild.name,
                                                                                    channel_name=channel.name))
        self.stream_manager.clear_channel(channel)

    # BOT ACTIONS

    async def say(self, ctx, message):
        message = "```" + message + "```"
        await ctx.message.channel.send(message)
