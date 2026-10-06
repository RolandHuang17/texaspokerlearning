#!/usr/bin/env python3
"""``data/src/glossary.yaml`` -> ``data/gen/glossary.json`` plus the terminology assertions.

Chinese poker vocabulary has no standard, so this file is the standard, and the assertions are what
make it stick:

* ids unique;
* ``zh`` and ``en`` both non-empty (a term with one language is not bilingual);
* ``first_seen`` names a lesson that exists in the curriculum;
* ``avoid`` entries never appear in the ``zh`` label of any other term, which is how "防守频率" and
  "最低防守频率" stop meaning two different things in two different chapters;
* a term used by a lesson must be registered (enforced by ``tools/check_bilingual.py`` reading this
  artifact).
"""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from _bootstrap import bootstrap_path, fail, ok

bootstrap_path()

from pokergto.artifacts import GEN_DIR, SRC_DIR, write_artifact  # noqa: E402

SCHEMA_VERSION = "1.0.0"


def load(path: Path) -> list[dict[str, object]]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        return list(payload.get("terms", []))
    return list(payload or [])


def check(terms: list[dict[str, object]], *, curriculum_path: Path | None) -> list[str]:
    problems: list[str] = []
    seen: set[str] = set()
    zh_labels: dict[str, str] = {}
    for term in terms:
        term_id = str(term.get("id", ""))
        if not term_id:
            problems.append("a glossary entry has no id")
            continue
        if term_id in seen:
            problems.append(f"duplicate glossary id {term_id!r}")
        seen.add(term_id)
        for key in ("zh", "en"):
            value = term.get(key)
            if not isinstance(value, str) or not value.strip():
                problems.append(f"{term_id}: {key!r} must be a non-empty string")
        first_seen = str(term.get("first_seen", ""))
        if curriculum_path is not None and curriculum_path.exists():
            payload = yaml.safe_load(curriculum_path.read_text(encoding="utf-8")) or {}
            lesson_ids = {
                lesson["id"]
                for chapter in payload.get("chapters", [])
                for lesson in chapter.get("lessons", [])
            }
            if first_seen and first_seen not in lesson_ids:
                problems.append(
                    f"{term_id}: first_seen {first_seen!r} is not a registered lesson id"
                )
        zh = str(term.get("zh", ""))
        if zh and zh in zh_labels and zh_labels[zh] != term_id:
            problems.append(
                f"{term_id}: zh label {zh!r} is already used by {zh_labels[zh]!r}; two terms sharing "
                "one Chinese label is exactly the drift this file exists to prevent"
            )
        zh_labels[zh] = term_id

    all_avoided: dict[str, str] = {}
    for term in terms:
        term_id = str(term.get("id", "?"))
        for rejected in term.get("avoid", []) or []:
            for other in terms:
                if str(other.get("id")) == term_id:
                    continue
                if str(other.get("zh", "")) == str(rejected):
                    problems.append(
                        f"{term_id}: lists {rejected!r} in avoid, but that is "
                        f"{other.get('id')}'s official zh label"
                    )
            if str(rejected) in all_avoided and all_avoided[str(rejected)] != term_id:
                problems.append(
                    f"{term_id}: rejected synonym {rejected!r} is also rejected by "
                    f"{all_avoided[str(rejected)]}; merge the entries"
                )
            all_avoided[str(rejected)] = term_id
    return problems


def to_artifact(terms: list[dict[str, object]]) -> dict[str, object]:
    normalized = []
    for term in terms:
        entry = dict(term)
        entry.setdefault("abbrev", None)
        entry.setdefault("symbol", None)
        entry.setdefault("avoid", [])
        entry.setdefault("note_zh", None)
        entry.setdefault("note_en", None)
        entry.setdefault("related", [])
        entry.setdefault("derivation_ref", None)
        normalized.append(entry)
    return {"schema_version": SCHEMA_VERSION, "terms": normalized}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--src", type=Path, default=SRC_DIR / "glossary.yaml")
    parser.add_argument("--curriculum", type=Path, default=SRC_DIR / "curriculum.yaml")
    parser.add_argument("--out", type=Path, default=GEN_DIR / "glossary.json")
    parser.add_argument("--check", action="store_true", help="assert but do not write")
    args = parser.parse_args(argv)

    if not args.src.exists():
        ok("no glossary.yaml yet: terminology gate passes on an empty tree")
        return 0

    terms = load(args.src)
    problems = check(terms, curriculum_path=args.curriculum)
    if problems:
        for problem in problems:
            fail(problem)
        return 1
    if not args.check:
        write_artifact(args.out, to_artifact(terms), schema="glossary")
    ok(
        f"glossary: {len(terms)} terms validated"
        + (" (check only)" if args.check else f" -> {args.out.name}")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
