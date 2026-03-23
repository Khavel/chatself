# chatself 🪞

> *Know yourself through your conversations.*

**chatself** is an open-source tool that turns your WhatsApp chat history into a personal mirror — revealing your communication patterns, relationship dynamics, emotional evolution, and the person you've become over the years.

---

## What you'll discover

- **Your verbal tics** — the phrases and words you repeat without noticing
- **Your emoji & sticker signature** — what you reach for when words aren't enough
- **Relationship dynamics** — who initiates, who responds, who's drifting
- **Your evolution year by year** — how your language, habits, and circle have changed
- **The conversations that shaped you** — key moments hidden in plain sight

---

## Quickstart

### 1. Export your WhatsApp chats

On your phone: **Settings → Chats → Export chat → Without media**

Send yourself the `.txt` files for the conversations you want to analyze.

### 2. Install

```bash
pip install chatself
```

Or from source:

```bash
git clone https://github.com/yourusername/chatself
cd chatself
pip install -e .
```

### 3. Analyze

```bash
# Analyze a single exported chat
chatself analyze chat_with_Ana.txt

# Analyze a folder of exports
chatself analyze ./my_exports/

# Full interactive session (requires OpenAI or Anthropic API key)
chatself reflect ./my_exports/ --ai
```

---

## Advanced: Full history from Android backup

If you want your **complete history** (all chats, all years), chatself supports the decrypted WhatsApp SQLite database (`msgstore.db`).

See [docs/full-history.md](docs/full-history.md) for the step-by-step guide.

---

## Privacy

**Your data never leaves your machine** unless you explicitly use the `--ai` flag (which sends anonymized summaries — never raw messages — to the LLM API of your choice).

All processing is local. No accounts. No telemetry.

---

## Output

chatself produces:

| Output | Description |
|--------|-------------|
| `report.json` | Full structured analysis |
| `report.html` | Visual dashboard (open in browser) |
| Interactive CLI | Ask questions about yourself |

---

## Modules

| Module | What it does |
|--------|-------------|
| `parsers` | Parse WhatsApp `.txt` exports and `msgstore.db` |
| `analytics.patterns` | Activity hours, response times, message ratios |
| `analytics.vocabulary` | Verbal tics, n-grams, language evolution |
| `analytics.emojis` | Emoji frequency, context, signature |
| `analytics.relationships` | Balance, asymmetry, drift over time |
| `analytics.timeline` | Year-by-year personal evolution |

---

## Contributing

PRs welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## License

MIT
