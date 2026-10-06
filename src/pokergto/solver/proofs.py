"""The proof registry: which games are validated, to what tolerance, and against what anchor.

This file is the enforcement half of ADR-0002. A lesson may cite a solver result as ``ready`` only if
the game that produced it is listed here, and ``tools/run_solver.py`` refuses to write an artifact for
a game that is not listed or that fails its assertions. The rule exists because a converging solver is
not the same as a correct one: CFR will happily converge to the equilibrium of the game you actually
coded, which is only the game you meant to document if somebody checked.

Each entry records:

* ``closed_form`` -- the analytic anchor, e.g. Kuhn's game value ``-ante/18``;
* ``thresholds`` -- the maximum exploitability allowed, in chips per hand, and the iteration count
  that must be reached to earn it;
* ``assertions`` -- named checks executed against the average strategy, including the one-street game's
  agreement with :mod:`pokergto.odds`, which is the cross-validation between the curriculum's math
  core and its solver.

Thresholds come from observed convergence, not from wishfulness: Kuhn's CFR+ reaches ~1e-5 in 2,000
iterations and plain CFR ~3e-3 in the same budget, so the gates are set a decade below what each run
actually achieves and a decade above what a broken implementation produced during development (a
squashed-reach bug stalled at 0.89 exploitability, which no sane threshold would admit).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any, Callable, Sequence

import numpy as np

from ..errors import ProofGateError
from ..odds import bluff_fraction_at_indifference, minimum_defense_frequency
from .cfr import SolveResult
from .games import kuhn as build_kuhn
from .games import one_street_bluff_catcher as build_one_street
from .tree import GameTree

ANTE = 1.0
KUHN_VALUE = -float(Fraction(1, 18)) * ANTE


@dataclass(frozen=True, slots=True)
class Assertion:
    """A named check on a solve result. Each one reports a measured value, not a pass/fail bool, so a
    failing run leaves a number in the build log."""

    name: str
    description: dict[str, str]
    check: Callable[[GameTree, SolveResult, dict[str, Any]], tuple[float, float]]
    """``check`` returns ``(measured, expected)``; the tolerance is ``entry.tolerances[name]``."""


@dataclass(frozen=True, slots=True)
class ProofEntry:
    game: str
    #: The solver_run schema's ``game`` enum value. ``game`` is the registry key, which is per
    #: parameterisation: three bet sizes are three entries of the one family.
    family: str
    builder: Callable[[], GameTree]
    algorithm: str
    iterations: int
    exploitability_threshold: float
    measure_every: int = 0
    assertions: tuple[Assertion, ...] = ()
    tolerances: dict[str, float] = field(default_factory=dict)
    notes: dict[str, str] = field(default_factory=dict)

    def build(self) -> GameTree:
        return self.builder()


#: Artifact ``checks[].kind`` for each assertion. The values come from ``common.schema.json``'s
#: ``check.kind`` enum, so adding an assertion without registering its kind here fails validation
#: rather than silently writing an artifact that cannot be checked.
CHECK_KIND_BY_ASSERTION: dict[str, str] = {
    "game_value_closed_form": "game_value_closed_form",
    "toy_game_value": "game_value_closed_form",
    "mdf_equality": "mdf_equality",
    "bluff_indifference": "bluff_indifference",
    "king_calls_when_faced": "frequency_bounds",
    "jack_never_calls": "frequency_bounds",
    "jack_bluff_in_family": "frequency_bounds",
    "value_bets_always": "frequency_bounds",
}


def _report(result: SolveResult) -> dict[str, dict[str, float]]:
    return result.strategy_report()


def assert_kuhn_value(_tree: GameTree, result: SolveResult, _cfg: dict[str, Any]) -> tuple[float, float]:
    return result.game_value, KUHN_VALUE


def assert_king_calls_when_faced(_tree: GameTree, result: SolveResult, _cfg: dict[str, Any]) -> tuple[float, float]:
    """Calling with the king when facing a bet is strictly dominant for either player, so every
    equilibrium does it. This is a *dominance* claim, which is why it can be asserted -- unlike "always
    open a bet with the king", which cannot (see the note on KUHN)."""
    report = _report(result)
    return 0.5 * (report["2:0:K"]["call"] + report["3:1:K"]["call"]), 1.0


def assert_jack_never_calls(_tree: GameTree, result: SolveResult, _cfg: dict[str, Any]) -> tuple[float, float]:
    """Folding the jack to a bet is strictly dominant: it never wins a showdown, so calling only adds
    money to a lost pot."""
    report = _report(result)
    return 0.5 * (report["2:0:J"]["call"] + report["3:1:J"]["call"]), 0.0


