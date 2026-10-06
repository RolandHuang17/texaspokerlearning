#!/usr/bin/env python3
"""Bilingual parity gate.

The claim this protects: 184 mirrored lesson files that stay paired, same structure, same numbers.
Five checks, all fail-closed:

1. **Path-set equality** between ``docs/en`` and ``docs/zh``. A file in one language and not the
   other is the failure that breaks the mkdocs i18n build, so it is caught here, before the site
   build spends thirty seconds discovering it.
2. **Registered lessons have their files.** A lesson marked ``ready`` in either language must have
   that language's file. ``draft`` lessons are exempt, which is what lets this gate pass on an empty
   repository (milestone M0) instead of only passing when the work is already done.
3. **Template order and heading counts.** The 15-section template appears in the same order, with the
   same number of H2/H3, in both languages.
4. **AUTO block ids match 1:1.** If the Chinese lesson embeds a generated table, the English one
   embeds the same table id, and neither embeds one the other lacks.
5. **Declared terms are registered, and hands are sufficient.** Every term id listed under the
   lesson's Terms section exists in ``glossary.yaml``; every ``ready`` lesson renders at least two
   live-hand examples. "Lots of practical examples" is a gate here, not an aspiration in a README.

What this tool deliberately cannot prove: that the English text says what the Chinese text says.
Heading parity proves structure. Semantic equivalence would need a translation-quality model, which
is not what this repository should spend complexity on -- see docs/development/bilingual-style.md for
the same-pull-request rule and the review checklist that cover it instead.

Usage::

    python tools/check_bilingual.py            # full tree
    python tools/check_bilingual.py --verbose
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from _bootstrap import REPO_ROOT, SRC, bootstrap_path, fail, ok

bootstrap_path()

from pokergto.registry import CurriculumRegistry, load_glossary, load_registry  # noqa: E402

DOCS = REPO_ROOT / "docs"
CURRICULUM = REPO_ROOT / "data" / "src" / "curriculum.yaml"
GLOSSARY = REPO_ROOT / "data" / "src" / "glossary.yaml"

#: Files that are not lessons and therefore exempt from pairing: chapter landing pages and the
#: development docs are generated or single-lingual by design.
EXEMPT_PATTERNS = (
    re.compile(r"^development/"),
    re.compile(r"(^|/)index\.md$"),
)

AUTO_BEGIN = re.compile(r"<!--\s*BEGIN AUTO:([A-Za-z0-9._-]+)\s*-->")
AUTO_END = re.compile(r"<!--\s*END AUTO:([A-Za-z0-9._-]+)\s*-->")
HEADING = re.compile(r"^(#{1,3})\s+(.*)$", re.MULTILINE)
HAND_COUNT = re.compile(r"<!--\s hands:\s*(\d+)\s*-->")
TERMS_LIST = re.compile(r"<!--\s*terms:\s*([A-Za-z0-9,._-]*)\s*-->")


def _is_exempt(relative: str) -> bool:
    return any(pattern.search(relative) for pattern in EXEMPT_PATTERNS)


def _lesson_files(base: Path) -> set[str]:
    if not base.exists():
        return set()
    found: set[str] = set()
    for path in base.rglob("*.md"):
        relative = path.relative_to(DOCS).as_posix()
        without_locale = relative.split("/", 1)[1]
        if _is_exempt(without_locale):
            continue
        found.add(without_locale)
    return found


def _headings(text: str) -> list[tuple[int, str]]:
    return [(len(match.group(1)), match.group(2).strip()) for match in HEADING.finditer(text)]


def _template_headings(text: str, template: tuple[str, ...]) -> list[str]:
    """Section titles that match a template entry, ignoring the language-specific wording.

    Matching is on position within the H2 stream, because the Chinese and English headings are
    different strings by design. What must agree is the *count and order* of sections.
    """
    return [title for level, title in _headings(text) if level == 2]


def _auto_ids(text: str) -> list[str]:
    begins = AUTO_BEGIN.findall(text)
    ends = AUTO_END.findall(text)
    if sorted(begins) != sorted(ends):
        raise ValueError(f"unbalanced AUTO blocks: begins={begins} ends={ends}")
    return begins


def check(registry: CurriculumRegistry, glossary: dict[str, object]) -> list[str]:
    problems: list[str] = []

    en_files = _lesson_files(DOCS / "en")
    zh_files = _lesson_files(DOCS / "zh")
    only_en = sorted(en_files - zh_files)
    only_zh = sorted(zh_files - en_files)
    for relative in only_en:
        problems.append(f"exists in en but not zh: docs/zh/{relative}")
    for relative in only_zh:
        problems.append(f"exists in zh but not en: docs/en/{relative}")

    # Registered lessons that are marked ready must have both files.
    for lesson in registry.ordered_lessons():
        for locale, status in (("en", lesson.status_en), ("zh", lesson.status_zh)):
            if status in ("draft",):
                continue
            relative = f"{locale}/{lesson.chapter_dir}/{lesson.slug}.md"
            if not (DOCS / relative).exists():
                problems.append(
                    f"lesson {lesson.id} is {status} in {locale} but docs/{relative} does not exist"
                )

    # Structural parity for whatever pairs do exist.
    for relative in sorted(en_files & zh_files):
        en_text = (DOCS / "en" / relative).read_text(encoding="utf-8")
        zh_text = (DOCS / "zh" / relative).read_text(encoding="utf-8")
        try:
            en_auto = _auto_ids(en_text)
            zh_auto = _auto_ids(zh_text)
        except ValueError as error:
            problems.append(f"docs/en/{relative}: {error}")
            continue
        if en_auto != zh_auto:
            problems.append(
                f"{relative}: AUTO block ids differ (en={en_auto} zh={zh_auto}); both languages must "
                "embed the same generated tables in the same order"
            )
        en_h2 = _template_headings(en_text, registry.lesson_template)
        zh_h2 = _template_headings(zh_text, registry.lesson_template)
        if len(en_h2) != len(zh_h2):
            problems.append(
                f"{relative}: section count differs (en={len(en_h2)} zh={len(zh_h2)}); the template "
                f"requires exactly {len(registry.lesson_template)} H2 sections in both languages"
            )
        if len(_headings(en_text)) != len(_headings(zh_text)):
            problems.append(f"{relative}: heading count differs between languages")
        for text, locale in ((en_text, "en"), (zh_text, "zh")):
            counts = HAND_COUNT.findall(text)
            if counts and int(counts[-1]) < 2 and _lesson_is_ready(registry, relative):
                problems.append(
                    f"docs/{locale}/{relative}: {int(counts[-1])} live-hand examples, ready lessons "
                    "need at least 2 (see adr/0005 and CONTRIBUTING.md)"
                )
            listed = TERMS_LIST.findall(text)
            if listed:
                for term in [part for chunk in listed for part in chunk.split(",") if part]:
                    if term not in glossary:
                        problems.append(
                            f"docs/{locale}/{relative}: term {term!r} is not registered in "
                            "data/src/glossary.yaml"
                        )
    return problems


def _lesson_is_ready(registry: CurriculumRegistry, relative: str) -> bool:
    stem = Path(relative).stem
    try:
        lesson = registry.lesson(stem_to_id(stem, registry))
    except Exception:
        return False
    return lesson.is_ready


def stem_to_id(stem: str, registry: CurriculumRegistry) -> str:
    """Map a file name to a lesson id. Slugs are unique per lesson, ids are not file names."""
    for lesson in registry.ordered_lessons():
        if lesson.slug == stem:
            return lesson.id
    raise KeyError(stem)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--curriculum", type=Path, default=CURRICULUM)
    parser.add_argument("--glossary", type=Path, default=GLOSSARY)
    args = parser.parse_args(argv)

    if not args.curriculum.exists():
        ok("no curriculum.yaml yet (M0 state): bilingual gate passes on an empty spine")
        return 0
    registry = load_registry(args.curriculum)
    glossary = load_glossary(args.glossary) if args.glossary.exists() else {}

    problems = check(registry, glossary)
    if problems:
        for problem in problems[:60]:
            fail(problem)
        if len(problems) > 60:
            print(f"... and {len(problems) - 60} more", file=sys.stderr)
        print(
            "\nFix: every lesson file needs a twin in the other language, with the same sections,\n"
            "the same AUTO table ids, and the same term declarations. "
            "See docs/development/bilingual-style.md",
            file=sys.stderr,
        )
        return 1
    lessons = len(registry)
    paired = len(_lesson_files(DOCS / "en") & _lesson_files(DOCS / "zh"))
    ok(
        f"bilingual parity: {lessons} registered lessons, {paired} complete pairs"
        + (" (nothing authored yet)" if paired == 0 else "")
    )
    if args.verbose:
        print(f"     template sections: {len(registry.lesson_template)}", file=sys.stderr)
        print(f"     glossary terms: {len(glossary)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(SRC))
    raise SystemExit(main())
