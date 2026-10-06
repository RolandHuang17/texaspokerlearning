"""Evaluator correctness: the pin that everything downstream stands on.

Equity, the solver's showdown payoffs, range-vs-range tables, and therefore every number in the
curriculum reduce to "who wins this seven-card hand". A one-in-a-million evaluator bug is a
one-in-a-million wrong table, so this file is unapologetically expensive:

* ``test_all_five_card_hands_match_reference`` enumerates **all 2,598,960** hands and asserts both the
  category counts and agreement with the naive rulebook oracle (``slow``, CI only);
* the seven-card fast path is cross-checked against "best of 21 sub-hands" over random boards;
* the wheel, the board-pairing tie, and the "flush beats straight" ordering each get a named test,
  because those three are where evaluators actually break.
"""

from __future__ import annotations

import random
from collections import Counter
from itertools import combinations

import pytest

from pokergto.cards import Card, class_key, standard_deck
from pokergto.evaluator import (
    Category,
    best_score,
    category_of,
    describe,
    evaluate5,
    evaluate7,
    evaluate7_reference,
    showdown,
)
from tests.reference_evaluator import naive_evaluate5, naive_evaluate7

DECK = standard_deck()

#: C(52,5) category counts. Derived in ``tools/gen_tables.py`` and asserted here: if these drift,
#: ``table.01-05.hand-class-counts`` must drift with them, and both changes mean the evaluator broke.
EXPECTED_COUNTS = {
    Category.STRAIGHT_FLUSH: 40,
    Category.FOUR_OF_A_KIND: 624,
    Category.FULL_HOUSE: 3744,
    Category.FLUSH: 5108,
    Category.STRAIGHT: 10200,
    Category.THREE_OF_A_KIND: 54912,
    Category.TWO_PAIR: 123552,
    Category.ONE_PAIR: 1098240,
    Category.HIGH_CARD: 1302540,
}


def test_hand_class_counts_total_is_c_52_5() -> None:
    assert sum(EXPECTED_COUNTS.values()) == 2_598_960


@pytest.mark.docs
def test_five_and_seven_card_arities_are_enforced() -> None:
    with pytest.raises(ValueError):
        evaluate5(DECK[:4])
    with pytest.raises(ValueError):
        evaluate7(DECK[:8])


def _cards(text: str) -> tuple[Card, ...]:
    return tuple(Card.parse(text[index : index + 2]) for index in range(0, len(text), 2))


def test_wheel_scores_as_high_five_not_broadway() -> None:
    """A-5-4-3-2 is a straight whose highest card is the five.

    Every evaluator eventually gets this wrong in one of two ways: reading the ace as high and
    reporting a Broadway straight, or failing to see the straight at all.
    """
    wheel = _cards("Ac5d4h3s2c")
    assert category_of(evaluate5(wheel)) is Category.STRAIGHT
    assert evaluate5(wheel) < evaluate5(_cards("KdQhJsTc9d"))
    assert describe(evaluate5(wheel)).endswith("5")


def test_six_card_boards_exercise_the_sub_hand_enumeration() -> None:
    """Six cards go through C(6,5) rather than C(7,5), a path the seven-card tests never touch.

    The two cases below are the ones that separate a correct wheel from a correct flush: four clubs
    with an ace-five straight is neither, while five clubs including A-5 is a wheel straight flush and
    outranks both.
    """
    assert category_of(evaluate7(_cards("Ac5d4h3s2cKh"))) is Category.STRAIGHT
    assert category_of(evaluate7(_cards("Ac5c4c3cKcQc"))) is Category.FLUSH
    assert category_of(evaluate7(_cards("Ac5c4c3c2cKc"))) is Category.STRAIGHT_FLUSH


def test_broadway_and_royal_flush_are_distinct_categories() -> None:
    assert category_of(evaluate7(_cards("AdKdQdTdJd7c2h"))) is Category.STRAIGHT_FLUSH
    assert "royal" in describe(evaluate7(_cards("AdKdQdTdJd7c2h"))).lower()
    assert category_of(evaluate7(_cards("AcKdQhJcTd7c2h"))) is Category.STRAIGHT


def test_flush_beats_straight_and_full_house_beats_flush() -> None:
    flush = _cards("Ac2c5c7c9cKdQh")
    straight = _cards("Ad3h5c6s7dKcQh")
    boat = _cards("AcAdAsKhKdQc9h")
    assert evaluate7(flush) > evaluate7(straight)
    assert evaluate7(boat) > evaluate7(flush)


