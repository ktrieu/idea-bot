from dotenv import load_dotenv
import os
import discord

load_dotenv()

client = discord.Client()

ALLOWED_CHANNELS = {"random"}

COMMAND = "!idea"


def should_respond(message):
    return message.channel.name in ALLOWED_CHANNELS and message.content == COMMAND


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if should_respond(message):
        print(message)


client.run(os.environ.get("DISCORD_TOKEN"))
