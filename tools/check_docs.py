#!/usr/bin/env python3
"""Offline check of bilingual Markdown and local links; never modifies docs."""
from __future__ import annotations

import re
from pathlib import Path
import sys
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+['\"][^'\"]+['\"])?\)")
FENCE = re.compile(r"(?ms)^(\x60{3,}|~{3,}).*?^\1[ \t]*$")
ZH = re.compile(r"[\u4e00-\u9fff]")
EN_HEADING = re.compile(r"(?m)^## (?:English|EN\b)")
ZH_HEADING = re.compile(r"(?m)^## (?:中文|Chinese)")
DOCS = [
    ROOT / "README.md", ROOT / "AGENTS.md", ROOT / "CLAUDE.md",
    ROOT / "docs/README.md", ROOT / "docs/architecture.md",
    *(ROOT / "docs/guides").glob("*.md"),
    *(ROOT / "docs/routine").glob("*.md"),
    ROOT / "skills/model-router/SKILL.md",
    *(ROOT / "skills/model-router/references").glob("*.md"),
    ROOT / "release/notes.md", ROOT / "CHANGELOG.md",
    ROOT / "CONTRIBUTING.md", ROOT / "SECURITY.md",
]


def check(path: Path) -> list[str]:
    if not path.is_file():
        return [f"missing: {path.relative_to(ROOT)}"]
    failures = []
    content = path.read_text(encoding="utf-8")
    if not (ZH.search(content) and EN_HEADING.search(content) and ZH_HEADING.search(content)):
        failures.append(f"missing Chinese/English sections: {path.relative_to(ROOT)}")
    body = FENCE.sub("", content)
    for href in LINK.findall(body):
        if href.startswith(("#", "//")) or re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", href):
            continue
        relative = unquote(href.split("#", 1)[0].split("?", 1)[0])
        if not relative:
            continue
        resolved = (path.parent / relative).resolve()
        if not resolved.is_relative_to(ROOT.resolve()) or not resolved.exists():
            failures.append(f"broken local link: {path.relative_to(ROOT)} -> {href}")
    return failures


def main() -> int:
    errors = [error for doc in dict.fromkeys(DOCS) for error in check(doc)]
    routine = list((ROOT / "docs/routine").glob("20??-??-??-*.md"))
    if len(routine) < 18:
        errors.append(f"unexpected historical log count: {len(routine)}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"Documentation OK: {len(set(DOCS))} bilingual files; {len(routine)} historical logs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
