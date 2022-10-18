from phobbot_dev.commandhandler import ch
from twython import Twython
import asyncio
import discord
import pprint

class CircleBuffer:
    # self-explanatory
    def __init__(self, ch):
        self.ch = ch
        # global database
        server = "info"
        db = self.ch._server_db(server)
        relay_info = db["relay_info"]

        if "circle_buffer" not in relay_info:
            self.buffer_size = 512
            self.buffer = [None] * self.buffer_size
            self.index = 0
            relay_info["circle_buffer"] = {}
            relay_info["circle_buffer"]["buffer"] = self.buffer
            relay_info["circle_buffer"]["buffer_size"] = self.buffer_size
            relay_info["circle_buffer"]["index"] = self.index
            self.ch._save_server_db(server, db)
        else:
            self.buffer = relay_info["circle_buffer"]["buffer"]
            self.buffer_size = relay_info["circle_buffer"]["buffer_size"]
            self.index = relay_info["circle_buffer"]["index"]

    def add(self, a):
        self.buffer[self.index] = a
        self.index = (self.index + 1) % self.buffer_size
        # global database
        server = "info"
        db = self.ch._server_db(server)
        relay_info = db["relay_info"]
        relay_info["circle_buffer"]["buffer"] = self.buffer
        relay_info["circle_buffer"]["index"] = self.index
        self.ch._save_server_db(server, db)
        
    def check_if_in_buffer(self, a):
        return (a in self.buffer)

class TwitterTimer:
    def __init__(self, ch):
        self.wait    = 25
        self.loop    = asyncio.get_event_loop()
        self.task    = self.loop.create_task(self.check_mentions())
        self.ch      = ch
        # auth with twitter and save it to the TwitterTimer
        self.twitter = Twython(ch.settings["twitter_api_key"], ch.settings["twitter_api_secret"],
                          ch.settings["twitter_oauth_token"], ch.settings["twitter_oauth_secret"])
        self.user_id = self.ch._server_db("info")["twitter_user_id"]
        # for storing replied messages to. don't wanna flood the channel with threads
        self.circle_buffer = CircleBuffer(ch)

    def create_embed(self, tweet):
        embed=discord.Embed(color=0x8cc8f4, title="🐦 New Twitter mention!", url=f"https://twitter.com/{tweet['user']['screen_name']}/status/{tweet['id']}")
        embed.set_thumbnail(url=tweet['user']['profile_image_url_https'])
        name = tweet['user']['name']
        if len(tweet['user']['name']) > 24:
            name = name[:24] + "..."

        embed.add_field(name=f"{name} | @{tweet['user']['screen_name']}", value=tweet['text'], inline=False)
        embed.set_footer(text="If this is a question, help us out by answering on Twitter!"
                              "\nClick the header to follow the question to Twitter."
                              "\nReact with ✅ to mark as resolved."
                              "\nReact with ❌ to mark as a non-question.")
        return embed

    def get_latest_tweets(self):
        if not self.ch.bot.is_ready():
            return

        # global database
        server = "info"
        db = self.ch._server_db(server)
        relay_info = db["relay_info"]

        # get mentions and save id
        mentions = []
        if "since_id" not in relay_info:
            # first time run, get everything (max 20 items returned)
            mentions = self.twitter.get_mentions_timeline(include_entities=True, trim_user=False)
        else: 
            mentions = self.twitter.get_mentions_timeline(include_entities=True, trim_user=False, since_id=relay_info['since_id'])

        if mentions:
            # store the last received tweet to the database
            relay_info['since_id'] = mentions[0]['id']
            self.ch._save_server_db(server, db)

        return mentions

    async def check_mentions(self):
        # pretty console printing needed for debugging
        # pp = pprint.PrettyPrinter(indent=2)
        while True:
            # loop forever in the event loop
            try:
                tweets = self.get_latest_tweets()
            except:
                # silently fail and try again later
                await asyncio.sleep(self.wait)
                continue

            if not tweets:
                # if there's no tweets, wait until the next api call
                await asyncio.sleep(self.wait)
                continue

            # global database
            server = "info"
            db = self.ch._server_db(server)

            # bail if the relay channel doesn't exist
            relay_info = db["relay_info"]
            if "relay_channel_id" not in relay_info:
                await asyncio.sleep(self.wait)
                continue

            tweets.reverse() # post tweets in order

            for tweet in tweets:
                # pp.pprint(tweet)

                # if the tweet exists in our circle buffer, that means
                # it's a part of an ongoing thread. we don't wanna flood
                # the channel with thread replies!

                # the start of a new reply / mention / thread, mark it for future ignore

                if tweet['in_reply_to_status_id']:
                    if self.circle_buffer.check_if_in_buffer(tweet['in_reply_to_status_id']):
                        self.circle_buffer.add(tweet['id'])
                        continue

                self.circle_buffer.add(tweet['id'])
                
                # create the embed and send it off to the relay channel
                embed = self.create_embed(tweet)
                try:
                    await self.ch.bot.get_channel(relay_info['relay_channel_id']).send(embed=embed)
                except:
                    pass
            await asyncio.sleep(self.wait)

    def stop(self):
        # not used atm
        self.task.cancel()

class Command(ch.Command): 
    def __init__(self, commandhandler):
        commandlist = [
                {
                    "name": "set_relay_channel",
                    "alias": [],
                    "function": self.set_relay_channel
                }
        ]

        self.commandhandler = commandhandler

        # global database
        server = "info"
        db = self.commandhandler._server_db(server)
        # create the relay info sub-db if not exists
        if "relay_info" not in db:
            db["relay_info"] = {}
        self.commandhandler._save_server_db(server, db)

        self.twittertimer = TwitterTimer(commandhandler)

        super().__init__(commandlist)

    def set_relay_channel(self, server, params, message):
        if "Dev" not in [role.name for role in message.author.roles]:
            return # silently do nothing
        # global database
        server = "info"
        db = self.commandhandler._server_db(server)
        # save the relay channel id
        db["relay_info"]["relay_channel_id"] = message.channel.id
        self.commandhandler._save_server_db(server, db)
        return "relay db: " + str(db["relay_info"])