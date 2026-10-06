"""Chapter 02's arithmetic, tested as arithmetic.

Every lesson in ``02-the-math-of-one-decision`` cites one of these functions, and chapter 04 cites the
break-even surface. A wrong sign here is not a wrong number in one table -- it is a wrong *rule* taught
in both languages, which is why the checks below re-solve equations by substitution instead of pinning
printed values: a pinned value can be pinned to a mistake.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from pokergto.errors import InputError
from pokergto.ev import (
    DecisionComparison,
    break_even_equity_to_bet,
    compare,
    ev_bet,
    ev_call,
    ev_check,
    ev_fold,
    ev_pure_bluff,
    ev_pure_value,
    ev_shove,
    regret,
)

POT = 10.0
BET = 5.0


def _gap(pot: Fraction, bet: Fraction, fold: Fraction, equity: Fraction) -> Fraction:
    """``EV(bet) - EV(check)`` at an equity, in exact arithmetic."""
    return ev_bet(pot, bet, fold, equity, exact=True) - ev_check(pot, equity, exact=True)


# --- the four primitives ---------------------------------------------------------------


def test_folding_is_zero_by_convention_in_both_arithmetics() -> None:
    assert ev_fold() == 0.0
    assert ev_fold(exact=True) == Fraction(0)


def test_call_equity_formula_matches_hand_arithmetic() -> None:
    # Facing 5 into a pot of 10 with 40% equity: win 15, lose 5.
    assert ev_call(POT, BET, 0.4) == pytest.approx(0.4 * 15 - 0.6 * 5)
    assert ev_call(POT, BET, Fraction(2, 5), exact=True) == Fraction(3)


def test_pure_bluff_breaks_even_exactly_at_the_mdf_fold_frequency() -> None:
    """The identity chapter 02 exists to teach: a bluff is +EV exactly past ``bet/(pot+bet)``."""
    from pokergto.odds import required_fold_frequency

    floor = required_fold_frequency(POT, BET)
    assert ev_pure_bluff(POT, BET, floor) == pytest.approx(0.0, abs=1e-12)
    assert ev_pure_bluff(POT, BET, floor + 0.1) > 0
    assert ev_pure_bluff(POT, BET, floor - 0.1) < 0


def test_pure_value_is_the_always_called_bound() -> None:
    assert ev_pure_value(POT, BET, 0.25) == pytest.approx(0.25 * POT + 0.75 * (POT + BET))


def test_shove_is_a_bet_with_bet_equal_to_stack() -> None:
    """Not a new formula: the same one with the stack substituted, which is what makes chapter 12
    provable rather than chart-memorised."""
    assert ev_shove(POT, 20, 0.4, 0.7) == pytest.approx(ev_bet(POT, 20, 0.3, 0.4))


# --- the break-even surface (chapter 04) -----------------------------------------------


GRID = [
    (Fraction(1), Fraction(1, 3)),
    (Fraction(1), Fraction(1, 2)),
    (Fraction(1), Fraction(3, 4)),
    (Fraction(1), Fraction(1)),
    (Fraction(1), Fraction(2)),
]
FOLDERS = [Fraction(v).limit_denominator(100) for v in (0.1, 0.25, 0.4, 0.5, 0.625, 0.8)]


@pytest.mark.parametrize("pot,bet", GRID)
@pytest.mark.parametrize("fold", FOLDERS)
def test_break_even_threshold_re_substitutes_to_zero(
    pot: Fraction, bet: Fraction, fold: Fraction
) -> None:
    solved = break_even_equity_to_bet(pot, bet, fold)
    if solved.threshold is None:
        # The equity-independent line. Asserting it is a *size-and-frequency* verdict rather than
        # skipping keeps the degenerate case covered: a bug here shows up as "no threshold" silently.
        assert solved.regime in {"all", "none", "indifferent"}
        return
    assert _gap(pot, bet, fold, solved.threshold) == 0


@pytest.mark.parametrize("pot,bet", GRID)
def test_regime_direction_is_the_sign_of_the_denominator(pot: Fraction, bet: Fraction) -> None:
    """The teaching-critical case: a high enough fold frequency inverts the inequality.

    ``above`` must get worse below the threshold and ``below`` must get better below it. Asserting a
    single direction for all rows is how a lesson ends up teaching the bluff regime backwards.
    """
    for fold in FOLDERS:
        solved = break_even_equity_to_bet(pot, bet, fold)
        if solved.threshold is None:
            continue
        step = Fraction(1, 100)
        above = _gap(pot, bet, fold, solved.threshold + step)
        below = _gap(pot, bet, fold, solved.threshold - step)
        if solved.regime == "above":
            assert above > 0 >= below, (pot, bet, fold, above, below)
        elif solved.regime == "below":
            assert below > 0 >= above, (pot, bet, fold, below, above)


def test_at_the_needed_fold_frequency_the_threshold_is_exactly_zero() -> None:
    """The same fact from the bettor's side: if the opponent folds precisely enough for the bluff to
    break even, then *air* is indifferent between betting and checking. Nothing here assumes a hand."""
    from pokergto.odds import required_fold_frequency

    for bet in (Fraction(1, 3), Fraction(1, 2), Fraction(1), Fraction(2)):
        fold = required_fold_frequency(Fraction(1), bet)
        solved = break_even_equity_to_bet(1, bet, fold)
        assert solved.threshold == 0, (bet, solved)
        assert solved.regime == "above"


def test_equity_alone_never_makes_a_bet_correct() -> None:
    """No size against a sane fold frequency can ask for more than certain equity.

    If a threshold above 1 ever appeared in the ``above`` regime, the arithmetic would be claiming that
    some hand sizes are unwinnable by definition -- the sort of confident-but-impossible number a table
    can carry silently forever.
    """
    for bet in (
        Fraction(1, 4),
        Fraction(1, 3),
        Fraction(1, 2),
        Fraction(3, 4),
        Fraction(1),
        Fraction(2),
    ):
        for fold in FOLDERS:
            solved = break_even_equity_to_bet(1, bet, fold)
            if solved.regime == "above":
                assert solved.threshold is not None and solved.threshold <= 1


def test_when_the_fold_frequency_is_extreme_enough_equity_stops_mattering() -> None:
    """``2b(1−f) = fp`` is the equity-independent line, and it is reachable: a pot-sized bet facing
    two-thirds folds makes bet and check equal for every hand, strong or weak."""
    solved = break_even_equity_to_bet(1, 1, Fraction(2, 3))
    assert solved.regime == "all"
    assert solved.threshold is None
    # Just below that line the same size stops being automatically correct.
    assert break_even_equity_to_bet(1, 1, Fraction(2, 3) - Fraction(1, 10)).regime == "above"


def test_impossible_inputs_are_refused() -> None:
    with pytest.raises(InputError):
        break_even_equity_to_bet(10, 5, Fraction(3, 2))
    with pytest.raises(InputError):
        break_even_equity_to_bet(10, -5, Fraction(1, 2))


# --- comparing actions -----------------------------------------------------------------


def test_compare_ranks_and_marks_the_best_row() -> None:
    rows = compare(
        POT,
        [("check", 0), ("bet 1/3", BET / 3), ("bet pot", BET * 2)],
        fold_frequencies={"check": 0, "bet 1/3": Fraction(1, 4), "bet pot": Fraction(1, 2)},
        equities_when_called={
            "check": Fraction(2, 5),
            "bet 1/3": Fraction(2, 5),
            "bet pot": Fraction(2, 5),
        },
    )
    assert isinstance(rows[0], DecisionComparison)
    assert rows[0].ev_exact >= max(row.ev_exact for row in rows)
    assert sum(row.best for row in rows) == 1


def test_regret_of_the_best_action_is_zero_and_others_are_positive() -> None:
    rows = compare(
        POT,
        [("check", 0), ("bet half", BET)],
        fold_frequencies={"check": 0, "bet half": Fraction(1, 5)},
        equities_when_called={"check": Fraction(1, 5), "bet half": Fraction(1, 5)},
    )
    values = regret(rows)
    assert min(values.values()) == pytest.approx(0.0)
    assert all(value >= 0 for value in values.values())
