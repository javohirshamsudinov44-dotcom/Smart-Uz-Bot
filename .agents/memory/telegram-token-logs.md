---
name: Smart Uz API logging
description: Safe logging for Telegram and OpenAI credentials used by the polling bot.
---

Do not log raw Telegram or OpenAI request details: Telegram Bot API URLs contain the bot token, and HTTP request logs can expose endpoint URLs or credential-bearing details. Redact both runtime secrets and URLs from messages and tracebacks.

**Why:** Startup logging exposed the bot token, requiring revocation. The installed OpenAI HTTP client also emitted request URLs through an `httpx2` logger, bypassing suppression configured only for `httpx`.

**How to apply:** Keep token/key-aware handler redaction, suppress observed HTTP client loggers, and retain URL sanitization as a fallback if logger names change.
