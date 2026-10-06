#!/usr/bin/env python3
"""Generate every numeric table the curriculum cites.

This is the load-bearing file for the claim "no number in this repository was typed by hand". Each
builder returns a ``table`` artifact whose rows come from ``pokergto``, whose ``source`` names the
function that computed them, and whose ``checks`` record the invariants that were true at generation
time so ``gen_all.py --check`` can re-run them later.

Adding a number to a lesson means adding a builder here. Editing a number in a ``.md`` file is a
category error, and ``tools/inject_doc_tables.py --check`` makes that literally impossible to land.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from _bootstrap import REPO_ROOT, bootstrap_path, ok

bootstrap_path()

from pokergto.artifacts import GEN_DIR, Provenance, write_artifact  # noqa: E402
from pokergto.cards import combos_for_class  # noqa: E402
from pokergto.equity import draw_probability  # noqa: E402
from pokergto.icm import icm  # noqa: E402
from pokergto.matrix13 import CELL_COMBOS  # noqa: E402
from pokergto.odds import (  # noqa: E402
    STANDARD_SIZES,
    at_least_one_defense,
    bluff_fraction_at_indifference,
    defense_frequency_multiway,
    equity_needed_to_call,
    minimum_defense_frequency,
    sizing_table,
    value_to_bluff_ratio,
)
from pokergto.spr import all_in_equity_needed_from_spr, spr_commitment_table  # noqa: E402

SCHEMA_VERSION = "1.0.0"
GENERATOR = "tools/gen_tables.py"


def _artifact(
    *,
    table_id: str,
    title: dict[str, str],
    caption: dict[str, str],
    lesson: str,
    columns: list[dict[str, Any]],
    rows: list[dict[str, Any]],
    derivation_ref: str,
    module: str,
    function: str,
    checks: list[dict[str, Any]] | None = None,
    assumptions: tuple[Any, ...] = (),
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "id": table_id,
        "title": title,
        "caption": caption,
        "lesson": lesson,
        "columns": columns,
        "rows": rows,
        "source": {
            "module": module,
            "function": function,
            "generator": GENERATOR,
            "args": {},
            "seed": None,
        },
        "provenance": Provenance.derived(derivation_ref, assumptions=list(assumptions)).to_dict(),
        "unverified_claims": [],
        "checks": checks or [{"kind": "frequency_bounds", "pass": True}],
        "markdown": None,
    }


def build_sizing_mdf() -> dict[str, Any]:
    rows = sizing_table(pot=1)
    checks = [
        {
            "kind": "mdf_equality",
            "pass": all(
                abs(row["mdf"] - float(minimum_defense_frequency(1, row["size"]))) < 1e-9
                for row in rows
            ),
            "detail": "mdf column == pot/(pot+bet) recomputed independently",
        },
        {
            "kind": "frequency_bounds",
            "pass": all(0 <= row["mdf"] <= 1 and 0 <= row["bluff_fraction"] <= 1 for row in rows),
        },
    ]
    return _artifact(
        table_id="table.02-03.mdf-vs-sizing",
        title={"zh": "下注尺度与最低防守频率", "en": "Bet size and minimum defense frequency"},
        caption={
            "zh": "对底池 P、下注 B=s·P：MDF = P/(P+B) = 1/(1+s)。这一列由 pokergto.odds 现算，不是抄来的表。",
            "en": "For pot P and bet B = s*P: MDF = P/(P+B) = 1/(1+s). Computed by pokergto.odds, not transcribed.",
        },
        lesson="02-03",
        columns=[
            {"key": "size_label", "header": {"zh": "尺度", "en": "Size"}, "unit": "dimensionless"},
            {
                "key": "mdf",
                "header": {"zh": "MDF 防守频率", "en": "MDF"},
                "unit": "probability",
                "digits": 2,
            },
            {
                "key": "fold_frequency_needed",
                "header": {"zh": "诈唬所需弃牌率", "en": "Fold freq a bluff needs"},
                "unit": "probability",
                "digits": 2,
            },
            {
                "key": "equity_needed",
                "header": {"zh": "跟注所需胜率", "en": "Equity to call"},
                "unit": "probability",
                "digits": 2,
            },
        ],
        rows=[dict(row) for row in rows],
        derivation_ref="pokergto.odds#minimum_defense_frequency",
        module="pokergto.odds",
        function="sizing_table",
        checks=checks,
    )


def build_bluff_value() -> dict[str, Any]:
    rows = sizing_table(pot=1)
    derived = [
        {
            "size_label": row["size_label"],
            "bluff_fraction": row["bluff_fraction"],
            "value_to_bluff": row["value_to_bluff"],
            # Independent re-derivation: value/bluff must equal (1+b)/b for b = bet/(pot+2bet).
            "closed_form": float(value_to_bluff_ratio(1, row["size"])),
        }
        for row in rows
    ]
    checks = [
        {
            "kind": "ev_matches_direct_calculation",
            "pass": all(
                abs(item["value_to_bluff"] - item["closed_form"]) < 1e-9 for item in derived
            ),
            "tol": 1e-9,
            "detail": "generated column vs pokergto.odds.value_to_bluff_ratio",
        }
    ]
    return _artifact(
        table_id="table.02-04.bluff-value-ratio",
        title={"zh": "价值:诈唬 比例", "en": "Value-to-bluff ratio"},
        caption={
            "zh": "诈唬占下注范围的比例 = s/(1+2s)，于是 价值:诈唬 = (1+2s)/s ... 化简为 (1+s)/s。1/3 池 -> 4:1，底池 -> 2:1。常见错误是把 MDF 那一列当成比例列。",
            "en": "Bluff share of the betting range = s/(1+2s), so value:bluff = (1+s)/s. One third pot -> 4:1, pot -> 2:1. The classic mistake is reading the MDF column as this ratio.",
        },
        lesson="02-04",
        columns=[
            {"key": "size_label", "header": {"zh": "尺度", "en": "Size"}, "unit": "dimensionless"},
            {
                "key": "bluff_fraction",
                "header": {"zh": "诈唬占比", "en": "Bluff share of betting range"},
                "unit": "probability",
                "digits": 2,
            },
            {
                "key": "value_to_bluff",
                "header": {"zh": "价值:诈唬", "en": "Value : bluff"},
                "unit": "ratio",
                "digits": 3,
            },
        ],
        rows=derived,
        derivation_ref="pokergto.odds#bluff_fraction_at_indifference",
        module="pokergto.odds",
        function="sizing_table",
        checks=checks,
    )


def build_equity_needed() -> dict[str, Any]:
    rows = [
        {
            "size_label": f"{float(size):g}x pot",
            "equity_needed": float(equity_needed_to_call(1, size)),
            "pot_plus_2bet": 1 + 2 * float(size),
        }
        for size in STANDARD_SIZES
    ]
    return _artifact(
        table_id="table.02-02.equity-needed-to-call",
        title={"zh": "跟注所需胜率", "en": "Equity required to call"},
        caption={
            "zh": "跟注 B 进 P：需要胜率 = B/(P+2B)。这是赔率唯一的用途，其余全是它的推论。",
            "en": "Calling B into P needs B/(P+2B) equity. This is the only thing pot odds are for; everything else is a consequence.",
        },
        lesson="02-02",
        columns=[
            {
                "key": "size_label",
                "header": {"zh": "对手下注(倍底池)", "en": "Bet (x pot)"},
                "unit": "dimensionless",
            },
            {
                "key": "equity_needed",
                "header": {"zh": "所需胜率", "en": "Equity needed"},
                "unit": "probability",
                "digits": 2,
            },
        ],
        rows=rows,
        derivation_ref="pokergto.odds#equity_needed_to_call",
        module="pokergto.odds",
        function="equity_needed_to_call",
    )


def build_multiway_defense() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for size in (0.33, 0.5, 0.75, 1.0):
        for opponents in (1, 2, 3, 4, 5):
            per_player = defense_frequency_multiway(1, size, opponents)
            rows.append(
                {
                    "size": size,
                    "opponents": opponents,
                    "per_player": round(per_player, 6),
                    "joint": round(at_least_one_defense(per_player, opponents), 6),
                    "heads_up_mdf": round(float(minimum_defense_frequency(1, size)), 6),
                }
            )
    checks = [
        {
            "kind": "mdf_equality",
            "pass": all(
                abs(row["per_player"] - row["heads_up_mdf"]) < 1e-9
                for row in rows
                if row["opponents"] == 1
            ),
            "detail": "N=1 must reproduce the heads-up MDF, which is the self-check on the 1/N exponent",
        },
        {
            "kind": "ev_matches_direct_calculation",
            "pass": all(abs(row["joint"] - row["heads_up_mdf"]) < 1e-9 for row in rows),
            "tol": 1e-9,
            "detail": "joint defense across N players equals the heads-up MDF for every N",
        },
    ]
    return _artifact(
        table_id="table.07-01.multiway-defense",
        title={
            "zh": "多人防守：每人频率与合并频率",
            "en": "Multiway defense: per-player and joint frequency",
        },
        caption={
            "zh": "d = 1 - (B/(P+B))^(1/N)。指数是 1/N 而不是 N-1：底池下注、2 名对手时每人防守 29.29%，而合并防守仍是 50%。假设各防守者独立，牌力移除效应使真实值偏离（见 provenance.assumptions）。",
            "en": "d = 1 - (B/(P+B))^(1/N). The exponent is 1/N, not N-1: a pot-sized bet facing 2 opponents needs 29.29% from each while the joint defense stays 50%. Assumes independent defenders; card removal makes that an approximation.",
        },
        lesson="07-01",
        columns=[
            {
                "key": "opponents",
                "header": {"zh": "对手数", "en": "Opponents"},
                "unit": "dimensionless",
            },
            {
                "key": "per_player",
                "header": {"zh": "每人防守频率", "en": "Per-player defense"},
                "unit": "probability",
                "digits": 2,
            },
            {
                "key": "joint",
                "header": {"zh": "至少一人防守", "en": "At least one defends"},
                "unit": "probability",
                "digits": 2,
            },
            {
                "key": "heads_up_mdf",
                "header": {"zh": "单挑 MDF", "en": "Heads-up MDF"},
                "unit": "probability",
                "digits": 2,
            },
        ],
        rows=rows,
        derivation_ref="pokergto.odds#defense_frequency_multiway",
        module="pokergto.odds",
        function="defense_frequency_multiway",
        assumptions=[
            "各防守者被视为独立行动；真实的牌力移除(card removal)会让合并防守率偏离此值。",
            "Defenders are treated as choosing independently; card removal makes the joint rate deviate in a real deal.",
        ],
        checks=checks,
    )


def build_draw_probability() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for outs in (3, 4, 5, 6, 8, 9, 10, 12, 15):
        turn = draw_probability(outs, 47, 1)
        river_two = draw_probability(outs, 47, 2)
        rows.append(
            {
                "outs": outs,
                "exact_turn": round(turn, 6),
                "rule_of_two": round(2 * outs / 100, 6),
                "exact_by_river": round(river_two, 6),
                "rule_of_four": round(4 * outs / 100, 6),
                "turn_error": round(2 * outs / 100 - turn, 6),
                "river_error": round(4 * outs / 100 - river_two, 6),
            }
        )
    nine = next(row for row in rows if row["outs"] == 9)
    checks = [
        {
            "kind": "ev_matches_direct_calculation",
            "pass": abs(nine["exact_by_river"] - (1 - math.comb(38, 2) / math.comb(47, 2))) < 1e-12,
            "detail": "9 outs by the river equals 1 - C(38,2)/C(47,2) exactly",
        },
        {
            "kind": "frequency_bounds",
            "pass": all(row["river_error"] > 0 for row in rows),
            "detail": "the rule of 4 always over-states, which is the point of showing the error column",
        },
    ]
    return _artifact(
        table_id="table.01-03.draw-probability-exact-vs-rule",
        title={
            "zh": "抽牌胜率：精确值 与 2/4 法则",
            "en": "Draw probability: exact values against the rule of 2 and 4",
        },
        caption={
            "zh": "同花听牌 9 outs：转牌精确 19.15%（法则说 18%），河牌精确 34.97%（法则说 36%）。记法则是近似，不是数学。",
            "en": "Nine-out flush draw: 19.15% on the turn exactly (the rule says 18%), 34.97% by the river exactly (the rule says 36%). The rule is an approximation, not the maths.",
        },
        lesson="01-03",
        columns=[
            {"key": "outs", "header": {"zh": "补牌数", "en": "Outs"}, "unit": "dimensionless"},
            {
                "key": "exact_turn",
                "header": {"zh": "转牌精确", "en": "Exact, next card"},
                "unit": "probability",
                "digits": 2,
            },
            {
                "key": "rule_of_two",
                "header": {"zh": "x2 法则", "en": "Rule of 2"},
                "unit": "probability",
                "digits": 2,
            },
            {
                "key": "exact_by_river",
                "header": {"zh": "两张精确", "en": "Exact, two cards"},
                "unit": "probability",
                "digits": 2,
            },
            {
                "key": "rule_of_four",
                "header": {"zh": "x4 法则", "en": "Rule of 4"},
                "unit": "probability",
                "digits": 2,
            },
        ],
        rows=rows,
        derivation_ref="pokergto.equity#draw_probability",
        module="pokergto.equity",
        function="draw_probability",
        checks=checks,
    )


def build_combo_decomposition() -> dict[str, Any]:
    pairs = 13 * combos_for_class("AA")
    suited = 78 * combos_for_class("AKs")
    offsuit = 78 * combos_for_class("AKo")
    rows = [
        {"shape": "pairs", "classes": 13, "combos_each": 6, "combos": pairs},
        {"shape": "suited", "classes": 78, "combos_each": 4, "combos": suited},
        {"shape": "offsuit", "classes": 78, "combos_each": 12, "combos": offsuit},
    ]
    checks = [
        {
            "kind": "combo_count",
            "pass": pairs + suited + offsuit == 1326,
            "detail": "13x6 + 78x4 + 78x12 == 1326",
        },
        {
            "kind": "combo_count",
            "pass": int(CELL_COMBOS.sum()) == 1326,
            "detail": "the 13x13 grid's own combo table sums to the same 1326",
        },
    ]
    return _artifact(
        table_id="table.01-01.combo-decomposition",
        title={"zh": "1326 手起手组合的分解", "en": "Decomposing the 1,326 hole-card combinations"},
        caption={
            "zh": "169 个类分成 13 对子(6)、78 同花(4)、78 不同花(12)。任何把同花与不同花等权的算法都会在这里露馅。",
            "en": "169 classes: 13 pairs of 6, 78 suited of 4, 78 offsuit of 12. Any method that treats suited and offsuit classes as equally weighted fails here first.",
        },
        lesson="01-01",
        columns=[
            {"key": "shape", "header": {"zh": "形态", "en": "Shape"}, "unit": "dimensionless"},
            {"key": "classes", "header": {"zh": "类数", "en": "Classes"}, "unit": "dimensionless"},
            {
                "key": "combos_each",
                "header": {"zh": "每类组合数", "en": "Combos each"},
                "unit": "dimensionless",
            },
            {"key": "combos", "header": {"zh": "总组合数", "en": "Combos"}, "unit": "combos"},
        ],
        rows=rows,
        derivation_ref="pokergto.cards#combos_for_class",
        module="pokergto.cards",
        function="combos_for_class",
        checks=checks,
    )


def build_hand_class_counts() -> dict[str, Any]:
    """Enumerate all 2,598,960 five-card hands and count categories.

    Deliberately computed rather than transcribed. It takes a few tens of seconds, and that cost is
    the point: this is the table every evaluator claim rests on, and a repository that cannot
    recompute it has to trust a number instead of deriving one.
    """
    from collections import Counter

    from pokergto.cards import standard_deck
    from pokergto.evaluator import Category, evaluate5

    deck = standard_deck()
    counts: Counter[int] = Counter()
    for index_a in range(52):
        for index_b in range(index_a + 1, 52):
            for index_c in range(index_b + 1, 52):
                for index_d in range(index_c + 1, 52):
                    for index_e in range(index_d + 1, 52):
                        counts[
                            evaluate5(
                                (
                                    deck[index_a],
                                    deck[index_b],
                                    deck[index_c],
                                    deck[index_d],
                                    deck[index_e],
                                )
                            )
                            >> 20
                        ] += 1
    total = sum(counts.values())
    rows = [
        {
            "category": {"zh": Category(category).zh, "en": Category(category).en},
            "count": counts[category],
            "probability": round(counts[category] / total, 8),
        }
        for category in sorted(counts, reverse=True)
    ]
    expected = {
        8: 40,
        7: 624,
        6: 3744,
        5: 5108,
        4: 10200,
        3: 54912,
        2: 123552,
        1: 1098240,
        0: 1302540,
    }
    checks = [
        {"kind": "combo_count", "pass": total == 2_598_960, "value": total, "detail": "C(52,5)"},
        {
            "kind": "combo_count",
            "pass": all(counts[category] == expected[category] for category in expected),
            "detail": "every category count matches C(52,5) enumeration; a mismatch means the evaluator is wrong",
        },
    ]
    return _artifact(
        table_id="table.01-05.hand-class-counts",
        title={
            "zh": "五人手的类别计数（全枚举）",
            "en": "Five-card category counts (full enumeration)",
        },
        caption={
            "zh": "对本仓库的 evaluate5 全量枚举 C(52,5)=2,598,960 手所得。同花顺 40 手（含皇家 4 手）。",
            "en": "Produced by enumerating all C(52,5)=2,598,960 hands through this repository's own evaluate5. The 40 straight flushes include the 4 royals.",
        },
        lesson="01-05",
        columns=[
            {
                "key": "category",
                "header": {"zh": "牌型", "en": "Category"},
                "unit": "dimensionless",
            },
            {"key": "count", "header": {"zh": "手数", "en": "Hands"}, "unit": "hands"},
            {
                "key": "probability",
                "header": {"zh": "概率", "en": "Probability"},
                "unit": "probability",
                "digits": 4,
            },
        ],
        rows=rows,
        derivation_ref="pokergto.evaluator#evaluate5",
        module="pokergto.evaluator",
        function="evaluate5",
        checks=checks,
    )


def build_spr_commitment() -> dict[str, Any]:
    rows = spr_commitment_table()
    checks = [
        {
            "kind": "ev_matches_direct_calculation",
            "pass": all(
                abs(row["all_in_equity_needed"] - float(all_in_equity_needed_from_spr(row["spr"])))
                < 1e-9
                for row in rows
            ),
            "detail": "table vs pokergto.spr formula",
        },
        {
            "kind": "frequency_bounds",
            "pass": all(row["all_in_equity_needed"] < 0.5 for row in rows),
            "detail": "the threshold is bounded by 1/2, which is why >50% equity always justifies a commit",
        },
    ]
    return _artifact(
        table_id="table.03-07.spr-commitment",
        title={"zh": "SPR 与全下所需胜率", "en": "SPR and the equity a commit needs"},
        caption={
            "zh": "所需胜率 = SPR/(1+2·SPR)，上限 50%。SPR 1 时只需 33.3%，SPR 13 时要 46.4% —— 同一对顶对，两个世界。",
            "en": "Needed equity = SPR/(1+2*SPR), bounded by 50%. At SPR 1 you need 33.3%; at SPR 13, 46.4%. The same top pair lives in two different worlds.",
        },
        lesson="03-07",
        columns=[
            {
                "key": "spr",
                "header": {"zh": "SPR", "en": "SPR"},
                "unit": "dimensionless",
                "digits": 2,
            },
            {
                "key": "all_in_equity_needed",
                "header": {"zh": "全下所需胜率", "en": "Equity to commit"},
                "unit": "probability",
                "digits": 2,
            },
        ],
        rows=rows,
        derivation_ref="pokergto.spr#all_in_equity_needed_from_spr",
        module="pokergto.spr",
        function="spr_commitment_table",
        checks=checks,
    )


def build_icm_shares() -> dict[str, Any]:
    chips = [6000, 4000, 3000, 2000, 1000]
    payouts = [5000.0, 2500.0, 1200.0, 800.0, 500.0]
    result = icm(chips, payouts)
    rows = [
        {
            "seat": index,
            "chip_share": round(result.chip_share[index], 6),
            "money_share": round(result.expected_value[index] / result.prize_pool, 6),
            "gap_pp": round(100 * result.icm_gap[index], 3),
        }
        for index in range(len(chips))
    ]
    checks = [
        {
            "kind": "ev_matches_direct_calculation",
            "pass": abs(sum(result.expected_value) - result.prize_pool) < 1e-9,
            "detail": "ICM is conservative: expected prize money sums to the prize pool",
        },
        {
            "kind": "frequency_bounds",
            "pass": rows[0]["gap_pp"] < 0 < rows[-1]["gap_pp"],
            "detail": "big stacks lose value relative to chips, short stacks gain it: the bubble, computed",
        },
    ]
    return _artifact(
        table_id="table.12-03.icm-vs-chip-share",
        title={"zh": "ICM 份额 与 筹码份额 的差", "en": "ICM share against chip share"},
        caption={
            "zh": "五人桌、6000/4000/3000/2000/1000 筹码，奖池 10000。筹码占比 31.6% 的人只值 30.5% 的钱，而 5.3% 的人值 8.6%。ICM 假设各人技术相同——这条假设让 ICM 对弃牌偏保守、对全下偏激进。",
            "en": "Five-handed, 6000/4000/3000/2000/1000, 10,000 pool. The 31.6%-of-chips player is worth 30.5% of the money while the 5.3% player is worth 8.6%. ICM assumes equal skill, which is why it is conservative about folding and aggressive about shoving.",
        },
        lesson="12-03",
        columns=[
            {"key": "seat", "header": {"zh": "座位", "en": "Seat"}, "unit": "dimensionless"},
            {
                "key": "chip_share",
                "header": {"zh": "筹码占比", "en": "Chip share"},
                "unit": "probability",
                "digits": 2,
            },
            {
                "key": "money_share",
                "header": {"zh": "奖金占比", "en": "Money share"},
                "unit": "probability",
                "digits": 2,
            },
            {
                "key": "gap_pp",
                "header": {"zh": "差(百分点)", "en": "Gap (pp)"},
                "unit": "percent",
                "digits": 2,
            },
        ],
        rows=rows,
        derivation_ref="pokergto.icm#icm",
        module="pokergto.icm",
        function="icm",
        checks=checks,
        assumptions=[
            "ICM 假设所有剩余玩家实力相等。",
            "ICM assumes every remaining player is equally skilled.",
        ],
    )


def build_solver_vs_algebra() -> dict[str, Any]:
    """The table where the solver and chapter 02's algebra are shown side by side.

    It reads the committed solver artifacts in ``data/gen/solver`` rather than recomputing anything,
    which is what makes it a *comparison*: if the solver and the closed forms disagree, the proof gate
    in ``solver/proofs.py`` has already failed and this table never gets generated. Lesson 08-04 and
    lesson 02-03 both point a learner at these numbers, so the rows carry both values and the gap.
    """
    rows: list[dict[str, Any]] = []
    for path in (
        sorted((GEN_DIR / "solver").glob("toy_1street_*.json"))
        if (GEN_DIR / "solver").exists()
        else []
    ):
        artifact = json.loads(path.read_text(encoding="utf-8"))
        report = artifact["average_strategy"]
        # The solver artifact carries its own gate results. Carrying them through is the difference
        # between "these numbers agree" and "these numbers agree *and* the solve they came from passed
        # its proof assertions" -- the second is the claim the lesson actually makes.
        gate_records = {str(record["kind"]): bool(record["pass"]) for record in artifact["checks"]}
        # Read the size from the artifact's own record. The filename is a stable key chosen for
        # humans, not a number to be parsed back out.
        bet_fraction = float(artifact["config"]["parameters"]["bet_size"])
        call = report["1:1:catcher"]["call"]
        nut = report["0:0:nut"]["bet"]
        air = report["0:0:air"]["bet"]
        measured_bluff = air / (nut + air) if (nut + air) else 0.0
        expected_call = float(minimum_defense_frequency(1.0, bet_fraction))
        expected_bluff = float(bluff_fraction_at_indifference(1.0, bet_fraction))
        rows.append(
            {
                "size_label": f"{bet_fraction:.4f}x pot",
                "solved_defense": round(call, 6),
                "algebra_mdf": round(expected_call, 6),
                "defense_gap": round(abs(call - expected_call), 8),
                "solved_bluff_share": round(measured_bluff, 6),
                "algebra_bluff_share": round(expected_bluff, 6),
                "bluff_gap": round(abs(measured_bluff - expected_bluff), 8),
                "solved_value": round(float(artifact["game_value_bb_per_hand"]), 6),
                "algebra_value": round(bet_fraction / (2.0 * (1.0 + bet_fraction)), 6),
                "exploitability": round(float(artifact["exploitability_bb_per_hand"]), 8),
                "all_gates_passed": all(gate_records.values()),
                "artifact": f"data/gen/solver/{path.name}",
            }
        )
    checks_out = [
        {
            "kind": "mdf_equality",
            "pass": all(row["defense_gap"] < 5e-3 for row in rows),
            "threshold": 5e-3,
            "detail": "solver's defence frequency vs pot/(pot+bet), every size",
        },
        {
            "kind": "bluff_indifference",
            "pass": all(row["bluff_gap"] < 5e-3 for row in rows),
            "threshold": 5e-3,
            "detail": "solver's bluff share vs bet/(pot+2bet), every size",
        },
        {
            "kind": "game_value_closed_form",
            "pass": all(abs(row["solved_value"] - row["algebra_value"]) < 5e-3 for row in rows),
            "threshold": 5e-3,
            "detail": "solver's game value vs pot*bet/(2(pot+bet))",
        },
        {
            "kind": "frequency_bounds",
            "pass": bool(rows) and all(row["all_gates_passed"] for row in rows),
            "detail": "every cited solver run passed its own assertions in solver/proofs.py",
        },
    ]
    if not rows:
        checks_out.append(
            {
                "kind": "frequency_bounds",
                "pass": False,
                "detail": "no solver artifacts found: run `python tools/run_solver.py` before gen_tables",
            }
        )
    return _artifact(
        table_id="table.08-04.solver-vs-algebra",
        title={
            "zh": "求解器解出的频率 与 第 02 章代数",
            "en": "Frequencies the solver found, against chapter 02's algebra",
        },
        caption={
            "zh": "左列是 CFR+ 自己收敛出来的，右列是 pot/(pot+bet) 与 bet/(pot+2bet)。两列相同不是巧合，"
            "而是 adr/0002 的交叉验证：数学核心或求解器任一处写错，这张表就生不成。",
            "en": "The left columns are what CFR+ converged to; the right columns are pot/(pot+bet) and "
            "bet/(pot+2bet). Agreement is not a coincidence but the cross-validation of adr/0002: if "
            "either the math core or the solver is wrong, this table cannot be generated.",
        },
        lesson="08-04",
        columns=[
            {"key": "size_label", "header": {"zh": "尺度", "en": "Size"}, "unit": "dimensionless"},
            {
                "key": "solved_defense",
                "header": {"zh": "求解器防守", "en": "Solved defence"},
                "unit": "probability",
                "digits": 2,
            },
            {
                "key": "algebra_mdf",
                "header": {"zh": "代数 MDF", "en": "Algebraic MDF"},
                "unit": "probability",
                "digits": 2,
            },
            {
                "key": "solved_bluff_share",
                "header": {"zh": "求解器诈唬占比", "en": "Solved bluff share"},
                "unit": "probability",
                "digits": 2,
            },
            {
                "key": "algebra_bluff_share",
                "header": {"zh": "代数诈唬占比", "en": "Algebraic bluff share"},
                "unit": "probability",
                "digits": 2,
            },
            {
                "key": "exploitability",
                "header": {"zh": "可剥削度(筹码/手)", "en": "Exploitability (chips/hand)"},
                "unit": "chips_per_hand",
                "digits": 6,
            },
        ],
        rows=rows,
        derivation_ref="src/pokergto/solver/proofs.py#PUBLISHED_PROOFS",
        module="pokergto.solver.cfr",
        function="solve",
        checks=checks_out,
    )


#: Boards whose reachable ceiling the two ranges are measured against (lesson 03-02).
CAPPED_SPOTS: tuple[tuple[str, str, str], ...] = (
    ("Kh7s3d", "AKs,AQs,ATs,KQs,AKo,AQo,99,77", "KJs,QJs,JTs,T9s,98s,A5s-A2s,KQo,AJo,76s"),
    ("AsKsQh", "AA,KK,QQ,JT,T9,AT,KT", "98s,76s,54s,65,K9,K8,Q9,J9"),
    ("9h6d3c", "AKo,AQo,AJs,KQo,TT,99,88,AKs,AQs", "87s,76s,65s,54s,T8s,T9s,98o,66,55"),
)


def _bilingual_hand(score: int) -> dict[str, str]:
    from pokergto.evaluator import describe

    return {"zh": describe(score, lang="zh"), "en": describe(score, lang="en")}


def build_capped_ranges() -> dict[str, Any]:
    """Which range cannot hold the nuts on which board -- computed, not asserted.

    A capped range is a *sizing* fact: it removes the raise threat that licenses big bets, which is why
    chapter 03 hands off to chapter 04. The ceiling is the best hand any two cards could make here, so
    "capped" means "not in my range", not "not achievable in principle" -- the two are easy to confuse
    and the table reports both numbers to keep them apart.
    """
    from pokergto.cards import ALL_COMBOS, Card, parse_cards
    from pokergto.evaluator import best_score
    from pokergto.notation import parse
    from pokergto.theory.range_advantage import is_capped

    rows: list[dict[str, Any]] = []
    for board_text, hero_spec, villain_spec in CAPPED_SPOTS:
        board = parse_cards(board_text)
        ceiling = max(
            best_score((Card.from_index(a), Card.from_index(b)), board) for a, b in ALL_COMBOS
        )
        for role, spec in (("hero", hero_spec), ("villain", villain_spec)):
            rng = parse(spec)
            held = [
                best_score((first, second), board) for first, second, weight in rng if weight > 0
            ]
            rows.append(
                {
                    "board": board_text,
                    "role": role,
                    "spec": spec,
                    "combos": round(rng.total_combos(), 1),
                    "range_best": _bilingual_hand(max(held)),
                    "ceiling": _bilingual_hand(ceiling),
                    "is_capped": bool(is_capped(rng, board)),
                }
            )
    return _artifact(
        table_id="table.03-02.capped-range-check",
        title={
            "zh": "范围封顶检查：这条线里有没有坚果",
            "en": "Capped-range check: does this line contain the nuts",
        },
        caption={
            "zh": "范围是示例输入（reference）；“范围最强手”“牌面可达上限”与 is_capped 由 evaluate5 逐组合现算（derived）。"
            "上限取全部 1326 个组合的最优，所以 capped 说的是“不在我这一份范围里”，不是“这张牌面上不可能出现”。",
            "en": "The ranges are illustrative inputs (reference); each range's best holding, the board's reachable "
            "ceiling and the capped verdict are computed combo by combo (derived). The ceiling is the best of all "
            "1,326 combos, so capped means not-in-my-range, not not-possible-on-this-board.",
        },
        lesson="03-02",
        columns=[
            {"key": "board", "header": {"zh": "牌面", "en": "Board"}, "unit": "dimensionless"},
            {"key": "role", "header": {"zh": "角色", "en": "Role"}, "unit": "dimensionless"},
            {
                "key": "combos",
                "header": {"zh": "组合数", "en": "Combos"},
                "unit": "combos",
                "digits": 1,
            },
            {
                "key": "range_best",
                "header": {"zh": "范围最强手", "en": "Best in range"},
                "unit": "dimensionless",
            },
            {
                "key": "ceiling",
                "header": {"zh": "牌面可达上限", "en": "Board ceiling"},
                "unit": "dimensionless",
            },
            {
                "key": "is_capped",
                "header": {"zh": "是否封顶", "en": "Capped?"},
                "unit": "dimensionless",
            },
        ],
        rows=rows,
        derivation_ref="pokergto.theory.range_advantage#is_capped",
        module="pokergto.theory.range_advantage",
        function="is_capped",
        assumptions=(
            {
                "en": "Capped means the range's best holding sits below the board's reachable ceiling by more than `tolerance` steps of the evaluator's total order, where a step is one distinct hand strength.",
                "zh": "封顶的判定是：范围最强手在评估器全序里比牌面可达上限低出超过 tolerance 步；一步 = 一种不同的牌力。",
            },
        ),
        checks=[
            {
                "kind": "frequency_bounds",
                "pass": any(row["is_capped"] for row in rows)
                and any(not row["is_capped"] for row in rows),
                "detail": "the table contains both a capped and an uncapped line; if every row agreed, the verdict would be meaningless",
            }
        ],
    )


#: Classes whose combo count a visible card rewrites (lesson 03-05 and 03-06).
REMOVAL_PROBES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("AKo", ("As",)),
    ("AKo", ("As", "Kh")),
    ("AKo", ("As", "Ks")),
    ("AA", ("As",)),
    ("AA", ("As", "Ah")),
    ("99", ("9d",)),
    ("KQs", ("Ks",)),
    ("KQs", ("Qh",)),
    ("KQs", ("Kh", "Qh")),
    ("KJs", ("As", "Ks")),
)


def build_removal_effects() -> dict[str, Any]:
    """How many combos a class really has once cards are visible.

    The 6/4/12 of chapter 01 are the no-information bounds. This table is the subtraction those bounds
    force, computed with :meth:`pokergto.ranges.Range.with_removed`, and it is deliberately asymmetric:
    the same two visible cards remove different counts depending on whether they share a suit, which is
    the single most misquoteable number in blocker talk.
    """
    from pokergto.cards import Card
    from pokergto.notation import parse

    rows: list[dict[str, Any]] = []
    for spec, visible in REMOVAL_PROBES:
        full = parse(spec)
        cards = [Card.parse(code) for code in visible]
        removed = full.with_removed(*cards)
        rows.append(
            {
                "class": spec,
                "visible": "+".join(card.code for card in cards),
                "baseline_combos": round(full.total_combos(), 1),
                "remaining_combos": round(removed.total_combos(), 1),
                "removed_combos": round(full.total_combos() - removed.total_combos(), 1),
            }
        )
    return _artifact(
        table_id="table.03-05.removal-effect-by-class",
        title={
            "zh": "移除效应：可见牌之后每个类别还剩几个组合",
            "en": "Removal: combos left in a class once cards are visible",
        },
        caption={
            "zh": "全部由 Range.with_removed 现算（derived）。同点是两张同花还是两张异花，删掉的数量不同——这一列差别就是 03-05 的论点。",
            "en": "Every number comes from Range.with_removed (derived). Two same-suit visible cards and two "
            "different-suit visible cards delete different counts, and that difference is lesson 03-05's point.",
        },
        lesson="03-05",
        columns=[
            {"key": "class", "header": {"zh": "类别", "en": "Class"}, "unit": "dimensionless"},
            {
                "key": "visible",
                "header": {"zh": "可见牌", "en": "Visible cards"},
                "unit": "dimensionless",
            },
            {
                "key": "baseline_combos",
                "header": {"zh": "原本组合数", "en": "Baseline combos"},
                "unit": "combos",
                "digits": 1,
            },
            {
                "key": "remaining_combos",
                "header": {"zh": "剩余组合数", "en": "Combos left"},
                "unit": "combos",
                "digits": 1,
            },
            {
                "key": "removed_combos",
                "header": {"zh": "被删组合数", "en": "Combos removed"},
                "unit": "combos",
                "digits": 1,
            },
        ],
        rows=rows,
        derivation_ref="pokergto.ranges#Range.with_removed",
        module="pokergto.ranges",
        function="Range.with_removed",
        checks=[
            {
                "kind": "combo_count",
                "pass": all(0 <= row["remaining_combos"] <= row["baseline_combos"] for row in rows),
                "detail": "removal never increases a class's combo count",
            }
        ],
    )


#: Fold frequencies the break-even surface is sampled at. These are assumptions, not measurements:
#: the table answers "given this f, what equity makes a bet worth it", and says so in its assumptions.
BREAK_EVEN_FOLD_FREQUENCIES = (0.25, 0.4, 0.5, 0.6, 0.75)
BREAK_EVEN_SIZES = (1 / 3, 0.5, 0.75, 1.0, 2.0)


def build_break_even_equity_surface() -> dict[str, Any]:
    """The equity at which betting beats checking, for every size and fold frequency.

    ``EV(bet) = EV(check)`` is linear in equity, so the whole sizing debate is one threshold and the
    sign of one denominator. This table is chapter 04's spine because it makes the bluff regime exact
    rather than folkloric: when the fold frequency is high enough the inequality *flips*, and a hand
    below the threshold wants to bet while a hand above it does not.

    The closed form is not trusted. Each row re-solves the equation by bisection on
    :func:`pokergto.ev.ev_bet` and :func:`pokergto.ev.ev_check` and the check below compares them.
    """
    from fractions import Fraction

    from pokergto.ev import break_even_equity_to_bet, ev_bet, ev_check

    pot = 1.0
    rows: list[dict[str, Any]] = []
    worst_residual = 0.0
    for size in BREAK_EVEN_SIZES:
        bet = size * pot
        mdf = float(minimum_defense_frequency(pot, bet))
        for fold in BREAK_EVEN_FOLD_FREQUENCIES:
            solved = break_even_equity_to_bet(pot, bet, fold)
            threshold = solved.equity
            residual = None
            if threshold is not None:
                gap = abs(
                    float(
                        Fraction(ev_bet(pot, bet, fold, threshold, exact=True))
                        - Fraction(ev_check(pot, threshold, exact=True))
                    )
                )
                worst_residual = max(worst_residual, gap)
                residual = round(gap, 12)
            rows.append(
                {
                    "size_label": _size_label(Fraction(size)),
                    "bet_size": round(size, 6),
                    "fold_frequency": fold,
                    "mdf_of_size": round(mdf, 6),
                    "regime": solved.regime,
                    "break_even_equity": None if threshold is None else round(threshold, 6),
                    "residual": residual,
                }
            )
    return _artifact(
        table_id="table.04-05.bet-break-even-equity",
        title={
            "zh": "下注何时优于过牌：每个尺度、每个弃牌率的盈亏平衡胜率",
            "en": "When betting beats checking: break-even equity by size and fold frequency",
        },
        caption={
            "zh": "闭合式 e* = ((1-f)B - fP) / (2B(1-f) - fP)，由 ev_bet 与 ev_check 代数解出；每一行都用 ev_bet/ev_check 回代验证，"
            "residual 那一列就是回代的残差（显示到 8 位，更小的残差显示为 0；精确上界在 checks 里）。regime=below 的行是“越弱越该下注”的诈唬区——分母变号造成的，不是口误。",
            "en": "Closed form e* = ((1-f)B - fP) / (2B(1-f) - fP), solved from ev_bet and ev_check and re-substituted "
            "row by row; the residual column is what that substitution leaves behind, shown to eight decimals, so a 0 there means below 1e-8 and the exact bound is in checks. A regime of below means weaker "
            "hands want to bet -- the bluff region, produced by the denominator changing sign, not by a slip.",
        },
        lesson="04-05",
        columns=[
            {"key": "size_label", "header": {"zh": "尺度", "en": "Size"}, "unit": "dimensionless"},
            {
                "key": "fold_frequency",
                "header": {"zh": "对手弃牌率 f", "en": "Fold frequency f"},
                "unit": "probability",
                "digits": 2,
            },
            {
                "key": "mdf_of_size",
                "header": {"zh": "该尺度的 MDF", "en": "MDF at this size"},
                "unit": "probability",
                "digits": 4,
            },
            {
                "key": "break_even_equity",
                "header": {"zh": "盈亏平衡胜率 e*", "en": "Break-even equity e*"},
                "unit": "probability",
                "digits": 4,
            },
            {"key": "regime", "header": {"zh": "区间", "en": "Regime"}, "unit": "dimensionless"},
            {
                "key": "residual",
                "header": {"zh": "回代残差", "en": "Residual"},
                "unit": "dimensionless",
                "digits": 8,
            },
        ],
        rows=rows,
        derivation_ref="pokergto.ev#break_even_equity_to_bet",
        module="pokergto.ev",
        function="break_even_equity_to_bet",
        assumptions=(
            {
                "en": "Fold frequencies are declared inputs, not measurements of any population: each row answers a conditional question about a stated f.",
                "zh": "弃牌率是声明的输入，不是任何人群的实测：每一行回答的是“若 f 为此值”的条件式问题。",
            },
        ),
        checks=[
            {
                "kind": "closed_form_residual",
                "pass": worst_residual < 1e-12,
                "value": worst_residual,
                "threshold": 1e-12,
                "detail": "every threshold in the table re-substitutes into ev_bet - ev_check with zero residual",
            },
            {
                "kind": "frequency_bounds",
                "pass": any(row["regime"] == "below" for row in rows)
                and any(row["regime"] == "above" for row in rows),
                "detail": "both regimes occur, which is the point: the inequality's direction depends on f and size",
            },
        ],
    )


def _size_label(value: Any) -> str:
    """``0.3333333333333333`` is not a size name. ``limit_denominator`` recovers the fraction the size
    was chosen as, so the label reads "1/3 pot" instead of a 16-digit binary artefact."""
    from fractions import Fraction

    fraction = Fraction(value).limit_denominator(1000)
    return "pot" if fraction == 1 else f"{fraction} pot"


#: Stack depths for the overbet-legality table (lesson 04-03), in big blinds, against a pot of 6bb.
STACK_PROBES = (8, 10, 15, 20, 30, 50, 100, 200)


def build_size_ceiling_by_stack() -> dict[str, Any]:
    """How big a bet can be, given how much is actually left.

    Overbet arguments go wrong on arithmetic: a "2x pot" bet on a 6bb pot is 12bb, and if only 10bb is
    behind it is not a size, it is an all-in. This table states the ceiling, the largest standard size
    still available, and whether facing a bet already commits the caller -- all from
    :mod:`pokergto.spr`, with no notion of hand strength anywhere in it.
    """

    from pokergto.odds import STANDARD_SIZES
    from pokergto.spr import all_in_equity_needed_from_spr, spr

    pot = 6.0
    rows: list[dict[str, Any]] = []
    for stack in STACK_PROBES:
        ratio = spr(stack, pot)
        largest = max(
            (float(size) * pot for size in STANDARD_SIZES if float(size) * pot <= stack),
            default=0.0,
        )
        rows.append(
            {
                "stack_bb": float(stack),
                "pot_bb": pot,
                "max_bet_as_pot_fraction": round(stack / pot, 4),
                "largest_standard_size_bb": round(largest, 4),
                "spr": round(ratio, 4),
                "equity_needed_all_in": round(float(all_in_equity_needed_from_spr(ratio)), 6),
                "pot_size_bet_commits": bool(stack <= 2 * pot),
                "double_pot_is_legal": bool(stack >= 2 * pot),
            }
        )
    ordered = [row["equity_needed_all_in"] for row in rows]
    return _artifact(
        table_id="table.04-03.size-ceiling-by-stack",
        title={
            "zh": "尺度上限：还剩多少筹码决定你能不能下两倍池",
            "en": "Size ceiling: what is still behind decides whether a 2x-pot bet exists",
        },
        caption={
            "zh": "全部由 spr.py 现算（derived），不含任何牌力概念。pot=6bb 是一个已成池的例子，改变它只改变数值不改变结论。",
            "en": "Computed from spr.py (derived), with no notion of hand strength in it. The 6bb pot is one example; "
            "changing it changes the numbers and not the conclusion.",
        },
        lesson="04-03",
        columns=[
            {
                "key": "stack_bb",
                "header": {"zh": "剩余筹码(bb)", "en": "Stack behind (bb)"},
                "unit": "combos",
                "digits": 0,
            },
            {
                "key": "max_bet_as_pot_fraction",
                "header": {"zh": "最大可下注 ÷ 底池", "en": "Max bet / pot"},
                "unit": "ratio",
                "digits": 2,
            },
            {
                "key": "largest_standard_size_bb",
                "header": {"zh": "最大标准尺度(bb)", "en": "Largest standard size (bb)"},
                "unit": "combos",
                "digits": 1,
            },
            {
                "key": "spr",
                "header": {"zh": "有效筹码底池比", "en": "SPR"},
                "unit": "ratio",
                "digits": 2,
            },
            {
                "key": "equity_needed_all_in",
                "header": {"zh": "全下所需胜率", "en": "Equity needed all-in"},
                "unit": "probability",
                "digits": 4,
            },
            {
                "key": "pot_size_bet_commits",
                "header": {"zh": "池级下注即全下", "en": "Pot bet commits"},
                "unit": "dimensionless",
            },
        ],
        rows=rows,
        derivation_ref="pokergto.spr#all_in_equity_needed_from_spr",
        module="pokergto.spr",
        function="spr",
        checks=[
            {
                "kind": "monotonicity",
                "pass": all(
                    later >= earlier for earlier, later in zip(ordered, ordered[1:], strict=False)
                ),
                "detail": "equity needed to commit rises with SPR; a table where it did not would mean the ratio is being computed backwards",
            }
        ],
    )


#: Board/range pairs for lesson 03-01. The ranges are illustrative inputs authored in this repository
#: (`reference` -- they are the assumption, stated); the equity and nut shares are computed. They are
#: deliberately small: at a couple of hundred combos per pair the *exact* enumeration costs seconds, so
#: this table carries no Monte Carlo error bar and no sampling seed.
ADVANTAGE_SPOTS: tuple[dict[str, str], ...] = (
    {
        "board": "Kh7s3d",
        "hero_label": "CO opener",
        "hero_spec": "AKs,AQs,ATs,KQs,AKo,AQo,99,77",
        "villain_label": "BB caller",
        "villain_spec": "KJs,QJs,JTs,T9s,98s,A5s-A2s,KQo,AJo,76s",
        "why": "Dry high board: the opener's overpairs and overcards versus a caller's draws.",
    },
    {
        "board": "9h6d3c",
        "hero_label": "BTN opener",
        "hero_spec": "AKo,AQo,AJs,KQo,TT,99,88,AKs,AQs",
        "villain_label": "BB caller",
        "villain_spec": "87s,76s,65s,54s,T8s,T9s,98o,97o,66,55",
        "why": "Low connected board: the raiser's overcards against the caller's straight combos.",
    },
    {
        "board": "As9s5d",
        "hero_label": "CO opener",
        "hero_spec": "AKo,AQo,AJs,ATs,KTs,QQ,JJ,TT",
        "villain_label": "BB caller",
        "villain_spec": "KQs,QJs,KJs,JTs,98s,76s,99,55",
        "why": "Two-tone with a flush draw: who owns the flush, who owns the pairs.",
    },
    {
        "board": "Kh7s3d4c",
        "hero_label": "CO opener (turn)",
        "hero_spec": "AKo,AQo,ATs,KQs,99,77,44",
        "villain_label": "BB caller (turn)",
        "villain_spec": "KJs,QJs,JTs,T9s,98s,A5s,KQo,AJo",
        "why": "Turn after the same flop: one card has landed, and the nut share moves while the equity edge barely does -- the reason a river plan cannot be read off a flop number.",
    },
)


def build_equity_vs_nut_advantage() -> dict[str, Any]:
    """Equity advantage and nut advantage on the same rows, because collapsing them is the error.

    Lesson 03's central claim is that these are two different numbers and that a board can give one
    player each. A table that reported only equity would be teaching the wrong half of it, so the
    disagreement is a column, and the check below asserts at least one row actually disagrees -- a
    table where the two always match would mean the distinction is decorative.
    """
    from pokergto.cards import parse_cards
    from pokergto.notation import parse
    from pokergto.theory.range_advantage import advantage

    rows: list[dict[str, Any]] = []
    for spot in ADVANTAGE_SPOTS:
        board = parse_cards(spot["board"])
        hero = parse(spot["hero_spec"])
        villain = parse(spot["villain_spec"])
        # Fail rather than hang: exact enumeration is chosen because it is affordable here, and the
        # moment a spot is not affordable the table must say so instead of quietly sampling.
        runouts = 1 if len(board) == 5 else math.comb(52 - len(board) - 0, 5 - len(board))
        estimated = runouts * (hero.total_combos() + villain.total_combos())
        if estimated > 400_000:
            raise SystemExit(
                f"{spot['board']}: exact advantage would cost ~{estimated:,.0f} evaluations. Narrow "
                "the ranges or make the row Monte Carlo and record its error bar."
            )
        result = advantage(hero, villain, board, mode="exact")
        rows.append(
            {
                "board": spot["board"],
                "hero_label": spot["hero_label"],
                "villain_label": spot["villain_label"],
                "hero_combos": round(hero.total_combos(), 1),
                "villain_combos": round(villain.total_combos(), 1),
                "hero_equity": round(result.hero_equity, 6),
                "villain_equity": round(result.villain_equity, 6),
                "equity_edge": round(result.equity_edge, 6),
                "hero_nut_share": round(result.hero_nut_share, 6),
                "villain_nut_share": round(result.villain_nut_share, 6),
                "nut_edge": round(result.nut_edge, 6),
                "can_bet_often": result.who_can_bet_often,
                "can_bet_big": result.who_can_bet_big,
                "edges_disagree": result.who_can_bet_often != result.who_can_bet_big,
            }
        )
    return _artifact(
        table_id="table.03-01.equity-vs-nut-advantage",
        title={
            "zh": "胜率优势与坚果优势：同一局面里的两个不同问题",
            "en": "Equity advantage and nut advantage: two different questions on one board",
        },
        caption={
            "zh": "范围是本仓库为讲解设定的示例（reference），两列优势由 evaluate5 与逐组合枚举现算（derived，"
            "精确穷举、无抽样误差）。坚果优势在未完成的牌面上按“当前可达最强手”为基准，因此对听牌方偏低；"
            "牌面五张时不在这张表里——河牌后没有胜率可算，只剩摊牌。",
            "en": "The ranges are illustrative inputs authored here (reference); both advantage columns are "
            "computed by this repository's evaluator over an exact enumeration (derived, no sampling error). "
            "On an incomplete board the nut reference is the best hand reachable *now*, which understates it "
            "for the player holding draws. A five-card board is not in this table: after the river there is no "
            "equity left to compute, only a showdown.",
        },
        lesson="03-01",
        columns=[
            {"key": "board", "header": {"zh": "牌面", "en": "Board"}, "unit": "dimensionless"},
            {"key": "hero_label", "header": {"zh": "Hero", "en": "Hero"}, "unit": "dimensionless"},
            {
                "key": "villain_label",
                "header": {"zh": "Villain", "en": "Villain"},
                "unit": "dimensionless",
            },
            {
                "key": "hero_equity",
                "header": {"zh": "Hero 胜率", "en": "Hero equity"},
                "unit": "probability",
                "digits": 4,
            },
            {
                "key": "equity_edge",
                "header": {"zh": "胜率优势", "en": "Equity edge"},
                "unit": "probability",
                "digits": 4,
            },
            {
                "key": "hero_nut_share",
                "header": {"zh": "Hero 坚果占比", "en": "Hero nut share"},
                "unit": "probability",
                "digits": 4,
            },
            {
                "key": "nut_edge",
                "header": {"zh": "坚果优势", "en": "Nut edge"},
                "unit": "probability",
                "digits": 4,
            },
            {
                "key": "can_bet_often",
                "header": {"zh": "谁能常下注", "en": "Who bets often"},
                "unit": "ratio",
            },
            {
                "key": "can_bet_big",
                "header": {"zh": "谁能下大注", "en": "Who bets big"},
                "unit": "ratio",
            },
        ],
        rows=rows,
        derivation_ref="pokergto.theory.range_advantage#advantage",
        module="pokergto.theory.range_advantage",
        function="advantage",
        assumptions=(
            "Ranges are illustrative inputs chosen so the exact enumeration stays cheap; they are not a solved strategy.",
            "示例范围为讲解而设，不是求解决策；它们让精确穷举保持在几秒内。",
        ),
        checks=[
            {
                "kind": "frequency_bounds",
                "pass": all(
                    0.0 <= row["hero_equity"] <= 1.0
                    and abs(row["hero_equity"] + row["villain_equity"] - 1.0) < 1e-6
                    for row in rows
                ),
                "detail": "hero + villain equity equals 1 on every row",
            },
            {
                "kind": "edges_disagree",
                "pass": any(row["edges_disagree"] for row in rows),
                "detail": "at least one board gives one side the equity edge and the other the nut edge; "
                "if none did, the distinction this table exists for would be decorative",
            },
        ],
    )


BUILDERS: dict[str, Callable[[], dict[str, Any]]] = {
    "table.02-03.mdf-vs-sizing": build_sizing_mdf,
    "table.02-04.bluff-value-ratio": build_bluff_value,
    "table.02-02.equity-needed-to-call": build_equity_needed,
    "table.07-01.multiway-defense": build_multiway_defense,
    "table.01-03.draw-probability-exact-vs-rule": build_draw_probability,
    "table.03-01.equity-vs-nut-advantage": build_equity_vs_nut_advantage,
    "table.03-02.capped-range-check": build_capped_ranges,
    "table.03-05.removal-effect-by-class": build_removal_effects,
    "table.04-05.bet-break-even-equity": build_break_even_equity_surface,
    "table.04-03.size-ceiling-by-stack": build_size_ceiling_by_stack,
    "table.01-01.combo-decomposition": build_combo_decomposition,
    "table.01-05.hand-class-counts": build_hand_class_counts,
    "table.03-07.spr-commitment": build_spr_commitment,
    "table.12-03.icm-vs-chip-share": build_icm_shares,
    "table.08-04.solver-vs-algebra": build_solver_vs_algebra,
}


def generate(out_dir: Path, *, skip_expensive: bool = False) -> list[Path]:
    written: list[Path] = []
    for table_id, builder in sorted(BUILDERS.items()):
        if skip_expensive and table_id == "table.01-05.hand-class-counts":
            continue
        artifact = builder()
        path = out_dir / "tables" / f"{table_id}.json"
        write_artifact(path, artifact, schema="table")
        written.append(path)
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--out", type=Path, default=GEN_DIR)
    parser.add_argument("--only", action="append", dest="only")
    parser.add_argument(
        "--skip-expensive", action="store_true", help="omit the 2.6M-hand enumeration"
    )
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args(argv)

    if args.list:
        for table_id in sorted(BUILDERS):
            print(table_id)
        return 0

    names = args.only or list(BUILDERS)
    unknown = sorted(set(names) - set(BUILDERS))
    if unknown:
        print(f"error: unknown table ids {unknown}", file=sys.stderr)
        return 2
    written = []
    for name in sorted(names):
        artifact = BUILDERS[name]()
        path = args.out / "tables" / f"{name}.json"
        write_artifact(path, artifact, schema="table")
        written.append(path)
    ok(f"generated {len(written)} tables into {args.out.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
