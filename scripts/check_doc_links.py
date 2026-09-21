#!/usr/bin/env python3
"""Fail if any relative Markdown link in the repo points at a missing file.

Stdlib only, so CI can run it before installing anything. External links (http/https/mailto)
and pure anchors are skipped; `file.md#anchor` checks only the file part.
Usage: python3 scripts/check_doc_links.py [root]
"""

from __future__ import annotations

import re
import sys
from collections.abc import Iterator
from pathlib import Path

LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
SKIP_DIRS = {".git", "node_modules", ".venv", "dist", ".pytest_cache"}
SKIP_PREFIXES = ("http://", "https://", "mailto:", "#", "tel:")


def iter_markdown(root: Path) -> Iterator[Path]:
    for path in root.rglob("*.md"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        yield path


def main(root: Path) -> int:
    broken: list[tuple[Path, str]] = []
    checked = 0
    for md in iter_markdown(root):
        text = md.read_text(encoding="utf-8", errors="replace")
        for match in LINK_RE.finditer(text):
            target = match.group(1)
            if target.startswith(SKIP_PREFIXES) or "://" in target:
                continue
            file_part = target.split("#", 1)[0]
            if not file_part:
                continue
            candidate = (md.parent / file_part).resolve()
            checked += 1
            if not candidate.exists():
                broken.append((md.relative_to(root), target))
    if broken:
        for md, target in broken:
            print(f"BROKEN: {md} -> {target}")
        print(f"FAIL: {len(broken)} broken links ({checked} checked)")
        return 1
    print(f"OK: 0 broken links ({checked} checked)")
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()))
