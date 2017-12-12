import asyncio
import copy
from datetime import datetime
import logging
import json
from json import decoder
import os

from discord import colour, embeds

import cfg
from discord_bot import utils

LOG = logging.getLogger('debug')

HEADERS = {"Client-ID": cfg.TWITCH_API_CLIENT_ID, "accept": cfg.TWITCH_API_ACCEPT}


class Stream(object):

    def __init__(self, username, everyone=False):
        self.username = str(username)
        self.id = None
        self.is_online = False
        self.everyone = everyone
        self.last_notification_date = None

    def __eq__(self, other):
        return self.username == other

    def __hash__(self):
        return hash(self.username)

    def __str__(self):
        return str(self.username)

    async def get_id(self):
        """ Get user id """
        url = "{twitch_api_url}/users?login={twitch_username}".format(twitch_api_url=cfg.TWITCH_API_URL,
                                                                      twitch_username=self.username)
        body, status_code = await utils.request(url, headers=HEADERS)
        if status_code == 200:
            try:
                user = json.loads(body)['users'][0]
                LOG.debug("API data for {twitch_username}: {data} ({url})"
                          .format(twitch_username=self.username, data=user, url=url))
            except decoder.JSONDecodeError:
                LOG.warning("Cannot retrieve channel information for {twitch_username} ({status_code} bad json format)"
                            .format(twitch_username=self.username, status_code=status_code))
            except KeyError:
                LOG.warning("Cannot retrieve channel data for {twitch_username} ({status_code} empty body)"
                            .format(twitch_username=self.username, status_code=status_code))
            except (ValueError, TypeError):
                LOG.exception("Cannot retrieve channel data for {twitch_username} ({status_code})"
                              .format(twitch_username=self.username, status_code=status_code))
            else:
                self.id = user['_id']

    async def get_status(self):
        """ Get stream API data """
        if not self.id:
            await self.get_id()

        url = "{twitch_api_url}/streams/{id}".format(twitch_api_url=cfg.TWITCH_API_URL, id=self.id)
        body, status_code = await utils.request(url, headers=HEADERS)
        if status_code == 200:
            try:
                stream = json.loads(body)
            except decoder.JSONDecodeError:
                LOG.warning("Cannot retrieve stream information for {twitch_username} ({status_code} bad json format)"
                            .format(twitch_username=self.username, status_code=status_code))
            except KeyError:
                LOG.warning("Cannot retrieve stream data for {twitch_username} ({status_code} empty body)"
                            .format(twitch_username=self.username, status_code=status_code))
            except (ValueError, TypeError):
                LOG.exception("Cannot retrieve stream data for {twitch_username} ({status_code})"
                              .format(twitch_username=self.username, status_code=status_code))
            else:
                return stream
        else:
            LOG.debug("No response from the API for {twitch_username}'s stream status"
                      .format(twitch_username=self.username))

    def update_last_notification_date(self):
        """ Update the date when the last notification has been sent """
        self.last_notification_date = datetime.now()

    def is_notification_already_sent(self):
        """ Check if a notification has not already been sent within X seconds """
        if not self.last_notification_date:
            return False
        else:
            now = datetime.now()
            delta = now - self.last_notification_date
            return delta.seconds < cfg.MAX_NOTIFICATION_RATE


