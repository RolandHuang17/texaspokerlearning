#!/usr/bin/env python3
"""Turn authored quiz *templates* into items whose answers the engine computed.

The failure this exists to prevent is the one every poker quiz site has: a number typed into an answer
field by a person, going stale the moment the arithmetic around it is corrected, and being taught with
confidence anyway. Here an author writes a **domain** -- which quantity, over which input ranges -- and
this tool instantiates items and asks :mod:`pokergto` for the answer. There is no field in
``data/src/quizzes`` where an answer may be written, so there is nothing to go stale.

Two things are checked when an item is built, not later:

* the answer lies inside the question's own stated domain, so a nonsense prompt ("defend 130% of the
  time") cannot be generated at all;
* :func:`pokergto.artifacts.validate_artifact` accepts the artifact, and the answer records which engine
  function produced it, so ``tools/check_quiz_answers.py`` can recompute it in CI.

Usage::

    python tools/gen_quizzes.py            # write data/gen/quizzes
    python tools/gen_quizzes.py --check    # byte-compare against the committed tree
"""

from __future__ import annotations

import argparse
import random
from fractions import Fraction
from pathlib import Path
from typing import Any

from _bootstrap import REPO_ROOT, bootstrap_path, fail, ok

bootstrap_path()

from pokergto.artifacts import GEN_DIR, Provenance, write_artifact  # noqa: E402
from pokergto.equity import draw_probability  # noqa: E402
from pokergto.odds import (  # noqa: E402
    as_fraction,
    equity_needed_to_call,
    minimum_defense_frequency,
    value_to_bluff_ratio,
)

#: Committed quiz items land here; ``check_quiz_answers.py`` reads the same constant, so the gate
#: cannot be pointed at a directory this generator never writes.
QUIZ_OUT = GEN_DIR / "quizzes"

SCHEMA_VERSION = "1.0.0"
BANK = REPO_ROOT / "data" / "src" / "quizzes" / "quizzes.yaml"
#: Determinism, not variety: the bank is small, and `gen_all --check` compares bytes, so the seed is
#: part of the artifact's identity rather than a knob to be tuned.
SEED = 20261007

#: The quantities the engine can answer for. This is the whole authoring surface: an item names one of
#: these keys, and an author never supplies the resulting number.
COMPUTED: dict[str, str] = {
    "minimum-defense-frequency": "pokergto.odds#minimum_defense_frequency",
    "equity-needed-to-call": "pokergto.odds#equity_needed_to_call",
    "value-to-bluff-ratio": "pokergto.odds#value_to_bluff_ratio",
    "draw-probability": "pokergto.equity#draw_probability",
}


def _answer(kind: str, parameters: dict[str, Any]) -> tuple[Fraction, str]:
    """One place where a question becomes an arithmetic call. Anything else would be a typed answer."""
    if kind == "minimum-defense-frequency":
        bet = as_fraction(parameters["bet"])
        return (
            minimum_defense_frequency(parameters["pot"], bet, exact=True),
            f"MDF = P/(P+B) = {parameters['pot']}/({parameters['pot']}+{bet})",
        )
    if kind == "equity-needed-to-call":
        bet = as_fraction(parameters["bet"])
        return (
            equity_needed_to_call(parameters["pot"], bet, exact=True),
            f"equity needed = B/(P+2B) = {bet}/({parameters['pot']}+2*{bet})",
        )
    if kind == "value-to-bluff-ratio":
        bet = as_fraction(parameters["bet"])
        return (
            value_to_bluff_ratio(parameters["pot"], bet, exact=True),
            f"value:bluff = (P+B)/B = ({parameters['pot']}+{bet})/{bet}",
        )
    if kind == "draw-probability":
        return (
            as_fraction(
                draw_probability(
                    parameters["outs"], parameters["unseen"], parameters["cards_to_come"]
                )
            ),
            f"{parameters['outs']} outs, {parameters['cards_to_come']} card(s) to come "
            f"from {parameters['unseen']} unseen",
        )
    raise KeyError(f"no engine answer for question kind {kind!r}")


def _domain_ok(kind: str, parameters: dict[str, Any], answer: Fraction) -> str | None:
    """Refuse an item whose answer is outside the arithmetic's own stated meaning."""
    if (
        kind in {"minimum-defense-frequency", "equity-needed-to-call", "draw-probability"}
        and not 0.0 <= float(answer) <= 1.0
    ):
        return f"answer {float(answer):.4f} is not a probability"
    if kind == "value-to-bluff-ratio" and answer <= 0:
        return f"ratio {float(answer):.4f} is not positive"
    if kind == "minimum-defense-frequency" and float(answer) < 0.2:
        # Not a maths bound -- a teaching one. MDF below 20% means a bet bigger than 4x the pot, which
        # no lesson in this curriculum uses, so an item asking it would teach a number nobody can apply.
        return f"MDF {float(answer):.4f} is below the 20% floor this bank is scoped to"
    return None


