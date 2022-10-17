import json
import importlib
from pathlib import Path

class Command:
    def __init__(self, commandlist):
        self.commandlist = commandlist

class CommandHandler:
    """Class commands, commands can use server id to sort data"""
    def __init__(self, data, settings, bot):
        # use the bot's data folder that's passed in.
        # server json files will be stored here!
        self.bot = bot
        self.data_folder = data
        self.settings = settings
        self._commandlist = [
            {
                "module": "base",
                "name": "source",
                "alias": ["github", "sourcecode"],
                "function": lambda a,b: "Source code: https://github.com/Savestate2A03/twitter-mention-discord-relay"
            },
        ]

        # import modules based on name (in the commands directory)
        added_modules = ["twitter"]
        for module in added_modules:
            imported_module = importlib.import_module("." + module, package="phobbot_dev.commandhandler.commands")
            commands = imported_module.Command(self)
            for c in commands.commandlist:
                c["module"] = module # document what module the command is from
            self._commandlist.extend(commands.commandlist)

    # this just gets the server.json and returns it as a dict
    def _server_db(self, server):
        server_db = self.data_folder.joinpath(str(server) + ".json")

        # create essentially empty server json if not found
        if not server_db.is_file():
            with open(server_db, "w") as sdb: 
                json.dump({"id": server}, sdb)

        # return the json as a dict using json.load
        with open(server_db, "r") as sd: 
            return json.load(sd)

    # pass in a server id and a dict to save it as the server database
    def _save_server_db(self, server, db):
        server_db = self.data_folder.joinpath(str(server) + ".json")

        with open(server_db, "w") as sdb: 
            json.dump(db, sdb)

    def decode(self, server, user_command, params, message):
        # lower the user command for consistency
        user_command = user_command.lower()
        # search through the _commandlist array for one that matches our command
        for command in self._commandlist:
            if user_command == command["name"] or user_command in command["alias"]:
                return command["function"](server, params, message)
        # if no command is found, return None
        return None