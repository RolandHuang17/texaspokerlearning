"""Expected value of a single decision, under one stated convention.

**The convention, which every formula here assumes.** Measure the decision only, relative to
folding. Folding is ``0`` by definition — whatever you already committed to the pot is gone in both
branches, so it cancels out of every difference and never appears in a formula.

* ``pot``  — chips in the middle *before* the actor adds anything.
* ``bet``  — chips the actor must add.
* ``e``    — hero's equity when the money goes in.

Then, from the rules of the game rather than from folklore:

* calling wins ``pot + bet`` (the pot plus the opponent's bet) and loses ``bet``, so
  ``EV(call) = e·(pot + 2·bet) − bet``, and breaking even needs ``e = bet/(pot + 2·bet)``;
* betting wins ``pot`` uncontested with probability ``f`` (everyone folds) and otherwise realizes
  ``EV(call)`` at size ``bet``, so
  ``EV(bet) = f·pot + (1−f)·(e·(pot + 2·bet) − bet)``;
* a pure bluff (``e = 0``) collapses to the identity the whole curriculum hangs on:
  ``EV(bluff) = f·pot − (1−f)·bet``, zero exactly when ``f = bet/(pot+bet)``, whose complement is
  the minimum defense frequency.

This is why ``EV(fold)`` is written as a function returning ``0.0`` instead of being skipped: the
zero is a *choice of reference point*, and learners who never state it end up double-counting their
own prior money — the most common arithmetic error in self-taught hand reviews.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import cast

from .odds import Number, as_fraction

Result = float | Fraction


def ev_fold(*, exact: bool = False) -> Result:
    """``0`` by convention: the reference point every other action is measured against."""
    return Fraction(0) if exact else 0.0


def ev_call(pot: Number, bet: Number, equity: Number, *, exact: bool = False) -> Result:
    """``e(pot + 2bet) - bet``. ``bet`` here is the amount to face."""
    p, b, e = (as_fraction(x) for x in (pot, bet, equity))
    value = e * (p + 2 * b) - b
    return value if exact else float(value)


def ev_bet(
    pot: Number,
    bet: Number,
    fold_frequency: Number,
    equity_when_called: Number,
    *,
    exact: bool = False,
) -> Result:
    """``f·pot + (1-f)·(e(pot + 2bet) - bet)``.

    ``fold_frequency`` is the probability that *every* opponent folds. With several defenders this
    is where the multiway algebra bites: an individual defense rate of 30% against a pot-sized bet
    is a joint fold rate of 49%, not 70%. See :func:`pokergto.odds.defense_frequency_multiway`.
    """
    p, b, f, e = (as_fraction(x) for x in (pot, bet, fold_frequency, equity_when_called))
    if not 0 <= f <= 1:
        raise ValueError(f"fold_frequency must be in [0,1], got {float(f)}")
    when_called = e * (p + 2 * b) - b
    value = f * p + (1 - f) * when_called
    return value if exact else float(value)


def ev_pure_bluff(
    pot: Number, bet: Number, fold_frequency: Number, *, exact: bool = False
) -> Result:
    """``f·pot - (1-f)·bet``. Named separately because it is the equation MDF is *derived from*;
    a learner should be able to write it down from memory.
    """
    return ev_bet(pot, bet, fold_frequency, 0, exact=exact)


def ev_pure_value(
    pot: Number, bet: Number, fold_frequency: Number, *, exact: bool = False
) -> Result:
    """The always-called-and-wins bound: ``f·pot + (1-f)·(pot + bet)``. Useful for sizing: a
    monster's EV rises with bet size only through the fold frequency it can sustain.
    """
    return ev_bet(pot, bet, fold_frequency, 1, exact=exact)


def ev_check(pot: Number, equity_at_showdown: Number, *, exact: bool = False) -> Result:
    """Checking and seeing the showdown for free: ``e·pot``."""
    p, e = (as_fraction(x) for x in (pot, equity_at_showdown))
    value = e * p
    return value if exact else float(value)


def ev_shove(
    pot: Number, stack: Number, equity: Number, call_frequency: Number, *, exact: bool = False
) -> Result:
    """All-in as a special case of :func:`ev_bet` with ``bet = stack``. Keeping it as its own entry
    point is a teaching choice: short-stack MTT play *is* the case where ``bet`` is not a free
    variable, and chapter 12 works entirely in these terms.
    """
    return ev_bet(pot, stack, 1 - as_fraction(call_frequency), equity, exact=exact)


@dataclass(frozen=True, slots=True)
class DecisionComparison:
    """The output of :func:`compare`. One row per candidate action, ranked, with regrets."""

    action: str
    bet: float
    ev: float
    ev_exact: Fraction
    best: bool

    @property
    def regret(self) -> float:
        """EV lost against the best action in this table. A "common mistake" section states this,
        so the learner knows the price of the leak rather than only that it is a leak.
        """
        return 0.0 if self.best else self.ev


def compare(
    pot: Number,
    candidates: Sequence[tuple[str, Number]],
    *,
    fold_frequencies: dict[str, Number],
    equities_when_called: dict[str, Number],
) -> list[DecisionComparison]:
    """Rank several bet sizes against each other.

    ``candidates`` maps an action label to its size (0 means check/fold is not modelled here; pass
    it explicitly as ``("check", 0)`` and a fold frequency of 0 to get showdown EV).
    """
    rows: list[DecisionComparison] = []
    for action, size in candidates:
        bet = as_fraction(size)
        if bet == 0:
            value = cast(Fraction, ev_check(pot, equities_when_called[action], exact=True))
        else:
            value = cast(
                Fraction,
                ev_bet(
                    pot, bet, fold_frequencies[action], equities_when_called[action], exact=True
                ),
            )
        rows.append(DecisionComparison(action, float(bet), float(value), value, False))
    best_value = max(row.ev_exact for row in rows)
    ranked = [
        DecisionComparison(r.action, r.bet, r.ev, r.ev_exact, r.ev_exact == best_value)
        for r in rows
    ]
    ranked.sort(key=lambda row: row.ev_exact, reverse=True)
    return ranked


def regret(rows: Sequence[DecisionComparison]) -> dict[str, float]:
    """EV lost by each action relative to the best. This is the quantity the trainer reports as
    bb/100, and the quantity a "leak" is defined as.
    """
    if not rows:
        return {}
    best = max(row.ev_exact for row in rows)
    return {row.action: float(best - row.ev_exact) for row in rows}
