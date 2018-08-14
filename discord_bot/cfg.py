import importlib


class Config:

    def load(self, filename):
        try:
            module = importlib.import_module("etc." + filename)

            self.CONF_NAME = filename

            # CLIENT
            self.COMMAND_PREFIX = getattr(module, "COMMAND_PREFIX", "!")
            self.ADMIN_ROLES = getattr(module, "ADMIN_ROLES", [])
            self.LOADED_EXTENSIONS = getattr(module, "LOADED_EXTENSIONS", [])
            self.DISCORD_BOT_TOKEN = getattr(module, "DISCORD_BOT_TOKEN")

            # TWITCH COG
            self.TWITCH_API_URL = getattr(module, "TWITCH_API_URL",  "https://api.twitch.tv/kraken")
            self.TWITCH_API_ACCEPT = getattr(module, "TWITCH_API_ACCEPT", "application/vnd.twitchtv.v5+json")
            self.TWITCH_API_CLIENT_ID = getattr(module, "TWITCH_API_CLIENT_ID", None)
            self.MIN_OFFLINE_DURATION = getattr(module, "MIN_OFFLINE_DURATION", 60)

            # DAB COG
            self.DAB_COOLDOWN = getattr(module, "DAB_COOLDOWN", 0)

            # ORI RANDO COG
            self.SEEDGEN_API_URL = getattr(module, "SEEDGEN_API_URL",  "http://orirandocoopserver.appspot.com")
            self.SEEDGEN_COOLDOWN = getattr(module, "SEEDGEN_COOLDOWN", 0)
            self.RANDO_ROLE = getattr(module, "RANDO_ROLE", None)

            # DATABASE
            self.DB_HOST = getattr(module, "DB_HOST", None)
            self.DB_PORT = getattr(module, "DB_PORT", 5432)
            self.DB_NAME = getattr(module, "DB_NAME", None)
            self.DB_USER = getattr(module, "DB_USER", None)
            self.DB_PASSWORD = getattr(module, "DB_PASSWORD", None)

        except Exception as e:
            if type(e) == ImportError:
                message = f"Cannot find the configuration file 'etc/{filename}.py'"
            elif type(e) == AttributeError:
                message = f"Missing configuration variable: {e.args[0]}"
            else:
                message = f"Cannot import the configuration file 'etc/{filename}.py'"
            raise type(e)(message)


CONF = Config()
