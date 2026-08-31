# Clean Agent (Vrav AI v2)

Local tool-using AI agent for Ollama / BgGPT. MIT. Clean-room.

## Highlights

- Anti-hallucination: low temp, tool-first, reflection, **verifier**, **JSON final schema**
- Structured answers: `answer` + `sources` + `confidence`
- Telegram rate limit (**SQLite-persisted** across restarts)
- Dream: manual, auto, interval, or **5-field cron** (`0 */6 * * *`)

## Quick start

```bash
pip install -e ".[telegram]"
python main.py status
python main.py --json
python main.py cron-dream --cron "0 */6 * * *"
python main.py telegram
python -m pytest tests/ -q
```

## License

MIT
