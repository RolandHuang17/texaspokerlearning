#!/usr/bin/env python3
"""Dead-link and dead-asset check for the bilingual docs tree.

``mkdocs build --strict`` already refuses a broken *internal* link, so this tool covers what it
cannot see: relative paths that resolve outside the tree, referenced assets that were never
generated, and artifact ids named in lesson prose that do not exist under ``data/gen``.

The artifact-id check is the one that earns its keep. A lesson that cites
``table.02-03.mdf-vs-sizing2`` by hand has produced a sentence about a table that does not exist --
the exact failure this repository is structured to prevent -- and no other gate would notice.

Usage::

    python tools/check_docs_links.py [--verbose]
"""

from __future__ import annotations

import argparse
import re
import sys

from _bootstrap import REPO_ROOT, bootstrap_path, fail, ok

bootstrap_path()

DOCS = REPO_ROOT / "docs"
GEN = REPO_ROOT / "data" / "gen"

# markdown inline link / image: [label](target) or ![alt](target), optional title ignored
LINK = re.compile(r"(!?)\[[^\]]*\]\(([^)\s]+)")
ARTIFACT_CITED = re.compile(
    r"`(table\.[A-Za-z0-9._-]+|range\.[A-Za-z0-9._-]+|solver\.[A-Za-z0-9._-]+)`"
)
EXTERNAL = re.compile(r"^(https?:|mailto:|#)")


def _targets(text: str) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    for marker, target in LINK.findall(text):
        if EXTERNAL.match(target):
            continue
        path_part = target.split("#", 1)[0]
        if path_part:
            found.append(("image" if marker == "!" else "link", path_part))
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)

    files = sorted(DOCS.rglob("*.md")) if DOCS.exists() else []
    known = {path.stem for path in GEN.rglob("*.json")} if GEN.exists() else set()
    problems: list[str] = []
    links = artifacts = 0

    for file in files:
        relative = file.relative_to(REPO_ROOT).as_posix()
        text = file.read_text(encoding="utf-8")
        for kind, target in _targets(text):
            links += 1
            if target.startswith("../") or target.startswith("./"):
                resolved = (file.parent / target).resolve()
                if not resolved.exists():
                    problems.append(f"{relative}: {kind} target missing -> {target}")
            elif target.startswith("docs/"):
                if not (REPO_ROOT / target).exists():
                    problems.append(f"{relative}: {kind} target missing -> {target}")
        for artifact in ARTIFACT_CITED.findall(text):
            artifacts += 1
            if artifact not in known:
                problems.append(
                    f"{relative}: cites `{artifact}` which is not in data/gen "
                    "(run `python tools/gen_all.py`, or fix the id)"
                )

    for problem in problems:
        fail(problem)
    if problems:
        return 1
    ok(f"docs links: {links} link(s) and {artifacts} artifact reference(s) resolve")
    if args.verbose:
        print(f"     files scanned: {len(files)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
