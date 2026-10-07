#!/usr/bin/env python3
"""Write -- and verify -- the board-sampled preflop all-in matrix artifact (``adr/0007``).

    python tools/gen_preflop.py --out data/gen    # ~9 min: generate the artifact itself
    python tools/gen_preflop.py --verify          # ~23 s: the tier every push can afford
    python tools/gen_preflop.py --verify --file data/gen/preflop/preflop.all-in-matrix.json

Two tiers, because one measured number makes the other necessary. Generating the committed 20,000-board matrix
costs 465-499 s (23-25 ms per board, measured 2026-10-07, depending on load), and ``tools/gen_all.py --check`` -- the repository's
byte-diff gate -- runs on every push. Making every push pay eight and a half minutes for a number nobody
touched is not rigour, it is a tax that teaches contributors to reach for ``--skip``. So the per-push tier
re-derives what a *single batch* determines: batch 0 of the declared seed, 1,000 boards, hashed and compared
byte for byte against ``sampling.first_batch_sha256``. Any change to the evaluator, the pair enumeration, the
legality filter, the RNG arithmetic or the serialisation moves that digest. The proof is exact rather than
statistical (no threshold has to be invented and then defended) and unconditional rather than path-filtered (an
edit to ``artifacts.py`` or a numpy bump changes bytes without touching a path that "should" matter). The full
board set is re-derived on the schedule and by ``gen_all.py --check --include-slow``; see ``adr/0008``.

Everything else here is re-derived from the committed cells alone: zero-sum, the exact diagonal, the ordered-cell
count, the declared decimal precision, the summary statistics, the closed-form comparison count, and the distance
from the exhaustively enumerated cells the engine carries in ``pokergto.preflop.EXACT_CELLS``. Those numbers are
recomputed, never re-read -- which is the difference between an invariant and a receipt.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from _bootstrap import REPO_ROOT, bootstrap_path, fail, ok

bootstrap_path()

from pokergto.artifacts import (  # noqa: E402
    GEN_DIR,
    Provenance,
    unverified_claim,
    validate_artifact,
    write_artifact,
)
from pokergto.cards import HAND_CLASSES_169  # noqa: E402
from pokergto.preflop import (  # noqa: E402
    EXACT_CELLS,
    N_CLASSES,
    NONDEALABLE,
    all_in_matrix,
    batch_panel,
)

SCHEMA_VERSION = "1.0.0"
ARTIFACT_ID = "preflop.all-in-matrix"
ARTIFACT_RELPATH = Path("preflop") / f"{ARTIFACT_ID}.json"

#: Pinned literals. An artifact that describes a function which no longer exists, or a class order it never
#: used, is worse than no metadata: it is a plausible lie with a schema around it.
ORIENTATION = "pairs-then-suited-then-offsuit-descending-rank"
ESTIMATOR = "pokergto.preflop.all_in_matrix"

#: The budget ``adr/0007`` settled on after measuring boundary stability: 0 of 169 classes flip their MDF
#: verdict between independent seeds at this size, closest class (QQ) 9.6 standard errors from the line.
BOARDS = 20_000
BATCHES = 20
SEED = 202_610_071

#: Decimal places per stored value. ``artifacts.FLOAT_DIGITS`` quantises to twelve, and on a quantity whose own
#: error bar is 0.003 that is decoration; six keeps every digit this artifact can defend.
DIGITS = 6
ZERO_SUM_TOLERANCE = 1e-6
#: Summary statistics are re-summed in Python at verify time, so this absorbs only the 12-decimal quantisation
#: ``dumps`` applies -- it is not a licence to be wrong about a cell.
SUM_TOLERANCE = 1e-12

#: ``C(48, 5) / C(52, 5)``: the chance that a four-card hole set is disjoint from a uniform five-card board.
SURVIVAL = math.comb(48, 5) / math.comb(52, 5)
EXPECTED_CELLS = N_CLASSES * N_CLASSES
#: The agreement test this artifact points at, so a stored deviation always names what re-runs it.
AGREEMENT_TEST = (
    "tests/test_preflop.py::test_the_sampled_matrix_agrees_with_the_exact_cells_within_its_own_error_bars "
    "(8,000 boards, seed 202610072); at this artifact's own budget tools/gen_preflop.py --verify re-derives "
    "the comparison below"
)

TITLE = {
    "zh": "翻前全下胜率矩阵（169 x 169 类别），基于 {boards:,} 张公共牌抽样",
    "en": "Preflop all-in equity by class (169 x 169), sampled over {boards:,} boards",
}
CAPTION = {
    "zh": "equity[i][j] 是 hero 类别 i 与 villain 类别 j 全下时的底池份额；stderr 是该格由独立批次量出的标准差。",
    "en": "equity[i][j] is hero class i's share of the pot all-in against villain class j; stderr is that "
    "cell's independent-batch standard error.",
}
SAMPLER = {
    "zh": "抽 {boards:,} 张五人公共牌面（每张牌面把 52 个随机键排序取最小的五个）；对每张牌面，枚举并比较全部"
    "可发的 (hero, villain) 有序组合对——既不共享手牌，也不含牌面上的牌。发牌层面不做任何抽样。",
    "en": "{boards:,} five-card boards drawn uniformly (each board is the five lowest of 52 random keys); for "
    "every board, all dealable ordered (hero, villain) combo pairs are enumerated and compared -- no shared "
    "card, no combo holding a board card. Nothing is sampled at the deal level.",
}
NOTE = {
    "zh": "只抽样公共牌，不抽样遍历（adr/0007）。逐批面板未提交，所以范围级（加权求和）的数字无法从本文件重算，"
    "必须由生成器同一次运行产出为独立产物。",
    "en": "Sampled in the board only, not in the traversal (adr/0007). The per-batch panels are not committed, "
    "so range-level (weighted) numbers cannot be recomputed from this file -- a generator run emits them as "
    "their own artifacts.",
}
ASSUMPTIONS = (
    {
        "zh": "全下胜率一律发满五张公共牌，不论是否已被 dominate；平局分池，两边各记 0.5。",
        "en": "All-in equity runs every board to five cards regardless of dominance; ties split the pot and "
        "are credited 0.5 to each side.",
    },
    {
        "zh": "两人各两张手牌，不计盲注结构、前注与抽水：这里的数字是底池份额，不是以 bb 计的期望值。",
        "en": "Two players, two hole cards each, no blinds, antes or rake: a cell is a share of the pot, not "
        "an expected value in bb.",
    },
    {
        "zh": "同一张牌面内牌张排除是精确的：含牌面牌的组合被剔除，互相共享手牌的组合永不发出。",
        "en": "Card removal is exact within a board: a combo holding a board card is excluded, and two combos "
        "sharing a card are never dealt together.",
    },
    {
        "zh": "各批次取自互不相同的随机数流（种子按批递增），报告的标准差因此是量出来的，不是公式猜的。",
        "en": "Batches draw from distinct RNG streams (the seed advances per batch), which is what makes the "
        "reported standard error measured rather than assumed.",
    },
)
UNVERIFIED = (
    unverified_claim(
        zh="全部 28,561 个有序格都在各自声明的误差棒内与穷举枚举一致。",
        en="All 28,561 ordered cells agree with exhaustive enumeration within their declared standard errors.",
        why_zh="只有三格做过穷举枚举（AA v KK、AKo v QQ、72o v 22，实测各 142-178 秒）。其余格由零和、对角、"
        "全填充与闭式分母这些恒等式兜住，但没有逐格的精确对照。",
        why_en="Three cells have been enumerated exactly (AA v KK, AKo v QQ, 72o v 22, at 142-178 s each). "
        "The rest are held by identities -- zero-sum, diagonal, populated -- and the closed-form denominator, "
        "not by a per-cell exact reference.",
        path_zh="在 tests/test_preflop.py 的 slow 层增加精确旗舰格，或把该测试的抽样预算提到与本产物同级。",
        path_en="Add exact marquee cells to the slow tier of tests/test_preflop.py, or raise that test's board "
        "budget to this artifact's own.",
    ),
)

DETAIL = {
    "determinism": "batch 0 re-derived from sampling.seed / boards_per_batch / batches hashes to "
    "first_batch_sha256; tools/gen_preflop.py --verify runs this on every push (adr/0008)",
    "zero_sum": "equity[i][j] + equity[j][i] == 1 on the stored cells, to the last quantised bit",
    "diagonal_half": "a class against itself is 0.5 exactly, and its dispersion is 0.0 exactly -- symmetric "
    "enumeration, not an estimate",
    "cells_populated": "169 x 169 ordered cells including the diagonal, every one finite",
}


def _prose(template: dict[str, str], boards: int) -> dict[str, str]:
    """Fill the board count into a bilingual string.

    The count is interpolated rather than written out because ``--boards`` is a real flag: an artifact generated
    at 400 boards whose own title says 20,000 is the drift this tool exists to catch, and ``verify`` below reads
    the number back out of the prose.
    """
    return {locale: text.format(boards=boards) for locale, text in template.items()}


def _digest(panel: np.ndarray) -> str:
    """sha256 of one batch's integer wins/ties/pair-count panel, in a declared byte layout.

    The panel arrives float64 because that is what the accumulation adds into, so integrality is asserted rather
    than assumed -- and the cast is explicitly big-endian. ``ndarray.tobytes()`` follows machine byte order,
    which would make a committed digest a function of the laptop that wrote it.
    """
    array = np.ascontiguousarray(panel)
    if not np.all(array == np.rint(array)):
        raise SystemExit(
            "the batch panel holds a non-integral count; a digest of it would not be a count"
        )
    return hashlib.sha256(array.astype(">i8").tobytes()).hexdigest()


def _expected_comparisons(boards: int) -> int:
    """How much comparison work the grid is expected to rest on, from combinatorics rather than from the sample."""
    disjoint_ordered_pairs = int((~NONDEALABLE).sum())
    return round(boards * disjoint_ordered_pairs * SURVIVAL)


def _off_diagonal_sum(values: list[list[float]]) -> tuple[float, float, str, str]:
    """Mean and maximum of the off-diagonal cells, summed in pure Python, plus the cell holding the maximum.

    ``numpy.mean`` uses pairwise summation, whose order is a property of the build; a field a verifier has to
    re-derive should not depend on it. The maximum is reported together with the cell that carries it, so no
    tie-breaking convention has to be trusted.
    """
    cells = [(i, j) for i in range(N_CLASSES) for j in range(N_CLASSES) if i != j]
    picked = [values[i][j] for i, j in cells]
    largest = max(picked)
    first = cells[picked.index(largest)]
    return (
        sum(picked) / len(picked),
        largest,
        HAND_CLASSES_169[first[0]],
        HAND_CLASSES_169[first[1]],
    )


def _measured(payload: dict[str, Any]) -> dict[str, Any]:
    """Everything the artifact claims about its own cells, recomputed from the cells rather than re-read.

    This is the function that makes ``--verify`` a check instead of a diff. It pays for one batch (a measured
    23 s at the committed 1,000 boards per batch) because the batch digest is the only per-push proof that the
    engine still produces these numbers.
    """
    equity = np.array(payload["equity"], dtype=float)
    stderr = np.array(payload["stderr"], dtype=float)
    digits = int(payload["sampling"]["digits"])
    mean, largest, hero, villain = _off_diagonal_sum(payload["stderr"])
    sampling = payload["sampling"]
    board_digest = _digest(
        batch_panel(0, seed=int(sampling["seed"]), per_batch=int(sampling["boards_per_batch"]))
    )
    equity_gap = float(np.max(np.abs(equity - np.round(equity, digits))))
    stderr_gap = float(np.max(np.abs(stderr - np.round(stderr, digits))))
    return {
        "cells_populated": int(np.isfinite(equity).sum()) if equity.shape == stderr.shape else 0,
        "zero_sum_residual": float(np.max(np.abs(equity + equity.T - 1.0))),
        "diagonal_gap": float(np.max(np.abs(np.diagonal(equity) - 0.5))),
        "diagonal_stderr_gap": float(np.max(np.abs(np.diagonal(stderr)))),
        "precision_gap": max(equity_gap, stderr_gap),
        "mean_stderr_off_diagonal": mean,
        "max_stderr_off_diagonal": largest,
        "max_stderr_cell": {"hero": hero, "villain": villain},
        "expected_comparisons": _expected_comparisons(int(sampling["boards"])),
        "first_batch_sha256": board_digest,
        "shape": list(equity.shape),
        "all_finite": bool(np.isfinite(equity).all() and np.isfinite(stderr).all()),
    }


def _crosschecks(payload: dict[str, Any]) -> dict[str, Any]:
    """The exhaustively enumerated anchors, and this artifact's distance from them in its own sigmas."""
    equity = payload["equity"]
    stderr = payload["stderr"]
    agreement = []
    for (hero, villain), exact in sorted(EXACT_CELLS.items()):
        i, j = HAND_CLASSES_169.index(hero), HAND_CLASSES_169.index(villain)
        sampled = equity[i][j]
        error = stderr[i][j]
        agreement.append(
            {
                "hero": hero,
                "villain": villain,
                "exact": float(exact),
                "sampled": sampled,
                "deviation_sigma": abs(sampled - exact) / error if error > 0 else 0.0,
                "test": AGREEMENT_TEST,
            }
        )
    return {
        "exact_cells": {
            f"{hero}:{villain}": float(value) for (hero, villain), value in EXACT_CELLS.items()
        },
        "agreement": agreement,
    }


