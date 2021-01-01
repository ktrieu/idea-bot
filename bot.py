from dotenv import load_dotenv
import os
import discord
import logging
import generator
from generator import GeneratorProcess, GenerateRequest, StopRequest
from multiprocessing import Pipe
import sys
import util

load_dotenv()

ALLOWED_CHANNELS = {"ideas", "random"}

COMMAND = "!idea"


class IdeaBotClient(discord.Client):
    def __init__(self):
        super().__init__()
        self.messages_generated = 0
        self.logger = util.create_logger("idea-bot")
        parent_conn, child_conn = Pipe()
        self.conn = parent_conn
        self.generator_process = GeneratorProcess(conn=child_conn)
        self.generator_process.start()

    def should_respond(self, message):
        return message.channel.name in ALLOWED_CHANNELS and message.content.startswith(
            COMMAND
        )

    def terminate_worker_process(self):
        self.conn.send(StopRequest())

    async def on_message(self, message):
        if message.author == self.user:
            return

        if not self.should_respond(message):
            return

        space_idx = message.content.find(" ")

        initial_text = None

        if space_idx != -1:
            initial_text = message.content[space_idx + 1 :]

        self.logger.info(
            f"{message.author} ({message.id}) requested message with prefix: {initial_text}"
        )

        sent_message = await message.channel.send("Let me think...")

        self.logger.info(f"Scheduling generation for {message.id}...")

        self.conn.send(GenerateRequest(initial_text, message.id))


if __name__ == "__main__":
    print("Creating client...")
    client = IdeaBotClient()
    print("Starting bot...")
    client.run(os.environ.get("DISCORD_TOKEN"))
    print("Terminating worker process...")
    client.terminate_worker_process()
