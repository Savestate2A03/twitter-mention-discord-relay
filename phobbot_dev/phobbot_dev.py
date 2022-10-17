import discord
import requests
import shutil
import json
import re
from pathlib import Path

from phobbot_dev.commandhandler.ch import CommandHandler

# subclass of the discord client itself. we add some functionality to
# it and then call the super when we're done setting our stuff up.
class PhobbotDev(discord.Client):
    def __init__(self):
        # data folder containing all bot data
        self.data = Path(Path(__file__).parent.resolve().joinpath("data"))

        # if we don't have data made, copy it from the sample data folder and prompt for required user input
        if not self.data.is_dir():
            # copy the sample data folder to the data folder
            sample_data = Path(Path(__file__).parent.resolve().joinpath("sample_data"))
            shutil.copytree(sample_data, self.data)

            info_dict = None
            # start the prompt for user data
            with open(self.data.joinpath("info.json"), "r") as info: 
                info_dict = json.load(info)
                for setting in info_dict.keys():
                    # if the value of a key in the sample json is null, prompt for it
                    if info_dict[setting] is None:
                        user_input = input(setting + " -> ")
                        info_dict[setting] = user_input

            # close and re-open the json, except writable and save our changes 
            with open(self.data.joinpath("info.json"), "w") as info: 
                json.dump(info_dict, info, indent = 4)

        # load bot settings into instance
        self.settings = None
        with open(self.data.joinpath("info.json"), "r") as info: 
            self.settings = json.load(info)

        # set up commands
        self.commandhandler = CommandHandler(self.data, self.settings, self)

        # set up bot
        super().__init__()

    def api_key(self):
        return self.settings["discord_api_key"]

    def prefix(self):
        # making this per-server would be smart but 
        # considering the scope, it's fine for now
        return self.settings["prefix"]

    # async overrides

    async def on_ready(self):
        print('Logged in as {0.user}'.format(self))

    async def on_message(self, message):
        if message.author == self.user:
            return

        if message.content.strip().startswith(self.prefix()):
            try: 
                # regex matching a command format, not using prefix yet
                match = re.search(r'^!(\S+)\s*(.*)$', message.content.strip())
            except:
                # don't think this should ever trigger, but just in case
                print("command detected, regex search failed: " + message.content.strip())
                return
            command_response = self.commandhandler.decode(message.guild.id, match.group(1), match.group(2), message)
            if command_response is not None:
                await message.channel.send(command_response)