#!/usr/bin/env python3
"""Cost budget for the solver and the exact-enumeration paths: what a claim may cost, and what it cost.

ADR-0002 says a solver claim enters this repository only through ``solver/proofs.py``. That rule holds
a claim's *correctness*; this file holds its *size*. A mathematically valid solve that takes eleven
minutes and two gigabytes is not a teaching artifact -- it is a reason the project does not run on a
laptop, and it arrives one street at a time, each step looking reasonable. So each game family declares
a wall-clock and memory budget here, and a breach fails the build.

The same argument applies to the evaluator, and more quietly: a speed-up that is never measured can be
lost one refactor at a time, and an exact-enumeration claim that was affordable on the day it was
written stops being affordable when someone changes a loop. So the vectorised evaluator's throughput has
a floor here, and the widest exact enumeration any lesson cites has a ceiling. Both are re-derived
numbers, not restated prose.

Timings deliberately never enter ``data/gen`` (a byte-level timestamp would make ``gen_all --check``
noise; see ``run_solver.py``). They are printed to the build log, where they are useful and harmless.

Usage::

    python tools/cost_probe.py                 # every registered proof, then the enumeration paths
    python tools/cost_probe.py --game kuhn
    python tools/cost_probe.py --budget-only   # print the table, solve nothing
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import tracemalloc
from pathlib import Path

import numpy as np

from _bootstrap import bootstrap_path, fail, ok

bootstrap_path()

from pokergto.cards import Card  # noqa: E402
from pokergto.equity import range_equity  # noqa: E402
from pokergto.evaluator import evaluate7_many  # noqa: E402
from pokergto.ranges import Range, from_chart  # noqa: E402
from pokergto.solver.proofs import PUBLISHED_PROOFS, ProofEntry  # noqa: E402
from run_solver import run_entry  # noqa: E402

#: Wall-clock seconds and peak Python-allocated megabytes allowed per game family. The second column
#: is measured, not guessed: on the author's machine (2026-10-06, py3.12, Windows) Kuhn at its
#: registered 20,000 iterations takes ~40s and a 1-street toy at 4,000 takes ~1.5s, with peak Python
#: allocation under 1 MB. The budgets are that baseline with room for a slower CI runner and a laptop
#: on battery, plus a memory ceiling that says "do not blow up" rather than "this is the estimate".
#: Raising one is a deliberate act, and it should come with a reason in the pull request.
BUDGETS: dict[str, tuple[float, float]] = {
    "kuhn": (150.0, 256.0),
    "toy_1street": (60.0, 256.0),
    # Leduc is the first family the textbook per-deal recursion cannot afford: 360 deals x 85 public
    # nodes costs about 0.23 s per iteration, so its registered 10,000 iterations would run for about
    # thirty-eight minutes. The public-tree form in ``solver/vector.py`` finishes the same solve in 35 s,
    # which is a measured 65x at that size (68x at 50 iterations, 77x at 200 -- the ratio grows with the
    # iteration count because the fixed per-step Python overhead is amortised),
    # and that file has to clear every registered gate before it may write an artifact
    # (``tests/test_solver_vector.py``), which is what makes this budget an optimisation rather than a
    # new claim. Measured 2026-10-07 on the author's laptop (py3.12, Windows): 35 s, peak under 1 MB.
    "leduc": (180.0, 256.0),
}

#: Families with no declared budget are a failure, not a free pass: an undeclared game is exactly how
#: "just one more street" enters silently.
MISSING_BUDGET = "no budget declared for family"

# ---------------------------------------------------------------------------
# Enumeration costs (not solves): the exact-equity paths, and the throughput the
# ``adr/0002`` Rule B affordability statement is calculated from.
# ---------------------------------------------------------------------------

#: Floors and ceilings for the enumeration probes, each with roughly the same four-times headroom the
#: solver budgets use. Measured on the author's laptop (py3.12, Windows) on 2026-10-07:
#: ``evaluate7_many`` 313,984 hands/s (scalar ``evaluate7`` 46,296, scalar ``evaluate5`` 62,118,
#: ``evaluate5_many`` 1,028,474), and the 884-versus-442-combo flop enumeration 7.84 s / 262 MB. The
#: exact preflop hand-versus-hand case (``AhAs`` versus ``7d2s``, 1,712,304 runouts, 17.3 s) is
#: deliberately not probed here: it would dominate this script, and it is the number lesson 01-04 cites.
MIN_EVALUATOR_RATE = 100_000.0  # seven-card hands per second
MAX_EVALUATOR_SECONDS = 60.0
MAX_EXACT_EQUITY_SECONDS = 30.0
MAX_EXACT_EQUITY_MB = 1024.0


def _probe_evaluator() -> tuple[str, list[str]]:
    """Score a fixed block of random seven-card hands, and check the batch path is still a batch path."""
    rows = 1 << 18
    # Deal by ranking a row of random keys: ``Generator.choice(..., replace=False)`` refuses a two
    # dimensional ``size``, and sorting 52 keys per row is faster than a Python loop over hands anyway.
    keys = np.random.default_rng(20261007).random((rows, 52), dtype=np.float64)
    codes = np.argsort(keys, axis=1, kind="stable")[:, :7].astype(np.int64)
    started = time.perf_counter()
    scores = evaluate7_many(codes)
    seconds = time.perf_counter() - started
    rate = rows / seconds
    problems: list[str] = []
    if rate < MIN_EVALUATOR_RATE:
        problems.append(
            f"evaluate7_many: {rate:,.0f} hands/s is under the {MIN_EVALUATOR_RATE:,.0f} hands/s floor "
            "(the vectorised evaluator was replaced by something slower)"
        )
    if seconds > MAX_EVALUATOR_SECONDS:
        problems.append(
            f"evaluate7_many: {seconds:.1f}s over {rows:,} rows exceeds {MAX_EVALUATOR_SECONDS:.0f}s"
        )
    if int(scores.min()) < 0:
        problems.append("evaluate7_many: negative scores, the packing is broken")
    row = (
        f"{'evaluate7_many':<28} {rows:>9,} hands "
        f"used {seconds:>6.1f}s / {rate:>9,.0f} hands-per-s "
        f"of {MAX_EVALUATOR_SECONDS:>4.0f}s / {MIN_EVALUATOR_RATE:>7,.0f} floor"
    )
    return row, problems


def _probe_exact_equity() -> tuple[str, list[str]]:
    """Time the widest exact enumeration a lesson actually cites, and re-derive its number."""
    chart_path = (
        Path(__file__).resolve().parents[1]
        / "data"
        / "gen"
        / "ranges"
        / "range.02-03.mdf-floor-vs-half-pot.json"
    )
    defense = from_chart(json.loads(chart_path.read_text(encoding="utf-8")))
    fold = Range(1.0 - defense.weights)
    board = tuple(Card.parse(c) for c in ("Kh", "7h", "2d"))
    tracemalloc.start()
    started = time.perf_counter()
    result = range_equity(defense, fold, board, mode="exact")
    seconds = time.perf_counter() - started
    peak_mb = tracemalloc.get_traced_memory()[1] / (1024.0 * 1024.0)
    tracemalloc.stop()
    problems: list[str] = []
    if seconds > MAX_EXACT_EQUITY_SECONDS:
        problems.append(
            f"exact flop range equity: {seconds:.1f}s against a {MAX_EXACT_EQUITY_SECONDS:.0f}s budget"
        )
    if peak_mb > MAX_EXACT_EQUITY_MB:
        problems.append(
            f"exact flop range equity: {peak_mb:.0f} MB against a {MAX_EXACT_EQUITY_MB:.0f} MB budget"
        )
    if abs(result.equity - 0.5591717398) > 1e-9:
        problems.append(
            f"exact flop range equity: {result.equity:.10f} is not the 0.5591717398 lesson 01-04 cites"
        )
    row = (
        f"{'exact_flop_range_equity':<28} {result.iterations:>9,} runouts "
        f"used {seconds:>6.1f}s / {peak_mb:>5.1f} MB "
        f"of {MAX_EXACT_EQUITY_SECONDS:>4.0f}s / {MAX_EXACT_EQUITY_MB:>5.0f} MB"
    )
    return row, problems


def _probe_enumerations() -> list[str]:
    problems: list[str] = []
    for probe in (_probe_evaluator, _probe_exact_equity):
        row, found = probe()
        print(row)
        problems.extend(found)
    return problems


def _measure(entry: ProofEntry) -> tuple[float, float]:
    tracemalloc.start()
    started = time.perf_counter()
    try:
        _artifact, _curve, elapsed = run_entry(entry)
    finally:
        peak = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()
    seconds = elapsed if elapsed else time.perf_counter() - started
    return float(seconds), peak / (1024.0 * 1024.0)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument(
        "--game", action="append", dest="games", help="limit to these proof entries"
    )
    parser.add_argument(
        "--budget-only", action="store_true", help="print the declared budgets and solve nothing"
    )
    args = parser.parse_args(argv)

    entries = [
        entry
        for name, entry in sorted(PUBLISHED_PROOFS.items())
        if not args.games or name in set(args.games)
    ]
    if not entries:
        fail("no registered proof matched; PUBLISHED_PROOFS is the only source of solver artifacts")
        return 1

    problems: list[str] = []
    rows: list[str] = []
    for entry in entries:
        budget = BUDGETS.get(entry.family)
        if budget is None:
            problems.append(f"{entry.game}: {MISSING_BUDGET} ({entry.family})")
            continue
        allowed_seconds, allowed_mb = budget
        if args.budget_only:
            rows.append(
                f"{entry.game:<28} {entry.iterations:>9,} iterations "
                f"budget {allowed_seconds:>6.0f}s / {allowed_mb:>5.0f} MB"
            )
            continue
        seconds, peak_mb = _measure(entry)
        rows.append(
            f"{entry.game:<28} {entry.iterations:>9,} iterations "
            f"used {seconds:>6.1f}s / {peak_mb:>5.1f} MB "
            f"of {allowed_seconds:>6.0f}s / {allowed_mb:>5.0f} MB"
        )
        if seconds > allowed_seconds:
            problems.append(
                f"{entry.game}: took {seconds:.1f}s against a {allowed_seconds:.0f}s budget"
            )
        if peak_mb > allowed_mb:
            problems.append(
                f"{entry.game}: peaked at {peak_mb:.0f} MB against a {allowed_mb:.0f} MB budget"
            )

    if not args.budget_only:
        problems.extend(_probe_enumerations())

    for row in rows:
        print(row)
    for problem in problems:
        fail(problem)
    if problems:
        print(
            "\nEither the solve is too big to be a teaching artifact, or the budget is a deliberate\n"
            "decision waiting to be written down. Both are answered by changing this file, not by\n"
            "commenting the check out. See adr/0002.",
            file=sys.stderr,
        )
        return 1
    if not args.budget_only:
        ok(f"cost probe: {len(entries)} proof games and the enumeration paths inside their budgets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