def assert_jack_bluff_in_family(_tree: GameTree, result: SolveResult, _cfg: dict[str, Any]) -> tuple[float, float]:
    """Player 0's jack-bluffing frequency may be anywhere in ``[0, 1/3]`` -- the equilibrium is a
    family, not a point. The assertion is on membership: demanding one particular member would be
    testing the implementation's trajectory, not game theory.

    The ``expected`` reported in the log is the family's upper bound, which is the number that actually
    constrains the check.
    """
    report = _report(result)
    return report["0:0:J"]["bet"], 1.0 / 3.0


def _one_street_entry(bet_size: float, iterations: int = 4000) -> ProofEntry:
    def assert_defense(tree: GameTree, result: SolveResult, _cfg: dict[str, Any]) -> tuple[float, float]:
        report = _report(result)
        return report["1:1:catcher"]["call"], float(minimum_defense_frequency(1.0, bet_size))

    def assert_bluff_share(tree: GameTree, result: SolveResult, _cfg: dict[str, Any]) -> tuple[float, float]:
        report = _report(result)
        nut = report["0:0:nut"]["bet"]
        air = report["0:0:air"]["bet"]
        measured = air / (nut + air) if (nut + air) > 0 else 0.0
        return measured, float(bluff_fraction_at_indifference(1.0, bet_size))

    def assert_value_bets(tree: GameTree, result: SolveResult, _cfg: dict[str, Any]) -> tuple[float, float]:
        report = _report(result)
        return report["0:0:nut"]["bet"], 1.0

    def assert_toy_game_value(_tree: GameTree, result: SolveResult, _cfg: dict[str, Any]) -> tuple[float, float]:
        """Hero's equilibrium value is ``pot * bet / (2 * (pot + bet))`` -- a third independent
        quantity that has to agree, not just the two frequencies.

        Derivation, so the assertion is not a fitted constant: the nut hand bets and gains ``pot/2``
        when the opponent folds plus ``bet`` when called, i.e. ``pot/2 + d*bet`` with ``d`` the call
        frequency. Air is indifferent by construction, earning exactly its check value of ``-pot/2``.
        Averaging the two equally likely holdings leaves ``d*bet/2 = pot*bet / (2(pot+bet))``.
        """
        return result.game_value, bet_size / (2.0 * (1.0 + bet_size))

    return ProofEntry(
        game=f"toy_1street_{bet_size:g}".replace(".", "p").replace("/", "_"),
        family="toy_1street",
        builder=lambda size=bet_size: build_one_street(pot=1.0, bet_size=size),
        algorithm="cfr_plus",
        iterations=iterations,
        exploitability_threshold=2e-4,
        assertions=(
            Assertion(
                "mdf_equality",
                {
                    "zh": "解出的防守频率必须等于 pot/(pot+bet)",
                    "en": "The solved defense frequency must equal pot/(pot+bet)",
                },
                assert_defense,
            ),
            Assertion(
                "bluff_indifference",
                {
                    "zh": "下注范围中的诈唬占比必须等于 bet/(pot+2bet)",
                    "en": "The bluff share of the betting range must equal bet/(pot+2bet)",
                },
                assert_bluff_share,
            ),
            Assertion(
                "value_bets_always",
                {"zh": "坚果手牌必须 100% 下注", "en": "The nut hand must bet with frequency 1"},
                assert_value_bets,
            ),
            Assertion(
                "toy_game_value",
                {
                    "zh": "均衡价值必须等于 pot*bet/(2(pot+bet))",
                    "en": "Equilibrium value must equal pot*bet/(2(pot+bet))",
                },
                assert_toy_game_value,
            ),
        ),
        tolerances={
            "mdf_equality": 2e-3,
            "bluff_indifference": 2e-3,
            "value_bets_always": 1e-3,
            "toy_game_value": 2e-3,
        },
        notes={
            "zh": "这是课程数学核心与求解器互相校验的那一环：两边任一写错，这里就红。",
            "en": "The loop where the curriculum's math core and its solver validate each other. An error "
            "on either side turns this red.",
        },
    )


