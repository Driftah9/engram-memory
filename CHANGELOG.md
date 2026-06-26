# Changelog

All notable changes to engram-memory will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — 2026-06-26

### Added

- Initial release of engram-memory
- MemoryStore class for managing persistent knowledge
- SQLite backend with FTS5 full-text search
- Manifest JSON fallback for DB-down recovery
- Section-level line pointers for fine-grained retrieval
- Relation graph via `see_also` links
- FTS5 input sanitizer for safe queries
- Complete test suite (9 tests, 100% pass)
- Full API documentation
- Architecture documentation
- Contributing guidelines

### Features

- Markdown files as source of truth
- Four knowledge types: user, feedback, project, reference
- YAML frontmatter for metadata
- H2 sections for content organization
- Query by keyword, type, or section
- Follow relation chains
- Manifest-based queries when DB is unavailable

---

## Unreleased

### Planned

- Async query API
- Optional vector similarity (sqlite-vec integration)
- Multi-agent knowledge sharing
- Web UI for browsing
- Automated knowledge consolidation
- Per-agent knowledge isolation
