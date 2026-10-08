# Python Telegram Bot

A Python Telegram bot for Smart Uz, built with aiogram 3. It uses long polling
and reads `TELEGRAM_BOT_TOKEN` and `OPENAI_API_KEY` from Replit Secrets.

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
- `💬 AI bilan suhbat` — sends follow-up text to OpenAI with Uzbek as the default response language
- Other menu options — respond with a friendly preparation notice
- `🏠 Bosh menyu` — return from an option screen to the main menu

AI conversation history is kept temporarily per user and chat, and cleared
when they return to the main menu. Edit `telegram_bot/bot.py` to connect other
menu options. Never commit credentials or print them in logs.
