from dotenv import load_dotenv
import os
import discord
import logging
from generator import GeneratorProcess, GenerateRequest, StopRequest
from multiprocessing import Queue

load_dotenv()

ALLOWED_CHANNELS = {"ideas", "random"}

COMMAND = "!idea"


class IdeaBotClient(discord.Client):
    def __init__(self):
        super().__init__()
        self.messages_generated = 0
        logging.basicConfig(
            filename="idea-bot.log",
            level=logging.INFO,
        )
        self.requests = Queue()
        self.results = Queue()
        self.generator_process = GeneratorProcess(requests=self.requests, results=self.results)
        self.generator_process.start()

    def should_respond(self, message):
        return message.channel.name in ALLOWED_CHANNELS and message.content.startswith(
            COMMAND
        )

    def terminate_worker_process(self):
        self.requests.put(StopRequest())

    async def on_message(self, message):
        if message.author == self.user:
            return

        if not self.should_respond(message):
            return

        space_idx = message.content.find(" ")

        initial_text = None

        if space_idx != -1:
            initial_text = message.content[space_idx + 1 :]

        logging.info(
            f"{message.author} ({message.id}) requested message with prefix: {initial_text}"
        )

        sent_message = await message.channel.send("Let me think...")

        logging.info(f"Scheduling generation for {message.id}...")

        self.requests.put(GenerateRequest(initial_text, message.id))


if __name__ == "__main__":
    print("Creating client...")
    client = IdeaBotClient()
    print("Logging in...")
    client.run(os.environ.get("DISCORD_TOKEN"))
    print("Terminating worker process...")
    client.terminate_worker_process()
