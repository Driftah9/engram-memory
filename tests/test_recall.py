"""Tests for inline [[wiki-link]] relations and NL-robust smart_recall."""

import tempfile
from pathlib import Path

from engram import MemoryStore, smart_recall


def test_inline_wikilinks_become_relations():
    """A [[node-name]] in the body should create a relation edge."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "a.md").write_text(
            "---\nname: node-a\ntype: reference\ndescription: A\n---\n\n"
            "Body of A that links to [[node-b]] inline.\n"
        )
        (tmp / "b.md").write_text(
            "---\nname: node-b\ntype: reference\ndescription: B\n---\n\nBody of B.\n"
        )
        store = MemoryStore(str(tmp))
        store.build()
        rels = store.relations_from("node-a")
        assert "node-b" in rels


def test_see_also_and_inline_merge_without_duplicates():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "a.md").write_text(
            "---\nname: node-a\ntype: reference\ndescription: A\n"
            "metadata:\n  relations:\n    see_also:\n      - node-b\n---\n\n"
            "Links to [[node-b]] again and to [[node-c]].\n"
        )
        store = MemoryStore(str(tmp))
        store.build()
        rels = store.relations_from("node-a")
        assert rels.count("node-b") == 1   # not duplicated
        assert "node-c" in rels


def test_no_self_links():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "a.md").write_text(
            "---\nname: node-a\ntype: reference\ndescription: A\n---\n\n"
            "A note that mentions [[node-a]] itself.\n"
        )
        store = MemoryStore(str(tmp))
        store.build()
        assert "node-a" not in store.relations_from("node-a")


def test_smart_recall_natural_language(memory_store):
    """A full sentence should still retrieve a hit (where AND-FTS might not)."""
    memory_store.build()
    hits = memory_store.smart_recall("what are the communication style preferences")
    assert hits
    assert any("feedback_communication" in h["source"] for h in hits)
    assert all({"text", "source", "score"} <= set(h) for h in hits)


def test_smart_recall_module_level(memory_store):
    memory_store.build()
    hits = smart_recall(memory_store, "AI research project status")
    assert hits
    assert hits[0]["source"].startswith("engram:")


def test_smart_recall_empty_on_stopwords_only(memory_store):
    memory_store.build()
    assert smart_recall(memory_store, "the and for with") == []
