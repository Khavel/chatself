# chatself 🪞

![tests](https://github.com/Khavel/chatself/actions/workflows/tests.yml/badge.svg)
![PyPI](https://img.shields.io/pypi/v/chatself)
![python](https://img.shields.io/pypi/pyversions/chatself)

I had 5 years of WhatsApp conversations sitting on my phone and realized I had no idea what was actually in them. Not the events — I remembered those. But the *patterns*. Who I was at 2am. How I talked to people I was in love with. Whether I'd changed at all.

So I built this.

---

## What it does

Parses your exported WhatsApp chats and tells you things like:

- words and phrases you repeat without noticing
- who always writes first (you or them)
- how the balance shifted over months
- your emoji signature
- the longest silences, and who broke them
- how your vocabulary changed year to year

Optional: plug in an OpenAI or Anthropic key and have a conversation about what it all means.

---

## Install

```bash
pip install chatself
# with AI support:
pip install "chatself[ai]"
```

---

## Usage

Export a chat from WhatsApp: **Settings → Chats → Export chat → Without media**

```bash
# single chat
chatself analyze "Chat with Ana.txt" --name Ana

# whole folder
chatself analyze ./exports/ --name Ana

# save an HTML report
chatself analyze "Chat with Ana.txt" --name Ana --html report.html

# talk to an AI about it (needs ANTHROPIC_API_KEY or OPENAI_API_KEY)
chatself analyze "Chat with Ana.txt" --name Ana --ai anthropic
```

The `--ai` flag sends only pre-computed stats to the LLM — not your actual messages.

---

## Full history (Android)

If you want everything, not just one export, you can use the decrypted `msgstore.db` from your Android backup. chatself includes a `DbParser` for that. Instructions coming in the wiki.

---

## Privacy

Everything runs locally. No accounts, no telemetry, no cloud.
The only exception is `--ai`, which sends anonymized summaries (word frequencies, ratios, timestamps) to the API you choose.

---

## Contributing

Open issues, send PRs. The codebase is small and straightforward — parsers, analyzers, a CLI, an HTML builder.

---

MIT

