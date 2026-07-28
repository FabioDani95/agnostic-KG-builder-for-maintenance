#!/usr/bin/env python3
"""Fail when a relative Markdown link points to a missing local path."""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
EXCLUDED_DIRS = {".claude", ".codex", ".git", ".venv", "node_modules"}


def markdown_files() -> list[Path]:
    return sorted(
        path
        for path in REPO_ROOT.rglob("*.md")
        if not any(part in EXCLUDED_DIRS for part in path.relative_to(REPO_ROOT).parts)
    )


def missing_links(path: Path) -> list[str]:
    failures: list[str] = []
    text = path.read_text(encoding="utf-8")
    for match in MARKDOWN_LINK.finditer(text):
        target = match.group(1).split("#", 1)[0].strip()
        if not target or "://" in target or target.startswith("mailto:"):
            continue
        if not (path.parent / target).resolve().exists():
            failures.append(f"{path.relative_to(REPO_ROOT)}: missing {target}")
    return failures


def main() -> int:
    files = markdown_files()
    failures = [failure for path in files for failure in missing_links(path)]
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print(f"Checked {len(files)} Markdown files: all local link targets exist.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
