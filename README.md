# Clean Agent (Vrav AI v2)

Production **clean-room** local AI agent for Ollama / BgGPT.

MIT licensed. No proprietary code.

## Anti-hallucination (BgGPT)

| Mechanism | Effect |
|-----------|--------|
| temperature 0.12 | Less invention |
| Tool-first prompt | Verify before stating facts |
| Forced reflection | Extra check when no tools used |
| **Verifier pass** | Second LLM pass strips unsupported claims |
| Real tool output only | No fabricated stdout/files |
| Permission gate | Blocks dangerous bash / system writes |
| web_search + URL citation | Ground current facts |

## Features

- Agentic loop + tools (bash, files, memory, skills, sub-agents, **web_search**)
- Long-term memory (SQLite FTS5 + MEMORY.md)
- Dream — consolidate memory; auto after 5 sessions
- Telegram bot channel
- Health / status check
- Logging, permissions, Docker, CI

## Quick start

```bash
pip install -e .
pip install -e ".[telegram]"   # optional

ollama list

python main.py
python main.py -m bggpt-gemma3-12b
python main.py --confirm
python main.py dream
python main.py status
python main.py telegram
```

### Telegram

```bash
export TELEGRAM_BOT_TOKEN=123:ABC
export TELEGRAM_ALLOWED_USERS=111,222
python main.py telegram
```

### Docker

```bash
docker build -t clean-agent .
docker run --rm -it --network host -v $(pwd)/data:/app/data clean-agent status
```

## License

MIT
