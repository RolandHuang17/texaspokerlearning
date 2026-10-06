"""``poker`` — the command line a learner actually types.

The CLI is part of the teaching apparatus, so its output is the *derivation*, not a verdict: it shows
the formula, the inputs, and the error bar. Every subcommand has a ``--json`` form that emits exactly
what the engine computed, which is what ``tools/gen_tables.py`` and the docs AUTO blocks consume.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from typing import Any

from . import __version__
from .cards import parse_cards
from .equity import range_equity
from .errors import InputError, PokerGtoError
from .icm import icm
from .matrix13 import Grid13
from .notation import parse, to_spec
from .odds import (
    STANDARD_SIZES,
    at_least_one_defense,
    defense_frequency_multiway,
    minimum_defense_frequency,
    sizing_table,
)
from .ranges import Range
from .render import grid_to_text, markdown_table, table_from_artifact
from .spr import all_in_equity_needed_from_spr, spr


def _emit(payload: Any, *, as_json: bool, text: str) -> int:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(text)
    return 0


def _cmd_odds(args: argparse.Namespace) -> int:
    rows = sizing_table(pot=args.pot)
    artifact = {
        "columns": [
            {"key": "size_label", "header": {"zh": "尺度", "en": "Size"}, "unit": "dimensionless"},
            {
                "key": "mdf",
                "header": {"zh": "MDF", "en": "MDF"},
                "unit": "probability",
                "digits": 2,
            },
            {
                "key": "equity_needed",
                "header": {"zh": "跟注所需胜率", "en": "Equity to call"},
                "unit": "probability",
                "digits": 2,
            },
            {
                "key": "bluff_fraction",
                "header": {"zh": "诈唬占比", "en": "Bluff share"},
                "unit": "probability",
                "digits": 2,
            },
            {
                "key": "value_to_bluff",
                "header": {"zh": "价值:诈唬", "en": "Value:bluff"},
                "unit": "ratio",
                "digits": 2,
            },
        ],
        "rows": rows,
    }
    return _emit(
        {"pot": args.pot, "rows": rows},
        as_json=args.json,
        text=table_from_artifact(artifact, locale=args.lang),
    )


def _cmd_mdf(args: argparse.Namespace) -> int:
    single = minimum_defense_frequency(args.pot, args.bet)
    payload: dict[str, Any] = {
        "pot": args.pot,
        "bet": args.bet,
        "bet_over_pot": args.bet / args.pot,
        "mdf": round(single, 6),
        "opponents": args.opponents,
    }
    if args.opponents > 1:
        per_player = defense_frequency_multiway(args.pot, args.bet, args.opponents)
        payload["per_player_defense"] = round(per_player, 6)
        payload["joint_defense"] = round(at_least_one_defense(per_player, args.opponents), 6)
    text = (
        f"bet = {args.bet / args.pot:.3f} pot\n"
        f"MDF  = pot/(pot+bet) = {args.pot:.3f}/({args.pot:.3f}+{args.bet:.3f}) = {single:.4f}\n"
    )
    if args.opponents > 1:
        text += (
            f"     with {args.opponents} opponents: d = 1-((bet/(pot+bet))^(1/{args.opponents}))"
            f" = {payload['per_player_defense']:.4f} each,"
            f" joint {payload['joint_defense']:.4f} (equals the heads-up MDF)\n"
        )
    return _emit(payload, as_json=args.json, text=text)


def _cmd_equity(args: argparse.Namespace) -> int:
    board = parse_cards(args.board) if args.board else ()
    villain_spec = args.villain if args.range_villain is None else args.range_villain
    if villain_spec is None:
        raise SystemExit("equity needs an opponent: a second hand or range after your own")
    result = range_equity(
        _range_arg(args.hero),
        _range_arg(villain_spec),
        board,
        mode=args.mode,
        iterations=args.iterations,
        seed=args.seed,
    )
    payload = {
        "hero": args.hero,
        "villain": villain_spec,
        "board": args.board or "",
        "exact": result.exact,
        "equity": round(result.equity, 6),
        "wins": round(result.wins, 6),
        "ties": round(result.ties, 6),
        "losses": round(result.losses, 6),
        "iterations": result.iterations,
        "seed": result.seed,
        "stderr": round(result.stderr, 8),
        "ci95": [round(value, 6) for value in result.error_bar_95],
    }
    note = (
        ""
        if result.exact
        else f"\nMonte Carlo: sampled {result.iterations} runouts, seed {result.seed}."
    )
    return _emit(payload, as_json=args.json, text=f"{result}{note}")


def _range_arg(text: str) -> Range:
    """Accept either one specific combo (``AdKd``) or a 169-class range (``88+,ATs+``).

    A hand you are holding and a range you are teaching are the same object to the engine. Making
    the learner use a different flag for each is how documentation ends up quoting commands that
    fail, and every command in these lessons is run before it is written down.
    """
    try:
        cards = parse_cards(text)
    except InputError:
        cards = ()
    if len(cards) == 2:
        return Range.from_cards(cards)
    return parse(text)


def _cmd_range(args: argparse.Namespace) -> int:
    rng = parse(args.spec)
    grid = Grid13.from_range(rng)
    spec = to_spec(rng)
    payload = {
        "input": args.spec,
        "canonical_spec": spec,
        "combos": rng.total_combos(),
        "range_percentage": round(100.0 * rng.total_combos() / 1326.0, 4),
        "classes": len(rng.frequency_map()),
    }
    text = (
        grid_to_text(grid, locale=args.lang)
        + f"\n{payload['combos']:.1f} combos = {payload['range_percentage']:.2f}% of 1326"
    )
    return _emit(payload, as_json=args.json, text=text)


def _cmd_spr(args: argparse.Namespace) -> int:
    ratio = spr(args.stack, args.pot)
    needed = all_in_equity_needed_from_spr(ratio)
    payload = {
        "stack": args.stack,
        "pot": args.pot,
        "spr": round(ratio, 4),
        "all_in_equity_needed": round(needed, 6),
    }
    text = (
        f"SPR = {args.stack}/{args.pot} = {ratio:.3f}\n"
        f"equity needed to commit the whole stack = SPR/(1+2*SPR) = {needed:.4f}"
    )
    return _emit(payload, as_json=args.json, text=text)


def _cmd_icm(args: argparse.Namespace) -> int:
    chips = [int(part) for part in args.chips.split(",")]
    payouts = [float(part) for part in args.payouts.split(",")]
    result = icm(chips, payouts)
    rows = [
        [
            str(index),
            str(chips[index]),
            f"{100 * result.chip_share[index]:.2f}%",
            f"{result.expected_value[index]:.2f}",
            f"{100 * result.expected_value[index] / result.prize_pool:.2f}%",
            f"{100 * result.icm_gap[index]:+.2f}pp",
        ]
        for index in range(len(chips))
    ]
    text = markdown_table(
        ["#", "chips", "chip share", "ICM value", "money share", "money - chips"],
        rows,
        align=["center", "right", "right", "right", "right", "right"],
    )
    return _emit(
        {
            "chips": chips,
            "payouts": payouts,
            "chip_share": [round(v, 6) for v in result.chip_share],
            "expected_value": [round(v, 4) for v in result.expected_value],
            "icm_gap": [round(v, 6) for v in result.icm_gap],
            "prize_pool": result.prize_pool,
        },
        as_json=args.json,
        text=text,
    )


def _cmd_sizes(args: argparse.Namespace) -> int:
    return _emit(
        {"standard_sizes": [float(size) for size in STANDARD_SIZES]},
        as_json=args.json,
        text="\n".join(f"{float(size):.4f}" for size in STANDARD_SIZES),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="poker",
        description="pokergto: derive the number instead of memorising it.",
    )
    parser.add_argument("--version", action="version", version=f"pokergto {__version__}")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", help="machine-readable output")
    common.add_argument("--lang", choices=("en", "zh"), default="en", help="output language")
    sub = parser.add_subparsers(dest="command", required=True)

    odds = sub.add_parser(
        "odds",
        help="the sizing table: MDF, equity needed, bluff share, value:bluff",
        parents=[common],
    )
    odds.add_argument("--pot", type=float, default=1.0)
    odds.set_defaults(func=_cmd_odds)

    mdf = sub.add_parser(
        "mdf", help="minimum defense frequency, heads-up or multiway", parents=[common]
    )
    mdf.add_argument("--pot", type=float, required=True)
    mdf.add_argument("--bet", type=float, required=True)
    mdf.add_argument("--opponents", type=int, default=1)
    mdf.set_defaults(func=_cmd_mdf)

    equity = sub.add_parser(
        "equity", help="hand or range equity on an optional board", parents=[common]
    )
    equity.add_argument("hero", help="'AhAs' (one combo) or a range spec like '22+,ATs+'")
    equity.add_argument("villain", nargs="?", help="your opponent, hand or range")
    equity.add_argument(
        "--range-villain", dest="range_villain", help="explicit range for the opponent"
    )
    equity.add_argument("--board", default="")
    equity.add_argument("--mode", choices=("exact", "mc", "auto"), default="auto")
    equity.add_argument("--iterations", type=int, default=20_000)
    equity.add_argument("--seed", type=int, default=0)
    equity.set_defaults(func=_cmd_equity)

    rng = sub.add_parser("range", help="render a range spec as a 13x13 grid", parents=[common])
    rng.add_argument("spec")
    rng.set_defaults(func=_cmd_range)

    spr_cmd = sub.add_parser(
        "spr", help="stack-to-pot ratio and the commitment threshold", parents=[common]
    )
    spr_cmd.add_argument("--stack", type=float, required=True)
    spr_cmd.add_argument("--pot", type=float, required=True)
    spr_cmd.set_defaults(func=_cmd_spr)

    icm_cmd = sub.add_parser(
        "icm", help="independent chip model over a payout structure", parents=[common]
    )
    icm_cmd.add_argument("--chips", required=True, help="comma separated, in seat order")
    icm_cmd.add_argument("--payouts", required=True, help="comma separated, highest first")
    icm_cmd.set_defaults(func=_cmd_icm)

    sizes = sub.add_parser(
        "sizes", help="the sizing ladder the curriculum reasons over", parents=[common]
    )
    sizes.set_defaults(func=_cmd_sizes)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    # Windows consoles default to a legacy code page, which turns every Chinese lesson label into
    # mojibake. Reconfigure rather than telling contributors to change their system settings.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except Exception:  # pragma: no cover - exotic streams in tests
            pass
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except PokerGtoError as error:
        # Domain errors print one clean line. A traceback for "you wrote 73o instead of 73s" would
        # be noise, and noise is what makes learners stop typing commands.
        print(f"error: {error}", file=sys.stderr)
        return 2
    except (ValueError, SystemExit) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
