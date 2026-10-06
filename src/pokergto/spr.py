"""SPR, pot commitment, and implied odds: when the pre-flop money decides the post-flop game.

**SPR (stack-to-pot ratio)** is ``effective_stack / pot`` at the moment a street begins. It is the
single number that converts "what should I do with top pair?" from a memorised line into an
arithmetic threshold, because it fixes how much of your stack a full bet-sizing sequence can move.

The commitment question then has an exact answer rather than a vibe: with ``S`` chips behind and a
pot of ``P``, shoving all-in risks ``S`` to win ``P`` and needs
``equity = S / (P + 2S) = SPR / (1 + 2·SPR)``. That is a one-line formula whose consequences fill
chapter 03.
"""

from __future__ import annotations

from collections.abc import Sequence
from fractions import Fraction

from .odds import Number, as_fraction


def spr(effective_stack: Number, pot: Number) -> float:
    """Stack-to-pot ratio at the start of a street."""
    s, p = float(as_fraction(effective_stack)), float(as_fraction(pot))
    if p <= 0:
        raise ValueError("SPR needs a positive pot")
    return s / p


def all_in_equity_needed(pot: Number, stack: Number, *, exact: bool = False) -> float | Fraction:
    """Equity required to commit ``stack`` into ``pot``: ``S/(P + 2S)``.

    Written both ways in the lessons, because the SPR form is the memorable one and the pot form is
    the one you actually compute with: ``SPR/(1 + 2·SPR)``.
    """
    p, s = (as_fraction(x) for x in (pot, stack))
    value = s / (p + 2 * s)
    return value if exact else float(value)


def all_in_equity_needed_from_spr(spr_value: Number, *, exact: bool = False) -> float | Fraction:
    """The same threshold as a function of SPR alone."""
    x = as_fraction(spr_value)
    value = x / (1 + 2 * x)
    return value if exact else float(value)


def commit_threshold_equity(spr_value: Number, *, exact: bool = False) -> float | Fraction:
    """Alias of :func:`all_in_equity_needed_from_spr` under the name chapter 03 uses. Kept as a
    deliberate synonym, not a second implementation.
    """
    return all_in_equity_needed_from_spr(spr_value, exact=exact)


def spr_commitment_table(spr_values: Sequence[Number] | None = None) -> list[dict[str, object]]:
    """The table that makes "SPR decides commitment" checkable rather than rhetorical.

    ``digits`` is fixed here so docs, trainer and CLI show identical values.
    """
    values = (
        list(spr_values)
        if spr_values is not None
        else [0.25, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 13.0, 20.0]
    )
    rows: list[dict[str, object]] = []
    for value in values:
        x = as_fraction(value)
        needed = all_in_equity_needed_from_spr(x, exact=True)
        rows.append(
            {
                "spr": round(float(x), 4),
                "all_in_equity_needed": round(float(needed), 6),
                # A hand needs this much equity to be a profitable stack-off; the "class" column is
                # what makes the number usable at a table, and it is derived, not asserted.
                "one_pair_commits": bool(float(needed) <= 0.5),
                "top_pair_two_kickers_commits": bool(float(needed) <= 0.65),
            }
        )
    return rows


def implied_odds_break_even_equity(
    pot: Number,
    bet: Number,
    expected_future_winnings: Number,
    *,
    exact: bool = False,
) -> float | Fraction:
    """Equity needed to call when you expect to *win* more money later on the streets.

    ``bet / (pot + 2·bet + future)``: extra future value lowers the equity you need. This is the
    formal statement of implied odds, and the reason a suited connector plays a 4-bet-free pot
    differently from a same-equity raggie hand.
    """
    p, b, f = (as_fraction(x) for x in (pot, bet, expected_future_winnings))
    value = b / (p + 2 * b + f)
    return value if exact else float(value)


def reverse_implied_odds_penalty(
    pot: Number, bet: Number, expected_future_losses: Number, *, exact: bool = False
) -> float | Fraction:
    """The mirror case: equity needed rises when you expect to pay off. Same algebra, opposite sign,
    which is why "dominated draws exit fast" is arithmetic rather than temperament.
    """
    p, b, f = (as_fraction(x) for x in (pot, bet, expected_future_losses))
    value = (b + f) / (p + 2 * b)
    return value if exact else float(value)


def max_profitable_commit_fraction(spr_value: Number, equity: Number) -> float:
    """Fraction of the remaining stack you may commit at this equity before the extra money turns
    into a losing shove. Chapter 03-08 uses it to separate "float" from "shove" without a
    memorised chart.

    Derivation: committing ``S'`` needs ``S'/(P + 2S')`` equity, which rises with ``S'`` and is
    bounded by ``1/2``. Solving ``S'/(P+2S') = e`` gives ``S' = eP/(1-2e)``, hence
    ``f = S'/S = e/((1-2e)·SPR)``. Any equity above ``1/2`` means the bound is never reached and the
    whole stack is committable.
    """
    x = float(as_fraction(spr_value))
    e = float(as_fraction(equity))
    if x <= 0:
        return 1.0
    if e <= 0:
        return 0.0
    if e >= 0.5:
        return 1.0
    fraction = e / ((1 - 2 * e) * x)
    return max(0.0, min(1.0, fraction))
