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

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any

from ..errors import ProofGateError
from ..odds import bluff_fraction_at_indifference, minimum_defense_frequency
from .cfr import SolveResult
from .exploitability import br_pair, infoset_reach
from .games import REACH_FLOOR, leduc_dominance
from .games import kuhn as build_kuhn
from .games import leduc as build_leduc
from .games import one_street_bluff_catcher as build_one_street
from .tree import GameTree, pad_strategy

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
    #: How the game was parameterised, recorded into every artifact it produces. Without this a
    #: reader -- or a table generator -- has to infer ``bet_size`` from a filename, which is exactly
    #: what broke when these keys stopped being formatted numbers.
    parameters: dict[str, float] = field(default_factory=dict)
    measure_every: int = 0
    #: Which implementation produces this entry's artifacts: ``"cfr"`` for the textbook per-deal recursion
    #: in :mod:`pokergto.solver.cfr`, ``"vector"`` for the public-tree form in
    #: :mod:`pokergto.solver.vector`. The default is the textbook form on purpose: that one is the
    #: definition of correctness here, so a game has to be too big for it before the faster form takes
    #: over. ``tests/test_solver_vector.py`` holds the two against each other on every registered gate,
    #: which is what makes the choice an optimisation rather than a new claim.
    implementation: str = "cfr"
    assertions: tuple[Assertion, ...] = ()
    tolerances: dict[str, float] = field(default_factory=dict)
    notes: dict[str, str] = field(default_factory=dict)

    def build(self) -> GameTree:
        return self.builder()

    @property
    def expected_algorithm(self) -> str:
        """The ``algorithm`` string the artifact this entry produces has to carry.

        Derived rather than written twice: the solver names itself, and both ``tools/run_solver.py`` and
        the test that re-reads the committed artifact compare against this, so a registry that changed
        implementation without changing the label would fail instead of shipping an artifact that
        describes the wrong arithmetic.
        """
        return f"{self.algorithm}_vector" if self.implementation == "vector" else self.algorithm


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
    "nut_never_folded": "frequency_bounds",
    "worst_never_called": "frequency_bounds",
    "value_bracket": "value_bracket",
}


def _report(result: SolveResult) -> dict[str, dict[str, float]]:
    return result.strategy_report()


def assert_kuhn_value(
    _tree: GameTree, result: SolveResult, _cfg: dict[str, Any]
) -> tuple[float, float]:
    return result.game_value, KUHN_VALUE


def assert_king_calls_when_faced(
    _tree: GameTree, result: SolveResult, _cfg: dict[str, Any]
) -> tuple[float, float]:
    """Calling with the king when facing a bet is strictly dominant for either player, so every
    equilibrium does it. This is a *dominance* claim, which is why it can be asserted -- unlike "always
    open a bet with the king", which cannot (see the note on KUHN)."""
    report = _report(result)
    return 0.5 * (report["2:0:K"]["call"] + report["3:1:K"]["call"]), 1.0


def assert_jack_never_calls(
    _tree: GameTree, result: SolveResult, _cfg: dict[str, Any]
) -> tuple[float, float]:
    """Folding the jack to a bet is strictly dominant: it never wins a showdown, so calling only adds
    money to a lost pot."""
    report = _report(result)
    return 0.5 * (report["2:0:J"]["call"] + report["3:1:J"]["call"]), 0.0


def assert_jack_bluff_in_family(
    _tree: GameTree, result: SolveResult, _cfg: dict[str, Any]
) -> tuple[float, float]:
    """Player 0's jack-bluffing frequency may be anywhere in ``[0, 1/3]`` -- the equilibrium is a
    family, not a point. The assertion is on membership: demanding one particular member would be
    testing the implementation's trajectory, not game theory.

    The ``expected`` reported in the log is the family's upper bound, which is the number that actually
    constrains the check.
    """
    report = _report(result)
    return report["0:0:J"]["bet"], 1.0 / 3.0


def _make_one_street_builder(size: float) -> Callable[[], GameTree]:
    """Bound the bet size into its own function.

    A default-argument lambda (``lambda size=bet_size: ...``) is the usual shortcut and mypy cannot
    infer through it; a named factory makes the closure explicit and keeps the registry readable when
    the same game appears at three sizes.
    """

    def build() -> GameTree:
        return build_one_street(pot=1.0, bet_size=size)

    return build


