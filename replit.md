# Python Telegram Bot

An independent Python Telegram bot starter alongside the workspace's existing API and design artifacts.

## Run & Operate

- Start the **Telegram Bot** workflow or run `python main.py` to launch the bot
- `uv sync` — install the Python dependencies
- `pnpm --filter @workspace/api-server run dev` — run the API server (port 5000)
- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas from the OpenAPI spec
- `pnpm --filter @workspace/db run push` — push DB schema changes (dev only)
- Required secret: `TELEGRAM_BOT_TOKEN` — Telegram token from BotFather
- Required env for the API server: `DATABASE_URL` — Postgres connection string

## Stack

- pnpm workspaces, Node.js 24, TypeScript 5.9
- API: Express 5
- DB: PostgreSQL + Drizzle ORM
- Validation: Zod (`zod/v4`), `drizzle-zod`
- API codegen: Orval (from OpenAPI spec)
- Build: esbuild (CJS bundle)
- Python 3.13 with `python-telegram-bot` 22.x
- Telegram updates: long polling

## Where things live

- `main.py` — Python bot entry point
- `telegram_bot/bot.py` — Telegram commands, message handlers, and startup
- `telegram_bot/README.md` — bot setup and command reference
- `pyproject.toml` / `uv.lock` — Python dependencies
- `artifacts/api-server` — existing shared API
- `artifacts/mockup-sandbox` — existing design canvas

## Architecture decisions

- Keep the Telegram token in Replit Secrets; application code reads it from the environment.
- Use long polling so the starter does not need a public webhook endpoint.

## Product

- `/start` and `/help` show the Uzbek Smart Uz main menu. Menu selections receive a preparation message and a home button.

## User preferences

- The user asked for a Python Telegram bot project.

## Gotchas

- Keep only one bot process polling with a given Telegram token at a time.

## Pointers

- See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details
