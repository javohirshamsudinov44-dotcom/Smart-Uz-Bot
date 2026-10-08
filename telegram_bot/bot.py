"""A small Telegram bot starter using long polling."""

import logging
import os
import traceback

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logger = logging.getLogger(__name__)


class TokenRedactionFilter(logging.Filter):
    """Prevent the bot token from leaking through log messages or tracebacks."""

    def __init__(self, token: str) -> None:
        super().__init__()
        self.token = token

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        if self.token in message:
            record.msg = message.replace(self.token, "[REDACTED]")
            record.args = ()

        if record.exc_info is not None:
            exception_text = "".join(traceback.format_exception(*record.exc_info))
            if self.token in exception_text:
                record.exc_info = None
                record.exc_text = exception_text.replace(self.token, "[REDACTED]")

        return True


async def start(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Welcome a user and point them to the available commands."""
    del context
    message = update.effective_message
    if message is not None:
        first_name = update.effective_user.first_name if update.effective_user else "there"
        await message.reply_text(
            f"Hi, {first_name}! I’m your Telegram bot starter. "
            "Send /help to see what I can do."
        )


async def help_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """List the starter bot's commands."""
    del context
    message = update.effective_message
    if message is not None:
        await message.reply_text(
            "Available commands:\n"
            "/start — welcome message\n"
            "/help — show this help\n"
            "/ping — check that I’m online\n"
            "/echo <text> — repeat text"
        )


async def ping(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Confirm that the bot is responding."""
    del context
    message = update.effective_message
    if message is not None:
        await message.reply_text("Pong!")


async def echo_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Repeat the text provided to /echo."""
    message = update.effective_message
    if message is None:
        return

    text = " ".join(context.args).strip()
    if not text:
        await message.reply_text("Usage: /echo <text>")
        return

    await message.reply_text(text)


async def echo_text(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Repeat ordinary text messages as a starter example."""
    del context
    message = update.effective_message
    if message is not None and message.text is not None:
        await message.reply_text(message.text)


async def handle_error(
    update: object, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Log a safe error summary without exposing request details or tokens."""
    del update
    error_name = type(context.error).__name__
    logger.error("An update could not be processed (%s).", error_name)


def build_application(token: str) -> Application:
    """Create the bot application and register its handlers."""
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("ping", ping))
    application.add_handler(CommandHandler("echo", echo_command))
    application.add_handler(MessageHandler(filters.COMMAND, help_command))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, echo_text)
    )
    application.add_error_handler(handle_error)
    return application


def main() -> None:
    """Start the bot using the token stored in the environment."""
    logging.basicConfig(
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        level=logging.INFO,
    )

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit(
            "TELEGRAM_BOT_TOKEN is missing. Add your bot token in Replit Secrets."
        )

    redaction_filter = TokenRedactionFilter(token)
    for handler in logging.getLogger().handlers:
        handler.addFilter(redaction_filter)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    logger.info("Starting the Telegram bot with long polling.")
    build_application(token).run_polling()


if __name__ == "__main__":
    main()