def _checks(measured: dict[str, Any]) -> list[dict[str, Any]]:
    """The invariant records, carrying values measured before the file existed.

    ``determinism`` gets no value because its value is a 64-character digest, not a magnitude; the schema's
    ``check`` shape would render it as a number field left null, which reads like an unfinished row.
    """
    return [
        {
            "kind": "determinism",
            "pass": True,
            "value": None,
            "threshold": None,
            "detail": DETAIL["determinism"],
        },
        {
            "kind": "zero_sum",
            "pass": measured["zero_sum_residual"] <= ZERO_SUM_TOLERANCE,
            "value": measured["zero_sum_residual"],
            "threshold": ZERO_SUM_TOLERANCE,
            "detail": DETAIL["zero_sum"],
        },
        {
            "kind": "diagonal_half",
            "pass": measured["diagonal_gap"] == 0.0 and measured["diagonal_stderr_gap"] == 0.0,
            "value": measured["diagonal_gap"],
            "threshold": 0.0,
            "detail": DETAIL["diagonal_half"],
        },
        {
            "kind": "cells_populated",
            "pass": measured["cells_populated"] == EXPECTED_CELLS,
            "value": measured["cells_populated"],
            "threshold": EXPECTED_CELLS,
            "detail": DETAIL["cells_populated"],
        },
    ]


