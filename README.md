# idea-bot
Permanently solving the article idea problem.

This project uses a version of GPT-2 trained on historical mathNEWS titles using [gpt-2-simple](https://github.com/minimaxir/gpt-2-simple) to generate new titles, with an optional prefix.

# Running

You'll need to train your own version of the model. I used [this Google Colaboratory notebook](https://colab.research.google.com/drive/1VLG8e7YSEwypxU-noRNhsv5dW4NfTGce), and a text file of all mathNEWS titles taken from the WordPress, **separated by double newlines**. Then, once you've followed the instructions, download the model, and place the `checkpoints/` folder next to `bot.py`. Then, run the bot.
