# idea-bot

Permanently solving the article idea problem.

This project uses a fine-tuned GPT-3 model to generate mathNEWS article titles.

# Running

You'll need an OpenAI API key from their private beta. Set that in the .env file.

Next, you'll need training data. If you have an XML dump from the WordPress, `process_dump.py` will process that into a format OpenAI expects. Then, run `fine_tune.py`. Fine-tuning takes about half an hour on the current dataset. When it finishes, fill in the fine-tuned model ID in the .env file.

Then, run `bot.py` and the bot should respond with ideas!

To limit the channels the bot operates in, look at `ALLOWED_CHANNELS` in `bot.py`.