def build_payload(
    *, boards: int = BOARDS, seed: int = SEED, batches: int = BATCHES
) -> dict[str, Any]:
    """Generate the artifact, then verify it before it is allowed onto disk."""
    matrix = all_in_matrix(boards, seed=seed, batches=batches)
    if not (np.isfinite(matrix.equity).all() and np.isfinite(matrix.stderr).all()):
        raise SystemExit(
            "refusing to write: a non-finite cell serialises as bare NaN, which is not JSON and would break "
            "the trainer's JSON.parse at the far end of the pipeline"
        )
    equity_rows = [[float(value) for value in row] for row in np.round(matrix.equity, DIGITS)]
    stderr_rows = [[float(value) for value in row] for row in np.round(matrix.stderr, DIGITS)]
    boards = int(matrix.boards)
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "id": ARTIFACT_ID,
        "title": _prose(TITLE, boards),
        "caption": dict(CAPTION),
        "orientation": ORIENTATION,
        "classes": list(HAND_CLASSES_169),
        "equity": equity_rows,
        "stderr": stderr_rows,
        "sampling": {
            "estimator": ESTIMATOR,
            "sampler": _prose(SAMPLER, boards),
            "seed": int(matrix.seed),
            "boards": int(matrix.boards),
            "batches": int(matrix.batches),
            "boards_per_batch": int(matrix.boards // matrix.batches),
            "board_space_size": math.comb(52, 5),
            "survival_probability": SURVIVAL,
            "expected_comparisons": _expected_comparisons(matrix.boards),
            "first_batch_sha256": _digest(matrix.panels[0]),
            "digits": DIGITS,
        },
        "summary": {},
        "crosschecks": {},
        "provenance": Provenance.derived(
            "pokergto.preflop#all_in_matrix", assumptions=list(ASSUMPTIONS), note=dict(NOTE)
        ).to_dict(),
        "checks": [],
        "unverified_claims": [dict(claim) for claim in UNVERIFIED],
    }
    measured = _measured(payload)
    payload["summary"] = {
        "cells_populated": measured["cells_populated"],
        "mean_stderr_off_diagonal": measured["mean_stderr_off_diagonal"],
        "max_stderr_off_diagonal": measured["max_stderr_off_diagonal"],
        "max_stderr_cell": measured["max_stderr_cell"],
    }
    payload["crosschecks"] = _crosschecks(payload)
    payload["checks"] = _checks(measured)
    problems = verify_payload(payload)
    if problems:
        raise SystemExit(
            "generated artifact failed its own verification: " + "; ".join(problems[:6])
        )
    return payload


