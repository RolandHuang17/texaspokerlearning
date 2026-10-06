"""The algebra of one decision. This module is the correctness spine of the curriculum.

Everything here is exact arithmetic over :class:`fractions.Fraction` when asked for, because a
teaching repository that rounds ``1/3`` to ``0.33`` and then cites it as derived is committing the
same sin as the folk wisdom it replaces. The convention:

* functions accept ``int | float | Fraction``;
* they return ``float`` by default and ``Fraction`` when ``exact=True``;
* tests pin the exact values, and the generated tables in ``data/gen/tables`` are produced with
  ``exact=True`` then formatted, so a lesson's number and its test are the same rational.

The three facts every later chapter leans on:

1. **Minimum defense frequency** ``d = pot / (pot + bet)``. Derived in chapter 02 from the
   indifference of a pure bluff: a bluff risks ``bet`` to win ``pot``, so it breaks even when the
   opponents fold with probability ``bet / (pot + bet)``. Defending more than ``pot/(pot+bet)``
   makes bluffing profitable for them; defending less makes your own folds exploitable.
2. **Bluff fraction at indifference** ``b = bet / (pot + 2*bet)`` of the *betting* range, where
   ``bet`` is measured relative to the pot before the bet. Derived from a bluff-catcher's
   indifference: it wins ``pot + bet`` against value and loses ``bet``... see chapter 02-04.
3. **Multiway defense** ``d = 1 - (bet / (pot + bet)) ** (1 / N)`` for ``N`` opponents acting
   after you, because a bluff must beat *all* of them to steal: ``(1-d)^N = bet/(pot+bet)``.
   Setting ``N = 1`` returns fact 1, which is the self-check the tests run.

Fact 3 assumes defenders choose independently. Card removal makes that false in a real deal — the
assumption is recorded in ``provenance.assumptions`` of every artifact that uses it, and stated in
the lesson, because a named assumption is a smaller lie than an implied one.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import cast

Number = int | float | Fraction

#: The sizing ladder every generated table walks. Pot fractions, bet size relative to the pot
#: before the bet. 1/3 pot and overbets are not conventions we adopt; they are things chapter 04
#: has to justify, and this ladder is what it justifies them against.
STANDARD_SIZES: tuple[Fraction, ...] = (
    Fraction(1, 4),
    Fraction(1, 3),
    Fraction(1, 2),
    Fraction(2, 3),
    Fraction(3, 4),
    Fraction(1),
    Fraction(3, 2),
    Fraction(2),
)


def as_fraction(value: Number) -> Fraction:
    """Convert without decimal round-trips. Floats go through ``limit_denominator`` so that
    ``0.3333333333333333`` becomes ``1/3`` rather than a 17-digit rational.
    """
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int):
        return Fraction(value)
    return Fraction(str(value)).limit_denominator(10**6)


def _out(value: Fraction, *, exact: bool) -> Number:
    return value if exact else float(value)


def pot_odds(pot: Number, bet: Number, *, exact: bool = False) -> Number:
    """Odds offered by calling ``bet`` into ``pot``: ``pot / bet`` (expressed as a ratio, e.g. 2.0
    for "2:1"). The *equity* you need is the reciprocal-ish form below.
    """
    p, b = as_fraction(pot), as_fraction(bet)
    if b <= 0:
        raise ValueError("pot_odds needs a positive bet")
    return _out(p / b, exact=exact)


def break_even_percentage(risk: Number, reward: Number, *, exact: bool = False) -> Number:
    """Probability of winning required for a gamble of ``risk`` to win ``reward`` to break even."""
    r, w = as_fraction(risk), as_fraction(reward)
    if r + w <= 0:
        raise ValueError("risk + reward must be positive")
    return _out(r / (r + w), exact=exact)


def equity_needed_to_call(pot: Number, bet: Number, *, exact: bool = False) -> Number:
    """Equity required to call ``bet`` into ``pot``: ``bet / (pot + 2*bet)``.

    Calling puts ``bet`` in, making the final pot ``pot + 2*bet`` (yours plus the caller-to-face's,
    already there). You need your share of that pot to at least equal your investment, which is
    exactly ``bet / (pot + 2*bet)``. Derived step by step in chapter 02-02.
    """
    p, b = as_fraction(pot), as_fraction(bet)
    if b <= 0:
        raise ValueError("bet must be positive")
    return _out(b / (p + 2 * b), exact=exact)


def required_fold_frequency(pot: Number, bet: Number, *, exact: bool = False) -> Number:
    """How often a bluff must win outright (all opponents fold) to break even: ``bet/(pot+bet)``."""
    p, b = as_fraction(pot), as_fraction(bet)
    return _out(b / (p + b), exact=exact)


def minimum_defense_frequency(pot: Number, bet: Number, *, exact: bool = False) -> Number:
    """MDF: the fraction of your range you must continue with (call or raise) so that a pure bluff
    cannot print money: ``pot / (pot + bet)``.
    """
    p, b = as_fraction(pot), as_fraction(bet)
    if p + b <= 0:
        raise ValueError("pot + bet must be positive")
    return _out(p / (p + b), exact=exact)


#: The name lessons cite. ``mdf`` and ``defense_frequency`` are kept as aliases so prose, code and
#: generated tables can use whichever reads best without creating a second implementation.
defense_frequency = minimum_defense_frequency
mdf = minimum_defense_frequency


def bluff_fraction_at_indifference(pot: Number, bet: Number, *, exact: bool = False) -> Number:
    """Fraction of a *betting* range that must be bluffs for a bluff-catcher to be indifferent
    between calling and folding: ``bet / (pot + 2*bet)``.
    """
    p, b = as_fraction(pot), as_fraction(bet)
    return _out(b / (p + 2 * b), exact=exact)


def value_to_bluff_ratio(pot: Number, bet: Number, *, exact: bool = False) -> Number:
    """Value combos per bluff combo at indifference: ``(pot + bet) / bet``.

    1/3 pot -> 4.0 (4:1), 1/2 pot -> 3.0, 2/3 pot -> 2.5, pot -> 2.0, 2x pot -> 1.5. These are the
    numbers a memorised "bluff-to-value ratio" chart is supposed to contain, and the reason the
    overbet side of that chart looks so bluff-heavy: a big bet only needs its bluffs to work less
    often because it risks more, and the ratio moves the opposite way to intuition.
    """
    b = as_fraction(bluff_fraction_at_indifference(pot, bet, exact=True))
    if b == 0:
        raise ValueError("zero bluffs has no finite ratio")
    return _out((1 - b) / b, exact=exact)


def defense_frequency_multiway(
    pot: Number, bet: Number, n_opponents: int, *, exact: bool = False
) -> Number:
    """Per-opponent MDF with ``n_opponents`` players still to act.

    ``(1-d)^N = bet/(pot+bet)``  ->  ``d = 1 - (bet/(pot+bet))^(1/N)``.

    The exponent is ``1/N``, **not** ``N`` and not ``N-1``. Two checks a learner can do by hand:
    ``N=1`` returns the ordinary MDF, and for a pot-sized bet with ``N=2`` each player defends
    29.29% while ``1-(1-d)^2`` = 50% is the ordinary pot-sized MDF, because *together* they must
    defend half the time.

    Assumes independent defenders; see the module docstring.
    """
    if n_opponents < 1:
        raise ValueError("need at least one opponent")
    if n_opponents == 1:
        return minimum_defense_frequency(pot, bet, exact=exact)
    if exact:
        raise ValueError(
            "multiway MDF involves an N-th root, which is irrational for most inputs; "
            "call with exact=False, or request N=1 for the closed form"
        )
    p, b = as_fraction(pot), as_fraction(bet)
    single_fold = float(b / (p + b))
    return float(1.0 - single_fold ** (1.0 / n_opponents))


def at_least_one_defense(per_player_frequency: Number, n_opponents: int) -> float:
    """Probability that at least one of ``n`` independent defenders continues."""
    d = float(as_fraction(per_player_frequency))
    if not 0.0 <= d <= 1.0:
        raise ValueError("frequency must be within [0,1]")
    return 1.0 - (1.0 - d) ** n_opponents


def effective_mdf_from_multiway(pot: Number, bet: Number, n_opponents: int) -> float:
    """The joint defense requirement, which is the single number worth memorising: it is exactly the
    heads-up MDF. Per-player defense falls as opponents are added; the *table's* total defense does
    not. Chapter 07-01 turns this into a lesson.
    """
    return at_least_one_defense(defense_frequency_multiway(pot, bet, n_opponents), n_opponents)


@dataclass(frozen=True, slots=True)
class SizingRow:
    """One row of the sizing table every odds lesson opens with. Field order is column order."""

    size: float
    size_label: str
    pot_odds: float
    equity_needed: float
    mdf: float
    bluff_fraction: float
    value_to_bluff: float
    fold_frequency_needed: float


def _label(size: Fraction) -> str:
    if size.denominator == 1:
        return f"{size.numerator}x pot"
    return f"{size.numerator}/{size.denominator} pot"


def sizing_table(
    sizes: Iterable[Number] | None = None, *, pot: Number = 1, digits: int = 6
) -> list[dict[str, object]]:
    """The table generated into ``data/gen/tables`` and injected into lessons and the trainer.

    Numbers are computed over Fractions and rounded only at the end. ``digits`` is centralised here
    so every consumer formats identically (ADR-0001 determinism).
    """
    rows: list[dict[str, object]] = []
    p = as_fraction(pot)
    for raw in sizes if sizes is not None else STANDARD_SIZES:
        s = as_fraction(raw)
        bet = s * p
        equity = equity_needed_to_call(p, bet, exact=True)
        defense = minimum_defense_frequency(p, bet, exact=True)
        bluff = bluff_fraction_at_indifference(p, bet, exact=True)
        rows.append(
            {
                "size": round(float(s), digits),
                "size_label": _label(s),
                "pot_odds": round(float(p / bet), digits),
                "equity_needed": round(float(equity), digits),
                "mdf": round(float(defense), digits),
                "bluff_fraction": round(float(bluff), digits),
                "value_to_bluff": round(float((1 - bluff) / bluff), digits),
                "fold_frequency_needed": round(float(bet / (p + bet)), digits),
            }
        )
    return rows


def indifference_check(
    pot: Number, bet: Number, fold_frequency: Number, *, tol: float = 1e-12
) -> bool:
    """Is a pure bluff EV-zero at this fold frequency? Used by the solver's closed-form gate: the
    converged strategy must answer *yes* here, or the math module and the solver disagree.
    """
    p, b, f = (as_fraction(x) for x in (pot, bet, fold_frequency))
    return abs(float(f - b / (p + b))) <= tol


def summarize(rows: Sequence[dict[str, object]]) -> str:
    """Compact rendering for CLI output and doctests. Not the docs renderer."""
    header = "size        equity    mdf      bluff%   value:bluff"
    lines = [header]
    for row in rows:
        equity = cast(float, row["equity_needed"])
        defense = cast(float, row["mdf"])
        bluff = cast(float, row["bluff_fraction"])
        ratio = cast(float, row["value_to_bluff"])
        lines.append(
            f"{cast(str, row['size_label']):<11} "
            f"{100 * equity:6.2f}%  {100 * defense:6.2f}%  "
            f"{100 * bluff:5.2f}%  {ratio:5.2f}:1"
        )
    return "\n".join(lines)
