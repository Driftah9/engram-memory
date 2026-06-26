# Technical Reference

Internals, schemas, and implementation details for contributors and advanced users. For a conceptual overview, see [architecture.md](architecture.md).

---

## File format

### YAML frontmatter

Every knowledge file begins with a YAML frontmatter block. Two formats are accepted:

**Flat format** (original):
```yaml
---
name: my-node-id
type: feedback
description: One-line searchable summary
session_date: 2026-06-26
see_also:
  - other-node
  - another-node
---
```

**Nested format** (current):
```yaml
---
name: my-node-id
type: feedback
description: One-line searchable summary
metadata:
  type: feedback
  session_date: 2026-06-26
  relations:
    see_also:
      - other-node
      - another-node
---
```

Both formats are parsed identically. `metadata.type` takes precedence over top-level `type` when both exist.

### Field reference

| Field | Required | Description |
|---|---|---|
| `name` | Yes | Unique node ID. Hyphenated lowercase. Used in relations and as DB primary key. |
| `type` | Yes | One of: `user`, `feedback`, `project`, `reference`. Controls filtering. |
| `description` | No | One-line summary. Indexed for FTS search. Appears in query results. |
| `session_date` | No | ISO date string (`YYYY-MM-DD`). When this knowledge was written. |
| `see_also` | No | List of node IDs this node relates to. Stored in `memory_relations`. |

### Sections

H2 headings (`## Heading`) divide a file into sections. Each section is:
- Indexed independently with its content
- Stored with line numbers pointing to its location in the file
- Searchable via `section_query()` without loading the full file

H3+ headings are treated as body content, not section boundaries.

---

## SQLite schema

The database has four tables:

```sql
-- Primary node index
CREATE TABLE memory_index (
    id           TEXT PRIMARY KEY,
    type         TEXT NOT NULL DEFAULT 'unknown',
    description  TEXT,
    file_path    TEXT NOT NULL,
    file_name    TEXT NOT NULL,
    line_start   INTEGER,        -- line where frontmatter ends / body begins
    line_end     INTEGER,        -- last line of file
    session_date TEXT,
    body         TEXT            -- full file body (after frontmatter)
);

-- Section-level line pointers
CREATE TABLE memory_sections (
    rowid      INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id    TEXT NOT NULL REFERENCES memory_index(id) ON DELETE CASCADE,
    heading    TEXT,
    line_start INTEGER,          -- first line of section
    line_end   INTEGER,          -- last line of section
    content    TEXT             -- section body text (for search)
);

-- Relation graph
CREATE TABLE memory_relations (
    from_id TEXT NOT NULL,
    to_id   TEXT NOT NULL,
    PRIMARY KEY (from_id, to_id)
);

-- FTS5 virtual table (indexes id, description, body)
CREATE VIRTUAL TABLE memory_fts USING fts5(
    id,
    description,
    body,
    content='memory_index',
    content_rowid='rowid'
);
```

### Indexes

```sql
CREATE INDEX idx_memory_type      ON memory_index(type);
CREATE INDEX idx_sections_node    ON memory_sections(node_id);
CREATE INDEX idx_relations_from   ON memory_relations(from_id);
CREATE INDEX idx_relations_to     ON memory_relations(to_id);
```

### FTS5 triggers

The FTS index is maintained by insert/delete/update triggers:

```sql
CREATE TRIGGER memory_fts_ai AFTER INSERT ON memory_index BEGIN
    INSERT INTO memory_fts(rowid, id, description, body)
    VALUES (new.rowid, new.id, new.description, new.body);
END;

CREATE TRIGGER memory_fts_ad AFTER DELETE ON memory_index BEGIN
    INSERT INTO memory_fts(memory_fts, rowid, id, description, body)
    VALUES ('delete', old.rowid, old.id, old.description, old.body);
END;

CREATE TRIGGER memory_fts_au AFTER UPDATE ON memory_index BEGIN
    INSERT INTO memory_fts(memory_fts, rowid, id, description, body)
    VALUES ('delete', old.rowid, old.id, old.description, old.body);
    INSERT INTO memory_fts(rowid, id, description, body)
    VALUES (new.rowid, new.id, new.description, new.body);
END;
```

