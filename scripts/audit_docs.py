#!/usr/bin/env python3
"""Repository gates that are cheaper than a test (stdlib only; runs first in CI).

Checks:
  1. Placeholders: no unfilled `[TODO]`/`[PLACEHOLDER]`/`[TBD]` in docs/, README or AGENTS.md.
  2. Raw SQL: no `text(` / `execute("SELECT ...")` in Python sources outside migrations and tests.
Usage: python3 scripts/audit_docs.py
"""

from __future__ import annotations

import re
import sys
from collections.abc import Iterator
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "node_modules", ".venv", "dist", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
PLACEHOLDER_RE = re.compile(r"\[(TODO|PLACEHOLDER|TBD)\]")


def walk(base: Path, suffixes: tuple[str, ...]) -> Iterator[Path]:
    for path in base.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file() and path.suffix in suffixes:
            yield path


def check_placeholders() -> list[str]:
    problems = []
    files = [*walk(ROOT / "docs", (".md",)), ROOT / "README.md", ROOT / "AGENTS.md"]
    for path in files:
        if not path.exists():
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if PLACEHOLDER_RE.search(line):
                problems.append(f"placeholder at {path.relative_to(ROOT)}:{lineno}")
    return problems


def check_raw_sql() -> list[str]:
    problems = []
    raw = re.compile(r"\btext\(|\.execute\(\s*[\"']\s*(SELECT|INSERT|UPDATE|DELETE)", re.I)
    for path in walk(ROOT, (".py",)):
        if "migrations" in path.parts or "tests" in path.parts or path.name == "audit_docs.py":
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if raw.search(line):
                problems.append(f"raw SQL at {path.relative_to(ROOT)}:{lineno}")
    return problems


def main() -> int:
    problems = check_placeholders() + check_raw_sql()
    for problem in problems:
        print(f"FAIL: {problem}")
    if problems:
        print(f"{len(problems)} problem(s)")
        return 1
    print("OK: repository audit passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
