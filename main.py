#!/usr/bin/python


import sys

from discordbot import async
from discordbot import client
from discordbot import log


sys.path.append('discordbot')

bot = client.Bot()

async.LoopManager(
    bot.start,
    bot.poll_streams
).start()
