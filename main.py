#!/usr/bin/python


import sys

from discord_bot import async
from discord_bot import client
from discord_bot import log


sys.path.append('discord_bot')

bot = client.Bot()

async.LoopManager(
    bot.start,
    bot.stream_manager.poll_streams
).start()
