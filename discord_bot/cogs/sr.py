import asyncio
import collections
import json
import logging
import re

from discord import colour, embeds
from discord.ext import commands

import cfg
from discord_bot import utils


LOG = logging.getLogger('debug')

HEADERS = {
    "Accept": "application/json",
    "X-API-Key": cfg.SR_API_KEY
}


class Speedrun:

    def __init__(self, bot):
        type(self).__name__ = "Speedrun.com commands"
        self.bot = bot
        self.games = []
        self.categories = []
        self.user_links = {}

    @staticmethod
    def _parse_pb_data(pb):
        """ Parse API run data

        :param pb: API run data
        :return: reduced dict of API run data
        """
        links = {link['rel']: link['uri'] for link in pb['run']['links']}

        return {
            'place': utils.ordinal(pb['place']),
            'game_url': links['game'],
            'category_url': links['category'],
            'time': utils.convert_time(pb['run']['times']['realtime_t']),
            'video_url': pb['run']['videos']['links'][0]['uri'],
        }

    @staticmethod
    def _parse_game_data(game):
        """ Parse API game data

        :param game: API game data
        :return: reduced dict of API game data
        """
        return {
            'id': game['id'],
            'name': game['names']['international'],
            'abbreviation': game['abbreviation'],
            'links': {link['rel']: link['uri'] for link in game['links']}
        }

    @staticmethod
    def _parse_category_data(category):
        """ Parse API category data

        :param category: API category data
        :return: reduced dict of API category data
        """
        return {
            'id': category['id'],
            'name': category['name'],
            'links': {link['rel']: link['uri'] for link in category['links']}
        }

    @staticmethod
    def _parse_record_data(record):
        """ Parse API record data

        :param record: API record data
        :return: reduced dict of API record data
        """
        return {
            'time': utils.convert_time(record['runs'][0]['run']['times']['realtime_t']),
            'video_url': record['runs'][0]['run']['videos']['links'][0]['uri']
        }

    @staticmethod
    def _get_summary_embed(summary):
        """ Build an embed

        :param summary: summary data to display
        :return: embed
        """
        embed = embeds.Embed()
        embed.colour = colour.Color.dark_gold()

        for game, categories in summary.items():
            value = ""
            for category, pb in categories.items():
                value += u"__**{category_name}**__:\n".format(category_name=category)
                for field_name, field_value in pb.items():
                    value += u"\t **{field_name}**: {field_value}\n".format(field_name=field_name,
                                                                            field_value=field_value)
            embed.add_field(name=game, value=value)

        return embed

    async def _get_user_links(self, name):
        """ Get user links (profile, personal bests, ..)

        :param name: username
        :return: user links
        """
        try:
            if name in self.user_links:
                return self.user_links[name]
            url = "{sr_api_url}/users?name={name}".format(sr_api_url=cfg.SR_API_URL, name=name)
            body, status_code = await utils.request(url, headers=HEADERS)

            links = json.loads(body)['data'][0]['links']
        except:
            LOG.exception("Cannot retrieve data for '{name}' ({status_code})".format(name=name, status_code=status_code))
        else:
            user_links = {link['rel']: link['uri'] for link in links}
            self.user_links[name] = user_links
            return user_links

    async def _get_game(self, arg):
        """ Retrieve game data from abbreviation or url

        - Request game data only if it is not already stored
        :param arg: url or abbreviation
        :return: reduced dict of API record data
        """
        for game in self.games:
            if game['links']['self'] == arg or game['abbreviation'] == arg:
                return game

        if re.match("http[s]*://.*", arg):
            url = arg
        else:
            url = "{sr_api_url}/games?abbreviation={abbreviation}" \
                .format(sr_api_url=cfg.SR_API_URL, abbreviation=arg)

        if url:
            game_body, status_code = await utils.request(url, headers=HEADERS)
            try:
                game = utils.flatten_list(json.loads(game_body)["data"])
            except:
                LOG.exception("Cannot retrieve game name: {url} ({status_code})"
                              .format(url=url, status_code=status_code))
            else:
                game = self._parse_game_data(game)
                if game not in self.games:
                    self.games.append(game)
                return game

    async def _get_game_records(self, arg):
        """ Retrieve records data from game abbreviation or url

        Request records data only if it is not already stored
        :param arg: url or abbreviation
        :return: reduced dict of API record data
        """
        try:
            stored_game = await self._get_game(arg)
            await self._get_categories(stored_game['links']['categories'])

            url = "{sr_api_url}/games/{game_id}/records".format(sr_api_url=cfg.SR_API_URL, game_id=stored_game['id'])
            records_body, status_code = await utils.request(url, headers=HEADERS)

            records = json.loads(records_body)["data"]
        except:
            LOG.exception("Cannot retrieve records for game: {game_id} ({status_code})"
                          .format(game_id=stored_game['name'], status_code=status_code))
        else:
            records_summary = collections.defaultdict(dict)
            for category in records:
                stored_category = await self._get_category(category['links'][1]['uri'])
                record = self._parse_record_data(category)
                records_summary[stored_game['name']][stored_category['name']] = record
            return records_summary

    async def _get_category(self, category_url):
        """ Retrieve category data from url

        Request category data only if it is not already stored
        :param category_url: category url
        :return: reduced dict of API category data
        """
        try:
            for category in self.categories:
                if category['links']['self'] == category_url:
                    return category

            category_body, status_code = await utils.request(category_url, headers=HEADERS)

            category = json.loads(category_body)["data"]
        except:
            LOG.exception("Cannot retrieve category name: {category_url} ({status_code})"
                          .format(category_url=category_url, status_code=status_code))
        else:
            category = self._parse_category_data(category)
            if not category in self.categories:
                self.categories.append(category)
            return category

    async def _get_categories(self, arg):
        """ Retrieve categories data from url and stores it

        Request categories data
        :param arg: categories url (<game_id>/categories)
        """
        try:
            if re.match("http[s]*://.*", arg):
                url = arg
            else:
                url = "{sr_api_url}/games/{game_id}/categories".format(sr_api_url=cfg.SR_API_URL, game_id=arg)

            category_body, status_code = await utils.request(url, headers=HEADERS)

            categories = json.loads(category_body)["data"]
        except:
            LOG.exception("Cannot retrieve category name: {arg} ({status_code})"
                          .format(arg=arg, status_code=status_code))
        else:
            for category in categories:
                category = self._parse_category_data(category)
                if category not in self.categories:
                    self.categories.append(category)

    async def _get_profile(self, name, abbreviation=None):
        """ Retrieve user's pb data

        :param name: username
        :param abbreviation: game abbreviation
        :return: reduced dict of user API data
        """
        try:
            user_links = await self._get_user_links(name)
            url = user_links['personal-bests']

            if abbreviation:
                url += "?game=" + abbreviation

            pb_body, status_code = await utils.request(url, headers=HEADERS)
            pbs = json.loads(pb_body)['data']
            game_ids = {pb['run']['game'] for pb in pbs}

            for game_id in game_ids:
                await self._get_categories(game_id)
        except:
            LOG.exception("Cannot retrieve profile for: {name} ({status_code})"
                          .format(name=name, status_code=status_code))
        else:
            profile = collections.defaultdict(dict)

            for pb in pbs:
                pb = self._parse_pb_data(pb)

                game = await self._get_game(pb['game_url'])
                category = await self._get_category(pb['category_url'])
                profile[game['name']][category['name']] = {
                    'place': pb['place'],
                    'time': pb['time'],
                    'video_url': pb['video_url']
                }
            return profile

    # COMMANDS

    @commands.command(pass_context=True, aliases=['sr'])
    async def sr(self, ctx, name, abbrevation=None):
        """ Display an user speedrun.com summary """
        name = name.lower()
        pending_message = await ctx.message.channel.send("Retrieving data for {name}...".format(name=name))
        try:
            summary = await self._get_profile(name, abbreviation=abbrevation)
            embed = self._get_summary_embed(summary)
        except:
            await pending_message.delete()
            LOG.exception("Cannot retrieve profile for {name} with game={game}".format(name=name, game=abbrevation))
        else:
            await pending_message.delete()
            if summary:
                await ctx.message.channel.send("Summary for {name}".format(name=name), embed=embed)

    @commands.command(pass_context=True, aliases=['wr'])
    async def wr(self, ctx, abbreviation):
        """Display a game world records """
        pending_message = await ctx.message.channel.send("Retrieving data for {game}...".format(game=abbreviation))
        try:
            summary = await self._get_game_records(abbreviation)
            embed = self._get_summary_embed(summary)
        except:
            await pending_message.delete()
            LOG.exception("Cannot retrieve records for game={game}".format(game=abbreviation))
        else:
            await pending_message.delete()
            if summary:
                await ctx.message.channel.send("Summary for {game}".format(game=abbreviation), embed=embed)


def setup(bot):
    bot.add_cog(Speedrun(bot))
