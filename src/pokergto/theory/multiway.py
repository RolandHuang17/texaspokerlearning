"""Multiway pots: what changes when more than one opponent gets a vote.

Chapter 02's MDF assumes a single defender. With ``N`` defenders a bluff must beat *all* of them, so
the fold condition is ``N`` independent folds rather than one:

    (1 - d)^N = bet / (pot + bet)      ->      d = 1 - (bet / (pot + bet))^(1/N)

Two consequences worth internalising, both computed rather than asserted:

* the **exponent is 1/N**. Not ``N - 1``, not ``N``. An earlier draft of this curriculum wrote
  ``1 - (1 - single)^(N-1)``, which is wrong, and the error is instructive: at ``N = 1`` the wrong
  formula collapses to the right answer, so it survives a single sanity check and only breaks once you
  add an opponent. The ``N = 1`` fallback is therefore a real test (``tests/test_odds.py``), not
  decoration.
* per-player defense falls as opponents are added while the **joint** defense requirement stays at the
  heads-up number. Two opponents each defend 29.3% against a pot-sized bet; together they defend 50%.
  "More players means more defense" and "more players means each player defends less" are both true
  and do not conflict.

What this module refuses to do is hide a heuristic inside a formula. The two things it reports are
separate by design: the independence-based frequencies above, which are exact *given* independence and
record that assumption wherever they are used; and the combinatorics below, which are exact with no
assumption at all -- count the combos in a betting range that can actually win, and the collapse of
bluffing three- and four-way stops being a rule to memorise. Card removal couples real defenders, so
the first set is an approximation and the second is not.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..cards import Card
from ..errors import InputError
from ..evaluator import Category, best_score, category_of
from ..odds import Number, as_fraction, minimum_defense_frequency
from ..ranges import Range

__all__ = [
    "MultiwayReport",
    "bluff_value_ratio",
    "continuation_fold_requirement",
    "describe",
    "joint_defense",
    "per_player_defense",
    "value_and_air_combos",
    "who_can_win",
]


def per_player_defense(pot: Number, bet: Number, n_opponents: int) -> float:
    """``1 - (bet/(pot+bet))**(1/N)``. Assumes independent defenders; see the module docstring."""
    if n_opponents < 1:
        raise InputError("need at least one opponent")
    p, b = as_fraction(pot), as_fraction(bet)
    if b <= 0:
        raise InputError("bet must be positive")
    if n_opponents == 1:
        return float(minimum_defense_frequency(p, b))
    return float(1.0 - float(b / (p + b)) ** (1.0 / n_opponents))


def joint_defense(pot: Number, bet: Number, n_opponents: int) -> float:
    """Probability at least one of ``N`` independent defenders continues.

    Identically ``pot/(pot+bet)`` for every ``N``, which is the point: the table's obligation does not
    shrink, it is spread over more people.
    """
    return 1.0 - (1.0 - per_player_defense(pot, bet, n_opponents)) ** n_opponents


def continuation_fold_requirement(pot: Number, bet: Number, n_opponents: int) -> float:
    """How often *everyone* must fold for the bluff to break even: ``bet/(pot+bet)``, unchanged by N.

    The bluff's requirement is on the joint fold, never on one player's fold. Conflating those is how
    "bluffing is harder multiway" turns into "each player must fold more", which is backwards.
    """
    p, b = as_fraction(pot), as_fraction(bet)
    return float(b / (p + b))


@dataclass(frozen=True, slots=True)
class MultiwayReport:
    """The three numbers, side by side, so the fallacy has nowhere to hide."""

    pot: float
    bet: float
    n_opponents: int
    per_player: float
    joint: float
    heads_up_mdf: float
    assumption: str = "defenders treated as independent; card removal makes this an approximation"


def describe(pot: Number, bet: Number, n_opponents: int) -> MultiwayReport:
    p, b = float(as_fraction(pot)), float(as_fraction(bet))
    return MultiwayReport(
        pot=p,
        bet=b,
        n_opponents=n_opponents,
        per_player=per_player_defense(p, b, n_opponents),
        joint=joint_defense(p, b, n_opponents),
        heads_up_mdf=float(minimum_defense_frequency(p, b)),
    )


def value_and_air_combos(
    betting_range: Range,
    board: tuple[Card, ...],
    *,
    minimum_category: Category = Category.ONE_PAIR,
) -> tuple[float, float]:
    """Split a betting range into combos that can win and combos that cannot, by enumeration.

    ``minimum_category`` is the bar for "can win": the default one pair is what a hand needs to beat a
    random continuing range at showdown. Raise it to two pair on a wet board and watch how fast a
    range's value share collapses -- that is the whole multiway story in one parameter.
    """
    if not 3 <= len(board) <= 5:
        raise InputError("board must be 3 to 5 cards")
    value = air = 0.0
    for first, second, weight in betting_range:
        score = best_score((first, second), board)
        if category_of(score) >= int(minimum_category):
            value += weight
        else:
            air += weight
    return value, air


def bluff_value_ratio(
    betting_range: Range,
    board: tuple[Card, ...],
    *,
    minimum_category: Category = Category.ONE_PAIR,
) -> float:
    """Actual air-to-value combo ratio of a range on a board.

    Compare this against chapter 02's indifference ratio and the discrepancy *is* the lesson: the
    algebra says what a balanced range must look like, the combinatorics says what your range can
    look like, and on a board where nothing is worth a value bet the second number is the binding
    constraint.
    """
    value, air = value_and_air_combos(betting_range, board, minimum_category=minimum_category)
    if value == 0:
        raise InputError(
            "the range holds no combo that can win, so there is no value side to form a ratio with"
        )
    return air / value


def who_can_win(
    ranges: tuple[Range, ...],
    board: tuple[Card, ...],
    *,
    minimum_category: Category = Category.ONE_PAIR,
) -> list[float]:
    """Share of all able-to-win combos contributed by each range, positionally.

    Going from two players to five roughly triples the chance that *someone* holds a pair or better,
    and that is the mechanism behind the frequency collapse. Nothing here assumes independence and
    nothing here needs a solver: it is counting.
    """
    if len(ranges) < 2:
        raise InputError("who_can_win needs at least two ranges")
    if not 3 <= len(board) <= 5:
        raise InputError("board must be 3 to 5 cards")
    able = [
        value_and_air_combos(rng, board, minimum_category=minimum_category)[0] for rng in ranges
    ]
    total = sum(able)
    if total == 0:
        return [0.0 for _ in ranges]
    return [share / total for share in able]