def test_two_pair_kicker_and_board_pair_ties() -> None:
    """Kickers decide between identical two pairs, and a paired board can tie two hands exactly."""
    hero = _cards("AhAs Kd".replace(" ", ""))
    assert hero[0].rank.value == 14
    top = _cards("AcKhQdQs7h2c3d")
    bottom = _cards("AcKhJdJs7h2c3d")
    assert evaluate7(top) > evaluate7(bottom)
    assert showdown(_cards("AdAh"), _cards("KdKh"), _cards("Qs7c3h")) == -1
    # Both players play the board: a genuine split.
    assert showdown(_cards("2d3c"), _cards("4d5c"), _cards("AcKdQhJsTh")) == 0


def test_describe_is_available_in_both_languages() -> None:
    score = evaluate7(_cards("AcAdAsKhKdQc9h"))
    assert describe(score, lang="en").startswith("full house")
    assert describe(score, lang="zh").startswith("葫芦")


@pytest.mark.parametrize("size", [5, 6, 7])
def test_fast_seven_card_path_matches_the_definition(size: int) -> None:
    """``evaluate7`` vs "the best of its C(n,5) sub-hands", over random boards.

    This is the test that caught the vectorised-CFR bug's cousin: an optimisation that is wrong in a
    way that only shows up on the rare shape. 20,000 random hands per arity is enough to cover
    straights, flushes, boats and splits many times over.
    """
    rng = random.Random(20260 + size)
    for _ in range(20_000):
        hand = rng.sample(DECK, size)
        assert evaluate7(hand) == evaluate7_reference(hand)


def test_ordering_is_consistent_with_showdown() -> None:
    rng = random.Random(7)
    for _ in range(2000):
        board = rng.sample(DECK, 3) + rng.sample(DECK[5:], 2)
        first = rng.sample(DECK[5:], 2)
        second = [card for card in rng.sample(DECK, 2) if card not in first and card not in board]
        if not second or len(second) != 2:
            continue
        sa = best_score(first, tuple(board))
        sb = best_score(second, tuple(board))
        result = showdown(first, second, tuple(board))
        expected = 0 if sa == sb else (-1 if sa > sb else 1)
        assert result == expected


@pytest.mark.slow
def test_all_five_card_hands_match_reference() -> None:
    """The expensive one: every C(52,5) hand, against the rulebook oracle and against the counts."""
    counts: Counter[int] = Counter()
    mismatches = 0
    for index_a in range(52):
        for index_b in range(index_a + 1, 52):
            for index_c in range(index_b + 1, 52):
                for index_d in range(index_c + 1, 52):
                    for index_e in range(index_d + 1, 52):
                        hand = (
                            DECK[index_a],
                            DECK[index_b],
                            DECK[index_c],
                            DECK[index_d],
                            DECK[index_e],
                        )
                        score = evaluate5(hand)
                        counts[score >> 20] += 1
                        if score != _naive_score(naive_evaluate5(hand)):
                            mismatches += 1
    assert mismatches == 0
    for category, expected in EXPECTED_COUNTS.items():
        assert counts[int(category)] == expected, (
            f"{category.name}: {counts[int(category)]} != {expected}"
        )


@pytest.mark.slow
def test_random_seven_card_hands_match_naive_best_of_21() -> None:
    rng = random.Random(4242)
    for _ in range(4000):
        hand = rng.sample(DECK, 7)
        assert evaluate7(hand) == _naive_score(naive_evaluate7(hand))


def _naive_score(pair: tuple[int, tuple[int, ...]]) -> int:
    category, tiebreak = pair
    padded = list(tiebreak[:5]) + [0] * (5 - min(len(tiebreak), 5))
    score = category << 20
    for shift, value in zip((16, 12, 8, 4, 0), padded, strict=True):
        score |= value << shift
    return score


def test_class_key_is_symmetric_and_suit_neutral() -> None:
    ace_spades, king_hearts = Card.parse("As"), Card.parse("Kh")
    assert class_key(ace_spades, king_hearts) == class_key(king_hearts, ace_spades) == "AKo"
    assert class_key(Card.parse("As"), Card.parse("Ah")) == "AA"
    # High rank is written first, and suitedness is decided by the suits, not by the argument order.
    assert class_key(Card.parse("5s"), Card.parse("Ah")) == "A5o"
    assert class_key(Card.parse("5h"), Card.parse("Ah")) == "A5s"


def test_combos_enumeration_covers_the_deck_exactly() -> None:
    keys = Counter(
        class_key(Card.from_index(a), Card.from_index(b)) for a, b in combinations(range(52), 2)
    )
    assert sum(keys.values()) == 1326
    assert len(keys) == 169
    assert keys["AA"] == 6 and keys["AKs"] == 4 and keys["AKo"] == 12
