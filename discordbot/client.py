import asyncio
import logging

from aiohttp import web_exceptions as aiohttp_exc
from discord import colour, embeds
from discord import errors as discord_exc
from discord.ext import commands
from discord.ext.commands import core

import cfg

from discordbot import stream

LOG = logging.getLogger('debug')


class Bot(commands.Bot):

    def __init__(self):

        # Client
        self.async_event(self.on_ready)
        self.async_event(self.on_error)

        self.stream_manager = stream.StreamManager(self, filename='channels')
        self.stream_manager.init()

        # Chat Bot
        super(Bot, self).__init__(command_prefix=cfg.COMMAND_PREFIX)

        # TEST
        self.add_command(
            core.Command(
                name="test",
                callback=self.test,
                pass_context=False,
                help="Test command"
            )
        )

        # STREAM
        stream_group = core.Group(
            name="stream",
            callback=self.stream,
            pass_context=True,
            invoke_without_command=True
        )

        # STREAM LIST
        stream_group.add_command(
            core.Command(
                name="list",
                callback=self.stream_list,
                pass_context=False,
                help="Show current tracked streams"
            )
        )

        # STREAM ADD
        stream_group.add_command(
            core.Command(
                name="add",
                callback=self.stream_add,
                pass_context=False,
                help="Add a stream to the tracked list"
            )
        )

        # STREAM EVERYONE
        stream_group.add_command(
            core.Command(
                name="everyone",
                callback=self.stream_everyone,
                pass_context=False,
                help="Add a stream to the tracked list (with @everyone)"
            )
        )

        # STREAM REMOVE
        stream_group.add_command(
            core.Command(
                name="remove",
                callback=self.stream_rm,
                pass_context=False,
                help="Remove a stream from the tracked list"
            )
        )

        self.add_command(stream_group)

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

    async def on_error(self, event, *args, **kwargs):
        LOG.exception('An error has occurred: {event}'.format(event=str(event)))

    # BOT ACTIONS

    async def say(self, ctx, message):
        message = "```" + message + "```"
        await ctx.message.channel.send(message)

    async def notify(self, channel_id, stream, stream_info):
        """ Send a message in discord chat to notify that a stream went online

        :param channel_id: the discord channel to send the notification in
        :param stream: stream object
        :param stream_info: stream info
        """
        twitch_icon_url = "https://www.shareicon.net/download/2015/09/08/98061_twitch_512x512.png"
        clock_icon_url = "http://www.iconsdb.com/icons/preview/caribbean-blue/clock-xxl.png"

        display_name = stream_info.get('channel').get('display_name')
        game = stream_info.get('game')
        title = stream_info.get('channel').get('status')
        logo = stream_info.get('channel').get('logo')
        profile_banner = stream_info.get('channel').get('profile_banner')

        twitch_channel = "https://twitch.tv/" + str(stream.username)

        message = ""
        if stream.everyone:
            message += "@everyone "

        message += "{display_name} is streaming!".format(display_name=display_name)

        embed = embeds.Embed()
        embed.colour = colour.Color.dark_blue()
        embed.description = "[{}]({})".format(twitch_channel, twitch_channel)

        embed.set_author(name=display_name, url=twitch_channel, icon_url=twitch_icon_url)
        embed.add_field(name="Playing", value=game)
        embed.add_field(name="Stream Title", value=title)
        embed.set_footer(text="Stream live time", icon_url=clock_icon_url)

        if logo:
            embed.set_thumbnail(url=logo)
        if profile_banner:
            embed.set_image(url=profile_banner)

        try:
            channel = self.get_channel(int(channel_id))
            LOG.debug("Sending notification for {username}'s stream in '{guild_name}:{channel_name}'"
                      .format(username=stream.username, guild_name=channel.guild.name, channel_name=channel.name))
            await channel.send(message, embed=embed)
        except discord_exc.DiscordException:
            LOG.exception("Cannot send alert for notification for {username}'s stream".format(username=stream.username))

    # BOT COMMANDS #

    async def test(self, ctx):
        """ Test command """
        await self.say(ctx, "Test!")

    async def stream(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.invoke(self.get_command('help'), "stream")

    async def stream_list(self, ctx):
        """ Shows tracked stream list """
        message = "♦ Tracked channels ♦ \n\n"
        channels = [self.get_channel(channel_id) for channel_id in self.stream_manager.streams]
        for channel in sorted(channels, key=lambda x: x.position):
            stream_data = self.stream_manager.streams[channel.id]
            if stream_data['guild_id'] == ctx.message.channel.guild.id:
                twitch_channels = []
                for stream in stream_data['twitch_channels']:
                    channel = stream.username
                    if stream.everyone:
                        channel += "*"
                    twitch_channels.append(channel)
                message += "- {channel_name}: {twitch_channels}\n\n".format(
                    channel_name=stream_data['channel_name'],
                    twitch_channels=", ".join(sorted(twitch_channels))
                )
        await self.say(ctx, message)

    async def stream_add(self, ctx, username):
        """ '!stream add [username]' to add a channel to the tracked list """
        self.stream_manager.add_stream(ctx.message.channel, username)
        await self.say(ctx, "{username} is now tracked in '{server_name}:{channel_name}'".format(
            username=username, server_name=ctx.message.channel.guild.name, channel_name=ctx.message.channel.name
        ))

    async def stream_everyone(self, ctx, username):
        """ '!stream everyone [username]' to add a channel to the tracked list and notify everyone """
        self.stream_manager.add_stream(ctx.message.channel, username, everyone=True)
        await self.say(ctx, "{username} is now tracked in '{server_name}:{channel_name}'".format(
            username=username, server_name=ctx.message.channel.guild.name, channel_name=ctx.message.channel.name
        ))

    async def stream_rm(self, ctx, username):
        """ '!stream remove [username]' to remove a channel from the tracked list """
        self.stream_manager.remove_stream(ctx.message.channel, username)
        await self.say(ctx, "{username} is no longer tracked in '{server_name}:{channel_name}'".format(
            username=username, server_name=ctx.message.channel.guild.name, channel_name=ctx.message.channel.name
        ))

    # POLL #

    async def poll_streams(self):
        await self.stream_manager.poll_streams()
