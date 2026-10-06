#!/usr/bin/env python3
"""Extract the CHANGELOG ``Unreleased`` section into release notes, and refuse to release on empty ones.

A version tag without notes wastes the release: nobody reading the repository later can tell what
changed, and the SemVer promise -- which of the four public surfaces moved -- becomes folklore. This
writes ``.release-notes.md`` for the release workflow and fails the build when there is nothing to
say, which is the cheapest possible guard on a tag that means nothing.

``.release-notes.md`` is a build artifact and is gitignored.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CHANGELOG = REPO_ROOT / "CHANGELOG.md"
OUTPUT = REPO_ROOT / ".release-notes.md"

SECTION = re.compile(r"^## \[(?P<version>[^\]]+)\]\s*$", re.MULTILINE)
BULLET = re.compile(r"^[-*]\s+\S", re.MULTILINE)


def extract_unreleased(text: str) -> str:
    """The body of ``## [Unreleased]``, or ``""`` when it holds no bullets.

    A section containing only sub-headings is empty: an author who added ``### Added`` and no entry
    has not described a change, and releasing on it is the failure this gate exists to catch.
    """
    matches = list(SECTION.finditer(text))
    for index, match in enumerate(matches):
        if match.group("version").strip().lower() != "unreleased":
            continue
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.end() : end].strip()
        return body if BULLET.search(body) else ""
    return ""


def main(argv: list[str] | None = None) -> int:
    if not CHANGELOG.exists():
        print("FAIL CHANGELOG.md is missing", file=sys.stderr)
        return 1
    notes = extract_unreleased(CHANGELOG.read_text(encoding="utf-8"))
    if not notes:
        print(
            "FAIL CHANGELOG.md has no Unreleased bullet points to release.\n"
            "     Describe what changed in the public surfaces first: engine signatures,\n"
            "     data/schema contracts, lesson ids, CLI report shape. See CONTRIBUTING.md.",
            file=sys.stderr,
        )
        return 1
    OUTPUT.write_text(notes + "\n", encoding="utf-8", newline="\n")
    print(f"ok   release notes: {len(notes.splitlines())} line(s) -> {OUTPUT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
