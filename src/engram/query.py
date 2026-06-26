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
    """Find sections containing all tokens from a term.

    Normalizes hyphens to spaces before tokenizing, so "multi-user" and
    "multi user" both find sections containing both words regardless of
    how they're joined in the source.

    Args:
        conn: SQLite connection with memory_sections and memory_index tables
        term: Search term — split on whitespace, each token must match
        exclude_ids: Node IDs to exclude (default: ['MEMORY', 'SCHEMA'])
        limit: Maximum number of results to return

    Returns:
        List of dicts with keys: id, type, file_path, file_name, heading, line_start, line_end

    Examples:
        >>> sections = section_query(conn, "SSDI")
        >>> sections = section_query(conn, "multi-user")        # finds "multi user" too
        >>> sections = section_query(conn, "priority partners", exclude_ids=["MEMORY"])
    """
    exclude = exclude_ids or ["MEMORY", "SCHEMA"]
    placeholders = ",".join("?" * len(exclude))

    tokens = term.replace("-", " ").split()
    if not tokens:
        return []

    token_clauses = " AND ".join(
        "(ms.content LIKE ? OR ms.heading LIKE ?)" for _ in tokens
    )
    token_params = [p for tok in tokens for p in (f"%{tok}%", f"%{tok}%")]

    rows = conn.execute(
        f"""
        SELECT mi.id, mi.type, mi.file_path, mi.file_name,
               ms.heading, ms.line_start, ms.line_end
        FROM memory_sections ms
        JOIN memory_index mi ON ms.node_id = mi.id
        WHERE ms.node_id NOT IN ({placeholders})
          AND {token_clauses}
        ORDER BY mi.type, mi.id
        LIMIT ?
        """,
        (*exclude, *token_params, limit),
    ).fetchall()

    return [dict(r) for r in rows]
