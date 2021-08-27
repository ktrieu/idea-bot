from dotenv import load_dotenv
import os
import discord
from generator import (
    GeneratorProcess,
    GenerateRequest,
    StopRequest,
    ResponseType,
)
from multiprocessing import Pipe
import util
import asyncio

load_dotenv()

ALLOWED_CHANNELS = {"secret-channel-name"}
ALLOWED_SERVER_IDS = {748228407472423015}

COMMAND = "!idea"

RESP_CHECK_INTERVAL_S = 1


class IdeaBotClient(discord.Client):
    def __init__(self):
        super().__init__()
        self.logger = util.create_logger("idea-bot")
        parent_conn, child_conn = Pipe()
        self.conn = parent_conn
        self.generator_process = GeneratorProcess(conn=child_conn)
        self.generator_process.start()
        self.loop.create_task(self.check_responses())

    def should_respond(self, message):
        return (
            message.channel.name in ALLOWED_CHANNELS
            and message.guild.id in ALLOWED_SERVER_IDS
            and message.content.startswith(COMMAND)
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

        self.conn.send(
            GenerateRequest(initial_text, sent_message.channel.id, sent_message.id)
        )

    async def check_responses(self):
        while True:
            while self.conn.poll():
                resp = self.conn.recv()
                if resp.type == ResponseType.GENERATE:
                    self.logger.info(
                        f"Response found, responding in message {resp.message_id}"
                    )
                    channel = await self.fetch_channel(resp.channel_id)
                    message = await channel.fetch_message(resp.message_id)
                    await message.edit(content=f"How about:\n{resp.generated}")
                else:
                    self.logger.error("Invalid message type received")
            await asyncio.sleep(RESP_CHECK_INTERVAL_S)


if __name__ == "__main__":
    print("Creating client...")
    client = IdeaBotClient()
    print("Starting bot...")
    client.run(os.environ.get("DISCORD_TOKEN"))
    print("Terminating worker process...")
    client.terminate_worker_process()
