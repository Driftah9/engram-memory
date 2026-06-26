"""SQLite schema for engram-memory."""

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS memory_index (
    id           TEXT PRIMARY KEY,
    type         TEXT NOT NULL DEFAULT 'unknown',
    description  TEXT,
    file_path    TEXT NOT NULL,
    file_name    TEXT NOT NULL,
    line_start   INTEGER,
    line_end     INTEGER,
    session_date TEXT,
    body         TEXT
);

CREATE TABLE IF NOT EXISTS memory_sections (
    rowid      INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id    TEXT NOT NULL REFERENCES memory_index(id) ON DELETE CASCADE,
    heading    TEXT,
    line_start INTEGER,
    line_end   INTEGER,
    content    TEXT
);

CREATE TABLE IF NOT EXISTS memory_relations (
    from_id TEXT NOT NULL,
    to_id   TEXT NOT NULL,
    PRIMARY KEY (from_id, to_id)
);

CREATE INDEX IF NOT EXISTS idx_mi_type ON memory_index(type);
CREATE INDEX IF NOT EXISTS idx_ms_node ON memory_sections(node_id);
CREATE INDEX IF NOT EXISTS idx_mr_from ON memory_relations(from_id);
CREATE INDEX IF NOT EXISTS idx_mr_to   ON memory_relations(to_id);

CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(
    id, description, body,
    content='memory_index',
    content_rowid='rowid'
);

CREATE TRIGGER IF NOT EXISTS fts_ai AFTER INSERT ON memory_index BEGIN
    INSERT INTO memory_fts(rowid, id, description, body)
    VALUES (new.rowid, new.id, new.description, new.body);
END;
CREATE TRIGGER IF NOT EXISTS fts_ad AFTER DELETE ON memory_index BEGIN
    INSERT INTO memory_fts(memory_fts, rowid, id, description, body)
    VALUES ('delete', old.rowid, old.id, old.description, old.body);
END;
CREATE TRIGGER IF NOT EXISTS fts_au AFTER UPDATE ON memory_index BEGIN
    INSERT INTO memory_fts(memory_fts, rowid, id, description, body)
    VALUES ('delete', old.rowid, old.id, old.description, old.body);
    INSERT INTO memory_fts(rowid, id, description, body)
    VALUES (new.rowid, new.id, new.description, new.body);
END;
"""
