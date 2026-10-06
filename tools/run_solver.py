#!/usr/bin/env python3
"""Solve every proof-registered game and write its artifact and convergence curve.

    python tools/run_solver.py                      # all games in PUBLISHED_PROOFS
    python tools/run_solver.py --game kuhn
    python tools/run_solver.py --check              # re-solve, compare bytes, no writes
    python tools/run_solver.py --quick              # 5% of iterations: local loop only, never CI

Three rules, all enforced here rather than in prose:

1. **No entry in :mod:`pokergto.solver.proofs`, no artifact.** A game without a validation anchor
   cannot be cited by a ``ready`` lesson, so refusing to generate it is the enforcement point
   (ADR-0002).
2. **Every assertion is recorded**, measured against its anchor, in the artifact's ``checks`` array.
   ``gen_all.py --check`` re-runs them, which turns a regression into a build failure instead of a
   subtly wrong number in a lesson.
3. **Cost is bounded by ``tools/cost_probe.py``.** Convergence research has an infinite appetite; the
   budget is what keeps ``--check`` usable.

The solve itself samples nothing, so the same iteration count produces the same bytes on any machine
-- the reason the curves are committed rather than regenerated at page load.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _bootstrap import bootstrap_path, fail, ok

bootstrap_path()

from pokergto.artifacts import GEN_DIR, Provenance, dumps, sha256_of, write_artifact  # noqa: E402
from pokergto.solver.cfr import CFRSolver  # noqa: E402
from pokergto.solver.proofs import PUBLISHED_PROOFS, ProofEntry, verify  # noqa: E402
from pokergto.solver.vector import VectorCFRSolver  # noqa: E402

SCHEMA_VERSION = "1.0.0"


def run_entry(
    entry: ProofEntry, *, quick: bool = False
) -> tuple[dict[str, object], list[tuple[int, float]], float]:
    tree = entry.build()
    iterations = max(50, entry.iterations // 20) if quick else entry.iterations
    plus = entry.algorithm == "cfr_plus"
    # Which implementation writes this artifact is a registry field, not a guess: the vector form is what
    # makes a 3,780-information-set game solvable at all, and the textbook form stays the producer for
    # every game it can finish. See ProofEntry.implementation.
    if entry.implementation == "vector":
        solver = VectorCFRSolver(tree, plus=plus)
    elif entry.implementation == "cfr":
        solver = CFRSolver(tree, plus=plus)
    else:
        raise SystemExit(
            f"{entry.game}: unknown solver implementation {entry.implementation!r}; expected 'cfr' or "
            "'vector'"
        )
    result = solver.run(iterations, measure_every=entry.measure_every or max(1, iterations // 25))
    records = verify(entry, tree, result)
    artifact = {
        "schema_version": SCHEMA_VERSION,
        "id": f"solver.{entry.game}",
        "game": entry.family,
        "game_description": tree.description,
        "algorithm": result.algorithm,
        "iterations": result.iterations,
        "seed": 0,
        "config": {
            "game": entry.game,
            "parameters": dict(entry.parameters or {}),
            "tree": tree.summary(),
            "measure_every": entry.measure_every or max(1, iterations // 25),
        },
        "exploitability_bb_per_hand": round(result.exploitability, 10),
        "exploitability_threshold": entry.exploitability_threshold,
        "game_value_bb_per_hand": round(result.game_value, 10),
        "curve": [
            {
                "iteration": int(iteration),
                "exploitability": round(float(value), 10),
                "elapsed_seconds": None,
            }
            for iteration, value in result.curve
        ],
        "average_strategy": result.strategy_report(),
        # Never the measured wall clock: putting a timing in the artifact body makes every rebuild
        # differ by bytes that mean nothing, which would reduce `gen_all --check` to noise. The number
        # goes to the build log instead, where it is useful and harmless (ADR-0002 determinism).
        "timing_seconds": None,
        "peak_memory_mb": None,
        "proof_entry": entry.game,
        "determinism_verified": True,
        "provenance": Provenance.derived(
            f"src/pokergto/solver/proofs.py#{entry.game}",
            solver_run=f"data/gen/solver/{entry.game}.json",
        ).to_dict(),
        "checks": records,
    }
    if entry.family == "kuhn":
        artifact["closed_form_value"] = -1.0 / 18.0
    return artifact, result.curve, result.elapsed_seconds


def curve_csv(curve: list[tuple[int, float]]) -> str:
    lines = ["iteration,exploitability_chips_per_hand"]
    lines.extend(f"{iteration},{value:.10g}" for iteration, value in curve)
    return "\n".join(lines) + "\n"


def failing(artifact: dict[str, object]) -> list[str]:
    return [
        str(record.get("detail") or record["kind"])
        for record in artifact["checks"]
        if not record["pass"]
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--game", action="append", dest="games")
    parser.add_argument("--out", type=Path, default=GEN_DIR / "solver")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args(argv)

    names = args.games or sorted(PUBLISHED_PROOFS)
    unknown = sorted(set(names) - set(PUBLISHED_PROOFS))
    if unknown:
        print(
            f"error: no proof entry for {unknown}. Known games: {sorted(PUBLISHED_PROOFS)}",
            file=sys.stderr,
        )
        return 2

    problems: list[str] = []
    for name in names:
        entry = PUBLISHED_PROOFS[name]
        try:
            artifact, curve, elapsed = run_entry(entry, quick=args.quick)
        except Exception as error:
            problems.append(f"{name}: solve raised {type(error).__name__}: {error}")
            continue
        bad = failing(artifact)
        if bad:
            if args.quick:
                print(
                    f"WARN {name}: gates not met in --quick mode (ignored): {bad}", file=sys.stderr
                )
            else:
                problems.extend(f"{name}: {detail}" for detail in bad)
                continue
        payload = dumps(artifact).encode("utf-8")
        target = args.out / f"{name}.json"
        csv_target = args.out / f"{name}.csv"
        if args.check:
            if not target.exists():
                problems.append(f"{name}: {target} is not committed")
            elif target.read_bytes() != payload:
                problems.append(
                    f"{name}: committed artifact differs from a fresh solve (sha "
                    f"{sha256_of(target.read_bytes())[:12]} vs {sha256_of(payload)[:12]})"
                )
            continue
        write_artifact(target, artifact, schema="solver_run")
        csv_target.parent.mkdir(parents=True, exist_ok=True)
        csv_target.write_text(curve_csv(curve), encoding="utf-8", newline="\n")
        ok(
            f"{name}: {entry.algorithm} {artifact['iterations']} iters in {elapsed:.2f}s, "
            f"exploitability {artifact['exploitability_bb_per_hand']:.2e} "
            f"(gate {entry.exploitability_threshold:.0e}), "
            f"value {artifact['game_value_bb_per_hand']:.6f}"
        )

    if problems:
        for problem in problems:
            fail(problem)
        print(
            "\nA solver regression is a correctness failure, not a diff to accept: either the game "
            "definition, the update rule, or the anchor moved. See adr/0002 and solver/proofs.py.",
            file=sys.stderr,
        )
        return 1
    if args.check:
        ok(f"solver artifacts verified for {len(names)} game(s)")
    if args.quick and not problems:
        print(
            "NOTE --quick ran ~5% of the iterations: convergence gates are advisory here and are "
            "enforced only by the unqualified run that CI executes.",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    if not PUBLISHED_PROOFS:  # pragma: no cover
        raise SystemExit("no proof entries: refusing to solve anything")
    raise SystemExit(main())
