"""A small Telegram bot starter using long polling."""

import asyncio
import logging
import os
import re
import traceback
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ChatAction
from aiogram.filters import Command, CommandStart
from aiogram.types import ErrorEvent, KeyboardButton, Message, ReplyKeyboardMarkup
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

HOME_BUTTON = "🏠 Bosh menyu"
PROFILE_BACK_BUTTON = "⬅️ Orqaga"
AI_CHAT_BUTTON = "💬 AI bilan suhbat"
PREMIUM_BUTTON = "⭐ Premium"
PREMIUM_BUY_BUTTON = "💳 Premium sotib olish"
PROFILE_BUTTON = "👤 Profilim"
MENU_OPTIONS = (
    AI_CHAT_BUTTON,
    "✍️ Matn yozish",
    "🌐 Tarjima",
    "📄 CV / Rezyume",
    "📸 Rasm tahlili",
    "🎨 AI rasm yaratish",
    "💡 G‘oya va maslahatlar",
    PREMIUM_BUTTON,
    PROFILE_BUTTON,
)
MENU_TEXT = "🤖 Smart Uz\nSizning aqlli AI yordamchingiz!"
PREPARING_TEXT = (
    "Bu funksiya hozir tayyorlanmoqda. "
    "Tez orada foydalanishingiz mumkin!"
)
PREMIUM_PAGE_TEXT = (
    "⭐ Smart Uz Premium\n"
    "Joriy holatingiz: Free\n\n"
    "⭐ Premium nima beradi?\n"
    "Premium imkoniyatlari faollashtirilganda shu yerda ko‘rsatiladi.\n\n"
    "💳 Premium tariflari\n"
    "Tariflar va narxlar hali belgilanmagan."
)
PREMIUM_NOT_ACTIVE_TEXT = (
    "Premium hozircha faollashtirilmagan. "
    "Hozircha hech qanday to‘lov olinmaydi."
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
OPENAI_MODEL = "gpt-5-mini"
MAX_HISTORY_MESSAGES = 20
MAX_TELEGRAM_MESSAGE_LENGTH = 4000
_URL_PATTERN = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)
_AUTH_HEADER_PATTERN = re.compile(
    r"(?i)(authorization\s*[:=]\s*)(?:bearer\s+)?[^\s,;]+"
)
_BEARER_PATTERN = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/-]+=*")
_OPENAI_KEY_PATTERN = re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{8,}\b")


def sanitize_diagnostic_text(text: str, *secrets: str) -> str:
    """Remove credentials and URLs before writing external errors to logs."""
    for secret in secrets:
        if secret:
            text = text.replace(secret, "[REDACTED]")
    text = _URL_PATTERN.sub("[URL REDACTED]", text)
    text = _AUTH_HEADER_PATTERN.sub(r"\1[REDACTED]", text)
    text = _BEARER_PATTERN.sub("Bearer [REDACTED]", text)
    text = _OPENAI_KEY_PATTERN.sub("[REDACTED]", text)
    return text[:500]


class SecretRedactionFilter(logging.Filter):
    """Prevent configured secrets from leaking through messages or tracebacks."""

    def __init__(self, *secrets: str) -> None:
        super().__init__()
        self.secrets = tuple(secret for secret in secrets if secret)

    def filter(self, record: logging.LogRecord) -> bool:
        original_message = record.getMessage()
        message = sanitize_diagnostic_text(original_message, *self.secrets)
        if original_message != message:
            record.msg = message
            record.args = ()

        if record.exc_info is not None:
            exception_text = "".join(traceback.format_exception(*record.exc_info))
            safe_exception_text = sanitize_diagnostic_text(
                exception_text, *self.secrets
            )
            if exception_text != safe_exception_text:
                record.exc_info = None
                record.exc_text = safe_exception_text

        if record.exc_text is not None:
            record.exc_text = sanitize_diagnostic_text(
                record.exc_text, *self.secrets
            )

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


def profile_keyboard() -> ReplyKeyboardMarkup:
    """Show the profile-only back button."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=PROFILE_BACK_BUTTON)]],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Bosh menyuga qayting",
    )


def premium_keyboard() -> ReplyKeyboardMarkup:
    """Show Premium purchase placeholder and back navigation."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=PREMIUM_BUY_BUTTON)],
            [KeyboardButton(text=PROFILE_BACK_BUTTON)],
        ],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Premium bo‘limi",
    )


