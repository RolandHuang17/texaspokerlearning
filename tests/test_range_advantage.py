"""Range advantage: the three numbers a sizing decision rests on, and what they are measured over.

Chapter 03's tables come out of this module, so these tests are about the *denominators*. A nut share is
a weight over combos the board still allows, which is why the functions here refuse a range that still
contains a board card rather than quietly narrowing it -- a share divided by six combos of "77" on a
board showing a seven is a number between zero and one that never looks wrong. The scoring itself is now
the vectorised batch path, so each test also re-runs the scalar definition over the same combos and
requires the two to agree element by element.

Also pinned here: :func:`pokergto.theory.range_advantage.board_ceiling` counts only hands that can be
dealt. That restriction is not hygiene. On ``5cKh3sTh4h`` the impossible combo ``Kh Ah`` outscores every
legal hand on the board, because the evaluator reads a repeated card as two of them.
"""

from __future__ import annotations

import numpy as np
import pytest

from pokergto.cards import Card, parse_cards
from pokergto.errors import InputError
from pokergto.evaluator import best_score, describe
from pokergto.notation import parse
from pokergto.ranges import Range
from pokergto.theory.range_advantage import advantage, board_ceiling, is_capped, nut_advantage

PHANTOM_BOARD = "5cKh3sTh4h"


def _scalar_scores(rng: Range, board: tuple[Card, ...]) -> list[tuple[int, float]]:
    """The definition, in Python loops: one ``best_score`` call per combo."""
    return [(best_score((first, second), board), weight) for first, second, weight in rng]


def _scalar_share(pairs: list[tuple[int, float]], cutoff: int) -> float:
    """Weight of the combos at or above ``cutoff``, divided by the weight of every combo handed in."""
    total = sum(weight for _score, weight in pairs)
    hits = sum(weight for score, weight in pairs if score >= cutoff)
    return hits / total if total else 0.0


def test_nut_advantage_scores_every_combo_the_batch_path_and_the_scalar_path_agree_on() -> None:
    """The batch rewrite must not be observable: same combos, same order, same integers."""
    for spec, board_text in (
        ("KK+,AKs", "Kh7h2d"),
        ("QJs,JTs,98s", "Kh7h2d"),
        ("22+,ATs+", "AsKsQh"),
        ("88+,AJs+,KQs", "9h6d3c"),
        ("54s,65s,76s", "Kh7h2d"),
    ):
        board = parse_cards(board_text)
        rng = parse(spec, exclude=board)
        from pokergto.evaluator import best_scores_many

        codes = np.array([(first.index, second.index) for first, second, _w in rng], np.int64)
        batch = best_scores_many(codes, np.array([c.index for c in board], np.int64))
        scalar = np.array([score for score, _weight in _scalar_scores(rng, board)], np.int64)
        assert np.array_equal(batch, scalar), f"{spec} on {board_text}"


def test_nut_shares_match_the_scalar_definition_including_the_near_nuts_knob() -> None:
    """Shares recomputed by hand, for the literal nuts and for a tolerance below them."""
    board = parse_cards("Kh7h2d")
    cases = [
        (parse("KK+,AKs", exclude=board), parse("QJs,JTs,98s", exclude=board), 0),
        (parse("KK+,AKs", exclude=board), parse("QJs,JTs,98s", exclude=board), 20),
        (parse("22+,ATs+", exclude=board), parse("87s,98s,T9s", exclude=board), 0),
    ]
    for hero, villain, near_nuts in cases:
        got = nut_advantage(hero, villain, board, near_nuts=near_nuts)
        hero_pairs, villain_pairs = _scalar_scores(hero, board), _scalar_scores(villain, board)
        cutoff = max(score for score, _w in hero_pairs + villain_pairs) - near_nuts
        assert got == pytest.approx(
            (_scalar_share(hero_pairs, cutoff), _scalar_share(villain_pairs, cutoff))
        )