def _one_street_entry(game: str, bet_size: float, iterations: int = 4000) -> ProofEntry:
    def assert_defense(
        tree: GameTree, result: SolveResult, _cfg: dict[str, Any]
    ) -> tuple[float, float]:
        report = _report(result)
        return report["1:1:catcher"]["call"], float(minimum_defense_frequency(1.0, bet_size))

    def assert_bluff_share(
        tree: GameTree, result: SolveResult, _cfg: dict[str, Any]
    ) -> tuple[float, float]:
        report = _report(result)
        nut = report["0:0:nut"]["bet"]
        air = report["0:0:air"]["bet"]
        measured = air / (nut + air) if (nut + air) > 0 else 0.0
        return measured, float(bluff_fraction_at_indifference(1.0, bet_size))

    def assert_value_bets(
        tree: GameTree, result: SolveResult, _cfg: dict[str, Any]
    ) -> tuple[float, float]:
        report = _report(result)
        return report["0:0:nut"]["bet"], 1.0

    def assert_toy_game_value(
        _tree: GameTree, result: SolveResult, _cfg: dict[str, Any]
    ) -> tuple[float, float]:
        """Hero's equilibrium value is ``pot * bet / (2 * (pot + bet))`` -- a third independent
        quantity that has to agree, not just the two frequencies.

        Derivation, so the assertion is not a fitted constant: the nut hand bets and gains ``pot/2``
        when the opponent folds plus ``bet`` when called, i.e. ``pot/2 + d*bet`` with ``d`` the call
        frequency. Air is indifferent by construction, earning exactly its check value of ``-pot/2``.
        Averaging the two equally likely holdings leaves ``d*bet/2 = pot*bet / (2(pot+bet))``.
        """
        return result.game_value, bet_size / (2.0 * (1.0 + bet_size))

    # The key is a name, not a formatted number: ``f"{1/3:g}"`` and ``f"{float(Fraction(1,3)):g}"``
    # differ in trailing digits, and an artifact filename that depends on float repr is how a
    # byte-determinism check starts failing for reasons nobody can read.
    return ProofEntry(
        game=game,
        parameters={"pot": 1.0, "bet_size": bet_size},
        family="toy_1street",
        builder=_make_one_street_builder(bet_size),
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
    parameters={"ante": ANTE},
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
def _leduc_entry(iterations: int = 10_000) -> ProofEntry:
    """Leduc's gates, none of which needs a closed form -- because there isn't one to cite.

    Three mechanisms, all computable from the tree alone:

    * **the value bracket.** Two exact best responses bound the true game value: ``-BR(1) <= v <= BR(0)``,
      and the width of that interval is ``2 x exploitability``. This is what lets the artifact publish a
      number for Leduc's value without trusting a solver's self-report or borrowing somebody else's table.
      The assertion measures the distance *outside* the bracket, so a passing run reports exactly ``0``.
    * **dominance at information sets the strategy actually reaches.** Folding the current nuts is
      strictly dominated, and so is calling with a hand that loses to every opponent holding. Both must
      survive into the solved strategy -- at the decisions that happen. Measured on the committed run, the
      residue that survives is ``1e-7`` at a reached information set and ``1e-2`` at the ones below the
      average strategy is whatever regret matching left behind and exploitability cannot see it, because
      getting there requires the opponent to walk a line they never walk. The exemption is the floor
      ``games.REACH_FLOOR``, stated here so a reader can re-run the claim with a different one.
    * **exploitability itself**, against the threshold below, in the half-sum convention.

    What this does *not* prove is stated where it matters: the bracket bounds the value, it does not
    identify a strategy, and Leduc has no analytic equilibrium to compare frequencies against. Anyone who
    wants that should read Kuhn's entry, which has it and says so.
    """
    def _frequency_at_reached(
        tree: GameTree,
        result: SolveResult,
        labels: tuple[str, ...],
        action: str,
    ) -> tuple[float, int]:
        positions = {label: index for index, label in enumerate(tree.infoset_labels)}
        matrix = pad_strategy(result.average_strategy, tree)
        reach = infoset_reach(tree, matrix)
        worst = 0.0
        exempt = 0
        for label in labels:
            index = positions[label]
            if reach[index] < REACH_FLOOR:
                exempt += 1
                continue
            choices = result.infoset_actions[index]
            if action not in choices:
                continue
            worst = max(worst, float(result.average_strategy[index][choices.index(action)]))
        return worst, exempt

    def assert_nut_never_folded(
        tree: GameTree, result: SolveResult, _cfg: dict[str, Any]
    ) -> tuple[float, float]:
        worst, _exempt = _frequency_at_reached(tree, result, leduc_dominance(tree).nut, "fold")
        return worst, 0.0

    def assert_worst_never_called(
        tree: GameTree, result: SolveResult, _cfg: dict[str, Any]
    ) -> tuple[float, float]:
        worst, _exempt = _frequency_at_reached(tree, result, leduc_dominance(tree).worst, "call")
        return worst, 0.0

    def assert_value_bracket(
        tree: GameTree, result: SolveResult, _cfg: dict[str, Any]
    ) -> tuple[float, float]:
        matrix = pad_strategy(result.average_strategy, tree)
        upper, lower = br_pair(tree, matrix)
        outside = max(0.0, result.game_value - upper) + max(0.0, -lower - result.game_value)
        return outside, 0.0

    return ProofEntry(
        game="leduc",
        parameters={"ante": ANTE, "bet_flop": 2.0, "bet_turn": 4.0, "cap": 2},
        family="leduc",
        builder=lambda: build_leduc(ante=ANTE),
        algorithm="cfr_plus",
        #: The vector form, because the per-deal recursion needs about seventy-six minutes for the
        #: iterations this gate wants. See ``ProofEntry.implementation``.
        implementation="vector",
        iterations=iterations,
        exploitability_threshold=1e-5,
        measure_every=500,
        assertions=(
            Assertion(
                "value_bracket",
                {
                    "zh": "博弈价值必须落在两条最佳响应给出的区间 [-BR(1), BR(0)] 内",
                    "en": "The game value must lie inside the bracket [-BR(1), BR(0)] the two exact best "
                    "responses give",
                },
                assert_value_bracket,
            ),
            Assertion(
                "nut_never_folded",
                {
                    "zh": "在真正会被走到的信息集上，坚果牌绝不能弃牌",
                    "en": "At information sets the strategy actually reaches, the nut hand is never folded",
                },
                assert_nut_never_folded,
            ),
            Assertion(
                "worst_never_called",
                {
                    "zh": "在真正会被走到的信息集上，必输牌绝不跟注",
                    "en": "At information sets the strategy actually reaches, a hand losing to every "
                    "opponent holding never calls",
                },
                assert_worst_never_called,
            ),
        ),
        tolerances={
            "value_bracket": 1e-12,
            # Measured at the committed solve: 7.8e-8 and 1.3e-7 respectively, across the 150 nut and 316
            # strictly-worst information sets that clear the reach floor. Read those as "one dominated
            # decision in ten million", not as zero -- a converged average strategy keeps a residue that
            # shrinks like 1/sqrt(T), and a gate that demanded exact zero would be a gate on the rounding.
            # (First draft of this comment said "measured exactly zero", because it was reading
            # ``strategy_report()``, which rounds to six decimal places. The assertion reads the raw
            # strategy. Numbers that look like zero and numbers that are zero are different claims.)
            "nut_never_folded": 1e-5,
            "worst_never_called": 1e-5,
        },
        notes={
            "zh": "Leduc 没有解析均衡可抄，所以这里用的是不需要闭式的三门禁：价值区间、可达信息集上的占优关系、"
            "以及可剥削度。区间给出的是价值的边界，不是策略的唯一性；未走到的信息集上的频率不是结论，是噪声。",
            "en": "Leduc has no analytic equilibrium to copy, so the gates are the three that do not need one: "
            "the value bracket, dominance at reached information sets, and exploitability. The bracket bounds "
            "the value, not the strategy's uniqueness, and a frequency at an unreachable information set is "
            "noise rather than a finding.",
        },
    )


PUBLISHED_PROOFS: dict[str, ProofEntry] = {
    KUHN.game: KUHN,
    "toy_1street_one_third": _one_street_entry("toy_1street_one_third", float(Fraction(1, 3))),
    "toy_1street_half_pot": _one_street_entry("toy_1street_half_pot", 0.5),
    "toy_1street_three_quarter_pot": _one_street_entry(
        "toy_1street_three_quarter_pot", float(Fraction(3, 4))
    ),
    "toy_1street_pot": _one_street_entry("toy_1street_pot", 1.0),
    # The overbet row is not decoration: chapter 04's claim is that a size is a *consequence* of the
    # range and the board, and the only way to show the closed forms still hold at 2x pot -- where the
    # bluff share rises to 40% and the value:bluff ratio falls to 3:2 -- is to solve it and check.
    "toy_1street_two_pot": _one_street_entry("toy_1street_two_pot", 2.0),
    "leduc": _leduc_entry(),
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