def _instantiate(template: dict[str, Any], rng: random.Random, variant: int) -> dict[str, Any]:
    """One item: draw inputs from the authored domain, then let the engine answer.

    Each variant gets its own stream -- ``random.Random(f"{seed}:{variant}")`` -- rather than being the
    nth draw of one long sequence, so widening one template's domain cannot renumber or re-roll another
    template's committed items. (A version of this used ``random.Random(seed, variant)``, which is not a
    two-argument constructor: the second positional lands in ``version`` and raises. Determinism here
    needs a stable *seed value*, and hashing a string is that.)
    """
    kind = str(template["kind"])
    if kind not in COMPUTED:
        raise KeyError(f"{template['id']}: unknown question kind {kind!r}")
    parameters = {
        key: (rng.choice(values) if isinstance(values, list) else values)
        for key, values in template["domain"].items()
    }
    answer, working = _answer(kind, parameters)
    problem = _domain_ok(kind, parameters, answer)
    if problem:
        raise SystemExit(f"{template['id']} variant {variant}: {problem} ({parameters})")
    probability_valued = kind in {
        "minimum-defense-frequency",
        "equity-needed-to-call",
        "draw-probability",
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "id": f"quiz.{template['id']}-{variant:02d}",
        "lesson": template.get("lesson"),
        "type": "numeric",
        "prompt": {
            "zh": _render(str(template["prompt"]["zh"]), parameters),
            "en": _render(str(template["prompt"]["en"]), parameters),
        },
        "parameters": {**parameters, "kind": kind},
        "answer": {"number": round(float(answer), 6)},
        "tolerance": {"absolute": 5e-5, "relative": None},
        "rationale": {
            "zh": f"{working}；答案由 {COMPUTED[kind]} 算出，不是填进去的。",
            "en": f"{working}; the answer is computed by {COMPUTED[kind]}, not typed in.",
        },
        "derivation_ref": COMPUTED[kind],
        "generator": {
            "module": "tools/gen_quizzes.py",
            "function": "_answer",
            "seed": int(template.get("seed", SEED)),
        },
        "provenance": Provenance.derived(
            COMPUTED[kind],
            assumptions=[
                {
                    "en": "The item's inputs are drawn from the authored domain; no population "
                    "frequency or opponent model is involved.",
                    "zh": "题目的输入来自作者设定的取值域；不涉及任何人群频率或对手模型。",
                }
            ],
        ).to_dict(),
        "checks": [
            {
                "kind": "frequency_bounds",
                "pass": float(answer) >= 0.0 and (float(answer) <= 1.0 or not probability_valued),
                "detail": "the computed answer is inside the kind's stated range",
            }
        ],
    }


def _render(text: str, parameters: dict[str, Any]) -> str:
    out = text
    for key, raw in parameters.items():
        # A Fraction formats as "1/3"; the prompt wants the decimal a learner would type back.
        out = out.replace("{" + key + "}", f"{float(raw) if isinstance(raw, Fraction) else raw:g}")
    return out


def build(bank: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for template in bank["templates"]:
        base = int(template.get("seed", SEED))
        for index in range(int(template.get("variants", 1))):
            items.append(_instantiate(template, random.Random(f"{base}:{index:02d}"), index))
    ids = [item["id"] for item in items]
    if len(set(ids)) != len(ids):
        raise SystemExit("duplicate quiz id generated; a template id is reused")
    return items


def generate(out: Path) -> list[Path]:
    import yaml

    if not BANK.exists():
        return []
    bank = yaml.safe_load(BANK.read_text(encoding="utf-8"))
    written: list[Path] = []
    for item in build(bank):
        path = out / "quizzes" / f"{item['id']}.json"
        write_artifact(path, item, schema="quiz")
        written.append(path)
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--out", type=Path, default=GEN_DIR)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if args.check:
        import filecmp
        import tempfile

        with tempfile.TemporaryDirectory(prefix="quizzes-") as tmp:
            produced = generate(Path(tmp))
            for path in produced:
                counterpart = args.out / "quizzes" / path.name
                if not counterpart.exists() or not filecmp.cmp(counterpart, path, shallow=False):
                    fail(f"{path.name} differs from the committed quiz item")
                    return 1
        ok(f"quiz items: {len(produced)} byte-identical")
        return 0
    written = generate(args.out)
    if not written:
        ok("no data/src/quizzes/quizzes.yaml yet: nothing to generate")
        return 0
    ok(f"gen_quizzes: wrote {len(written)} items")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
