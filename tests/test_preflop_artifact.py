"""The preflop matrix artifact: that it validates, that it verifies, and that both can fail.

``data/gen/preflop/preflop.all-in-matrix.json`` is the first sampled artifact this repository commits, and a
sampled artifact has two ways to be wrong that a deterministic one does not: its numbers can drift from the
engine that claims to produce them, and its error bars can be decoration. So the tests here are built around
``tools/gen_preflop.py``'s own verification rather than around a re-imagination of it -- the same ``verify`` CI
calls, reached through ``_tool`` so a negative test proves the gate fires instead of proving a copy of it.

Two budgets appear below. Most of this file runs against a payload generated at the smallest legal size (200
boards in 2 batches, a measured ~10 s including the batch re-derivation), because a structural property needs a
real artifact, not a big one. One test re-derives the committed 20,000-board matrix byte for byte, and that is
``slow`` because it is a measured 9 minutes; the scheduled workflow runs the same proof weekly.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from pokergto.artifacts import GEN_DIR, dumps
from pokergto.cards import HAND_CLASSES_169
from pokergto.errors import SchemaDriftError
from pokergto.preflop import N_CLASSES, batch_panel

REPO = Path(__file__).resolve().parents[1]
ARTIFACT = GEN_DIR / "preflop" / "preflop.all-in-matrix.json"

#: 200 boards in 2 batches: the engine's floor is 100 boards per batch, and every property asserted below is a
#: property of the artifact's structure, not of its sample size.
FIXTURE_BOARDS = 200
FIXTURE_BATCHES = 2
FIXTURE_SEED = 202_610_099


def _tool(name: str) -> Any:
    """Import a module from ``tools/`` inside the test process, the way CI actually calls it."""
    import importlib

    for entry in (str(REPO / "tools"), str(REPO / "src")):
        if entry not in sys.path:
            sys.path.insert(0, entry)
    return importlib.import_module(name)


@pytest.fixture(scope="module")
def gen() -> Any:
    return _tool("gen_preflop")


@pytest.fixture(scope="module")
def payload(gen: Any) -> dict[str, Any]:
    return gen.build_payload(boards=FIXTURE_BOARDS, seed=FIXTURE_SEED, batches=FIXTURE_BATCHES)


def _copy(chart: dict[str, Any]) -> dict[str, Any]:
    """A mutable deep copy through the repository's own serialiser, so quantisation is the real one."""
    return json.loads(dumps(chart))


def test_a_generated_payload_validates_and_verifies_clean(
    gen: Any, payload: dict[str, Any]
) -> None:
    """The happy path, asserted through the real schema and the real verifier, not a summary of them."""
    from pokergto.artifacts import validate_artifact

    validate_artifact(payload, "preflop_matrix")
    assert gen.verify_payload(payload) == []


def test_the_schema_refuses_an_artifact_that_does_not_declare_its_sampling(
    gen: Any, payload: dict[str, Any]
) -> None:
    """A sampled number that stops saying how it was sampled must fail at the boundary.

    ``sampling`` is what makes ``adr/0007``'s "exact conditional on the board set" checkable. Without it the file
    is a grid of decimals wearing a provenance block, which is the thing this repository refuses to publish.
    """
    from pokergto.artifacts import validate_artifact

    for mutation in ("drop sampling", "drop the batch digest", "drop the seed"):
        broken = _copy(payload)
        if mutation == "drop sampling":
            del broken["sampling"]
        elif mutation == "drop the batch digest":
            del broken["sampling"]["first_batch_sha256"]
        else:
            del broken["sampling"]["seed"]
        with pytest.raises(SchemaDriftError, match="preflop_matrix violation"):
            validate_artifact(broken, "preflop_matrix")
        assert gen.verify_payload(broken), f"{mutation}: the verifier also looked the other way"


