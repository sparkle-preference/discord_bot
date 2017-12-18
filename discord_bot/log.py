import logging
import os
from logging.handlers import RotatingFileHandler

from discord_bot import utils

LOG_PATTERN = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: [%(filename)s] %(message)s')
LOG_DIR = utils.get_project_dir() + "/log"

if not os.path.isdir(LOG_DIR):
    os.makedirs(LOG_DIR)

# discord logger
DISCORD_LOGGER = logging.getLogger("discord")
DISCORD_LOGGER.setLevel(logging.DEBUG)
DISCORD_FILE_HANDLER = RotatingFileHandler(LOG_DIR + "/discord.log", "a", 1000000, 1)
DISCORD_FILE_HANDLER.setFormatter(LOG_PATTERN)
DISCORD_LOGGER.addHandler(DISCORD_FILE_HANDLER)

# chat logger
UTILS_LOGGER = logging.getLogger("utils")
UTILS_LOGGER.setLevel(logging.DEBUG)
UTILS_FILE_HANDLER = RotatingFileHandler(LOG_DIR + "/utils.log", "a", 1000000, 1)
UTILS_FILE_HANDLER.setFormatter(LOG_PATTERN)
UTILS_LOGGER.addHandler(UTILS_FILE_HANDLER)

# debug logger
DEBUG_LOGGER = logging.getLogger("debug")
DEBUG_LOGGER.setLevel(logging.DEBUG)
DEBUG_FILE_HANDLER = RotatingFileHandler(LOG_DIR + "/debug.log", "a", 1000000, 1)
DEBUG_FILE_HANDLER.setFormatter(LOG_PATTERN)
DEBUG_LOGGER.addHandler(DEBUG_FILE_HANDLER)

# write in the console
STEAM_HANDLER = logging.StreamHandler()
STEAM_HANDLER.setFormatter(LOG_PATTERN)
STEAM_HANDLER.setLevel(logging.DEBUG)
UTILS_LOGGER.addHandler(STEAM_HANDLER)
DEBUG_LOGGER.addHandler(STEAM_HANDLER)
