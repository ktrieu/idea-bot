# idea-bot
Permanently solving the article idea problem.

This project uses a Markov chain trained on historical mathNEWS titles to generate new ones. It also includes a Discord bot to post these titles in response to a command.

# Running

You'll need a mathNEWS WordPress dump file. Name it `wordpress_dump.xml` and put it next to `bot.py`. Then, create your virtualenv, install the requirements, and run `python bot.py`. Remember to create your own `.env` file.
