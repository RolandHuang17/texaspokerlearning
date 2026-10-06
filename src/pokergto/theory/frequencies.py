"""Frequency balance: the conditions a mixed strategy has to satisfy to be unexploitable.

This module is the bridge between chapter 02's algebra and chapter 08's solver. The functions here
state the *test*, not the answer: given a bet size and a candidate pair of frequencies, they report
how far the pair is from making the bluff-catcher and the bluffer indifferent. The solver then has to
drive those gaps to zero, and :mod:`pokergto.solver.proofs` asserts exactly that -- which is why a bug
in ``odds.py`` and a bug in ``cfr.py`` cannot both go unnoticed.

Two conventions that cause most of the confusion in this area, stated once:

* ``pot`` is the money in the middle **before** the bet; ``bet`` is what is added.
* "defense frequency" is the share of the defender's **combos** that continue. "Call frequency" is one
  action's share inside that. A range that defends 70% by raising 20% and calling 50% is at the MDF
  floor even though it calls only half as often, and reading the second number as the first is the
  error this distinction exists to prevent.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from ..errors import InputError
from ..odds import (
    Number,
    as_fraction,
    bluff_fraction_at_indifference,
    minimum_defense_frequency,
    required_fold_frequency,
    value_to_bluff_ratio,
)

__all__ = [
    "BalanceReport",
    "balance_bluff_and_value",
    "bluff_indifference_gap",
    "defense_indifference_gap",
    "is_frequency_balanced",
    "value_bluff_split",
]

TOLERANCE = 1e-6


@dataclass(frozen=True, slots=True)
class BalanceReport:
    """How far a candidate strategy pair is from the two indifference conditions."""

    pot: float
    bet: float
    bet_over_pot: float
    defense_frequency: float
    mdf_required: float
    bluff_fraction: float
    bluff_fraction_required: float
    value_to_bluff: float
    fold_frequency_realised: float
    fold_frequency_required_by_bluff: float

    @property
    def defense_gap(self) -> float:
        return self.defense_frequency - self.mdf_required

    @property
    def bluff_gap(self) -> float:
        return self.bluff_fraction - self.bluff_fraction_required

    @property
    def exploitable_side(self) -> str:
        """Who is being exploited, and by what.

        Under-defending makes bluffs profitable for the aggressor; over-defending makes value bets
        profitable because you are calling with hands that beat only air. Both are leaks, and they are
        leaks in opposite directions, which is why the sign of the gap is the useful quantity.
        """
        if self.defense_gap < -TOLERANCE:
            return "under-defending: any two cards profit as a bluff"
        if self.defense_gap > TOLERANCE:
            return "over-defending: value bets print money against bluff-catchers"
        if self.bluff_gap > TOLERANCE:
            return "too many bluffs: the opponent profitably calls lighter"
        if self.bluff_gap < -TOLERANCE:
            return "too few bluffs: the opponent profitably folds everything but the nuts"
        return "balanced"


def balance_bluff_and_value(
    pot: Number, bet: Number, *, defense_frequency: Number, bluff_fraction: Number
) -> BalanceReport:
    """Compare a candidate defense frequency and bluff share against the closed forms."""
    p, b = as_fraction(pot), as_fraction(bet)
    if b <= 0:
        raise InputError("balance requires a positive bet")
    return BalanceReport(
        pot=float(p),
        bet=float(b),
        bet_over_pot=float(b / p),
        defense_frequency=float(as_fraction(defense_frequency)),
        mdf_required=float(minimum_defense_frequency(p, b)),
        bluff_fraction=float(as_fraction(bluff_fraction)),
        bluff_fraction_required=float(bluff_fraction_at_indifference(p, b)),
        value_to_bluff=float(value_to_bluff_ratio(p, b)),
        fold_frequency_realised=float(1 - as_fraction(defense_frequency)),
        fold_frequency_required_by_bluff=float(required_fold_frequency(p, b)),
    )


def defense_indifference_gap(pot: Number, bet: Number, defense_frequency: Number) -> float:
    """Signed distance from the MDF floor. Zero means the bluff is exactly indifferent.

    This is the quantity ``pokergto.solver.proofs`` requires the solver to drive to zero: the
    counterfactual value of a pure bluff is linear in this gap, so a gap of ``g`` gifts the aggressor
    roughly ``g`` times the pot per bluff attempt.
    """
    return float(as_fraction(defense_frequency)) - float(minimum_defense_frequency(pot, bet))


def bluff_indifference_gap(pot: Number, bet: Number, bluff_fraction: Number) -> float:
    """Signed distance from the bluff share that makes a bluff-catcher indifferent."""
    return float(as_fraction(bluff_fraction)) - float(bluff_fraction_at_indifference(pot, bet))


def is_frequency_balanced(
    pot: Number,
    bet: Number,
    *,
    defense_frequency: Number,
    bluff_fraction: Number,
    tolerance: float = 1e-3,
) -> bool:
    """Both indifference conditions met within ``tolerance``.

    The default tolerance is a teaching tolerance, not a numerical one: it is looser than the solver's
    own gates (``solver/proofs.py``) because the quantity a learner can check by hand is the rounded
    frequency, not the float.
    """
    return (
        abs(defense_indifference_gap(pot, bet, defense_frequency)) <= tolerance
        and abs(bluff_indifference_gap(pot, bet, bluff_fraction)) <= tolerance
    )


def value_bluff_split(
    pot: Number, bet: Number, total_betting_combos: Number
) -> tuple[float, float]:
    """``(value combos, bluff combos)`` for a betting range of the given size at indifference.

    Combo arithmetic, not class arithmetic: ``total_betting_combos`` is combos, and the result is the
    split that keeps a bluff-catcher honest. Feeding it a class count is the fastest way to a wrong
    answer here.
    """
    share = float(bluff_fraction_at_indifference(pot, bet))
    combos = float(as_fraction(total_betting_combos))
    if combos <= 0:
        raise InputError("a betting range with no combos has no split")
    bluffs = combos * share
    return combos - bluffs, bluffs


def break_even_defense_for_sizes(pot: Number, sizes: Sequence[Number]) -> list[tuple[float, float]]:
    """``[(bet, mdf), ...]`` for a ladder of bet sizes -- the shape of the curve chapter 02 draws."""
    p = as_fraction(pot)
    return [(float(as_fraction(size)), float(minimum_defense_frequency(p, size))) for size in sizes]
