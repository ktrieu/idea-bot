from dotenv import load_dotenv
import gpt_2_simple as gpt2
import os
import discord

load_dotenv()

ALLOWED_CHANNELS = {"ideas", "random"}

COMMAND = "!idea"
TEMP_NO_PREFIX = 0.9
TEMP_PREFIX = 1.2


class IdeaBotClient(discord.Client):
    def __init__(self, sess):
        super().__init__()
        self.sess = sess

    def should_respond(self, message):
        return message.channel.name in ALLOWED_CHANNELS and message.content.startswith(
            COMMAND
        )

    def generate_message(self, initial_text):
        # adding a prefix seems to constrain the model,
        # so crank up the temperature if one is provided
        temperature = TEMP_NO_PREFIX if initial_text is None else TEMP_PREFIX
        texts = gpt2.generate(
            self.sess,
            length=32,
            temperature=temperature,
            truncate="\n\n",
            prefix=initial_text,
            return_as_list=True,
            nsamples=5,
            batch_size=5,
        )
        # attempt to filter out failed generated text that doesn't expand on the prefix
        if initial_text is not None:
            texts = list(filter(lambda t: t != initial_text, texts))
        return texts[0]

    async def on_message(self, message):
        if message.author == self.user:
            return

        if not self.should_respond(message):
            return

        space_idx = message.content.find(" ")

        initial_text = None

        if space_idx != -1:
            initial_text = message.content[space_idx + 1 :]

        await message.channel.send(self.generate_message(initial_text))


if __name__ == "__main__":
    print("Loading text model...")
    sess = gpt2.start_tf_sess()
    gpt2.load_gpt2(sess)
    print("Creating client...")
    client = IdeaBotClient(sess)
    print("Bot started...")
    client.run(os.environ.get("DISCORD_TOKEN"))
