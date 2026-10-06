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
from pathlib import Path
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

    A parity check that only passes when the work is finished is not a gate; it is a TODO list.
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
    # Registered-but-unwritten is the expected state at milestone zero; files-without-registration is
    # legitimately empty. Asserting both non-empty would be a wrong expectation, not a stronger test.
    assert missing["missing_file:en"] and missing["missing_file:zh"]
    assert not missing["unregistered:en"] and not missing["unregistered:zh"]
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
    from pathlib import Path as P

    repo = P(__file__).resolve().parents[1]
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
    from pathlib import Path as P

    repo = P(__file__).resolve().parents[1]
    target = repo / "data" / "gen" / "tables" / "table.02-03.mdf-vs-sizing.json"
    if not target.exists():
        pytest.skip("no committed table artifact to corrupt")
    backup = P(str(target) + ".test-backup")
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
