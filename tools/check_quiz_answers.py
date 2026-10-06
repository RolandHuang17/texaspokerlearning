#!/usr/bin/env python3
"""Recompute every stored quiz answer and refuse the ones that do not match.

The quiz artifacts in ``data/gen/quizzes`` carry a ``derivation_ref`` naming the engine function that
produced their answer. This tool calls that function again with the parameters the item records and
compares. It is the gate that makes "answers are computed, not typed" a checked property rather than a
sentence in a README, and it catches three separate things:

* an answer edited by hand, or an author filling a key into the YAML (there is no such field, so this is
  mostly about someone adding one);
* an answer that was correct when generated and has since gone stale because ``pokergto.odds`` or
  ``pokergto.equity`` changed -- a lesson can carry the same formula, so the drift is real;
* a numeric answer the learner could not possibly be asked to match: NaN, negative, or a probability
  outside ``[0, 1]``.

Usage::

    python tools/check_quiz_answers.py             # check the committed tree
    python tools/check_quiz_answers.py --verbose
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

from _bootstrap import bootstrap_path, fail, ok

bootstrap_path()

from gen_quizzes import COMPUTED, QUIZ_OUT, _answer  # noqa: E402

#: Where committed quiz items live. From ``gen_quizzes`` rather than a second constant, so this gate
#: cannot be pointed at a directory the generator never writes.
QUIZ_DIR = QUIZ_OUT


def _resolve(reference: str) -> str:
    """The function name behind a ``module#function`` derivation ref."""
    module, _, function = reference.partition("#")
    if module not in {"pokergto.odds", "pokergto.equity"} or not function:
        raise KeyError(f"derivation ref {reference!r} names a module this gate does not trust")
    return function


def check_item(path: Path) -> list[str]:
    item = json.loads(path.read_text(encoding="utf-8"))
    kind = str(item["parameters"]["kind"])
    if item["derivation_ref"] != COMPUTED.get(kind):
        return [
            f"{path.name}: derivation_ref {item['derivation_ref']!r} is not the registered source"
        ]
    resolved = _resolve(str(item["derivation_ref"]))
    recomputed, _ = _answer(kind, dict(item["parameters"]))
    stored = item["answer"].get("number")
    if stored is None:
        return [f"{path.name}: no numeric answer stored"]
    delta = abs(float(recomputed) - float(stored))
    tolerance = float((item.get("tolerance") or {}).get("absolute") or 5e-5)
    problems: list[str] = []
    if not math.isfinite(float(stored)) or delta > tolerance:
        problems.append(
            f"{path.name}: stored {stored} but {resolved} gives {float(recomputed):.8f} "
            f"(delta {delta:.2e} > {tolerance:g})"
        )
    if kind != "value-to-bluff-ratio" and not 0.0 <= float(stored) <= 1.0:
        problems.append(f"{path.name}: {stored} is not a probability")
    if kind == "value-to-bluff-ratio" and float(stored) <= 0.0:
        problems.append(f"{path.name}: ratio {stored} is not positive")
    if not item.get("provenance", {}).get("verified"):
        problems.append(f"{path.name}: a computed answer must be marked verified")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--dir", type=Path, default=QUIZ_DIR)
    args = parser.parse_args(argv)
    if not args.dir.exists():
        ok("no data/gen/quizzes yet: nothing to recompute")
        return 0
    problems: list[str] = []
    paths = sorted(args.dir.glob("quiz.*.json"))
    for path in paths:
        problems.extend(check_item(path))
    for problem in problems:
        fail(problem)
    if problems:
        print(
            "\nA quiz answer is a claim about arithmetic. If the engine no longer agrees, the item is\n"
            "wrong -- regenerate with `python tools/gen_quizzes.py`, and fix the lesson that cites the\n"
            "same formula rather than editing the artifact.",
            file=sys.stderr,
        )
        return 1
    ok(f"quiz answers: {len(paths)} items recomputed from the engine and matched")
    if args.verbose:
        for path in paths:
            print(f"  {path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
