#!/usr/bin/env python3
"""Repository gates that are cheaper than a test (stdlib only; runs first in CI).

Checks:
  1. Placeholders: no unfilled `[TODO]`/`[PLACEHOLDER]`/`[TBD]` in docs/, README or AGENTS.md.
  2. Raw SQL: no `text(` / `execute("SELECT ...")` in Python sources outside migrations and tests.
  3. White-label: the brand names from brand.config.json never appear hard-coded in application
     source (apps/*/src, packages/*/src, services/*/src). They must come from the config.
Usage: python3 scripts/audit_docs.py
"""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Iterator
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "node_modules", ".venv", "dist", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
PLACEHOLDER_RE = re.compile(r"\[(TODO|PLACEHOLDER|TBD)\]")
SOURCE_SUFFIXES = (".py", ".ts", ".tsx", ".css", ".html")


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


def check_hardcoded_brand() -> list[str]:
    config = ROOT / "brand.config.json"
    if not config.exists():
        return ["brand.config.json missing"]
    brand = json.loads(config.read_text(encoding="utf-8"))
    names = {brand.get("brand", ""), brand.get("dataProvider", "")} - {""}
    pattern = re.compile("|".join(re.escape(n) for n in sorted(names, key=len, reverse=True)), re.I)
    problems = []
    for pattern_dir in ("apps/*/src", "packages/*/src", "services/*/src"):
        for base in ROOT.glob(pattern_dir):
            for path in walk(base, SOURCE_SUFFIXES):
                if ".test." in path.name:
                    continue  # tests may assert on the default brand
                for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                    if pattern.search(line):
                        problems.append(f"hard-coded brand at {path.relative_to(ROOT)}:{lineno}")
    return problems


def main() -> int:
    problems = check_placeholders() + check_raw_sql() + check_hardcoded_brand()
    for problem in problems:
        print(f"FAIL: {problem}")
    if problems:
        print(f"{len(problems)} problem(s)")
        return 1
    print("OK: repository audit passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
