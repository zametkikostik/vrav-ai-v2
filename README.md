# Clean Agent (Vrav AI v2)

Production **clean-room** local AI agent for Ollama / BgGPT.

MIT licensed. No proprietary code.

## Anti-hallucination

| Mechanism | Effect |
|-----------|--------|
| temperature 0.12 | Less invention |
| Tool-first prompt | Verify before stating facts |
| Forced reflection | Extra check when no tools used |
| **Verifier pass** | Strips unsupported claims |
| **Structured answer** | answer + sources + confidence |
| Permission gate | Blocks dangerous bash / system writes |
| web_search + URL citation | Ground current facts |

## Features

- Tools: bash, files, memory, skills, sub-agents, web_search
- Memory + Dream (manual, auto after 5 sessions, **cron**)
- Telegram with **rate limit** (default 20 req / 60s per user)
- Structured JSON output (`--json`)
- Docker + CI

## Quick start

```bash
pip install -e ".[telegram]"
python main.py status
python main.py -m bggpt-gemma3-12b
python main.py --json
python main.py dream
python main.py cron-dream --interval-hours 6
python main.py telegram
```

### Telegram rate limit

Configured in `config.py`: `tg_max_calls`, `tg_window_seconds`.

### Dream cron

```bash
python main.py cron-dream --interval-hours 6
```

## Tests

```bash
python -m pytest tests/ -q
```

## License

MIT
