---
name: Telegram token logging
description: Telegram Bot API request URLs include bot tokens; covers safe logging for polling bots.
---

For polling bots, do not log Telegram HTTP request URLs: the bot token appears in the URL path. Redact the token and suppress routine HTTP client request logs.

**Why:** Startup logging exposed the bot token, requiring revocation; routine HTTP request logs are secret-bearing.

**How to apply:** Keep token-aware handler redaction and disable HTTPX info logs whenever configuring Python Telegram bot logging.
