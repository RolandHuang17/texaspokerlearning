"""The closed forms of chapter 02, pinned exactly.

These tests are the arithmetic spine of the repository. Two of them exist because a draft of this
curriculum got the numbers wrong in the instructive way -- it read the MDF column as the
bluff-to-value column -- so the parameter tables below were written from the derivation and then made
to check the code against it. If ``pokergto.odds`` ever disagrees with these rationals, the docs are
wrong too, and that is a single failure rather than two.

Everything is asserted over :class:`fractions.Fraction`, not floats, because a teaching library that
rounds ``1/3`` and calls the result derived is doing the thing it claims to replace.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from pokergto.odds import (
    STANDARD_SIZES,
    as_fraction,
    at_least_one_defense,
    bluff_fraction_at_indifference,
    break_even_percentage,
    defense_frequency_multiway,
    equity_needed_to_call,
    indifference_check,
    minimum_defense_frequency,
    pot_odds,
    required_fold_frequency,
    sizing_table,
    value_to_bluff_ratio,
)

#: ``bet size (as a fraction of pot) -> (MDF, bluff share of the betting range, value:bluff)``.
#: Derived in lessons 02-03 and 02-04: ``MDF = 1/(1+s)``, ``bluff share = s/(1+2s)``,
#: ``value:bluff = (1+s)/s``.
CLOSED_FORM_TABLE = [
    (Fraction(1, 4), Fraction(4, 5), Fraction(1, 6), Fraction(5)),
    (Fraction(1, 3), Fraction(3, 4), Fraction(1, 5), Fraction(4)),
    (Fraction(1, 2), Fraction(2, 3), Fraction(1, 4), Fraction(3)),
    (Fraction(2, 3), Fraction(3, 5), Fraction(2, 7), Fraction(5, 2)),
    (Fraction(3, 4), Fraction(4, 7), Fraction(3, 10), Fraction(7, 3)),
    (Fraction(1), Fraction(1, 2), Fraction(1, 3), Fraction(2)),
    (Fraction(3, 2), Fraction(2, 5), Fraction(3, 8), Fraction(5, 3)),
    (Fraction(2), Fraction(1, 3), Fraction(2, 5), Fraction(3, 2)),
]


@pytest.mark.parametrize("size, mdf, bluff_share, value_to_bluff", CLOSED_FORM_TABLE)
def test_closed_forms_are_exact_rationals(
    size: Fraction, mdf: Fraction, bluff_share: Fraction, value_to_bluff: Fraction
) -> None:
    pot, bet = Fraction(1), size
    assert minimum_defense_frequency(pot, bet, exact=True) == mdf
    assert required_fold_frequency(pot, bet, exact=True) == 1 - mdf
    assert bluff_fraction_at_indifference(pot, bet, exact=True) == bluff_share
    assert value_to_bluff_ratio(pot, bet, exact=True) == value_to_bluff


def test_the_two_columns_that_get_confused_are_different_quantities() -> None:
    """The mistake this repository made in draft: reading MDF as the bluff-to-value column.

    At a one third pot the defense frequency is 75% and the value:bluff ratio is 4:1 -- two different
    numbers answering two different questions. Asserting the inequality is the point: a test that only
    checked the values would still pass if someone swapped the labels.
    """
    mdf = minimum_defense_frequency(1, Fraction(1, 3), exact=True)
    bluff_share = bluff_fraction_at_indifference(1, Fraction(1, 3), exact=True)
    assert mdf == Fraction(3, 4)
    assert bluff_share == Fraction(1, 5)
    assert mdf != bluff_share
    assert value_to_bluff_ratio(1, 1, exact=True) == 2  # pot-sized: 2:1, not the common 1:1


#: Generated tables round to six decimals by design (``artifacts.FLOAT_DIGITS`` and the per-column
#: ``digits``), so the comparison against exact algebra uses a tolerance that matches the published
#: precision. A tighter bound here would fail on rounding, not on mathematics.
TABLE_TOLERANCE = 5e-7


@pytest.mark.parametrize("size, mdf, bluff_share, _ratio", CLOSED_FORM_TABLE)
def test_generated_table_matches_the_closed_forms(
    size: Fraction, mdf: Fraction, bluff_share: Fraction, _ratio: Fraction
) -> None:
    # Ask the generator for exactly this size rather than searching its default ladder: the ladder
    # rounds to six decimals, so 1/3 is published as 0.333333 and a lookup by value would miss it.
    match = sizing_table(sizes=[size], pot=1)[0]
    assert abs(match["mdf"] - float(mdf)) < TABLE_TOLERANCE
    assert abs(match["bluff_fraction"] - float(bluff_share)) < TABLE_TOLERANCE
    assert abs(match["equity_needed"] - float(bluff_share)) < TABLE_TOLERANCE


def test_equity_needed_to_call_matches_bluff_share_denominator() -> None:
    """``B/(P+2B)`` appears twice for the same reason: a bluff-catcher's indifference and the share of
    a betting range that must be air are the same equation read from two sides."""
    for size, _mdf, bluff_share, _ratio in CLOSED_FORM_TABLE:
        assert equity_needed_to_call(1, size, exact=True) == bluff_share


def test_algebraic_identity_between_the_two_forms() -> None:
    """``value_to_bluff_ratio(pot, bet) == 1/call_threshold - 1`` ... stated as the identity the docs
    cite, so a refactor of either function that breaks the relationship fails here."""
    for size, *_rest in CLOSED_FORM_TABLE:
        bluff = bluff_fraction_at_indifference(1, size, exact=True)
        assert value_to_bluff_ratio(1, size, exact=True) == (1 - bluff) / bluff


def test_multiway_mdf_exponent_is_one_over_n_and_falls_back_to_heads_up() -> None:
    """The correction that matters: ``d = 1 - (B/(P+B))^(1/N)``.

    Two independent checks, both of which a wrong exponent fails:
    * ``N = 1`` must reproduce the ordinary MDF exactly;
    * for a pot-sized bet with two opponents, each defends 29.29% and the *joint* defense is the
      heads-up 50%, because the bluff needs everyone to fold.
    """
    assert defense_frequency_multiway(1, 1, 1) == pytest.approx(0.5, abs=1e-15)
    per_player = defense_frequency_multiway(1, 1, 2)
    assert per_player == pytest.approx(1 - 0.5**0.5, abs=1e-15)
    # Recovering 0.5 from ``1 - (1-d)^2`` squares a quantity near one and subtracts it from one, so
    # the residual is cancellation, not mathematics: 1e-9 is the honest bound for float64 here.
    assert at_least_one_defense(per_player, 2) == pytest.approx(0.5, abs=1e-9)
    # The joint requirement never changes with player count; the per-player share does.
    for opponents in (1, 2, 3, 4, 5):
        # The joint requirement is invariant in N; the per-player share is not. 1e-9 is the float
        # round-trip through an N-th root and its inverse, not a mathematical slack.
        assert at_least_one_defense(
            defense_frequency_multiway(1, 0.5, opponents), opponents
        ) == pytest.approx(float(minimum_defense_frequency(1, 0.5)), abs=1e-9)


def test_multiway_exact_mode_refuses_irrational_roots_instead_of_faking_them() -> None:
    """``exact=True`` would have to lie here: the cube root of 1/2 is not a rational.

    Refusing is the correct behaviour for a teaching library, and the error message is expected to
    name the alternative rather than dead-end the learner.
    """
    with pytest.raises(ValueError, match="N-th root"):
        defense_frequency_multiway(1, 1, 3, exact=True)
    # N=1 is the rational case, so exact still works there.
    assert defense_frequency_multiway(1, 1, 1, exact=True) == Fraction(1, 2)


def test_break_even_and_pot_odds_use_stated_conventions() -> None:
    assert break_even_percentage(2, 8, exact=True) == Fraction(1, 5)
    assert pot_odds(6, 2, exact=True) == Fraction(3, 1)
    with pytest.raises(ValueError):
        pot_odds(6, 0)


def test_indifference_check_is_the_gate_the_solver_uses() -> None:
    """``pokergto.solver.proofs`` asserts that CFR's converged defense frequency passes this check."""
    assert indifference_check(1, Fraction(1, 2), Fraction(1, 3))
    assert not indifference_check(1, Fraction(1, 2), Fraction(1, 2))
    assert not indifference_check(1, Fraction(1, 2), Fraction(1, 3) + Fraction(1, 1000), tol=1e-9)


def test_as_fraction_does_not_leak_binary_noise_into_rationals() -> None:
    assert as_fraction(0.3333333333333333) == Fraction(1, 3)
    assert as_fraction(0.75) == Fraction(3, 4)
    assert as_fraction(2) == Fraction(2)
    assert as_fraction(Fraction(5, 7)) == Fraction(5, 7)


def test_standard_sizes_cover_the_ladder_the_curriculum_reasons_over() -> None:
    assert Fraction(1, 3) in STANDARD_SIZES
    assert Fraction(2) in STANDARD_SIZES
    assert len(STANDARD_SIZES) == 8
