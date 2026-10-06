#!/usr/bin/env python3
"""``data/src/curriculum.yaml`` -> ``data/gen/index.en.json`` / ``index.zh.json`` + nav stubs.

The generated index is what the docs nav, the landing-page curriculum map, and the trainer's track
picker are built from. Nothing of the three is allowed to hold a hand-written lesson list, which is
why an authored-but-unregistered lesson file shows up as a build error here instead of as a page
nobody can reach.

Also emits ``data/gen/nav.yml``, the whole ``mkdocs.yml`` nav, so the site's table of contents and the
registry can never disagree.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

from _bootstrap import REPO_ROOT, bootstrap_path, fail, ok

bootstrap_path()

from pokergto.artifacts import GEN_DIR, SRC_DIR, write_artifact  # noqa: E402
from pokergto.registry import CurriculumRegistry, load_registry  # noqa: E402

MAX_UNAUTHORED_LISTING = 20


def build_index(
    registry: CurriculumRegistry, locale: str, *, extra_counts: dict[str, int]
) -> dict[str, Any]:
    chapters = []
    for chapter in registry.chapters:
        lessons = []
        for lesson in chapter.lessons:
            status = lesson.status_zh if locale == "zh" else lesson.status_en
            lessons.append(
                {
                    "id": lesson.id,
                    "slug": lesson.slug,
                    "title": dict(lesson.title),
                    "status": status,
                    "path": lesson.path(locale),
                    "prereq": list(lesson.prereq),
                    "scenario": list(lesson.scenario),
                    "hand_ids": list(lesson.hand_ids),
                    "quiz_ids": list(lesson.quiz_ids),
                    "table_ids": list(lesson.table_ids),
                    "spot_ids": list(lesson.spot_ids),
                    "unverified_count": 0,
                }
            )
        chapters.append(
            {
                "id": chapter.id,
                "slug": chapter.slug,
                "title": dict(chapter.title),
                "summary": dict(chapter.summary),
                "scenario": [tag for lesson in chapter.lessons for tag in lesson.scenario],
                "lessons": lessons,
            }
        )
    totals = dict(registry.totals)
    totals.update(extra_counts)
    return {
        "schema_version": registry.schema_version,
        "engine_version": registry.engine_version,
        "locale": locale,
        "totals": totals,
        "chapters": chapters,
    }


def build_nav(registry: CurriculumRegistry, locale: str, docs_root: Path) -> list[dict[str, Any]]:
    """The lesson tree for one locale, carrying only lessons that have a file.

    Two decisions live here. A nav entry pointing at a missing file is a ``--strict`` error, so an
    unauthored lesson must stay out of the fragment until its file lands -- the filter reads the same
    docs tree ``check_bilingual.py`` reads. And a chapter with no authored lessons gets no section at
    all, because mkdocs warns about an empty one.
    """
    nav: list[dict[str, Any]] = [{"Home": f"{locale}/index.md"}]
    for chapter in registry.chapters:
        pages = [
            {lesson.title[locale]: f"{locale}/{chapter.slug}/{lesson.slug}.md"}
            for lesson in chapter.lessons
            if (docs_root / locale / chapter.slug / f"{lesson.slug}.md").exists()
        ]
        if pages:
            nav.append({f"{chapter.id} {chapter.title[locale]}": pages})
    return nav


#: Contributor-facing engineering docs, single-language by design (adr/0005), so they sit outside
#: both locale trees. They live here rather than in ``mkdocs.yml`` because the whole nav is generated
#: from one fragment: mkdocs' ``!include`` constructor only resolves as a mapping value, not as a
#: sequence item, so a per-locale include cannot be composed in the config file.
DEVELOPMENT_PAGES = (
    "development/local-dev.md",
    "development/bilingual-style.md",
    "development/data-provenance.md",
    "development/solver-proof-policy.md",
    "development/adr.md",
)


def build_site_nav(registry: CurriculumRegistry, docs_root: Path) -> list[dict[str, Any]]:
    """The complete ``mkdocs.yml`` nav: two locale trees plus the development section."""
    return [
        {"English": build_nav(registry, "en", docs_root)},
        {"中文": build_nav(registry, "zh", docs_root)},
        {"Development": list(DEVELOPMENT_PAGES)},
    ]


def report_unauthored(registry: CurriculumRegistry, docs_root: Path) -> list[str]:
    lines: list[str] = []
    orphans = registry.find_orphans(docs_root) if docs_root.exists() else {}
    for key, values in sorted(orphans.items()):
        if values:
            shown = ", ".join(values[:MAX_UNAUTHORED_LISTING])
            more = (
                f" (+{len(values) - MAX_UNAUTHORED_LISTING} more)"
                if len(values) > MAX_UNAUTHORED_LISTING
                else ""
            )
            lines.append(f"{key}: {shown}{more}")
    for lesson_id, prereq in registry.unresolved_prerequisites():
        lines.append(
            f"dangling prereq: lesson {lesson_id} requires {prereq}, which is not registered"
        )
    for clash in registry.duplicate_paths():
        lines.append(f"path clash: {clash}")
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--src", type=Path, default=SRC_DIR / "curriculum.yaml")
    parser.add_argument("--out", type=Path, default=GEN_DIR)
    parser.add_argument("--docs", type=Path, default=REPO_ROOT / "docs")
    parser.add_argument(
        "--allow-unauthored",
        action="store_true",
        help="do not fail when ready lessons lack files (used by the M0/M1 bootstrap)",
    )
    args = parser.parse_args(argv)

    if not args.src.exists():
        ok("no curriculum.yaml yet: index gate passes on an empty spine")
        return 0

    registry = load_registry(args.src)
    counts = _counts_from_gen(args.out)
    problems: list[str] = []
    if not args.allow_unauthored:
        problems = report_unauthored(registry, args.docs)
    if problems:
        for problem in problems:
            fail(problem)
        print(
            "\nA lesson marked `ready` needs its file in that language, and no file may exist without\n"
            "being registered. Mark it `draft` if it is not written yet.",
            file=sys.stderr,
        )
        return 1

    for locale in ("en", "zh"):
        write_artifact(
            args.out / f"index.{locale}.json",
            build_index(registry, locale, extra_counts=counts),
            schema="index",
        )
    nav_path = args.out / "nav.yml"
    nav_path.write_text(
        yaml.safe_dump(
            build_site_nav(registry, args.docs), allow_unicode=True, sort_keys=False, width=100
        ),
        encoding="utf-8",
        newline="\n",
    )
    ok(
        f"curriculum index: {registry.totals['lessons']} lessons, "
        f"{registry.totals['lessons_ready']} ready in both languages"
    )
    return 0


def _counts_from_gen(gen_dir: Path) -> dict[str, int]:
    """Counts of authored artifacts, so the landing page totals are generated rather than typed."""

    def count(directory: str, suffix: str = ".json") -> int:
        target = gen_dir / directory
        return len(list(target.glob(f"*{suffix}"))) if target.exists() else 0

    return {
        "spots": count("spots"),
        "hands": count("hands"),
        "quizzes": count("quizzes"),
        "tables": count("tables"),
    }


if __name__ == "__main__":
    raise SystemExit(main())
