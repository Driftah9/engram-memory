"""NL-robust recall over an engram index. NEXUS:PORTABLE.

A raw natural-language prompt ("how is my memory handled in the live system") should
NOT be fed to FTS as an implicit-AND query — almost nothing matches every token, so
recall comes back empty. `smart_recall` strips stopwords, OR-matches the remaining
keywords (ranked), and returns the best-matching SECTION per node with exact line
pointers, so an agent can read ~10 lines instead of a whole file.

Pure stdlib; no assumptions about install location.
"""
import re
from typing import List, Dict

_STOP = {
    "the", "and", "for", "are", "but", "not", "you", "your", "with", "this", "that",
    "from", "what", "how", "why", "when", "where", "which", "who", "have", "has", "had",
    "was", "were", "will", "would", "can", "could", "should", "into", "out", "about",
    "did", "does", "doing", "done", "get", "got", "use", "used", "using", "via", "now",
    "live", "system", "based", "thing", "things", "like", "just", "also", "any", "all",
    "let", "lets", "its", "their", "they", "them", "our", "ours", "may", "per",
}


def keywords(query: str, cap: int = 10) -> List[str]:
    """Lowercase content words from a query, stopwords removed, deduped, capped."""
    out: List[str] = []
    for t in re.findall(r"[a-zA-Z0-9_]{3,}", (query or "").lower()):
        if t in _STOP or t in out:
            continue
        out.append(t)
    return out[:cap]


def smart_recall(store, query: str, k: int = 4) -> List[Dict]:
    """Return up to k precise, line-pointed hits for a natural-language query.

    Each hit: {text, source, score}. `source` is "engram:<file>:<start>-<end>".
    `store` is a MemoryStore. Falls back gracefully to [] on any error.
    """
    kws = keywords(query)
    if not kws:
        return []
    try:
        nodes = store.query(" OR ".join(kws), limit=k * 3)
    except Exception:
        return []
    hits: List[Dict] = []
    seen = set()
    try:
        con = store.connect()
    except Exception:
        return []
    try:
        for n in nodes:
            if n["file_name"] in seen:
                continue
            seen.add(n["file_name"])
            secs = con.execute(
                "SELECT heading, line_start, line_end, content "
                "FROM memory_sections WHERE node_id=?",
                (n["id"],),
            ).fetchall()
            best, best_score = None, 0
            for s in secs:
                content = (s["content"] or "").lower()
                score = sum(1 for kw in kws if kw in content)
                if score > best_score:
                    best, best_score = s, score
            if best is not None and best_score > 0:
                txt = " ".join((best["content"] or "").split())[:400]
                hits.append({
                    "text": f"[{n['id']} > {best['heading']}] {txt}",
                    "source": f"engram:{n['file_name']}:{best['line_start']}-{best['line_end']}",
                    "score": 0.9,
                })
            else:
                row = con.execute(
                    "SELECT description FROM memory_index WHERE id=?", (n["id"],)
                ).fetchone()
                desc = (row["description"] if row else "") or ""
                if desc:
                    hits.append({
                        "text": f"[{n['id']}] {desc}",
                        "source": f"engram:{n['file_name']}:{n['line_start']}-{n['line_end']}",
                        "score": 0.8,
                    })
            if len(hits) >= k:
                break
    finally:
        con.close()
    return hits[:k]
