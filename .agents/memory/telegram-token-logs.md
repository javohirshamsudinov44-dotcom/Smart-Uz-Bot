---
name: Smart Uz API logging
description: Safe logging for Telegram and OpenAI credentials used by the polling bot.
---

Do not log raw Telegram or OpenAI request details: Telegram Bot API URLs contain the bot token, and HTTP request logs can expose endpoint URLs or credential-bearing details. Redact both runtime secrets from messages and tracebacks.

**Why:** Startup logging exposed the bot token, requiring revocation; routine HTTP request logs are secret-bearing.

**How to apply:** Keep token/key-aware handler redaction and suppress HTTP client request logs whenever configuring the Smart Uz bot.