### Connection settings

```python
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA synchronous=NORMAL")
```

WAL mode allows concurrent reads while writing. `NORMAL` synchronous is safe for this use case (non-critical data that can be rebuilt).

---

## FTS5 query safety

SQLite FTS5 MATCH syntax treats several characters as operators. Raw user input passed directly to MATCH will crash with a syntax error.

**Problematic characters:**

| Character | FTS5 meaning | Sanitizer action |
|---|---|---|
| `'` apostrophe | Syntax boundary | Removed |
| `"` quote | Phrase grouping | Removed |
| `-` hyphen | NOT operator | Replaced with space |
| `*` asterisk | Prefix wildcard | Removed |
| `^` caret | Boost operator | Removed |
| `:` colon | Column filter | Replaced with space |
| `(` `)` parens | Grouping | Removed |

The sanitizer in `src/engram/sanitizer.py`:

```python
_FTS_SPECIAL = str.maketrans({
    "'": "", '"': "", "-": " ", "*": "", "^": "", ":": " ", "(": "", ")": ""
})

def sanitize_fts(term: str) -> str:
    return term.translate(_FTS_SPECIAL).strip()
```

All public query methods call `sanitize_fts()` before building the MATCH expression.

---

## Manifest JSON format

The manifest is a machine-readable fallback index written alongside the SQLite DB.

```json
{
  "generated": "2026-06-26T04:12:00",
  "count": 42,
  "nodes": {
    "user-profile": {
      "id": "user-profile",
      "type": "user",
      "description": "Who the user is and their preferences",
      "file_path": "/path/to/knowledge/user_profile.md",
      "file_name": "user_profile.md",
      "line_start": 8,
      "line_end": 47,
      "session_date": "2026-06-26",
      "sections": [
        {
          "heading": "Preferences",
          "line_start": 14,
          "line_end": 22
        },
        {
          "heading": "Constraints",
          "line_start": 24,
          "line_end": 31
        }
      ],
      "relations": ["another-node"]
    }
  }
}
```

`manifest_query()` does a case-insensitive substring search across `id`, `description`, and `file_name`.

---

## Build process

`MemoryStore.build()` runs this sequence:

1. Clear existing DB tables (fresh build)
2. Walk `knowledge_dir` for `*.md` files
3. For each file, call `parse_file(path)`:
   - Strip YAML frontmatter (between `---` delimiters)
   - Extract `id`, `type`, `description`, `session_date`, `see_also`
   - Identify H2 section boundaries by scanning lines
   - For each section, store heading + line range + content
4. INSERT each node into `memory_index`
5. INSERT sections into `memory_sections`
6. INSERT relations into `memory_relations` (with `INSERT OR IGNORE` for dedup)
7. Write manifest JSON
8. Return `{files, build_ms, db_kb, manifest_kb}` stats

Nodes named `MEMORY` or `SCHEMA` (case-insensitive) are excluded from `section_query()` results to prevent index files from flooding results.

---

## Query return shapes

### `query()` and `fts_query()`

```python
[
    {
        "id": "user-profile",
        "type": "user",
        "description": "Who the user is...",
        "file_name": "user_profile.md",
        "line_start": 8,
        "line_end": 47
    },
    ...
]
```

Note: `file_path` is **not** included in FTS results. Use `section_query()` or look up from the manifest to get the full path.

### `section_query()`

```python
[
    {
        "node_id": "user-profile",
        "heading": "Constraints",
        "line_start": 24,
        "line_end": 31,
        "file_path": "/full/path/to/user_profile.md"
    },
    ...
]
```

`file_path` is included — pass directly to `read_lines()`.

### `manifest_query()`

Returns a list of node dicts matching the manifest format above (full structure including sections).

---

## Source layout

```
src/engram/
├── __init__.py        # Public API exports
├── memory_store.py    # MemoryStore class (main entry point)
├── schema.py          # SQL schema string + PRAGMA setup
├── query.py           # fts_query(), section_query() as standalone functions
└── sanitizer.py       # sanitize_fts()
```

The standalone functions in `query.py` mirror the MemoryStore methods and accept a raw `sqlite3.Connection`. Useful for lower-level integration or when you want to manage the connection yourself.