def test_the_orientation_literal_is_pinned_and_a_reversed_class_order_is_caught_by_verify(
    gen: Any, payload: dict[str, Any]
) -> None:
    """Which layer catches which axis drift -- and why the schema cannot catch the subtler one.

    ``orientation`` is a ``const``, so renaming the order it claims fails validation. A *reversed* ``classes``
    array does not: JSON Schema can require 169 unique well-formed classes, and a reversed list satisfies every
    one of those assertions, because a schema describes shapes rather than identities. So that case belongs to
    the verifier, which compares ``classes`` against the order ``pokergto.cards.HAND_CLASSES_169`` actually
    produces -- the only thing that can catch a silently transposed grid before a lesson cites it.
    """
    from pokergto.artifacts import validate_artifact

    renamed = _copy(payload)
    renamed["orientation"] = "pairs-then-offsuit-then-suited"
    with pytest.raises(SchemaDriftError, match="preflop_matrix violation"):
        validate_artifact(renamed, "preflop_matrix")

    reversed_classes = _copy(payload)
    reversed_classes["classes"].reverse()
    validate_artifact(reversed_classes, "preflop_matrix")
    problems = gen.verify_payload(reversed_classes)
    assert any("classes is not" in problem for problem in problems), problems


def test_verification_notices_one_changed_digit_in_one_cell(
    gen: Any, payload: dict[str, Any]
) -> None:
    """The gate has to be capable of failing on the smallest edit a reviewer could miss.

    ``AA v KK`` is one of the cells the artifact cross-checks against exhaustive enumeration, and one unit in the
    sixth decimal breaks the zero-sum identity with its transpose. Anything that lets this through is not a
    verification step, it is a receipt.
    """
    mutated = _copy(payload)
    i, j = HAND_CLASSES_169.index("AA"), HAND_CLASSES_169.index("KK")
    mutated["equity"][i][j] = round(mutated["equity"][i][j] + 1e-6, 6)
    problems = gen.verify_payload(mutated)
    assert problems, "a single changed cell verified clean"
    assert any("zero-sum" in problem for problem in problems), problems


def test_verification_notices_a_summary_that_no_longer_describes_the_grid(
    gen: Any, payload: dict[str, Any]
) -> None:
    """``summary`` is re-summed in Python at verify time, so a plausible number cannot be hand-set."""
    mutated = _copy(payload)
    mutated["summary"]["mean_stderr_off_diagonal"] = 0.0029
    problems = gen.verify_payload(mutated)
    assert any("summary.mean_stderr_off_diagonal" in problem for problem in problems), problems


def test_verification_notices_a_title_that_names_somebody_elses_budget(
    gen: Any, payload: dict[str, Any]
) -> None:
    """Prose drifts from data in a generated file exactly like it does in a hand-written one.

    ``--boards`` is a real flag, so an artifact can be generated at one budget and described at another. The
    board count in the bilingual title and sampler text is read back against ``sampling.boards`` for that reason.
    """
    mutated = _copy(payload)
    mutated["title"]["en"] = mutated["title"]["en"].replace(f"{FIXTURE_BOARDS:,}", "20,000")
    problems = gen.verify_payload(mutated)
    assert any("does not name" in problem for problem in problems), problems


def test_a_non_finite_cell_is_refused_before_it_reaches_a_browser(
    gen: Any, payload: dict[str, Any], tmp_path: Path
) -> None:
    """``json.dumps`` writes a bare ``NaN``, which is not JSON and dies in ``JSON.parse``.

    The failure surfaces three steps downstream of this file -- the trainer fetches it and the screen goes blank
    -- so the guard is on the bytes as well as on the numbers: ``verify`` scans the text before it parses it.
    """
    broken = _copy(payload)
    broken["equity"][3][7] = float("nan")
    assert gen.verify_payload(broken), "a NaN cell verified clean"
    text = dumps(broken)
    assert "NaN" in text, "the serializer started refusing NaN; this test's premise moved"
    target = tmp_path / "preflop.all-in-matrix.json"
    target.write_text(text, encoding="utf-8", newline="\n")
    problems = gen.verify(target)
    assert any("NaN" in problem for problem in problems), problems


