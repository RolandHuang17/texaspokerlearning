"""The curriculum registry: ``data/src/curriculum.yaml`` as a queryable object.

This is what makes the spine *enforceable* rather than descriptive. ``tools/check_bilingual.py`` and
``tools/gen_curriculum_index.py`` both work through here, so there is one definition of "which
lessons exist, where their files are, and whether both languages are finished".

A registry that only reads YAML would be half the job; the interesting part is
:meth:`CurriculumRegistry.find_orphans`, which reports the lessons that exist as *files* but are not
registered, and the registered lessons that exist as no file. Both directions are required: a missing
mirror breaks the site build, and an unregistered file is content nobody can navigate to.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence

import yaml

from .errors import InputError

STATUS_ORDER = ("draft", "in-review", "ready", "deprecated")


@dataclass(frozen=True, slots=True)
class Lesson:
    id: str
    chapter: str
    order: int
    slug: str
    title: Mapping[str, str]
    tags: Mapping[str, Any]
    status_zh: str
    status_en: str
    prereq: tuple[str, ...] = ()
    spot_ids: tuple[str, ...] = ()
    hand_ids: tuple[str, ...] = ()
    quiz_ids: tuple[str, ...] = ()
    table_ids: tuple[str, ...] = ()
    glossary_new_terms: tuple[str, ...] = ()

    #: Directory name of the owning chapter, e.g. ``02-the-math-of-one-decision``.
    _chapter_dir: str = field(default="", compare=False)

    def path(self, locale: str) -> str:
        return f"docs/{locale}/{self._chapter_dir}/{self.slug}.md"

    @property
    def chapter_dir(self) -> str:
        return self._chapter_dir

    @property
    def is_ready(self) -> bool:
        """Both languages, or it is not ready. That single line is D4 expressed in code."""
        return self.status_zh == "ready" and self.status_en == "ready"

    @property
    def scenario(self) -> tuple[str, ...]:
        return tuple(self.tags.get("scenario", ()))


@dataclass(frozen=True, slots=True)
class Chapter:
    id: str
    order: int
    slug: str
    title: Mapping[str, str]
    summary: Mapping[str, str]
    lessons: tuple[Lesson, ...]


class CurriculumRegistry:
    """In-memory view of the spine, plus the consistency questions CI asks."""

    def __init__(self, payload: Mapping[str, Any], *, default_chapter_dirs: Mapping[str, str] | None = None):
        self.schema_version: str = payload["schema_version"]
        self.engine_version: str = payload["engine_version"]
        self.lesson_template: tuple[str, ...] = tuple(payload["lesson_template"])
        self.chapters: tuple[Chapter, ...] = _build_chapters(payload.get("chapters", []))
        self._lessons: dict[str, Lesson] = {
            lesson.id: lesson for chapter in self.chapters for lesson in chapter.lessons
        }
        if len(self._lessons) != sum(len(chapter.lessons) for chapter in self.chapters):
            raise InputError("duplicate lesson id in curriculum.yaml")

    # --- queries ----------------------------------------------------------------------

    def lesson(self, lesson_id: str) -> Lesson:
        try:
            return self._lessons[lesson_id]
        except KeyError as exc:
            raise InputError(f"unknown lesson id {lesson_id!r}") from exc

    def ordered_lessons(self) -> list[Lesson]:
        return [lesson for chapter in self.chapters for lesson in chapter.lessons]

    def by_scenario(self, scenario: str) -> list[Lesson]:
        return [lesson for lesson in self.ordered_lessons() if scenario in lesson.scenario]

    def __len__(self) -> int:
        return len(self._lessons)

    def __iter__(self) -> Iterator[Lesson]:
        return iter(self.ordered_lessons())

    @property
    def totals(self) -> dict[str, int]:
        lessons = self.ordered_lessons()
        return {
            "chapters": len(self.chapters),
            "lessons": len(lessons),
            "lessons_ready": sum(1 for lesson in lessons if lesson.is_ready),
            "lessons_draft": sum(1 for lesson in lessons if not lesson.is_ready),
        }

    # --- consistency questions --------------------------------------------------------

    def unresolved_prerequisites(self) -> list[tuple[str, str]]:
        """``(lesson, missing prereq)`` pairs. A dangling prerequisite is a broken learning path,
        which for a curriculum is a correctness bug, not a style one."""
        return [
            (lesson.id, prereq)
            for lesson in self.ordered_lessons()
            for prereq in lesson.prereq
            if prereq not in self._lessons
        ]

    def find_orphans(self, docs_root: Path) -> dict[str, list[str]]:
        """Files on disk vs lessons in the spine, in both directions and per locale.

        Returns ``{"missing_file:en": [...], "missing_file:zh": [...], "unregistered:en": [...],
        "unregistered:zh": [...]}``. Empty lists for every key is the passing state.
        """
        expected: dict[str, set[str]] = {"en": set(), "zh": set()}
        for lesson in self.ordered_lessons():
            for locale in ("en", "zh"):
                expected[locale].add(lesson.path(locale))
        present: dict[str, set[str]] = {"en": set(), "zh": set()}
        for locale in ("en", "zh"):
            base = docs_root / locale
            if not base.exists():
                continue
            for path in base.rglob("*.md"):
                relative = path.relative_to(docs_root).as_posix()
                if relative.startswith("development/") or "/development/" in relative:
                    continue
                if relative.endswith("index.md") or relative.endswith("README.md"):
                    continue
                present[locale].add(relative)
        report: dict[str, list[str]] = {}
        for locale in ("en", "zh"):
            report[f"missing_file:{locale}"] = sorted(expected[locale] - present[locale])
            report[f"unregistered:{locale}"] = sorted(present[locale] - expected[locale])
        return report

    def duplicate_paths(self) -> list[str]:
        """Two lessons whose files would collide. Cheap to check, catastrophic to discover later."""
        seen: dict[str, str] = {}
        clashes: list[str] = []
        for lesson in self.ordered_lessons():
            for locale in ("en", "zh"):
                path = lesson.path(locale)
                if path in seen and seen[path] != lesson.id:
                    clashes.append(f"{path} claimed by {seen[path]} and {lesson.id}")
                seen[path] = lesson.id
        return clashes


def _build_chapters(raw: Sequence[Mapping[str, Any]]) -> tuple[Chapter, ...]:
    chapters: list[Chapter] = []
    for chapter in sorted(raw, key=lambda item: item["order"]):
        lessons: list[Lesson] = []
        for lesson in sorted(chapter.get("lessons", []), key=lambda item: item["order"]):
            built = Lesson(
                id=lesson["id"],
                chapter=chapter["id"],
                order=lesson["order"],
                slug=lesson["slug"],
                title=dict(lesson["title"]),
                tags=dict(lesson.get("tags", {})),
                status_zh=lesson.get("status_zh", "draft"),
                status_en=lesson.get("status_en", "draft"),
                prereq=tuple(lesson.get("prereq", ())),
                spot_ids=tuple(lesson.get("spot_ids", ())),
                hand_ids=tuple(lesson.get("hand_ids", ())),
                quiz_ids=tuple(lesson.get("quiz_ids", ())),
                table_ids=tuple(lesson.get("table_ids", ())),
                glossary_new_terms=tuple(lesson.get("glossary_new_terms", ())),
                _chapter_dir=chapter["slug"],
            )
            lessons.append(built)
        chapters.append(
            Chapter(
                id=chapter["id"],
                order=chapter["order"],
                slug=chapter["slug"],
                title=dict(chapter["title"]),
                summary=dict(chapter.get("summary", {"zh": "", "en": ""})),
                lessons=tuple(lessons),
            )
        )
    return tuple(chapters)


def load_registry(path: Path) -> CurriculumRegistry:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise InputError(f"{path} did not parse to a mapping")
    return CurriculumRegistry(payload)


def load_glossary(path: Path) -> dict[str, dict[str, Any]]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    terms = payload.get("terms", []) if isinstance(payload, dict) else payload
    index: dict[str, dict[str, Any]] = {}
    for term in terms:
        term_id = term["id"]
        if term_id in index:
            raise InputError(f"duplicate glossary term {term_id!r} in {path.name}")
        index[term_id] = term
    return index
