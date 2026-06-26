"""Tests for MemoryStore.build() and basic functionality."""

import json
from pathlib import Path

import pytest

from engram import MemoryStore


def test_build_creates_database(memory_store):
    """Test that build() creates SQLite database."""
    stats = memory_store.build()

    assert memory_store.db_path.exists()
    assert stats["files"] == 3
    assert stats["build_ms"] > 0
    assert stats["db_kb"] > 0


def test_build_creates_manifest(memory_store):
    """Test that build() creates manifest.json."""
    memory_store.build()

    assert memory_store.manifest_path.exists()

    manifest = json.loads(memory_store.manifest_path.read_text())
    assert "user-profile" in manifest
    assert "feedback-communication" in manifest
    assert "project-ai" in manifest


def test_manifest_structure(memory_store):
    """Test manifest JSON structure."""
    memory_store.build()

    manifest = json.loads(memory_store.manifest_path.read_text())
    node = manifest["user-profile"]

    assert node["type"] == "user"
    assert node["description"] == "User identity and constraints"
    assert "file" in node
    assert "file_path" in node
    assert "sections" in node


def test_query_basic(memory_store):
    """Test basic full-text search."""
    memory_store.build()

    results = memory_store.query("Owner")
    assert len(results) > 0
    assert any(r["id"] == "user-profile" for r in results)


def test_query_type_filter(memory_store):
    """Test query with type filter."""
    memory_store.build()

    feedback = memory_store.query("communication", type_filter="feedback")
    assert len(feedback) > 0
    assert all(r["type"] == "feedback" for r in feedback)


def test_section_query(memory_store):
    """Test section-level search."""
    memory_store.build()

    sections = memory_store.section_query("Status")
    assert len(sections) > 0
    assert any(s["heading"] == "Status" for s in sections)


def test_relations(memory_store):
    """Test relation tracking."""
    memory_store.build()

    related = memory_store.relations_from("project-ai")
    assert "feedback-communication" in related


def test_read_lines(memory_store, temp_knowledge_dir):
    """Test reading specific lines from file."""
    memory_store.build()

    # Use section_query to get full node info including file_path
    sections = memory_store.section_query("Owner")
    if sections:
        section = sections[0]
        content = MemoryStore.read_lines(
            section["file_path"], section["line_start"], section["line_end"]
        )
        # Content should include the file body
        assert len(content) > 0


def test_manifest_query(memory_store):
    """Test manifest-based fallback query."""
    memory_store.build()

    results = memory_store.manifest_query("project")
    assert len(results) > 0
    assert any(r["id"] == "project-ai" for r in results)
