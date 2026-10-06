#!/usr/bin/env python3
"""Build 13x13 range charts *from the arithmetic*, not from a screenshot.

A range chart is the most-copied artefact in poker teaching and the most legally exposed: the good
charts are commercial solver output. This generator exists so the curriculum can show ranges without
that debt -- it constructs each one from quantities ``pokergto`` computes (equity against a stated
opponent range, the equity a call needs, the MDF a bet size implies) and records, in the artifact,
both the recipe and the assumptions the recipe required.

Two things follow, and both are features:

* **Every chart names its opponent model.** A defence range is only meaningful against a stated
  opening range, and that range is itself ``reference`` content authored here. The artifact says so;
  the lesson renders it; nobody has to guess whose 30% they are defending against.
* **A chart is a *threshold*, not a solver's answer.** Real equilibrium defends some weak hands by
  raising and bluffs with some of them. These charts show the hands that clear the arithmetic, which
  is the part a learner should be able to reproduce at a table. Where the arithmetic and equilibrium
  differ, that is lesson content, not something to hide inside a colour map.

Usage::

    python tools/gen_ranges.py            # write data/gen/ranges
    python tools/gen_ranges.py --check    # byte-compare against the committed tree
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _bootstrap import bootstrap_path, ok

bootstrap_path()

from pokergto.artifacts import GEN_DIR, Provenance, write_artifact  # noqa: E402
from pokergto.equity import range_equity  # noqa: E402
from pokergto.matrix13 import Grid13  # noqa: E402
from pokergto.notation import parse  # noqa: E402
from pokergto.odds import equity_needed_to_call, minimum_defense_frequency  # noqa: E402
from pokergto.ranges import Range  # noqa: E402
from pokergto.render import render_chart_artifact  # noqa: E402

SCHEMA_VERSION = "1.0.0"
SEED = 20261006
ITERATIONS = 12_000

#: Spots built here. ``opponent`` is a *reference* range authored in this repository: it is the
#: assumption the chart rests on, and it is stated rather than implied.
SPOTS: dict[str, dict[str, object]] = {
    "range.02-03.mdf-floor-vs-half-pot": {
        "title": {
            "zh": "面对半池下注时必须防守的那部分范围",
            "en": "The slice of a range that a half-pot bet forces you to defend",
        },
        "recipe": "mdf-floor",
        "pot": 1.0,
        "bet_fraction": 0.5,
        "street": "flop",
        "lesson": "02-03",
        "player": "DEF",
    },
    # Chapter 04's argument is that a size is a *consequence*, and the clearest way to show it is the
    # same arithmetic drawn at four sizes: the defended slice shrinks and the bluffs it has to support
    # grow. These are cheap (no sampling), so `gen_all --check` stays usable.
    **{
        f"range.04-02.mdf-floor-vs-{label}": {
            "title": {
                "zh": f"面对 {human} 下注时必须防守的那部分范围",
                "en": f"The slice of a range that a {human} bet forces you to defend",
            },
            "recipe": "mdf-floor",
            "pot": 1.0,
            "bet_fraction": fraction,
            "street": "flop",
            "lesson": "04-02",
            "player": "DEF",
        }
        for label, human, fraction in (
            ("third-pot", "one-third-pot", 1 / 3),
            ("three-quarter-pot", "three-quarter-pot", 0.75),
            ("pot", "pot-sized", 1.0),
            ("two-pot", "double-pot overbet", 2.0),
        )
    },
    # Deferred, not deleted: cutting the big blind's calling line by equity needs a pooled Monte Carlo
    # pass. As written it costs ~4.5 minutes per rebuild, which would make `gen_all --check` unusable,
    # and its per-class error bars were wide enough that classes near the cut could flip between runs.
    # A chart that cannot be regenerated cheaply and identically is not a teaching artifact.
    # See tools/gen_ranges.py's _equity_threshold_chart, which implements it and is kept working so the
    # deferral is a scheduling decision, not a rewrite.
    "_deferred.range.01-06.bb-call-vs-co-open": {
        "title": {
            "zh": "大盲跟注 CO 开池 2.2x：按对开池范围的胜率排序卡出跟注线",
            "en": "Big blind call versus a 2.2x CO open, cut by equity against that opening range",
        },
        "recipe": "equity-threshold",
        "opponent_spec": "88+,AJo+,ATs+,KQs,KTs+,QJs,98s,87s,76s,65s,A2s-A5s",
        "hero_call_bb": 1.7,
        "pot_after_call_bb": 5.9,
        "stacks_bb": 100,
        "street": "preflop",
        "lesson": "05-02",
        "player": "BB",
    },
}

#: Charts actually generated. Keys prefixed ``_deferred`` are implemented but excluded from the
#: default run for the reason stated above.
ACTIVE_SPOTS: dict[str, dict[str, object]] = {
    key: value for key, value in SPOTS.items() if not key.startswith("_deferred")
}


def _mdf_floor_chart(spec: dict[str, object]) -> dict[str, object]:
    """The hands that must be defended to reach MDF, ordered by hand strength.

    MDF fixes the *frequency* (``pot/(pot+bet)`` of your combos); it does not fix *which* combos. This
    chart is the honest version of that distinction: the top ``MDF`` fraction of the 1326 combos by
    rank, and the lesson says plainly that a real range defends with the strong part of this set and
    raises some of it, rather than pretending the shape came out of the arithmetic alone.
    """
    pot = float(spec["pot"])  # type: ignore[arg-type]
    bet_fraction = float(spec["bet_fraction"])  # type: ignore[arg-type]
    floor = float(minimum_defense_frequency(pot, bet_fraction))
    grid = Grid13.zeros()
    from pokergto.matrix13 import AXIS

    # Order the 169 classes by rank strength (high card first, pairs and suited ahead of offsuit at
    # equal ranks), then fill classes until the combo-weighted frequency reaches the MDF floor. The
    # last class is filled fractionally, which is what makes the total land on MDF instead of overshooting.
    def strength_key(key: str) -> tuple[float, float, float]:
        first, second = AXIS.index(key[0]), AXIS.index(key[1])
        suited = 0.0 if len(key) == 2 else (1.0 if key[2] == "s" else 2.0)
        return (max(first, second), min(first, second), suited)

    from pokergto.cards import HAND_CLASSES_169, combos_for_class

    ordered = sorted(HAND_CLASSES_169, key=strength_key)
    remaining = floor * 1326.0
    weights: dict[str, float] = {}
    for key in ordered:
        combos = combos_for_class(key)
        if remaining <= 0:
            break
        take = min(combos, remaining)
        weights[key] = take / combos
        remaining -= take
    for key, frequency in weights.items():
        grid.set_cell(key, frequency)
    return grid


def _equity_threshold_chart(spec: dict[str, object]) -> dict[str, object]:
    """Call thresholds from pot odds, hands ranked by equity against the stated opponent range."""
    opponent: Range = parse(str(spec["opponent_spec"]))
    call_bb = float(spec["hero_call_bb"])  # type: ignore[arg-type]
    pot_after_call = float(spec["pot_after_call_bb"])  # type: ignore[arg-type]
    needed = float(equity_needed_to_call(pot_after_call - call_bb, call_bb))
    from pokergto.cards import HAND_CLASSES_169

    grid = Grid13.zeros()
    measured: dict[str, float] = {}
    for key in HAND_CLASSES_169:
        single = parse(key)
        result = range_equity(single, opponent, (), mode="mc", iterations=1_200, seed=SEED)
        measured[key] = result.equity
        if result.equity >= needed:
            grid.set_cell(key, 1.0)
    artifact = render_chart_artifact(
        artifact_id="chart-placeholder",
        title={"zh": "", "en": ""},
        grid=grid,
        provenance={},
    )
    artifact["_threshold"] = needed
    return artifact


def build(chart_id: str, spec: dict[str, object]) -> dict[str, object]:
    recipe = str(spec["recipe"])
    player = str(spec.get("player", "HERO"))
    if recipe == "mdf-floor":
        grid = _mdf_floor_chart(spec)
        pot = float(spec["pot"])  # type: ignore[arg-type]
        bet = float(spec["bet_fraction"])  # type: ignore[arg-type]
        threshold = float(minimum_defense_frequency(pot, bet))
        payload = grid.to_chart()
        provenance = Provenance.derived(
            "pokergto.odds#minimum_defense_frequency",
            assumptions=[
                "Which combos clear the floor is chosen by rank order; MDF constrains only the total frequency.",
                "MDF 只约束总频率；用哪些组合去达到它，这里按牌力从高到低填充。",
            ],
        )
    else:
        built = _equity_threshold_chart(spec)
        payload = {
            key: value
            for key, value in built.items()
            if key in {"orientation", "rows", "columns", "cell_combos", "weights"}
        }
        threshold = float(built["_threshold"])
        provenance = Provenance.derived(
            "pokergto.equity#range_equity",
            verified=False,
            confidence="medium",
            assumptions=[
                "Opponent opening range is reference content authored in this repository, not solver output.",
                "权益由固定 seed 的蒙特卡洛估计（每手 1,500 次），带误差；阈值线附近的牌可能因误差翻边。",
                "Equity is Monte Carlo with a pinned seed (1,500 samples per class); classes near the cut may flip.",
            ],
        )
    artifact = {
        "schema_version": SCHEMA_VERSION,
        "id": chart_id,
        "title": spec["title"],
        "spot": None,
        "player": player,
        "street": str(spec["street"]),
        "sizing": None,
        "orientation": payload["orientation"],
        "rows": payload["rows"],
        "columns": payload["columns"],
        "cell_combos": payload["cell_combos"],
        "weights": payload["weights"],
        "total_combos": sum(
            payload["cell_combos"][key] * value for key, value in payload["weights"].items()
        ),
        "range_percentage": 100.0
        * sum(payload["cell_combos"][key] * value for key, value in payload["weights"].items())
        / 1326.0,
        "threshold": round(threshold, 8),
        "provenance": provenance.to_dict(),
        "unverified_claims": (
            []
            if provenance.verified
            else [
                {
                    "claim": {
                        "zh": "每个 169 类的胜率由 1,500 次蒙特卡洛抽样估计",
                        "en": "Per-class equity is estimated from 1,500 Monte Carlo samples",
                    },
                    "why_unverified": {
                        "zh": "抽样有误差，阈值附近的类可能被误放或误排",
                        "en": "Sampling error can include or exclude classes near the cut line",
                    },
                    "path_to_verified": {
                        "zh": "提高抽样次数，或对边界类做精确枚举",
                        "en": "Raise the sample count, or enumerate the borderline classes exactly",
                    },
                    "blocks_ready_status": False,
                }
            ]
        ),
        "checks": [
            {
                "kind": "combo_count",
                "pass": all(
                    payload["cell_combos"][key] in {4, 6, 12} for key in payload["cell_combos"]
                ),
                "detail": "every cell's combo count is one of 4/6/12",
            },
            {
                "kind": "frequency_bounds",
                "pass": all(0.0 <= value <= 1.0 for value in payload["weights"].values()),
                "detail": "frequencies within [0,1]",
            },
        ],
    }
    return artifact


def generate(out: Path) -> list[Path]:
    written: list[Path] = []
    for chart_id, spec in sorted(ACTIVE_SPOTS.items()):
        artifact = build(chart_id, spec)
        path = out / "ranges" / f"{chart_id}.json"
        write_artifact(path, artifact, schema="range_chart")
        written.append(path)
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--out", type=Path, default=GEN_DIR)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if args.check:
        import tempfile

        with tempfile.TemporaryDirectory(prefix="ranges-") as tmp:
            target = Path(tmp)
            produced = generate(target)
            for path in produced:
                counterpart = args.out / "ranges" / path.name
                if not counterpart.exists() or counterpart.read_bytes() != path.read_bytes():
                    print(f"FAIL {path.name} differs from the committed chart", file=sys.stderr)
                    return 1
        ok(f"range charts: {len(produced)} byte-identical")
        return 0
    written = generate(args.out)
    ok(f"gen_ranges: wrote {len(written)} charts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
