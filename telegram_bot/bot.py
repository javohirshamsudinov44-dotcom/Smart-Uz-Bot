"""A small Telegram bot starter using long polling."""

import logging
import os
import traceback

from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logger = logging.getLogger(__name__)

HOME_BUTTON = "🏠 Bosh menyu"
MENU_OPTIONS = (
    "💬 AI bilan suhbat",
    "✍️ Matn yozish",
    "🌐 Tarjima",
    "📄 CV / Rezyume",
    "📸 Rasm tahlili",
    "🎨 AI rasm yaratish",
    "💡 G‘oya va maslahatlar",
    "⭐ Premium",
    "👤 Profilim",
)
MENU_TEXT = "🤖 Smart Uz\nSizning aqlli AI yordamchingiz!"
PREPARING_TEXT = (
    "Bu funksiya hozir tayyorlanmoqda. "
    "Tez orada foydalanishingiz mumkin!"
)


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


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Build the compact two-column Smart Uz main menu."""
    rows = [
        [KeyboardButton(MENU_OPTIONS[index]), KeyboardButton(MENU_OPTIONS[index + 1])]
        for index in range(0, len(MENU_OPTIONS) - 1, 2)
    ]
    rows.append([KeyboardButton(MENU_OPTIONS[-1])])
    return ReplyKeyboardMarkup(
        rows,
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Menyudan birini tanlang",
    )


def home_keyboard() -> ReplyKeyboardMarkup:
    """Show a single button for returning from a feature response."""
    return ReplyKeyboardMarkup(
        [[KeyboardButton(HOME_BUTTON)]],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Bosh menyuga qayting",
    )


async def show_main_menu(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Send the Smart Uz welcome text and main menu."""
    del context
    message = update.effective_message
    if message is not None:
        await message.reply_text(MENU_TEXT, reply_markup=main_menu_keyboard())


async def help_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Bring the main menu back when a user asks for help."""
    await show_main_menu(update, context)


async def handle_text(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Respond to each menu button and keep a clear route home."""
    del context
    message = update.effective_message
    if message is None or message.text is None:
        return

    selection = message.text
    if selection == HOME_BUTTON:
        await message.reply_text(MENU_TEXT, reply_markup=main_menu_keyboard())
    elif selection in MENU_OPTIONS:
        await message.reply_text(
            f"{selection}\n\n{PREPARING_TEXT}",
            reply_markup=home_keyboard(),
        )
    else:
        await message.reply_text(
            "Iltimos, quyidagi menyudan bo‘limni tanlang.",
            reply_markup=main_menu_keyboard(),
        )


async def unknown_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Guide unsupported commands back to the menu."""
    del context
    message = update.effective_message
    if message is not None:
        await message.reply_text(
            "Buyruq topilmadi. Asosiy menyudan bo‘limni tanlang.",
            reply_markup=main_menu_keyboard(),
        )


async def handle_error(
    update: object, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Log a safe error summary without exposing request details or tokens."""
    del update
    error_name = type(context.error).__name__
    logger.error("An update could not be processed (%s).", error_name)


def build_application(token: str) -> Application:
    """Create the bot application and register menu handlers."""
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", show_main_menu))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(
        MessageHandler(filters.COMMAND, unknown_command)
    )
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)
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
