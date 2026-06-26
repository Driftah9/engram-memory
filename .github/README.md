# GitHub Configuration

This directory contains GitHub-specific configuration for engram-memory.

## Workflows

- **tests.yml** — Runs pytest on push/PR, checks code style with black/ruff, uploads coverage

## Templates

- **pull_request_template.md** — Template for pull requests
- **ISSUE_TEMPLATE/bug_report.md** — Template for bug reports
- **ISSUE_TEMPLATE/feature_request.md** — Template for feature requests

## Ownership

**CODEOWNERS** defines code review requirements. All changes require review from @Driftah9.

## CI/CD

Tests run automatically on:
- Push to `main` or `develop`
- Pull requests to `main` or `develop`

Status badge to add to README:
```markdown
[![Tests](https://github.com/Driftah9/engram-memory/actions/workflows/tests.yml/badge.svg)](https://github.com/Driftah9/engram-memory/actions)
```
