# Clean Agent

Production **clean-room** local AI agent for Ollama / BgGPT.

MIT licensed. No proprietary code.

## Anti-hallucination (BgGPT)

| Mechanism | Effect |
|-----------|--------|
| temperature 0.12 | Less invention |
| Tool-first prompt | Verify before stating facts |
| Forced reflection | Extra check when no tools used |
| Real tool output only | No fabricated stdout/files |
| Permission gate | Blocks dangerous bash / system writes |
| Source citation | Answers should reference tools/memory |

## Features

- Agentic loop + tools (bash, files, memory, skills, **sub-agents**)
- Long-term memory (SQLite FTS5 + MEMORY.md)
- **Dream** — consolidate memory; auto after 5 sessions
- **Telegram** bot channel
- **Health / status** check
- Logging, permissions, Docker

## Quick start

```bash
pip install -e .
# optional Telegram:
pip install -e ".[telegram]"

ollama list   # need a tool-calling model

python main.py                    # CLI
python main.py -m bggpt-gemma3-12b
python main.py --confirm          # confirm risky bash
python main.py dream
python main.py status
python main.py telegram           # needs TELEGRAM_BOT_TOKEN
```

### Telegram

```bash
export TELEGRAM_BOT_TOKEN=123:ABC
export TELEGRAM_ALLOWED_USERS=111,222   # optional whitelist
python main.py telegram
```

Commands in chat: `/start` `/help` `/dream` `/status` + free text tasks.

### Docker

```bash
docker build -t clean-agent .
docker run --rm -it --network host \
  -v $(pwd)/data:/app/data \
  -e OLLAMA_HOST=http://127.0.0.1:11434 \
  clean-agent cli

# or compose
cp .env.example .env   # fill token if needed
docker compose run --rm agent status
```

## Layout

```
main.py
config.py
core/          loop, llm, tools, permissions, prompts, subagent, health, logging
memory/        store, dream
channels/      cli, telegram_bot
skills/
Dockerfile
docker-compose.yml
```

## Safety

- Bash denylist + blocked regex patterns
- `--confirm` for caution commands
- No writes under `/etc`, `/usr`, `/bin`, …
- Telegram user allowlist via env
- Prefer container or dedicated user in production

## License

MIT
