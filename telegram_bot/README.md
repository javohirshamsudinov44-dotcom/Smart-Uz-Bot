# Python Telegram Bot

A small, runnable Telegram bot starter built with Python and
`python-telegram-bot`. It uses long polling and reads its token from the
`TELEGRAM_BOT_TOKEN` Replit Secret.

## Run it

The token is stored in Replit Secrets. Start the **Telegram Bot** workflow, or
run the project entry point with:

```bash
python main.py
```

To run it outside Replit, install the project dependencies with
[uv](https://docs.astral.sh/uv/):

```bash
uv sync
uv run python main.py
```

## Included behavior

- `/start` — welcome message
- `/help` — list commands
- `/ping` — return `Pong!`
- `/echo <text>` — repeat the supplied text
- Ordinary text messages are echoed back as a starter example

Edit `telegram_bot/bot.py` to add your own commands and behavior. Do not commit
bot tokens or paste them into chat; keep them in Replit Secrets.
