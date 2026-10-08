"""A small Telegram bot starter using long polling."""

import asyncio
import logging
import os
import traceback
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ChatAction
from aiogram.filters import Command, CommandStart
from aiogram.types import ErrorEvent, KeyboardButton, Message, ReplyKeyboardMarkup
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

HOME_BUTTON = "🏠 Bosh menyu"
AI_CHAT_BUTTON = "💬 AI bilan suhbat"
MENU_OPTIONS = (
    AI_CHAT_BUTTON,
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
AI_SYSTEM_PROMPT = (
    "Siz Smart Uz nomli aqlli AI yordamchisiz. Odatiy holatda o‘zbek tilida "
    "foydali, aniq, qisqa va do‘stona javob bering. Foydalanuvchi boshqa tilda "
    "so‘rasa, o‘sha tilda javob bering. Ishonchingiz komil bo‘lmagan faktlarni "
    "uydirmang."
)
AI_ERROR_MESSAGE = (
    "Kechirasiz, hozir AI bilan bog‘lanishda muammo yuz berdi. "
    "Iltimos, birozdan so‘ng qayta urinib ko‘ring."
)
OPENAI_MODEL = "gpt-5.4-mini"
MAX_HISTORY_MESSAGES = 20
MAX_TELEGRAM_MESSAGE_LENGTH = 4000


class SecretRedactionFilter(logging.Filter):
    """Prevent configured secrets from leaking through messages or tracebacks."""

    def __init__(self, *secrets: str) -> None:
        super().__init__()
        self.secrets = tuple(secret for secret in secrets if secret)

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        for secret in self.secrets:
            message = message.replace(secret, "[REDACTED]")
        if record.getMessage() != message:
            record.msg = message
            record.args = ()

        if record.exc_info is not None:
            exception_text = "".join(traceback.format_exception(*record.exc_info))
            if any(secret in exception_text for secret in self.secrets):
                for secret in self.secrets:
                    exception_text = exception_text.replace(secret, "[REDACTED]")
                record.exc_info = None
                record.exc_text = exception_text

        return True


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Build the compact two-column Smart Uz main menu."""
    rows = [
        [
            KeyboardButton(text=MENU_OPTIONS[index]),
            KeyboardButton(text=MENU_OPTIONS[index + 1]),
        ]
        for index in range(0, len(MENU_OPTIONS) - 1, 2)
    ]
    rows.append([KeyboardButton(text=MENU_OPTIONS[-1])])
    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Menyudan birini tanlang",
    )


def home_keyboard() -> ReplyKeyboardMarkup:
    """Show a single button for returning from a feature response."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=HOME_BUTTON)]],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Bosh menyuga qayting",
    )


async def send_long_message(
    message: Message, text: str, reply_markup: ReplyKeyboardMarkup
) -> None:
    """Split long model replies into Telegram-sized messages."""
    for offset in range(0, len(text), MAX_TELEGRAM_MESSAGE_LENGTH):
        await message.answer(
            text[offset : offset + MAX_TELEGRAM_MESSAGE_LENGTH],
            reply_markup=reply_markup if offset == 0 else None,
        )


async def handle_update_error(event: ErrorEvent) -> bool:
    """Log only an exception type; never include request details."""
    logger.error("Telegram update failed (%s).", type(event.exception).__name__)
    return True


