import collections
import json
import logging
import os

import aiohttp

DEBUG_LOG = logging.getLogger('debug')


def init_channels_file():
    channels_file_name = 'etc/channels.json'
    channels_file = get_file_path(channels_file_name)
    channels = None
    if os.path.exists(channels_file):
        DEBUG_LOG.debug("Loading {filename} to see if an init is needed".format(filename=channels_file_name))
        channels = load_json_file(channels_file_name)
    if channels is None:
        save_file(channels_file_name, "{}")
        DEBUG_LOG.debug("Channels data is invalid or not found, recreating a empty one...")


def get_last_modification_date(filename):
    return os.path.getmtime(get_file_path(filename))


def get_project_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


def get_file_path(filename):
    return "{project_dir}/{filename}".format(project_dir=get_project_dir(), filename=filename)


def save_file(filepath, data):
    with open(filepath, mode='w+', encoding="utf-8") as fs:
        fs.write(data)
        DEBUG_LOG.debug("Updating %s data: %s", filepath, str(data))


def save_json_file(filepath, data):
    with open(filepath, mode='w+', encoding="utf-8") as fs:
        json.dump(collections.OrderedDict(data), fs, indent=2)
        DEBUG_LOG.debug("Updating %s data: %s", filepath, str(data))


def load_file(filepath):
    with open(filepath, mode='r', encoding="utf-8") as fs:
        try:
            data = fs.read()
            DEBUG_LOG.debug("%s loaded: %s", filepath, data.replace("\n", ""))
            return data
        except FileNotFoundError:
            DEBUG_LOG.exception("Cannot load the file: %s", filepath)


def load_json_file(filename):
    if filename.split(".").pop() == "json":
        content = load_file(filename)
        if content:
            try:
                return json.loads(content)
            except (TypeError, ValueError):
                DEBUG_LOG.exception("Cannot load the json file: {filename}".format(filename=filename))
    else:
        DEBUG_LOG.error("'%s' is not a json file", filename)


async def request(url, headers):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                status_code = resp.status
                return await resp.text(), status_code
    except Exception:
        DEBUG_LOG.exception('Cannot request %s', url)
        return "", 400


def strfdelta(tdelta, fmt):
    d = {"days": tdelta.days}
    d['hours'], rem = divmod(tdelta.seconds, 3600)
    d["minutes"], d["seconds"] = divmod(rem, 60)
    return fmt.format(**d)
