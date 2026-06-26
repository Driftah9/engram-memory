"""Query helpers for engram-memory."""

import sqlite3
from typing import List, Dict, Optional

from .sanitizer import sanitize_fts


def fts_query(
    conn: sqlite3.Connection,
    term: str,
    type_filter: Optional[str] = None,
    limit: int = 20,
) -> List[Dict]:
    """Safe full-text search with optional type filtering.

    Args:
        conn: SQLite connection with memory_index and memory_fts tables
        term: Raw search term (will be sanitized)
        type_filter: Optional type to filter by ('user', 'feedback', 'project', 'reference')
        limit: Maximum number of results to return

    Returns:
        List of dicts with keys: id, type, file_name, line_start, line_end

    Examples:
        >>> results = fts_query(conn, "SSDI")
        >>> results = fts_query(conn, "Mattermost", type_filter="feedback", limit=10)
    """
    safe = sanitize_fts(term)
    if not safe:
        return []

    if type_filter:
        rows = conn.execute(
            """
            SELECT mi.id, mi.type, mi.file_name, mi.line_start, mi.line_end
            FROM memory_fts f JOIN memory_index mi ON mi.id=f.id AND mi.type=?
            WHERE memory_fts MATCH ? ORDER BY rank LIMIT ?
            """,
            (type_filter, safe, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT mi.id, mi.type, mi.file_name, mi.line_start, mi.line_end
            FROM memory_fts f JOIN memory_index mi ON mi.id=f.id
            WHERE memory_fts MATCH ? ORDER BY rank LIMIT ?
            """,
            (safe, limit),
        ).fetchall()

    return [dict(r) for r in rows]


def section_query(
    conn: sqlite3.Connection,
    term: str,
    exclude_ids: Optional[List[str]] = None,
    limit: int = 20,
) -> List[Dict]:
    """Find sections whose content or heading contains a term.

    Excludes index/schema nodes (MEMORY, SCHEMA) by default so results are
    always real content nodes, not metadata.

    Args:
        conn: SQLite connection with memory_sections and memory_index tables
        term: Search term (substring match, case-insensitive)
        exclude_ids: Node IDs to exclude (default: ['MEMORY', 'SCHEMA'])
        limit: Maximum number of results to return

    Returns:
        List of dicts with keys: id, type, file_path, file_name, heading, line_start, line_end

    Examples:
        >>> sections = section_query(conn, "SSDI")
        >>> sections = section_query(conn, "priority partners", exclude_ids=["MEMORY"])
    """
    exclude = exclude_ids or ["MEMORY", "SCHEMA"]
    placeholders = ",".join("?" * len(exclude))
    like = f"%{term}%"

    rows = conn.execute(
        f"""
        SELECT mi.id, mi.type, mi.file_path, mi.file_name,
               ms.heading, ms.line_start, ms.line_end
        FROM memory_sections ms
        JOIN memory_index mi ON ms.node_id = mi.id
        WHERE ms.node_id NOT IN ({placeholders})
          AND (ms.content LIKE ? OR ms.heading LIKE ?)
        ORDER BY mi.type, mi.id
        LIMIT ?
        """,
        (*exclude, like, like, limit),
    ).fetchall()

    return [dict(r) for r in rows]
