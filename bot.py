from dotenv import load_dotenv
import gpt_2_simple as gpt2
import os
import discord
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
import tensorflow as tf
import logging

load_dotenv()

ALLOWED_CHANNELS = {"ideas", "random"}

COMMAND = "!idea"
TEMPERATURE = 0.9
GENERATE_N_WORDS = 32
N_ATTEMPTS = 5
MAX_MESSAGES_BEFORE_RESET = 2


class IdeaBotClient(discord.Client):
    def __init__(self):
        super().__init__()
        self.sess = None
        self.sess_lock = Lock()
        self.reset_tf_session()
        self.executor = ThreadPoolExecutor()
        self.messages_generated = 0
        logging.basicConfig(
            filename="idea-bot.log",
            level=logging.INFO,
        )

    def should_respond(self, message):
        return message.channel.name in ALLOWED_CHANNELS and message.content.startswith(
            COMMAND
        )

    def generate_message(self, initial_text, message_id):
        if initial_text is None:
            logging.info(f"Generating prefixless message for {message_id}")
            return self.generate_potential_message(None)

        attempts = N_ATTEMPTS

        # Try N_ATTEMPTS times to generate a message that isn't just the initial text
        while attempts > 0:
            logging.info(
                f"Prefix message generation for {message_id}: attempt {N_ATTEMPTS - attempts + 1} of {N_ATTEMPTS}"
            )
            potential_message = self.generate_potential_message(initial_text)
            if potential_message != initial_text:
                logging.info(f"Prefix message generation success for {message_id}")
                return potential_message

            attempts -= 1

        # well, we tried
        logging.info(f"Attempts exhausted for {message_id}")
        return potential_message

    def generate_potential_message(self, initial_text):
        with self.sess_lock:
            with self.graph.as_default():
                # adding a prefix seems to constrain the model,
                # so crank up the temperature if one is provided
                generated = gpt2.generate(
                    self.sess,
                    length=GENERATE_N_WORDS,
                    temperature=TEMPERATURE,
                    truncate="\n\n",
                    prefix=initial_text,
                    return_as_list=True,
                )[0]
                self.messages_generated += 1
                return generated

    def reset_tf_session(self):
        with self.sess_lock:
            if self.sess is None:
                self.sess = gpt2.start_tf_sess()
            else:
                self.sess = gpt2.reset_session(self.sess)
            gpt2.load_gpt2(self.sess)
            self.graph = tf.get_default_graph()
            self.messages_generated = 0

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

        generated = await self.loop.run_in_executor(
            self.executor, lambda: self.generate_message(initial_text, message.id)
        )

        logging.info(
            f"Generation complete for {message.id}, {self.messages_generated} messages generated"
        )

        await sent_message.edit(content=f"How about:\n{generated}")

        logging.info(f"Reply sent for {message.id}")

        # FIX: gpt-2-simple slowly leaks memory over time, so reset the session after every message to combat this
        await self.loop.run_in_executor(self.executor, self.reset_tf_session)


if __name__ == "__main__":
    print("Creating client...")
    client = IdeaBotClient()
    print("Bot started...")
    client.run(os.environ.get("DISCORD_TOKEN"))
