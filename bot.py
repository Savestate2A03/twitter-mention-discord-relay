from phobbot_dev import phobbot_dev

bot = phobbot_dev.PhobbotDev()
# api key is defined in data/info.json
bot.run(bot.api_key())