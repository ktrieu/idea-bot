from dotenv import load_dotenv
import os
import discord

load_dotenv()

client = discord.Client()


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    print(message.content)


client.run(os.environ.get("DISCORD_TOKEN"))
