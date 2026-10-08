# Python Telegram Bot

A Python Telegram bot for Smart Uz, built with `python-telegram-bot`. It uses
long polling and reads its token from the `TELEGRAM_BOT_TOKEN` Replit Secret.

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

## Main menu

- `/start` and `/help` — show the Uzbek Smart Uz menu
- Nine emoji-labeled options — each responds with a friendly preparation notice
- `🏠 Bosh menyu` — return from an option screen to the main menu

Edit `telegram_bot/bot.py` to connect menu options to real services. Do not
commit bot tokens or paste them into chat; keep them in Replit Secrets.