def test_the_board_ceiling_counts_only_hands_that_can_be_dealt() -> None:
    """A phantom copy of a board card can outscore every legal hand, so it is not the ceiling.

    ``5cKh3sTh4h`` shows three hearts, so the best dealt flush is ``A-K-Q-T-4`` from ``Ah Qh``. The combo
    ``Kh Ah`` holds a king the board already holds, and :func:`best_score` -- which takes the caller's
    cards as given -- reads it as a second king: ``A-K-K-T-4``, and a king beats a queen in the third
    slot. Measured over 4,000 random boards, 100 of them have a strictly higher ceiling once such combos
    are counted, so an unfiltered ceiling really does call a range capped that is not.
    """
    board = parse_cards(PHANTOM_BOARD)
    ceiling = board_ceiling(board)
    assert describe(ceiling) == "flush A-K-Q-T-4"
    assert ceiling == best_score((Card.parse("Ah"), Card.parse("Qh")), board)
    phantom = best_score((Card.parse("Kh"), Card.parse("Ah")), board)
    assert phantom > ceiling, "the whole point: the undealtable hand is the better score"
    assert describe(phantom) == "flush A-K-K-T-4"


def test_is_capped_agrees_with_the_ceiling_it_is_documented_against() -> None:
    """One rule, one implementation: the column a table prints and the predicate cannot disagree."""
    for board_text in (PHANTOM_BOARD, "Kh7h2d", "AsKsQh", "AhAdKc", "2h7d9cJdTs"):
        board = parse_cards(board_text)
        ceiling = board_ceiling(board)
        richest = parse("22+,ATs+", exclude=board)
        assert is_capped(richest, board) == (
            max(score for score, _w in _scalar_scores(richest, board)) < ceiling
        )


def test_a_range_that_still_holds_a_board_card_is_refused() -> None:
    """The narrowing is the caller's job, and the refusal says so with the way to fix it.

    Both columns of an advantage number can otherwise be computed against different denominators --
    ``range_equity`` masks colliding combos internally while a nut share divides by whatever it was
    handed -- which puts a real equity next to an inflated share in the same table row.
    """
    board = parse_cards("AhKsQh")
    dirty = parse("AKs,AA")
    with pytest.raises(InputError, match="still holds"):
        nut_advantage(dirty, parse("QQ", exclude=board), board)
    with pytest.raises(InputError, match="exclude=board"):
        is_capped(dirty, board)
    assert not dirty.equal(parse("AKs,AA", exclude=board))


def test_capped_is_about_the_nuts_being_absent_not_about_the_range_being_small() -> None:
    """``AsKsQh``: the ceiling is a Broadway straight, pocket pairs top out at three of a kind.

    ``tolerance`` is in the evaluator's packed-integer units and it moves the bar *down*, so raising it
    makes "capped" a harder claim, not an easier one. Both sides of that are pinned here with the margin
    measured rather than guessed, because a plausible 1 or 2 asks a question nobody meant: adjacent hand
    strengths are thousands of integers apart.
    """
    board = parse_cards("AsKsQh")
    assert describe(board_ceiling(board)) == "straight A"
    pairs = parse("22+,ATs+", exclude=board)
    assert is_capped(pairs, board) is True
    straight = Range.from_cards([Card.parse("Jh"), Card.parse("Th")])
    assert is_capped(straight, board) is False

    gap = board_ceiling(board) - max(score for score, _w in _scalar_scores(pairs, board))
    assert gap > 0
    assert is_capped(pairs, board, tolerance=gap - 1) is True
    assert is_capped(pairs, board, tolerance=gap) is False


def test_advantage_reports_all_three_numbers_for_one_board() -> None:
    """One call is what a lesson's worked example uses, so its identity checks are pinned here."""
    board = parse_cards("Kh7h2d")
    hero = parse("KK+,AKs", exclude=board)
    villain = parse("QJs,JTs,98s", exclude=board)
    result = advantage(hero, villain, board, mode="exact", near_nuts=0)
    assert result.board == tuple(card.code for card in board)
    assert result.hero_equity + result.villain_equity == pytest.approx(1.0)
    assert result.nut_edge == pytest.approx(result.hero_nut_share - result.villain_nut_share)
    assert result.hero_combos == pytest.approx(hero.total_combos())
    assert result.villain_combos == pytest.approx(villain.total_combos())
    assert (result.board,) == (tuple(card.code for card in board),)