def verify_payload(payload: dict[str, Any]) -> list[str]:
    """Every reason this artifact is not what it says it is. Empty means it is.

    Deliberately redundant with ``build_payload``: the committed file is checked by re-deriving it, so a field
    cannot be edited into a passing state without the re-derivation noticing. Nothing here trusts ``checks`` --
    each recorded value is recomputed and compared.
    """
    problems: list[str] = []
    sampling = payload.get("sampling")
    summary = payload.get("summary", {})
    checks = {str(entry["kind"]): entry for entry in payload.get("checks", [])}

    if payload.get("id") != ARTIFACT_ID:
        problems.append(f"id is {payload.get('id')!r}, expected {ARTIFACT_ID!r}")
    if payload.get("orientation") != ORIENTATION:
        problems.append(
            f"orientation is {payload.get('orientation')!r}, which is not this artifact's order"
        )
    if not isinstance(sampling, dict):
        return [
            *problems,
            "no sampling block: a sampled artifact that does not say how it was sampled cannot be "
            "re-derived, and the schema refuses it too",
        ]
    required = {"seed", "boards", "batches", "boards_per_batch", "digits"}
    if missing := sorted(required - set(sampling)):
        return [*problems, f"sampling is missing {missing}, so nothing here can be re-derived"]
    if sampling.get("estimator") != ESTIMATOR:
        problems.append(
            f"estimator is {sampling.get('estimator')!r}; the engine function was renamed"
        )
    if payload.get("classes") != list(HAND_CLASSES_169):
        problems.append("classes is not pokergto.cards.HAND_CLASSES_169 in order")
    shape = (N_CLASSES, N_CLASSES)
    if len(payload.get("equity", [])) != shape[0] or any(
        len(row) != shape[1] for row in payload.get("equity", [])
    ):
        problems.append(f"equity is not a full {shape[0]}x{shape[1]} grid")
        return problems

    measured = _measured(payload)
    if not measured["all_finite"]:
        problems.append(
            "a cell is NaN or infinite; it would serialise as bare NaN, which is not JSON"
        )
    if measured["shape"] != list(shape):
        problems.append(f"equity/stderr shapes are {measured['shape']}, expected {list(shape)}")
    if measured["cells_populated"] != EXPECTED_CELLS:
        problems.append(
            f"{EXPECTED_CELLS - measured['cells_populated']} of {EXPECTED_CELLS} ordered cells are not finite"
        )
    if measured["zero_sum_residual"] > ZERO_SUM_TOLERANCE:
        problems.append(
            f"zero-sum broken by {measured['zero_sum_residual']:.3e} "
            f"(threshold {ZERO_SUM_TOLERANCE:.0e}): a cell was edited, not computed"
        )
    if measured["diagonal_gap"] != 0.0 or measured["diagonal_stderr_gap"] != 0.0:
        problems.append(
            f"diagonal is {0.5 + measured['diagonal_gap']:.9f} with dispersion "
            f"{measured['diagonal_stderr_gap']:.3e}; a class against itself is 0.5 with no error"
        )
    digits = int(sampling.get("digits", DIGITS))
    if measured["precision_gap"] > 0.0:
        problems.append(f"a stored value carries more than {digits} decimal places")

    for field, expected in (
        ("cells_populated", measured["cells_populated"]),
        ("mean_stderr_off_diagonal", measured["mean_stderr_off_diagonal"]),
        ("max_stderr_off_diagonal", measured["max_stderr_off_diagonal"]),
    ):
        got = summary.get(field)
        if not isinstance(got, float | int) or abs(float(got) - float(expected)) > SUM_TOLERANCE:
            problems.append(f"summary.{field} is {got!r}, re-derivation says {expected!r}")
    if summary.get("max_stderr_cell") != measured["max_stderr_cell"]:
        problems.append(
            f"summary.max_stderr_cell is {summary.get('max_stderr_cell')!r}, "
            f"re-derivation says {measured['max_stderr_cell']!r}"
        )

    boards = int(sampling.get("boards", -1))
    batches = int(sampling.get("batches", -1))
    per_batch = int(sampling.get("boards_per_batch", -1))
    if boards != per_batch * batches:
        problems.append(f"boards {boards} != boards_per_batch {per_batch} x batches {batches}")
    if per_batch < 100 or batches < 2:
        problems.append(
            f"sampling {batches} batches of {per_batch} boards cannot support an error bar"
        )
    if sampling.get("board_space_size") != math.comb(52, 5):
        problems.append(f"board_space_size {sampling.get('board_space_size')} is not C(52, 5)")
    if abs(float(sampling.get("survival_probability", 0.0)) - SURVIVAL) > SUM_TOLERANCE:
        problems.append("sampling.survival_probability is not C(48,5)/C(52,5)")
    stated = f"{boards:,}"
    for field, text in (
        ("title", payload.get("title", {}).get("en", "")),
        ("title (zh)", payload.get("title", {}).get("zh", "")),
        ("sampling.sampler", sampling.get("sampler", {}).get("en", "")),
        ("sampling.sampler (zh)", sampling.get("sampler", {}).get("zh", "")),
    ):
        if stated not in str(text):
            problems.append(f"{field} does not name the {stated} boards this artifact declares")
    if int(sampling.get("expected_comparisons", -1)) != measured["expected_comparisons"]:
        problems.append(
            f"expected_comparisons {sampling.get('expected_comparisons')} != closed form "
            f"{measured['expected_comparisons']}"
        )
    if sampling.get("first_batch_sha256") != measured["first_batch_sha256"]:
        problems.append(
            f"batch 0 of seed {sampling.get('seed')} hashes to {measured['first_batch_sha256'][:16]}..., "
            f"not the declared {str(sampling.get('first_batch_sha256'))[:16]}... -- the engine moved"
        )

    stored_exact = payload.get("crosschecks", {}).get("exact_cells", {})
    declared = {f"{hero}:{villain}": float(value) for (hero, villain), value in EXACT_CELLS.items()}
    if stored_exact != declared:
        problems.append(
            f"crosschecks.exact_cells {sorted(stored_exact)} does not equal pokergto.preflop.EXACT_CELLS "
            f"{sorted(declared)} -- one side was edited"
        )
    for entry in payload.get("crosschecks", {}).get("agreement", []):
        i, j = HAND_CLASSES_169.index(entry["hero"]), HAND_CLASSES_169.index(entry["villain"])
        sampled = payload["equity"][i][j]
        error = payload["stderr"][i][j]
        if abs(float(entry["sampled"]) - sampled) > SUM_TOLERANCE:
            problems.append(
                f"crosschecks {entry['hero']} v {entry['villain']}: sampled value is not the cell"
            )
        expected_sigma = abs(sampled - float(entry["exact"])) / error if error > 0 else 0.0
        if abs(float(entry["deviation_sigma"]) - expected_sigma) > 1e-9:
            problems.append(
                f"crosschecks {entry['hero']} v {entry['villain']}: deviation {entry['deviation_sigma']:.3f} "
                f"sigma, recomputed {expected_sigma:.3f}"
            )

    for kind, detail in DETAIL.items():
        entry = checks.get(kind)
        if entry is None:
            problems.append(f"no {kind} check recorded")
            continue
        if not entry.get("pass"):
            problems.append(f"{kind} check is recorded as failing; regenerate the artifact")
        if entry.get("detail") != detail:
            problems.append(f"{kind} check's detail no longer says what this tool measures")
    recorded_residual = checks.get("zero_sum", {}).get("value")
    if (
        recorded_residual is not None
        and abs(float(recorded_residual) - measured["zero_sum_residual"]) > SUM_TOLERANCE
    ):
        problems.append("the recorded zero-sum residual is not what the cells now say")
    if checks.get("cells_populated", {}).get("value") != measured["cells_populated"]:
        problems.append("the recorded cell count is not what the cells now say")
    return problems


