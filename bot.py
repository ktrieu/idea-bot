from dotenv import load_dotenv
from generator import load_model, generate
import os
import discord

load_dotenv()
title_model = load_model()

client = discord.Client()

ALLOWED_CHANNELS = {"random"}

COMMAND = "!idea"


def should_respond(message):
    return message.channel.name in ALLOWED_CHANNELS and message.content.startswith(
        COMMAND
    )


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    space_idx = message.content.find(" ")

    if space_idx != -1:
        initial_text = message.content[space_idx + 1 :]
        new_title = generate(title_model, initial_text)
    else:
        new_title = generate(title_model)

    await message.channel.send(f"Looking for an article idea? How about:\n{new_title}")


client.run(os.environ.get("DISCORD_TOKEN"))
