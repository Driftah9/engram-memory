# engram-memory

**Give your AI agent a memory that survives anything.**

engram-memory lets AI agents store knowledge, look it up instantly, and keep working even if the database goes down — because your knowledge is always backed by plain text files.

---

## The problem it solves

AI agents are forgetful by default. Every session starts fresh. Workarounds like dumping everything into a context window are slow, expensive, and hit limits fast.

engram-memory gives your agent a proper knowledge base:
- **Store** what it learns, organized by type
- **Search** it in milliseconds
- **Recover** automatically if anything breaks

---

## How it works

You keep your knowledge in simple markdown files — one topic per file, organized with a few lines of header info. engram-memory builds a fast search index on top of those files, so your agent can find exactly what it needs without reading everything.

If the index ever fails or gets corrupted, the agent falls back to a backup index file that never goes down. No data loss, no downtime.

```
Your markdown files
       ↓
   Fast search index (SQLite)
       ↓
   Your agent gets answers in milliseconds

   (If index breaks → backup index takes over automatically)
```

---

## Quick start

### Install

```bash
pip install engram-memory
```

### Create a knowledge file

```markdown
---
name: user-profile
type: user
description: Who the user is and their preferences
---

Name: Alice
Location: San Francisco
Prefers: concise answers, no jargon

## Preferences
Short responses unless asked for detail.

## Constraints
Budget is limited. Always flag costs upfront.
```

### Use it in your agent

```python
from engram import MemoryStore

# Point it at your folder of markdown files
store = MemoryStore("./knowledge")
store.build()  # Builds the search index

# Search for what you need
results = store.query("budget")
# → Tells you which file and which lines have the answer

# Read just those lines — not the whole file
content = store.read_lines(results[0]["file_path"],
                           results[0]["line_start"],
                           results[0]["line_end"])
# → "Budget is limited. Always flag costs upfront."
```

---

## What kind of knowledge can it store?

engram-memory uses four categories to keep things organized:

| Type | What goes here | Examples |
|---|---|---|
| **user** | Who the user is | Name, location, preferences, constraints |
| **feedback** | Rules you've learned | "User hates bullet lists", "always confirm before deleting" |
| **project** | Ongoing work | Current goals, decisions made, blockers |
| **reference** | Outside information | Research findings, documentation notes |

Your agent can search all of them at once, or narrow to just the type it needs.

---

## Key features

**Fast search**
Find relevant knowledge in under a millisecond. Works even across hundreds of files.

**Precise retrieval**
Results include the exact file and line numbers where the answer lives — not the whole document. Your agent loads only what it needs.

**Crash-proof fallback**
If the search index fails, a backup JSON index takes over with no code changes required. Your knowledge is never lost.

**Relations between topics**
Link knowledge files together. If "communication-style" relates to "user-profile", your agent can follow that connection automatically.

**No external services**
Runs entirely on your machine. No APIs, no cloud services, no vendor lock-in. Just Python and a SQLite file.

---

## When to use engram-memory

**Good fit:**
- Single AI agent that needs to remember things across sessions
- Small team sharing a knowledge base
- Projects where you want knowledge version-controlled in git
- Anywhere you need fast, reliable retrieval without setting up a server

**Not the right fit:**
- Large-scale distributed systems with many simultaneous writers
- Semantic/similarity search (use a vector database for that)
- Terabytes of data (this is designed for files-on-disk scale)

---

## Full documentation

- [API Reference](docs/api.md) — Every method and parameter
- [Architecture](docs/architecture.md) — How it works under the hood
- [Technical Details](docs/technical.md) — File formats, schema, internals
- [Contributing](CONTRIBUTING.md) — How to submit improvements

---

## Contributing

Found a bug? Have an idea? Read [CONTRIBUTING.md](CONTRIBUTING.md) first — it explains what makes a good contribution. Then open an issue.

---

## License

MIT — free to use, modify, and distribute. See [LICENSE](LICENSE).

---

Built by [Stryder Tech](https://strydertech.com) · Questions: admin@strydertech.com
