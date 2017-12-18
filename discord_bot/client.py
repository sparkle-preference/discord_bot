import logging
import pkgutil

from discord.ext import commands

import cfg
from discord_bot import cogs
from discord_bot import utils

LOG = logging.getLogger(__name__)


class Bot(commands.Bot):

    # BOT EVENTS #
    async def on_ready(self):
        LOG.debug("Bot is connected | user id: {bot_id} | username: {bot_name}"
                  .format(bot_id=self.user.id, bot_name=self.user))
        self.load_extensions()

    # BOT ACTIONS #
    def load_extensions(self):
        """ Load all the cogs """
        project_name = utils.get_project_name()
        cog_module_name = "{project_name}.cogs".format(project_name=project_name)
        cog_name_list = [(name, ispkg) for importer, name, ispkg in pkgutil.iter_modules(cogs.__path__)]
        for cog_name, ispkg in cog_name_list:
            if not ispkg:
                self.load_extension(cog_module_name + "." + cog_name)
                LOG.debug("The cog '{cog_name}' has been successfully loaded".format(cog_name=cog_name))

    async def say(self, ctx, message):
        message = "```" + message + "```"
        await ctx.message.channel.send(message)
