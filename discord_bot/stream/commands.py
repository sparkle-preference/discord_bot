from discord.ext import commands


class Stream:
    def __init__(self, bot):
        self.bot = bot

    @commands.group(pass_context=True)
    async def stream(self, ctx):
        """ Stream commands """
        if ctx.invoked_subcommand is None:
            await ctx.invoke(self.bot.get_command('help'), "stream")

    @stream.command()
    async def list(self, ctx):
        """  Show current tracked streams """
        message = "♦ Tracked channels ♦ \n\n"
        for channel_data in sorted(self.bot.stream_manager.streams.values(), key=lambda x: x['position']):
            if channel_data['guild_id'] == ctx.message.channel.guild.id:
                twitch_channels = []
                for stream in channel_data['twitch_channels']:
                    channel = stream.username
                    if stream.everyone:
                        channel += "*"
                    twitch_channels.append(channel)
                message += "- {channel_name}: {twitch_channels}\n\n".format(
                    channel_name=channel_data['channel_name'],
                    twitch_channels=", ".join(sorted(twitch_channels))
                )
        await self.bot.say(ctx, message)

    @stream.command()
    async def add(self, ctx, username):
        """ Add a stream to the tracked list """
        self.bot.stream_manager.add_stream(ctx.message.channel, username)
        await self.bot.say(ctx, "{username} is now tracked in '{server_name}:{channel_name}'".format(
            username=username, server_name=ctx.message.channel.guild.name, channel_name=ctx.message.channel.name
        ))

    @stream.command()
    async def everyone(self, ctx, username):
        """ Add a stream to the tracked list (with @everyone) """
        self.bot.stream_manager.add_stream(ctx.message.channel, username, everyone=True)
        await self.bot.say(ctx, "{username} is now tracked in '{server_name}:{channel_name}'".format(
            username=username, server_name=ctx.message.channel.guild.name, channel_name=ctx.message.channel.name
        ))

    @stream.command()
    async def remove(self, ctx, username):
        """ Remove a stream from the tracked list """
        self.bot.stream_manager.remove_stream(ctx.message.channel, username)
        await self.bot.say(ctx, "{username} is no longer tracked in '{server_name}:{channel_name}'".format(
            username=username, server_name=ctx.message.channel.guild.name, channel_name=ctx.message.channel.name
        ))


def setup(bot):
    bot.add_cog(Stream(bot))