KUHN = ProofEntry(
    game="kuhn",
    family="kuhn",
    builder=lambda: build_kuhn(ante=ANTE),
    algorithm="cfr_plus",
    iterations=20_000,
    exploitability_threshold=5e-5,
    measure_every=500,
    assertions=(
        Assertion(
            "game_value_closed_form",
            {"zh": "游戏价值必须等于 -1/18", "en": "The game value must equal -1/18"},
            assert_kuhn_value,
        ),
        Assertion(
            "king_calls_when_faced",
            {
                "zh": "面对下注时用国王跟注是严格占优，因此每个均衡都这么做",
                "en": "Calling with the king when faced is strictly dominant, so every equilibrium does it",
            },
            assert_king_calls_when_faced,
        ),
        Assertion(
            "jack_never_calls",
            {
                "zh": "面对下注时用杰克跟注是严格劣策略",
                "en": "Calling with the jack when faced is strictly dominated",
            },
            assert_jack_never_calls,
        ),
        Assertion(
            "jack_bluff_in_family",
            {
                "zh": "杰克的诈唬频率落在解析族 [0, 1/3] 内",
                "en": "The jack bluffing frequency lies inside the analytic family [0, 1/3]",
            },
            assert_jack_bluff_in_family,
        ),
    ),
    tolerances={
        "game_value_closed_form": 1e-4,
        "king_calls_when_faced": 1e-3,
        "jack_never_calls": 1e-3,
        "jack_bluff_in_family": 0.34,
    },
    notes={
        "zh": "Kuhn 是唯一有完整解析解的含诈唬博弈，因此它是求解器的验收标准。注意这里只断言占优关系与族边界，"
              "不断言开注频率：本仓库的 CFR+ 找到的均衡里，P0 用国王只下注约 64%，因为当 P1 用后两张牌弃掉"
              "三分之二时，国王下注与过牌恰好无差别。教科书里那句'国王总是下注'是均衡选择，不是必然结论，"
              "而这件事本身就是 08-03 的一课。",
        "en": "Kuhn is the only bluffing game with a complete analytic solution, which makes it the "
        "solver's acceptance test. Note what is asserted here: dominance relations and the family "
        "bound, never an opening frequency. This repository's CFR+ lands on an equilibrium where "
        "player 0 bets the king roughly 64% of the time, because when the queen folds two-thirds of "
        "the time facing a bet, the king is indifferent between betting and checking. The textbook's "
        "'always bet the king' is an equilibrium selection, not a necessity, and that distinction is "
        "lesson 08-03's point.",
    },
)

#: Every validated game. Adding a game means adding an entry with a real anchor here, then it can be
#: solved, committed, and cited. Without an entry the artifact cannot exist.
PUBLISHED_PROOFS: dict[str, ProofEntry] = {
    KUHN.game: KUHN,
    "toy_1street_0p333333333333": _one_street_entry(Fraction(1, 3)),
    "toy_1street_0p5": _one_street_entry(0.5),
    "toy_1street_1": _one_street_entry(1.0),
}


def entry_for(game: str) -> ProofEntry:
    try:
        return PUBLISHED_PROOFS[game]
    except KeyError as exc:
        raise ProofGateError(
            f"game {game!r} is not in PUBLISHED_PROOFS. A solver artifact may only be generated for a "
            "game with a validation anchor: add an entry to src/pokergto/solver/proofs.py first "
            "(see adr/0002)."
        ) from exc


def is_validated(game: str) -> bool:
    return game in PUBLISHED_PROOFS


def verify(entry: ProofEntry, tree: GameTree, result: SolveResult) -> list[dict[str, Any]]:
    """Run every assertion and return a record list for the artifact's ``checks`` field."""
    records: list[dict[str, Any]] = [
        {
            "kind": "exploitability",
            "value": float(result.exploitability),
            "threshold": float(entry.exploitability_threshold),
            "pass": result.exploitability <= entry.exploitability_threshold,
            "detail": "chips per hand, half-sum convention",
        }
    ]
    for assertion in entry.assertions:
        measured, expected = assertion.check(tree, result, {})
        tolerance = entry.tolerances.get(assertion.name, 1e-6)
        within_family = assertion.name == "jack_bluff_in_family"
        passed = (
            0.0 - 1e-12 <= measured <= 1.0 / 3.0 + 1e-12
            if within_family
            else abs(measured - expected) <= tolerance
        )
        records.append(
            {
                "kind": CHECK_KIND_BY_ASSERTION.get(assertion.name, "frequency_bounds"),
                "value": float(measured),
                "threshold": float(tolerance),
                "pass": bool(passed),
                "detail": f"{assertion.name}: measured {measured:.6g}, expected {expected:.6g}",
            }
        )
    return records


def require_validated(game: str) -> ProofEntry:
    """Used by generators and by the docs gate: an unvalidated game cannot back a ``ready`` lesson."""
    return entry_for(game)


def summary() -> Sequence[str]:
    return tuple(sorted(PUBLISHED_PROOFS))
