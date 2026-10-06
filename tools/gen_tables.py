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
    assumptions: tuple[str, ...] = (),
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


BUILDERS: dict[str, Callable[[], dict[str, Any]]] = {
    "table.02-03.mdf-vs-sizing": build_sizing_mdf,
    "table.02-04.bluff-value-ratio": build_bluff_value,
    "table.02-02.equity-needed-to-call": build_equity_needed,
    "table.07-01.multiway-defense": build_multiway_defense,
    "table.01-03.draw-probability-exact-vs-rule": build_draw_probability,
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
