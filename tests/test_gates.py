"""The gates must be able to fail.

Every "our CI enforces X" claim in this repository is worth nothing until someone has seen X
rejected. This file does that for the three integrity gates -- artifact schema, provenance, bilingual
parity -- by feeding each one input that looks plausible and must be refused.

These tests deliberately call the gate functions rather than shelling out to the tools, and
deliberately do not write into ``docs/`` or ``data/``: the checks read the repository tree, so a test
that mutated it would race with a lesson author and would make the fixture a lie about the working
tree. Where a check needs a tree, the test passes a synthetic one in.

Each test's docstring names the real failure mode it stands guard over, because a negative test with
no story rots into a tautology.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from random import Random
from typing import Any

import pytest

from pokergto.artifacts import validate_artifact
from pokergto.errors import ProvenanceError, SchemaDriftError

pytestmark = pytest.mark.docs


def _table_artifact() -> dict[str, Any]:
    """A minimal but completely valid ``table`` artifact, used as the mutation baseline."""
    return {
        "schema_version": "1.0.0",
        "id": "table.probe.case",
        "title": {"zh": "探针", "en": "probe"},
        "columns": [
            {"key": "size_label", "header": {"zh": "尺度", "en": "Size"}, "unit": "dimensionless"},
            {"key": "mdf", "header": {"zh": "防守", "en": "Defense"}, "unit": "probability"},
        ],
        "rows": [{"size_label": "1/3 pot", "mdf": 0.75}],
        "source": {
            "module": "pokergto.odds",
            "function": "sizing_table",
            "generator": "tools/gen_tables.py",
        },
        "provenance": {
            "kind": "derived",
            "verified": True,
            "confidence": "high",
            "license": "CC-BY-SA-4.0",
            "upstream": None,
            "derivation_ref": "pokergto.odds#minimum_defense_frequency",
        },
    }


# --- the artifact schema ---------------------------------------------------------------


def test_a_valid_artifact_validates() -> None:
    validate_artifact(_table_artifact(), "table")


def test_a_number_without_a_unit_is_refused() -> None:
    """Every cell in a lesson table has to say what it is measuring.

    A bare 0.75 in a bilingual table is the shape that "is this 75% or 0.75%?" questions come from,
    and the two languages can answer it differently while both looking correct.
    """
    artifact = _table_artifact()
    del artifact["columns"][1]["unit"]
    with pytest.raises(SchemaDriftError):
        validate_artifact(artifact, "table")


def test_an_unknown_column_unit_is_refused() -> None:
    artifact = _table_artifact()
    artifact["columns"][1]["unit"] = "big_blinds_per_hand"
    with pytest.raises(SchemaDriftError):
        validate_artifact(artifact, "table")


def test_an_unserializable_provenance_kind_is_refused() -> None:
    artifact = _table_artifact()
    artifact["provenance"]["kind"] = "copied"
    with pytest.raises((SchemaDriftError, ProvenanceError)):
        validate_artifact(artifact, "table")


# --- provenance ------------------------------------------------------------------------


@pytest.mark.parametrize(
    "mutate",
    [
        pytest.param(lambda p: p.pop("derivation_ref"), id="derived-without-pointer"),
        pytest.param(
            lambda p: p.update({"kind": "external", "upstream": None}),
            id="external-without-upstream",
        ),
        pytest.param(
            lambda p: p.update({"verified": True, "derivation_ref": None, "upstream": None}),
            id="verified-without-evidence",
        ),
        pytest.param(
            lambda p: p.update({"verified": True, "confidence": "low"}),
            id="verified-but-low-confidence",
        ),
    ],
)
def test_provenance_claims_that_point_at_nothing_are_refused(mutate: Any) -> None:
    """ADR-0005 in four shapes.

    The case that matters is the third: ``verified: true`` with nothing to resolve. A provenance
    field that can be flipped to true by editing a boolean is not a control, and this is the test
    that shows it is not one here.
    """
    artifact = _table_artifact()
    mutate(artifact["provenance"])
    with pytest.raises((SchemaDriftError, ProvenanceError)):
        validate_artifact(artifact, "table")


@pytest.mark.parametrize(
    "license_id",
    [
        "PioSolver-EULA",
        "GTO-Wizard-Terms",
        "proprietary",
        "all-rights-reserved",
        "CC-BY-NC-4.0",
    ],
)
def test_licences_that_cannot_legally_appear_here_are_refused(license_id: str) -> None:
    """NOTICE bans commercial solver output; the schema is what enforces NOTICE.

    ``CC-BY-NC-4.0`` is refused for the opposite reason -- it is not a free-content licence and
    would exclude the repository from open-education venues (ADR-0003). Both directions of "wrong
    licence" have to fail, or the allow-list is decoration.
    """
    artifact = _table_artifact()
    artifact["provenance"]["license"] = license_id
    with pytest.raises((SchemaDriftError, ProvenanceError)):
        validate_artifact(artifact, "table")


@pytest.mark.parametrize(
    "schema", ["table", "range_chart", "spot", "quiz", "hand_example", "solver_run"]
)
def test_provenance_block_is_required_not_merely_recommended(schema: str) -> None:
    """A bare record of every strategy-bearing kind must be refused.

    This is the copyright control expressed as a type: an unattributed claim does not fail review, it
    fails validation, so it cannot be merged by anyone including the maintainer.
    """
    with pytest.raises((SchemaDriftError, ProvenanceError)):
        validate_artifact({"schema_version": "1.0.0", "id": "probe"}, schema)


# --- bilingual parity ------------------------------------------------------------------


def _registry_with(lessons: list[dict[str, Any]]) -> Any:
    from pokergto.registry import CurriculumRegistry

    return CurriculumRegistry(
        {
            "schema_version": "1.0.0",
            "engine_version": "0.1.0",
            "lesson_template": ["s"] * 15,
            "chapters": [
                {
                    "id": "02",
                    "order": 2,
                    "slug": "02-probe",
                    "title": {"zh": "探针", "en": "probe"},
                    "tags": {"scenario": ["shared"]},
                    "lessons": lessons,
                }
            ],
        }
    )


def test_a_ready_lesson_without_a_translation_is_reported() -> None:
    """The D4 rule in one assertion: ``ready`` means both languages, in the same pull request.

    Without this the bilingual promise decays the standard way -- one language ships, the other
    becomes a backlog item, and the parity check never fires because nothing was ever marked ready.
    """
    registry = _registry_with(
        [
            {
                "id": "02-01",
                "order": 1,
                "slug": "probe",
                "title": {"zh": "探针", "en": "probe"},
                "tags": {"scenario": ["shared"]},
                "status_zh": "ready",
                "status_en": "draft",
            }
        ]
    )
    assert not registry.lesson("02-01").is_ready
    assert registry.totals["lessons_ready"] == 0
    assert registry.totals["lessons_draft"] == 1


def test_draft_lessons_may_legally_have_no_files_yet() -> None:
    """The gate passes on an empty tree, which is what lets it exist from milestone zero.

    A parity check that only passes when the work is finished is not a gate; it is a TODO list. The
    assertion below is the whole reason ``find_orphans`` reads status rather than the spine alone.
    """
    registry = _registry_with(
        [
            {
                "id": "02-01",
                "order": 1,
                "slug": "probe",
                "title": {"zh": "探针", "en": "probe"},
                "tags": {"scenario": ["shared"]},
                "status_zh": "draft",
                "status_en": "draft",
            }
        ]
    )
    missing = registry.find_orphans(Path("docs-nonexistent-check-only"))
    assert missing == {
        "missing_file:en": [],
        "missing_file:zh": [],
        "unregistered:en": [],
        "unregistered:zh": [],
    }


def test_a_draft_lesson_may_have_a_file_without_being_unregistered(
    tmp_path: Path, monkeypatch: Any
) -> None:
    """The authoring order the whole pipeline depends on: file first, status later.

    An earlier revision of ``find_orphans`` made ``unregistered`` compare against the *ready* set, so
    every drafted lesson on disk -- which is every lesson between an author's first commit and the
    maintainer's status flip -- was reported as a page nobody registered. The gate then failed the one
    state the repository is designed to support: work in progress.
    """
    bilingual = _tool("check_bilingual")
    registry = _registry_with(
        [
            {
                "id": "02-01",
                "order": 1,
                "slug": "probe",
                "title": {"zh": "探针", "en": "probe"},
                "tags": {"scenario": ["shared"]},
                "status_zh": "draft",
                "status_en": "draft",
            }
        ]
    )
    text = _lesson_text(2, ("hand.02-01-a", "hand.02-01-b"))
    monkeypatch.setattr(bilingual, "DOCS", _write_pair(tmp_path, text, text))
    problems = bilingual.check(registry, {})
    assert not problems, problems
    # ...and the same file becomes a real failure the moment the lesson claims to be ready.
    ready = _registry_with(
        [
            {
                "id": "02-01",
                "order": 1,
                "slug": "probe",
                "title": {"zh": "探针", "en": "probe"},
                "tags": {"scenario": ["shared"]},
                "status_zh": "ready",
                "status_en": "ready",
            }
        ]
    )
    missing = ready.find_orphans(tmp_path)
    assert not missing["missing_file:en"] and not missing["unregistered:en"]
    absent = ready.find_orphans(tmp_path / "nothing-here")
    assert absent["missing_file:en"] == ["docs/en/02-probe/probe.md"], (
        "the same lesson claiming `ready` with no file must be reported"
    )


def test_a_ready_lesson_with_no_file_on_disk_is_orphaned() -> None:
    """The other half of the same rule: ``ready`` is a claim, and a claim without a file fails.

    Without this the status field would be decoration -- a lesson could be marked ready while its file
    sat uncommitted, and every gate would still be green.
    """
    registry = _registry_with(
        [
            {
                "id": "02-01",
                "order": 1,
                "slug": "probe",
                "title": {"zh": "探针", "en": "probe"},
                "tags": {"scenario": ["shared"]},
                "status_zh": "ready",
                "status_en": "ready",
            }
        ]
    )
    orphans = registry.find_orphans(Path("docs-nonexistent-check-only"))
    assert orphans["missing_file:en"] == ["docs/en/02-probe/probe.md"]
    assert orphans["missing_file:zh"] == ["docs/zh/02-probe/probe.md"]
    assert registry.unresolved_prerequisites() == []
    assert registry.duplicate_paths() == []


def test_dangling_prerequisites_and_colliding_paths_are_caught() -> None:
    registry = _registry_with(
        [
            {
                "id": "02-01",
                "order": 1,
                "slug": "same",
                "title": {"zh": "a", "en": "a"},
                "tags": {"scenario": ["shared"]},
                "status_zh": "draft",
                "status_en": "draft",
                "prereq": ["99-99"],
            },
            {
                "id": "02-02",
                "order": 2,
                "slug": "same",
                "title": {"zh": "b", "en": "b"},
                "tags": {"scenario": ["shared"]},
                "status_zh": "draft",
                "status_en": "draft",
            },
        ]
    )
    assert registry.unresolved_prerequisites() == [("02-01", "99-99")]
    assert registry.duplicate_paths(), "two lessons with one slug must collide"


def test_an_unknown_lesson_id_raises_instead_of_returning_none() -> None:
    from pokergto.errors import InputError

    registry = _registry_with([])
    with pytest.raises(InputError):
        registry.lesson("02-99")


# --- determinism of the generated tree --------------------------------------------------


@pytest.mark.slow
def test_the_committed_tree_is_byte_reproducible() -> None:
    """``gen_all --check`` is the promise; this runs it so the promise is tested, not assumed.

    Marked ``docs`` rather than fast because it regenerates artifacts into a temporary directory,
    which is the same work CI does. It is skipped if the generator's dependencies are unavailable.
    """
    import subprocess
    import sys

    repo = Path(__file__).resolve().parents[1]
    script = repo / "tools" / "gen_all.py"
    if not script.exists():  # pragma: no cover
        pytest.skip("gen_all.py missing")
    result = subprocess.run(
        [sys.executable, str(script), "--check", "--skip", "solver"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.slow
def test_a_mutated_committed_artifact_is_detected() -> None:
    """The companion to the check above: prove the drift detector notices a single changed byte.

    Without this it is possible for ``--check`` to pass simply because it compared nothing.
    """
    import shutil
    import subprocess
    import sys

    repo = Path(__file__).resolve().parents[1]
    target = repo / "data" / "gen" / "tables" / "table.02-03.mdf-vs-sizing.json"
    if not target.exists():
        pytest.skip("no committed table artifact to corrupt")
    backup = Path(str(target) + ".test-backup")
    shutil.copy2(target, backup)
    try:
        payload = copy.deepcopy(target.read_bytes())
        mutated = payload.replace(b"0.75", b"0.74", 1)
        assert mutated != payload, "the fixture must actually mutate something"
        target.write_bytes(mutated)
        result = subprocess.run(
            [sys.executable, str(repo / "tools" / "gen_all.py"), "--check", "--only", "tables"],
            cwd=repo,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode != 0, "a changed committed artifact must fail the drift check"
    finally:
        shutil.move(backup, target)


# --- the hand-count gate, and the renderer's locale contract --------------------------------


def _tool(name: str) -> Any:
    """Import a module from ``tools/`` inside the test process.

    The gate functions are what CI calls, so a negative test has to reach the same code rather than
    re-implement it. ``tools/_bootstrap.py`` expects ``src`` on the path, which the loop below
    provides.
    """
    import importlib
    import sys

    repo = Path(__file__).resolve().parents[1]
    for entry in (str(repo / "tools"), str(repo / "src")):
        if entry not in sys.path:
            sys.path.insert(0, entry)
    return importlib.import_module(name)


_TEMPLATE_H2 = (
    "本节目标 / Objectives",
    "前置知识 / Prerequisites",
    "核心原理 / The principle",
    "推导 / Derivation",
    "直觉 / Intuition",
    "算例 / Worked examples",
    "生成表 / Generated tables",
    "实战牌局 / Live hands",
    "范围图 / Range chart",
    "为何成立、何时失效 / Why it works, when it breaks",
    "陷阱 / Common mistakes",
    "练习 / Drills",
    "自测清单 / Self-check",
    "来源与置信度 / Provenance and confidence",
    "术语 / Terms",
)


def _lesson_text(declared: int, hand_ids: tuple[str, ...]) -> str:
    """A lesson that satisfies every other structural rule, so a failure points at the hands."""
    body = "\n".join(f"## {heading}\n\nprose\n" for heading in _TEMPLATE_H2)
    hands = "\n".join(f"**`{hand_id}`**" for hand_id in hand_ids)
    before, _, after = body.partition("## 实战牌局 / Live hands\n\nprose\n")
    return f"<!-- hands: {declared} -->\n{before}## 实战牌局 / Live hands\n\n{hands}\n{after}"


def _ready_registry() -> Any:
    return _registry_with(
        [
            {
                "id": "02-01",
                "order": 1,
                "slug": "probe",
                "title": {"zh": "探针", "en": "probe"},
                "tags": {"scenario": ["shared"]},
                "status_zh": "ready",
                "status_en": "ready",
            }
        ]
    )


def _write_pair(tmp_path: Path, en: str, zh: str) -> Path:
    for locale, text in (("en", en), ("zh", zh)):
        lesson_dir = tmp_path / locale / "02-probe"
        lesson_dir.mkdir(parents=True, exist_ok=True)
        (lesson_dir / "probe.md").write_text(f"# probe\n\n{text}", encoding="utf-8")
    return tmp_path


def test_a_hand_declaration_that_does_not_match_the_files_is_reported(
    monkeypatch: Any, tmp_path: Path
) -> None:
    """``<!-- hands: 2 -->`` used to be an unreadable promise, and that made this gate inert.

    The first version of the check needed two spaces after ``<!--`` and matched nothing, so a lesson
    could claim examples it had not written. Now the declaration is compared against the ``hand.*``
    ids actually present, which is the difference between a rule and a decoration.
    """
    bilingual = _tool("check_bilingual")
    good = _lesson_text(2, ("hand.02-01-a", "hand.02-01-b"))
    overclaiming = _lesson_text(2, ("hand.02-01-a",))
    monkeypatch.setattr(bilingual, "DOCS", _write_pair(tmp_path, overclaiming, good))
    problems = bilingual.check(_ready_registry(), {})
    assert any("declares 2 live hands" in problem for problem in problems), problems


def test_the_two_languages_must_teach_the_same_live_hands(monkeypatch: Any, tmp_path: Path) -> None:
    """Mirrored lessons that quietly use different example hands are the drift a reader cannot see.

    Without this, the English author can swap in a hand they understand better and the lesson still
    "passes bilingual parity" because every heading lines up.
    """
    bilingual = _tool("check_bilingual")
    en = _lesson_text(2, ("hand.02-01-a", "hand.02-01-b"))
    zh = _lesson_text(2, ("hand.02-01-a", "hand.02-01-c"))
    monkeypatch.setattr(bilingual, "DOCS", _write_pair(tmp_path, en, zh))
    problems = bilingual.check(_ready_registry(), {})
    assert any("different live hands" in problem for problem in problems), problems


def test_a_ready_lesson_that_declares_nothing_is_reported(monkeypatch: Any, tmp_path: Path) -> None:
    """A lesson that omits the declaration cannot be audited, so omission is itself a failure."""
    bilingual = _tool("check_bilingual")
    text = "\n".join(f"## {heading}\n\nprose\n" for heading in _TEMPLATE_H2)
    monkeypatch.setattr(bilingual, "DOCS", _write_pair(tmp_path, text, text))
    problems = bilingual.check(_ready_registry(), {})
    assert any("no <!-- hands: N --> declaration" in problem for problem in problems), problems


def test_a_bilingual_table_cell_renders_in_the_requested_locale() -> None:
    """A cell written as ``{zh, en}`` is a first-class shape; a single-lingual string is not.

    The five-card category counts used to store the Chinese label in ``category`` and the English one
    in an unused ``category_en`` key, so the English lesson shipped Chinese row labels under English
    headers. Rendering refuses unknown cell shapes now, so the same class of bug cannot pass silently.
    """
    from pokergto.render import table_from_artifact

    artifact = {
        "schema_version": "1.0.0",
        "id": "table.probe",
        "title": {"zh": "探针", "en": "probe"},
        "columns": [
            {"key": "label", "header": {"zh": "名称", "en": "Label"}, "unit": "dimensionless"},
            {"key": "count", "header": {"zh": "数量", "en": "Count"}, "unit": "count"},
        ],
        "rows": [{"label": {"zh": "同花顺", "en": "straight flush"}, "count": 40}],
        "source": {"module": "pokergto.evaluator", "generator": "tools/gen_tables.py"},
        "provenance": {
            "kind": "derived",
            "verified": True,
            "note": {"zh": "探针", "en": "probe"},
        },
    }
    assert "straight flush" in table_from_artifact(artifact, locale="en")
    assert "同花顺" in table_from_artifact(artifact, locale="zh")


def test_an_unrenderable_cell_raises_instead_of_stringifying() -> None:
    from pokergto.errors import InvariantError
    from pokergto.render import table_from_artifact

    artifact = {
        "schema_version": "1.0.0",
        "id": "table.probe",
        "title": {"zh": "探针", "en": "probe"},
        "columns": [{"key": "x", "header": {"zh": "x", "en": "x"}, "unit": "dimensionless"}],
        "rows": [{"x": {"unexpected": "shape"}}],
        "source": {"module": "pokergto.render", "generator": "tools/gen_tables.py"},
        "provenance": {
            "kind": "derived",
            "verified": True,
            "note": {"zh": "探针", "en": "probe"},
        },
    }
    with pytest.raises(InvariantError):
        table_from_artifact(artifact, locale="en")


def test_the_trainer_sync_detects_a_stale_copy(tmp_path: Path, monkeypatch) -> None:
    """ADR-0004's enforcement point: a bundle built against old artifacts must not pass.

    The trainer renders numbers it did not compute, so its only claim to correctness is that
    ``trainer/public/data`` still equals ``data/gen``. This writes a real sync into a temporary
    trainer, corrupts one copied byte, and requires ``--check`` to notice.
    """
    sync_tool = _tool("sync_trainer_data")

    trainer = tmp_path / "trainer"
    trainer.mkdir()
    monkeypatch.setattr(sync_tool, "TRAINER", trainer)
    monkeypatch.setattr(sync_tool, "PUBLIC_DATA", trainer / "public" / "data")
    monkeypatch.setattr(sync_tool, "MANIFEST_TS", trainer / "src" / "generated" / "manifest.ts")

    assert sync_tool.sync(check=False) == 0
    assert sync_tool.sync(check=True) == 0, "a fresh sync must verify clean"

    victim = trainer / "public" / "data" / "tables" / "table.02-03.mdf-vs-sizing.json"
    victim.write_bytes(victim.read_bytes().replace(b"0.75", b"0.74", 1))
    assert sync_tool.sync(check=True) == 1, "a mutated artifact must fail the version check"


def test_a_tampered_quiz_answer_is_refused(tmp_path: Path) -> None:
    """The quiz answer key is not authored: arithmetic re-runs it. is a claim about arithmetic, so arithmetic re-runs it.

    Two separate fakes matter: a *changed* number (the drift case -- a corrected formula leaving a stale
    key behind) and an *unparseable* item (the case of someone adding an `answer` field to the authored
    YAML, where there is no such field today by design).
    """
    quizzes = _tool("gen_quizzes")
    checker = _tool("check_quiz_answers")
    bank = {
        "schema_version": "1.0.0",
        "engine_version": "0.1.0",
        "templates": [
            {
                "id": "probe.mdf",
                "lesson": "02-03",
                "kind": "minimum-defense-frequency",
                "variants": 1,
                "prompt": {"zh": "底池 {pot}，下注 {bet}。", "en": "Pot {pot}, bet {bet}."},
                "domain": {"pot": [10], "bet": [5]},
            }
        ],
    }
    out = tmp_path / "gen"
    items = [quizzes._instantiate(spec, Random(0), 0) for spec in bank["templates"]]
    assert items[0]["answer"]["number"] == pytest.approx(0.666667, abs=1e-5)
    for item in items:
        quizzes.write_artifact(out / "quizzes" / f"{item['id']}.json", item, schema="quiz")
    path = next((out / "quizzes").glob("quiz.*.json"))
    assert checker.check_item(path) == [], "a freshly generated item must pass"

    tampered = json.loads(path.read_text(encoding="utf-8"))
    tampered["answer"]["number"] = 0.75
    path.write_text(__import__("json").dumps(tampered), encoding="utf-8")
    problems = checker.check_item(path)
    assert problems and "stored 0.75" in problems[0], problems
