from dotenv import load_dotenv
import gpt_2_simple as gpt2
import os
import discord
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
import tensorflow as tf

load_dotenv()

ALLOWED_CHANNELS = {"ideas", "random"}

COMMAND = "!idea"
TEMPERATURE = 0.9
GENERATE_N_WORDS = 32
N_ATTEMPTS = 5


class IdeaBotClient(discord.Client):
    def __init__(self, sess):
        super().__init__()
        self.sess = sess
        self.graph = tf.get_default_graph()
        self.lock = Lock()
        self.executor = ThreadPoolExecutor()

    def should_respond(self, message):
        return message.channel.name in ALLOWED_CHANNELS and message.content.startswith(
            COMMAND
        )

    def generate_message(self, initial_text):
        if initial_text is None:
            return self.generate_potential_message(None)

        attempts = N_ATTEMPTS

        # Try N_ATTEMPTS times to generate a message that isn't just the initial text
        while attempts > 0:
            potential_message = self.generate_potential_message(initial_text)
            if potential_message != initial_text:
                return potential_message

            attempts -= 1

        # well, we tried
        return potential_message

    def generate_potential_message(self, initial_text):
        with self.lock:
            with self.graph.as_default():
                # adding a prefix seems to constrain the model,
                # so crank up the temperature if one is provided
                return gpt2.generate(
                    self.sess,
                    length=GENERATE_N_WORDS,
                    temperature=TEMPERATURE,
                    truncate="\n\n",
                    prefix=initial_text,
                    return_as_list=True,
                )[0]

    async def on_message(self, message):
        if message.author == self.user:
            return

        if not self.should_respond(message):
            return

        space_idx = message.content.find(" ")

        initial_text = None

        if space_idx != -1:
            initial_text = message.content[space_idx + 1 :]

        sent_message = await message.channel.send("Let me think...")

        generated = await self.loop.run_in_executor(
            self.executor, lambda: self.generate_message(initial_text)
        )

        await sent_message.edit(content=f"How about:\n{generated}")


if __name__ == "__main__":
    print("Loading text model...")
    sess = gpt2.start_tf_sess()
    gpt2.load_gpt2(sess)
    print("Creating client...")
    client = IdeaBotClient(sess)
    print("Bot started...")
    client.run(os.environ.get("DISCORD_TOKEN"))