class StreamManager(object):

    def __init__(self, bot, filename="channels"):
        self.bot = bot
        self.streams = None
        self.filepath = utils.get_file_path("etc/" + filename + ".json")

    def init(self):
        """ Initialize the stream file

        - Create it if it does not exist
        - Delete then create it if it's in a bad format
        - Load the content if there is one
        """

        etc_dirpath = utils.get_file_path("etc")
        if not os.path.isdir(etc_dirpath):
            LOG.debug("Missing 'etc/' directory, creating one...")
            os.makedirs(etc_dirpath)
            LOG.debug("{etc_dirpath}' directory successfully created".format(etc_dirpath=etc_dirpath))

        if os.path.exists(self.filepath):
            LOG.debug("Loading {filepath} to see if an init is needed".format(filepath=self.filepath))
            self.streams = utils.load_json_file(self.filepath)

        if not os.path.exists(self.filepath) or self.streams is None:
            self.streams = {}
            utils.save_file(self.filepath, u"{}")
            LOG.debug("data file is not found or corrupted, recreating an empty one...")

        for channel_id in self.streams:
            self.streams[channel_id]['twitch_channels'] = [
                Stream(twitch_username, everyone)
                for (twitch_username, everyone) in self.streams[channel_id]['twitch_channels']
            ]

    def _get_discord_channels_by_stream(self):
        """ Build a dictionary with the stream as key and a list of discord channel ids in which the stream is notified

        :return: a dictionary {<Stream> : ["discord_channel_id", "discord_channel_id"], <Stream> : ... }
        """
        channels_by_stream = {}
        for channel_id, channel_info in self.streams.items():
            for stream in channel_info['twitch_channels']:
                if stream not in channels_by_stream.keys():
                    channels_by_stream[stream] = []
                channels_by_stream[stream].append(channel_id)
        return channels_by_stream

    def _save(self):
        """ Save data in the file """
        output = {}
        for channel_id, channel_info in self.streams.items():
            output[channel_id] = {
                'channel_name': channel_info['channel_name'],
                'position': channel_info['position'],
                'guild_id': channel_info['guild_id'],
                'guild_name': channel_info['guild_name'],
                'twitch_channels': [(stream.username, stream.everyone) for stream in channel_info['twitch_channels']]
            }
        utils.save_json_file(self.filepath, output)

    @staticmethod
    def _get_embed_notification(stream, stream_info):
        """ Send a message in discord chat to notify that a stream went online

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

        return message, embed

    def add_stream(self, discord_channel, twitch_username, everyone=False):
        """ Add a stream in a discord channel tracklist

        :param discord_channel: The discord channel in which the stream notifications are enabled
        :param twitch_username: The stream to notify
        :param everyone: If True, add the tag @everyone to the bot notification
        :return:
        """
        channel_id = discord_channel.id
        if not channel_id in self.streams:
            self.streams[channel_id] = {
                'channel_name': discord_channel.name,
                'position': discord_channel.position,
                'guild_name': discord_channel.guild.name,
                'guild_id': discord_channel.guild.id,
                'twitch_channels': []
            }

        if twitch_username in self.streams[channel_id]['twitch_channels']:
            LOG.debug("{twitch_username}'s stream is already tracked in '{server_name}:{channel_name}'".format(
                twitch_username=twitch_username,
                server_name=discord_channel.guild.name,
                channel_name=discord_channel.name
            ))

        else:
            self.streams[channel_id]['twitch_channels'].append(Stream(twitch_username, everyone))
            LOG.debug("{twitch_username}'s stream is now tracked in '{server_name}:{channel_name}'".format(
                twitch_username=twitch_username,
                server_name=discord_channel.guild.name,
                channel_name=discord_channel.name
            ))
            self._save()

    def remove_stream(self, discord_channel, twitch_username):
        """ Disable bot notification for a stream in a specific channel

        :param discord_channel: the discord channel in which the stream must not be notified anymore
        :param twitch_username: the stream to be removed
        """
        channel_id = discord_channel.id
        if channel_id in self.streams.keys():
            if twitch_username in self.streams[channel_id]['twitch_channels']:
                self.streams[channel_id]['twitch_channels'].remove(twitch_username)
                LOG.debug("{twitch_username}'s stream is no longer tracked in '{server_name}:{channel_name}'".format(
                    twitch_username=twitch_username,
                    server_name=discord_channel.guild.name,
                    channel_name=discord_channel.name
                ))

            if not self.streams[channel_id]['twitch_channels']:
                del self.streams[channel_id]
                LOG.debug("The is no tracked stream in '{server_name}:{channel_name}' anymore".format(
                    server_name=discord_channel.guild.name,
                    channel_name=discord_channel.name
                ))
            self._save()
        else:
            LOG.debug("There is no tracked stream in '{server_name}:{channel_name}'".format(
                server_name=discord_channel.guild.name,
                channel_name=discord_channel.name
            ))

    def clear_channel(self, channel):
        """ Remove every stream tracked in a given channel (called when a discord channel is deleted)

        :param channel: the discord channel from which every stream must be removed
        """
        try:
            del self.streams[channel.id]
            self._save()
            LOG.debug("Every tracked stream have been removed from the deleted channel '{guild_name:channel_name}'"
                      .format(guild_name=channel.guild.name, channel_name=channel.name))
        except KeyError:
            LOG.warning("channel '{guild_name:channel_name}' not found".format(guild_name=channel.guild.name,
                                                                               channel_name=channel.name))

    async def poll_streams(self):
        """ Poll streams status every X seconds

        If a stream went online and no notification has been sent for a while, the bot notifies in the related discord
        channel.
        """
        while not self.bot.is_ready():
            LOG.debug('Waiting for the bot to be ready before starting to poll')
            await asyncio.sleep(1)
        while True:
            channels_by_stream = self._get_discord_channels_by_stream()
            if not channels_by_stream:
                await asyncio.sleep(10)
            for stream, discord_channel_ids in channels_by_stream.items():
                api_result = await stream.get_status()
                if api_result is not None:
                    status = api_result.get('stream')
                    if status:
                        if not stream.is_online:
                            if not stream.is_notification_already_sent():
                                message, embed = self._get_embed_notification(stream, status)
                                for channel_id in discord_channel_ids:
                                    channel = self.bot.get_channel(int(channel_id))
                                    await channel.send(message, embed=embed)
                                    LOG.debug(
                                        "Sending notification for {username}'s stream in '{guild_name}:{channel_name}'"
                                        .format(username=stream.username, guild_name=channel.guild.name,
                                                channel_name=channel.name)
                                    )
                                stream.update_last_notification_date()
                                stream.is_online = True
                            else:
                                LOG.debug("A notification has already been sent {username} within {max_rate}"
                                          .format(username=stream.username, max_rate=cfg.MAX_NOTIFICATION_RATE))
                    else:
                        if stream.is_online:
                            LOG.debug("{username} just went offline".format(username=stream.username))
                            stream.is_online = False
                else:
                    LOG.debug("No status for {username}, skipping iteration".format(username=stream.username))

                await asyncio.sleep(1)