def build_dispatcher(openai_client: AsyncOpenAI) -> Dispatcher:
    """Register Smart Uz handlers and keep temporary history per user and chat."""
    dispatcher = Dispatcher()
    active_chats: set[tuple[int, int]] = set()
    histories: dict[tuple[int, int], list[dict[str, str]]] = {}

    def session_key(message: Message) -> tuple[int, int]:
        sender_id = message.from_user.id if message.from_user else message.chat.id
        return message.chat.id, sender_id

    async def show_main_menu(message: Message) -> None:
        key = session_key(message)
        active_chats.discard(key)
        histories.pop(key, None)
        await message.answer(MENU_TEXT, reply_markup=main_menu_keyboard())

    async def handle_text(message: Message) -> None:
        text = message.text
        if not text:
            return

        key = session_key(message)
        if text == HOME_BUTTON:
            active_chats.discard(key)
            histories.pop(key, None)
            await show_main_menu(message)
            return

        if text in MENU_OPTIONS:
            if text == AI_CHAT_BUTTON:
                active_chats.add(key)
                histories.setdefault(key, [])
                await message.answer(
                    "Savolingizni yuboring — odatda o‘zbek tilida javob beraman. "
                    "Bosh menyuga qaytish uchun 🏠 Bosh menyu tugmasini bosing.",
                    reply_markup=home_keyboard(),
                )
            else:
                active_chats.discard(key)
                histories.pop(key, None)
                await message.answer(
                    f"{text}\n\n{PREPARING_TEXT}",
                    reply_markup=home_keyboard(),
                )
            return

        if text.startswith("/"):
            await message.answer(
                "Buyruq topilmadi. Asosiy menyudan bo‘limni tanlang.",
                reply_markup=main_menu_keyboard(),
            )
            return

        if key not in active_chats:
            await message.answer(
                "AI bilan suhbatni boshlash uchun menyudan shu bo‘limni tanlang.",
                reply_markup=main_menu_keyboard(),
            )
            return

        history = histories.setdefault(key, [])
        request_messages = [
            {"role": "system", "content": AI_SYSTEM_PROMPT},
            *history,
            {"role": "user", "content": text},
        ]
        try:
            await message.bot.send_chat_action(
                chat_id=message.chat.id,
                action=ChatAction.TYPING,
            )
            completion = await openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=request_messages,  # type: ignore[arg-type]
                max_completion_tokens=8192,
            )
            answer = completion.choices[0].message.content
            if not answer or not answer.strip():
                raise ValueError("OpenAI returned an empty response")
        except Exception as error:
            logger.error("AI request failed (%s).", type(error).__name__)
            await message.answer(AI_ERROR_MESSAGE, reply_markup=home_keyboard())
            return

        answer = answer.strip()
        history.extend(
            [
                {"role": "user", "content": text},
                {"role": "assistant", "content": answer},
            ]
        )
        if len(history) > MAX_HISTORY_MESSAGES:
            del history[:-MAX_HISTORY_MESSAGES]

        await send_long_message(message, answer, home_keyboard())

    dispatcher.message.register(show_main_menu, CommandStart())
    dispatcher.message.register(show_main_menu, Command("help"))
    dispatcher.message.register(handle_text, F.text)
    dispatcher.errors.register(handle_update_error)
    return dispatcher


def configure_logging(*secrets: str) -> None:
    """Install secret redaction and disable HTTP client request logging."""
    logging.basicConfig(
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        level=logging.INFO,
    )
    redaction_filter = SecretRedactionFilter(*secrets)
    for handler in logging.getLogger().handlers:
        handler.addFilter(redaction_filter)

    for logger_name in ("aiogram.client", "aiohttp", "httpx", "httpcore", "openai"):
        logging.getLogger(logger_name).setLevel(logging.CRITICAL + 1)


async def run_bot(telegram_token: str, openai_api_key: str) -> None:
    """Run aiogram long polling with one reusable asynchronous OpenAI client."""
    async with AsyncOpenAI(
        api_key=openai_api_key,
        timeout=30.0,
        max_retries=2,
    ) as openai_client:
        dispatcher = build_dispatcher(openai_client)
        bot = Bot(token=telegram_token)
        await dispatcher.start_polling(bot)


def main() -> None:
    """Load credentials securely and start the polling bot."""
    telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not telegram_token or not openai_api_key:
        missing = [
            name
            for name, value in (
                ("TELEGRAM_BOT_TOKEN", telegram_token),
                ("OPENAI_API_KEY", openai_api_key),
            )
            if not value
        ]
        raise SystemExit(
            f"Missing required Replit Secrets: {', '.join(missing)}."
        )

    configure_logging(telegram_token, openai_api_key)
    logger.info("Starting Smart Uz with Telegram long polling.")
    asyncio.run(run_bot(telegram_token, openai_api_key))


if __name__ == "__main__":
    main()
