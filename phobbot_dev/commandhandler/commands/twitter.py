from phobbot_dev.commandhandler import ch
from twython import Twython

class Command(ch.Command): 
    def __init__(self, commandhandler):
        commandlist = [
                {
                    "name": "test",
                    "alias": ["testing", "moretesting"],
                    "function": self.test
                },
                {
                    "name": "test2",
                    "alias": [],
                    "function": self.test2
                },
        ]
        self.commandhandler = commandhandler
        # set up twitter integration
        self.twitter = Twython(self.commandhandler.settings["twitter_api_key"], self.commandhandler.settings["twitter_api_secret"],
                          self.commandhandler.settings["twitter_oauth_token"], self.commandhandler.settings["twitter_oauth_secret"])

        super().__init__(commandlist)

    # testing commands
    def test(self, server, params, message):
        return "server id: " + str(server) + ", server database: " + str(self.commandhandler._server_db(server))

    def test2(self, server, params, message):
        return str(self.twitter.get_mentions_timeline(include_entities=False, trim_user=True))