def test_the_declared_batch_digest_is_the_digest_of_that_batch(
    gen: Any, payload: dict[str, Any]
) -> None:
    """The per-push proof, stated directly: re-run one batch, hash it, compare.

    ``sampling`` declares the seed, the boards per batch and the batch count precisely so batch 0 can be rebuilt
    without reading any code. This is the line that makes "the engine still produces this artifact" a byte
    comparison instead of a claim, and it costs a measured 2.6 s at this fixture's size, 23 s at the committed one.
    """
    sampling = payload["sampling"]
    panel = batch_panel(0, seed=int(sampling["seed"]), per_batch=int(sampling["boards_per_batch"]))
    assert gen._digest(panel) == sampling["first_batch_sha256"]
    assert panel.shape == (3, N_CLASSES, N_CLASSES)


def test_the_slow_step_is_registered_everywhere_its_artifact_is_named() -> None:
    """Wiring drift is the quiet way a committed artifact stops being generated.

    The directory has to be known to the schema map, to the manifest's kind enum, to the step list, and to the
    tiering rule that decides when it is re-derived. Four lists, one commit: this asserts they agree.
    """
    gen_all = _tool("gen_all")
    check_artifact_schema = _tool("check_artifact_schema")

    assert check_artifact_schema.DIRECTORY_SCHEMA["preflop"] == "preflop_matrix"
    names = [name for name, _ in gen_all.STEPS]
    assert "preflop" in names
    assert names.index("preflop") > names.index("solver"), (
        "the matrix belongs after the solver it follows"
    )
    assert "preflop" in gen_all.SLOW_STEPS
    manifest_schema = json.loads(
        (REPO / "data/schema/manifest.schema.json").read_text(encoding="utf-8")
    )
    kinds = manifest_schema["properties"]["files"]["additionalProperties"]["properties"]["kind"][
        "enum"
    ]
    assert "preflop_matrix" in kinds
    assert (
        gen_all._schema_for(Path("data/gen/preflop/preflop.all-in-matrix.json")) == "preflop_matrix"
    )


def test_a_missing_slow_artifact_fails_the_run_rather_than_being_carried_away(
    tmp_path: Path,
) -> None:
    """Skip must never read as deleted: with the committed matrix absent, ``--check`` refuses.

    The artifact's directory is moved aside, not edited, and restored in ``finally`` -- the same shape
    ``test_gates.py::test_a_mutated_committed_artifact_is_detected`` uses, because a gate is only as good as the
    demonstration that it can fail.
    """
    if not ARTIFACT.exists():
        pytest.skip("the committed matrix has not been generated yet")
    staging = tmp_path / "preflop-hold"
    shutil.move(str(ARTIFACT.parent), str(staging))
    try:
        result = subprocess.run(
            [sys.executable, str(REPO / "tools" / "gen_all.py"), "--check", "--only", "glossary"],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode != 0, (
            "a missing slow artifact was carried over as if it were present"
        )
        assert "no artifact" in result.stderr, result.stderr
    finally:
        shutil.move(str(staging), str(ARTIFACT.parent))


@pytest.mark.slow
def test_the_committed_matrix_is_byte_reproducible_at_its_declared_budget() -> None:
    """The matrix's own regeneration, paid weekly by the schedule and on demand by anyone who doubts it.

    This is the full-board-set re-derivation the per-push tier deliberately does not do (``adr/0008``): regenerate
    20,000 boards from the declared seed and fail on any byte difference. Everything else in the committed tree is
    covered by ``test_gates.py::test_the_committed_tree_is_byte_reproducible``.
    """
    if not ARTIFACT.exists():
        pytest.skip("the committed matrix has not been generated yet")
    result = subprocess.run(
        [sys.executable, str(REPO / "tools" / "gen_all.py"), "--check", "--only", "preflop"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.slow
def test_the_committed_matrix_cross_checks_the_cells_the_engine_calls_exactly(gen: Any) -> None:
    """The anchors in the committed file are the anchors in the engine, and neither was typed twice.

    Each exact cell costs 142-178 s to re-enumerate, so the file and ``pokergto.preflop.EXACT_CELLS`` share one
    source; this reads the committed file back and proves the two still name the same numbers.
    """
    from pokergto.preflop import EXACT_CELLS

    if not ARTIFACT.exists():
        pytest.skip("the committed matrix has not been generated yet")
    committed = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    assert committed["crosschecks"]["exact_cells"] == {
        f"{hero}:{villain}": float(value) for (hero, villain), value in EXACT_CELLS.items()
    }
    assert not gen.verify_payload(committed)
