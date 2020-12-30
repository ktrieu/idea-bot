from dotenv import load_dotenv
import os
import discord

load_dotenv()

client = discord.Client()

ALLOWED_CHANNELS = {"ideas", "random"}

COMMAND = "!idea"


def should_respond(message):
    return message.channel.name in ALLOWED_CHANNELS and message.content.startswith(
        COMMAND
    )


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if not should_respond(message):
        return

    space_idx = message.content.find(" ")

    if space_idx != -1:
        initial_text = message.content[space_idx + 1 :]
    else:
        pass

    await message.channel.send("TEST MASSAGE")


if __name__ == "__main__":
    print("Starting bot...")
    client.run(os.environ.get("DISCORD_TOKEN"))