def verify(path: Path) -> list[str]:
    """Verify one committed artifact file, including the byte-level reason the trainer can parse it."""
    if not path.exists():
        return [f"{path.relative_to(REPO_ROOT).as_posix()} does not exist"]
    text = path.read_text(encoding="utf-8")
    # json.loads accepts the bare NaN token, Python's json.dumps emits it, and JSON.parse in the browser does
    # neither. The failure would surface as a broken trainer page three steps downstream of this file.
    if "NaN" in text or "Infinity" in text:
        return [f"{path.name} contains a non-JSON numeric token (NaN/Infinity)"]
    payload = json.loads(text)
    try:
        validate_artifact(payload, "preflop_matrix")
    except Exception as error:
        # A schema violation is the problem being reported, not a crash to hide: this tool's job is to say
        # what is wrong with a committed artifact in one readable line.
        return [f"{path.name}: {error}"]
    return verify_payload(payload)


def generate(out: Path, *, boards: int, seed: int, batches: int) -> Path:
    payload = build_payload(boards=boards, seed=seed, batches=batches)
    path = out / ARTIFACT_RELPATH
    write_artifact(path, payload, schema="preflop_matrix")
    problems = verify(path)
    if problems:
        for problem in problems:
            fail(problem)
        raise SystemExit(f"{path.name} was written but does not verify")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--out", type=Path, default=GEN_DIR)
    parser.add_argument("--file", type=Path, help="artifact to verify (default: data/gen's matrix)")
    parser.add_argument(
        "--verify", action="store_true", help="re-derive and compare, write nothing"
    )
    parser.add_argument("--boards", type=int, default=BOARDS)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--batches", type=int, default=BATCHES)
    args = parser.parse_args(argv)

    if args.verify:
        target = args.file or args.out / ARTIFACT_RELPATH
        problems = verify(target)
        for problem in problems:
            fail(problem)
        if problems:
            return 1
        size = target.stat().st_size
        sampling = json.loads(target.read_text(encoding="utf-8"))["sampling"]
        ok(
            f"preflop matrix verified: batch 0 of {sampling['boards_per_batch']} boards re-derived, "
            f"{sampling['boards']} declared boards, {size / 1e6:.2f} MB on disk"
        )
        return 0

    path = generate(args.out, boards=args.boards, seed=args.seed, batches=args.batches)
    ok(f"preflop matrix: wrote {path.name} ({path.stat().st_size / 1e6:.2f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
