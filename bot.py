import SimpleIRC
import requests
import json
import time
import threading
import random

bot = SimpleIRC.IRCConnection()

bot.streams = []
bot.recordings = []

public_help_messages = ["Hello! I'm WatchCode. I help people find programming streams on IRC. Here's the command list.", "!help, !streams, !recording"]

private_help_messages = [
    "Here's more information about the bot and the commands.",
    "!help - Prints these lines",
    "!streams - Prints the current streams",
    "!recording - Gives a random recording"
]

def on_connect(bot):
    bot.set_nick("WatchCode")
    bot.send_user_packet("WatchCodeBot")

def on_welcome(bot):
    bot.send_message("NickServ", "identify {}".format(open("irc_pass.txt").read()))
    bot.join_channel("#WatchPeopleCode")
    bot.join_channel("#WatchCodeTest")

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
                bot.send_message(channel, "\"{}\" by {}: {}".format(stream["title"], stream["username"], stream["url"]))
        else:
            random_recording = random.choice(bot.recordings)
            bot.send_message(channel, "There are no streams at the moment {}. How about a random recording?".format(sender))
            bot.send_message(channel, "\"{}\" by {}: {}".format(random_recording["title"], random_recording["username"], random_recording["url"]))
    elif message.split()[0] == "!recording":
        random_recording = random.choice(bot.recordings)
        bot.send_message(channel, "Here's your recording {}.".format(sender))
        bot.send_message(channel, "\"{}\" by {}: {}".format(random_recording["title"], random_recording["username"], random_recording["url"]))
    elif message.split()[0] == "!help":
        for message_line in public_help_messages:
            bot.send_message(channel, message_line)
        for message_line in private_help_messages:
            bot.send_message(sender, message_line)

def thread(bot):
    while True:
        try:
            json_response = requests.get("http://watchpeoplecode.com/json").json()
            bot.recordings = json_response["completed"]
            new_streams =  json_response["live"]

            for stream in new_streams:
                is_match_found = False
                for known_stream in bot.streams:
                    if stream["title"] == known_stream["title"] and stream["url"] == known_stream["url"] and stream["username"] == known_stream["username"]:
                        is_match_found = True
                if not is_match_found:
                    bot.send_message("#WatchPeopleCode", "{} is now live. Go watch their stream called \"{}\" on {}.".format(stream["username"], stream["title"], stream["url"]))

            bot.streams = new_streams
            time.sleep(30)
        except Exception as error:
            bot.send_message("#WatchPeopleCode", "gkbrk: Help me father! {}".format(error))

bot.on_connect.append(on_connect)
bot.on_welcome.append(on_welcome)
bot.on_public_message.append(on_message)

bot.on_packet_received.append(lambda bot, packet: print(packet.command, packet.arguments, packet.prefix))

bot.connect("irc.freenode.net")

bot.run_loop()
