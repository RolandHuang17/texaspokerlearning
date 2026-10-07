#!/usr/bin/env python3
"""Validate every generated artifact against ``data/schema/*.json``.

Schemas that nothing validates against are documentation, not contracts. This tool is the contract
enforcement point, and it resolves cross-file ``$ref`` through a local registry so the build never
touches the network (see SECURITY.md).

Usage::

    python tools/check_artifact_schema.py            # everything in data/gen
    python tools/check_artifact_schema.py --file data/gen/tables/x.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import REPO_ROOT, bootstrap_path, fail, ok

bootstrap_path()

from pokergto.artifacts import GEN_DIR, validate_artifact  # noqa: E402

#: Which schema governs which directory. Kept explicit rather than inferred from filenames, because a
#: file named "spot.json" landing in ``ranges/`` is exactly the mistake this check exists to catch.
DIRECTORY_SCHEMA = {
    "tables": "table",
    "ranges": "range_chart",
    "spots": "spot",
    "quizzes": "quiz",
    "hands": "hand_example",
    "solver": "solver_run",
    "matrices": "range_chart",
    "preflop": "preflop_matrix",
    "viz": None,
}

SCHEMA_BY_ROOT = {
    "glossary.json": "glossary",
    "manifest.json": "manifest",
    "board_taxonomy.json": "board_taxonomy",
    "licensing_manifest.json": "licensing_manifest",
    "index.en.json": "index",
    "index.zh.json": "index",
    "drills.json": "drill_session",
}


def schema_for(path: Path) -> str | None:
    relative = path.relative_to(GEN_DIR)
    if relative.as_posix() in SCHEMA_BY_ROOT:
        return SCHEMA_BY_ROOT[relative.as_posix()]
    parts = relative.parts
    if len(parts) < 2:
        return None
    return DIRECTORY_SCHEMA.get(parts[0])


def check(files: list[Path]) -> list[str]:
    problems: list[str] = []
    unvalidated: list[str] = []
    for file in files:
        if file.suffix != ".json":
            continue
        try:
            payload = json.loads(file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            problems.append(f"{file.relative_to(REPO_ROOT)}: invalid JSON ({error})")
            continue
        schema = schema_for(file)
        if schema is None:
            unvalidated.append(file.relative_to(REPO_ROOT).as_posix())
            continue
        try:
            validate_artifact(payload if isinstance(payload, dict) else payload[0], schema)
        except Exception as error:
            problems.append(f"{file.relative_to(REPO_ROOT)}: {error}")
    if unvalidated:
        problems.append(
            "artifacts with no schema mapping (add one to DIRECTORY_SCHEMA or move the file): "
            + ", ".join(sorted(unvalidated))
        )
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--file", type=Path, action="append", dest="files")
    args = parser.parse_args(argv)

    files = args.files or (sorted(GEN_DIR.rglob("*.json")) if GEN_DIR.exists() else [])
    if not files:
        ok("no generated artifacts yet (M0 state): schema check passes on an empty tree")
        return 0

    problems = check([REPO_ROOT / file if not file.is_absolute() else file for file in files])
    for problem in problems:
        fail(problem)
    if problems:
        return 1
    ok(f"artifact schema: {len(files)} files validate against data/schema")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