def profile_text(user: object | None) -> str:
    """Format Telegram identity and clearly mark unavailable account metrics."""
    if user is None:
        return (
            "👤 Profilim\n\n"
            "Ism: Mavjud emas\n"
            "Telegram ID: Mavjud emas\n"
            "Premium holati: Free\n"
            "Bugungi AI foydalanish: Kuzatilmaydi\n"
            "Kunlik AI limiti: Belgilanmagan"
        )

    first_name = getattr(user, "first_name", None) or "Mavjud emas"
    user_id = getattr(user, "id", None)
    username = getattr(user, "username", None)
    lines = [
        "👤 Profilim",
        "",
        f"Ism: {first_name}",
    ]
    if username:
        lines.append(f"Telegram username: @{username}")
    lines.extend(
        [
            f"Telegram ID: {user_id if user_id is not None else 'Mavjud emas'}",
            "Premium holati: Free",
            "Bugungi AI foydalanish: Kuzatilmaydi",
            "Kunlik AI limiti: Belgilanmagan",
        ]
    )
    return "\n".join(lines)


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


def build_dispatcher(openai_client: AsyncOpenAI, *secrets: str) -> Dispatcher:
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

        if text == PROFILE_BACK_BUTTON:
            await show_main_menu(message)
            return

        if text == PREMIUM_BUY_BUTTON:
            await message.answer(
                PREMIUM_NOT_ACTIVE_TEXT,
                reply_markup=premium_keyboard(),
            )
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
            elif text == PROFILE_BUTTON:
                active_chats.discard(key)
                histories.pop(key, None)
                await message.answer(
                    profile_text(message.from_user),
                    reply_markup=profile_keyboard(),
                )
            elif text == PREMIUM_BUTTON:
                active_chats.discard(key)
                histories.pop(key, None)
                await message.answer(
                    PREMIUM_PAGE_TEXT,
                    reply_markup=premium_keyboard(),
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
        request_input = [*history, {"role": "user", "content": text}]
        try:
            await message.bot.send_chat_action(
                chat_id=message.chat.id,
                action=ChatAction.TYPING,
            )
            response = await openai_client.responses.create(
                model=OPENAI_MODEL,
                instructions=AI_SYSTEM_PROMPT,
                input=request_input,  # type: ignore[arg-type]
                max_output_tokens=8192,
            )
            answer = response.output_text
            if not answer or not answer.strip():
                raise ValueError("OpenAI returned an empty response")
        except Exception as error:
            status = getattr(error, "status_code", None)
            safe_message = sanitize_diagnostic_text(str(error), *secrets)
            logger.error(
                "OpenAI request failed: type=%s status=%s message=%s",
                type(error).__name__,
                status if status is not None else "unknown",
                safe_message or "No diagnostic message provided.",
            )
            if status == 401:
                user_error = (
                    "OpenAI API kaliti rad etildi (401). Administrator "
                    "Replit Secrets’dagi OPENAI_API_KEY qiymatini tekshirishi kerak."
                )
            elif status == 404:
                user_error = (
                    "Tanlangan OpenAI modeli topilmadi (404). "
                    "Administrator model sozlamasini tekshirishi kerak."
                )
            elif status == 429:
                user_error = (
                    "AI xizmati hozir band yoki limitga yetdi. "
                    "Iltimos, birozdan so‘ng qayta urinib ko‘ring."
                )
            else:
                user_error = AI_ERROR_MESSAGE
            await message.answer(user_error, reply_markup=home_keyboard())
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

    for logger_name in (
        "aiogram.client",
        "aiohttp",
        "httpx",
        "httpx2",
        "httpcore",
        "openai",
    ):
        logging.getLogger(logger_name).setLevel(logging.CRITICAL + 1)


async def run_bot(telegram_token: str, openai_api_key: str) -> None:
    """Run aiogram long polling with one reusable asynchronous OpenAI client."""
    async with AsyncOpenAI(
        api_key=openai_api_key,
        timeout=30.0,
        max_retries=2,
    ) as openai_client:
        dispatcher = build_dispatcher(
            openai_client, telegram_token, openai_api_key
        )
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
