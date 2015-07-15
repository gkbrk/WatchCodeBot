import JustIRC
import requests
import json
import time
import threading
import random

def get_date_time():
    return time.strftime("[%d-%m-%Y %H:%M]")

bot = JustIRC.IRCConnection()

with open("config.json") as config_file:
    config = json.loads(config_file.read())

bot.streams = []
bot.recordings = []
bot.upcoming = []

bot.muted = False

public_help_messages = ["Hello! I'm WatchCode. I help people find programming streams on IRC. Here's the command list.", "!help, !streams, !recording, !upcoming"]

private_help_messages = [
    "Here's more information about the bot and the commands.",
    "!help - Prints these lines",
    "!streams - Prints the current streams",
    "!recording - Gives a random recording",
    "!upcoming - Prints the upcoming streams"
]

def on_connect(bot):
    bot.set_nick(config["nick"])
    bot.send_user_packet(config["username"])

def on_welcome(bot):
    bot.send_message("NickServ", "identify {}".format(open("irc_pass.txt").read()))
    for channel in config["channels"]:
        bot.join_channel(channel)

    th = threading.Thread(target=thread, kwargs={"bot": bot})
    th.daemon = True
    th.start()

def on_message(bot, channel, sender, message):
    if len(message.split()) == 0:
        message = "."

    if message.split()[0] == "!streams":
        if len(bot.streams) > 0:
            bot.send_message(channel, "Here are your streams {}".format(sender))
            for stream in bot.streams:
                bot.send_message(channel, "\"{}\" by {}: {}".format(stream["title"], stream["user"], stream["url"]))
        else:
            if len(bot.recordings) > 1:
                random_recording = random.choice(bot.recordings)
                bot.send_message(channel, "There are no streams at the moment {}. How about a random recording?".format(sender))
                bot.send_message(channel, "\"{}\" by {}: {}".format(random_recording["title"], random_recording["user"], random_recording["url"]))
    elif message.split()[0] == "!recording":
        if len(bot.recordings) > 0:
            random_recording = random.choice(bot.recordings)
            bot.send_message(channel, "Here's your recording {}.".format(sender))
            bot.send_message(channel, "\"{}\" by {}: {}".format(random_recording["title"], random_recording["user"], random_recording["url"]))
    elif message.split()[0] == "!upcoming":
        if len(bot.upcoming) > 0:
            bot.send_message(channel, "Here are the upcoming streams {}.".format(sender))
            for stream in bot.upcoming:
                bot.send_message(channel, "\"{}\" by {}: {}".format(stream["title"], stream["user"], stream["url"]))
        else:
            if len(bot.streams) > 0:
                bot.send_message(channel, "There are no upcoming streams, but there are {} live streams.".format(len(bot.streams)))
            else:
                if len(bot.recordings) > 0:
                    random_recording = random.choice(bot.recordings)
                    bot.send_message(channel, "There are no upcoming or live streams at the moment. How about a random recording?".format(sender))
                    bot.send_message(channel, "\"{}\" by {}: {}".format(random_recording["title"], random_recording["user"], random_recording["url"]))
    elif message.split()[0] == "!help":
        for message_line in public_help_messages:
            bot.send_message(channel, message_line)
        for message_line in private_help_messages:
            bot.send_message(sender, message_line)
    elif message.split()[0] == "!shoot" and len(message.split()) > 1:
        bot.send_message(channel, "▄︻̷̿┻̿═━一 {} pew pew".format(message.split()[1]))

def thread(bot):
    counter = 10 #Get all the documents on startup
    while True:
        try:
            json_live = requests.get("http://watchpeoplecode.com/api/v1/streams/live").json()
            new_streams = json_live["data"]

            for stream in new_streams:
                match_found = False
                for known_stream in bot.streams:
                    if stream["title"] == known_stream["title"] and stream["url"] == known_stream["url"] and stream["user"] == known_stream["user"]:
                        match_found = True
                if not match_found:
                    for channel in config["channels"]:
                        if stream["username"]:
                            bot.send_message(channel, "\"{}\" by {} is now live on {}.".format(stream["title"], stream["user"], stream["url"]))
                        else:
                            bot.send_message(channel, "\"{}\" is now live on {}.".format(stream["title"], stream["url"]))
            
            bot.streams = new_streams
        except Exception as error:
            with open("errorlog.txt", "a") as error_file:
                error_file.write("[{}] {}\n".format(get_date_time(), error))

        if counter % 2 == 0:
            try:
                json_upcoming = requests.get("http://watchpeoplecode.com/api/v1/streams/upcoming").json()
                bot.upcoming = json_upcoming["data"]
            except Exception as error:
                with open("errorlog.txt", "a") as error_file:
                    error_file.write("[{}] {}\n".format(get_date_time(), error))

        if counter % 10 == 0:
            try:
                json_upcoming = requests.get("http://watchpeoplecode.com/api/v1/streams/completed").json()
                bot.recordings = json_upcoming["data"]
            except Exception as error:
                with open("errorlog.txt", "a") as error_file:
                    error_file.write("{} {}\n".format(get_date_time(), error))
        
        counter = (counter % 1000) + 1
        time.sleep(30)

bot.on_connect.append(on_connect)
bot.on_welcome.append(on_welcome)
bot.on_public_message.append(on_message)

bot.connect("irc.freenode.net")

bot.run_loop()
