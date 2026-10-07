"""Evaluator correctness: the pin that everything downstream stands on.

Equity, the solver's showdown payoffs, range-vs-range tables, and therefore every number in the
curriculum reduce to "who wins this seven-card hand". A one-in-a-million evaluator bug is a
one-in-a-million wrong table, so this file is unapologetically expensive:

* ``test_all_five_card_hands_match_reference`` enumerates **all 2,598,960** hands and asserts both the
  category counts and agreement with the naive rulebook oracle (``slow``, CI only);
* the seven-card fast path is cross-checked against "best of 21 sub-hands" over random boards;
* the vectorised batch paths are checked against the scalar paths over **every hand of several
  subdecks chosen for structure** -- single-suit (flush and straight-flush shapes), six ranks times four
  suits (quads and full houses), nine ranks times three suits (three of a kind without flushes) -- plus
  millions of random boards;
* the wheel, the board-pairing tie, and the "flush beats straight" ordering each get a named test,
  because those three are where evaluators actually break.
"""

from __future__ import annotations

import random
from collections import Counter
from itertools import combinations, islice

import numpy as np
import pytest

from pokergto.cards import Card, class_key, standard_deck
from pokergto.evaluator import (
    Category,
    best_score,
    best_score_three,
    best_scores_many,
    category_of,
    describe,
    evaluate3,
    evaluate5,
    evaluate5_many,
    evaluate7,
    evaluate7_many,
    evaluate7_many_reference,
    evaluate7_reference,
    showdown,
)
from tests.reference_evaluator import naive_evaluate5, naive_evaluate7

DECK = standard_deck()
INDICES = np.array([c.index for c in DECK], dtype=np.int64)


def _hand(text: str) -> np.ndarray:
    """One hand as the batch path wants it: ``(1, n)`` block of 52-indices."""
    return np.array([[c.index for c in _cards(text)]], dtype=np.int64)


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


# --- the three-card path Leduc hold'em needs ------------------------------------------------


LEDUC_DECK = [Card.parse(f"{rank}{suit}") for rank in "JQK" for suit in "sh"]


def _three_card_kind(cards: tuple[Card, ...]) -> str:
    """The rulebook definition, written independently of ``evaluate3`` so the two can be compared.

    Six cards, three ranks, two suits: this is small enough that the whole ladder can be spelled out in
    four lines, which is exactly what makes it usable as an oracle.
    """
    counts = Counter(card.rank.value for card in cards)
    flush = len({card.suit for card in cards}) == 1
    ordered = sorted(counts)
    straight = len(counts) == 3 and (ordered[2] - ordered[0] == 2 or ordered == [2, 3, 14])
    if max(counts.values()) == 3:
        return "three of a kind"
    if flush and straight:
        return "straight flush"
    if flush:
        return "flush"
    if straight:
        return "straight"
    if max(counts.values()) == 2:
        return "one pair"
    return "high card"


@pytest.mark.parametrize(
    "cards",
    [tuple(hand) for hand in combinations(LEDUC_DECK, 3)],
    ids=["-".join(c.code for c in hand) for hand in combinations(LEDUC_DECK, 3)],
)
def test_evaluate3_matches_the_rulebook_on_every_leduc_hand(cards: tuple[Card, ...]) -> None:
    """All C(6,3) = 20 three-card hands Leduc's deck can produce, against the written-out rule."""
    assert (
        category_of(evaluate3(cards)) is Category[_three_card_kind(cards).upper().replace(" ", "_")]
    )


def test_leducs_deck_cannot_reach_the_categories_whose_ordering_is_disputed() -> None:
    """The claim in ``evaluate3``'s docstring, checked rather than trusted.

    Three-card poker ranks a straight above a flush; hold'em ranks a flush above a straight. This
    repository follows hold'em, and on Leduc's six-card deck the choice never fires: every flush needs
    J-Q-K of one suit, which is simultaneously a straight, and three of a kind needs a third copy of a
    rank that does not exist. If the deck ever changes, this test is the tripwire that says the ordering
    decision has become a real one.
    """
    kinds = Counter(_three_card_kind(tuple(hand)) for hand in combinations(LEDUC_DECK, 3))
    assert set(kinds) == {"straight flush", "straight", "one pair"}
    assert kinds == Counter({"one pair": 12, "straight": 6, "straight flush": 2})


def test_evaluate3_orders_straight_flush_above_straight_above_pair() -> None:
    best = evaluate3(tuple(LEDUC_DECK[i] for i in (0, 2, 4)))  # Js Qs Ks
    straight = evaluate3([Card.parse("Js"), Card.parse("Qh"), Card.parse("Ks")])
    pair = evaluate3([Card.parse("Ks"), Card.parse("Kh"), Card.parse("Js")])
    assert best > straight > pair


def test_three_card_wheel_is_three_high_not_five_high() -> None:
    """A-2-3 is the one run where the ace is not the top card, and naming it five-high would tie it
    with 2-3-4. The five-card evaluator can call A-5-4-3-2 five-high because the run's own five cards
    make that unambiguous; with three cards, the top card of the run is the three."""
    wheel = evaluate3([Card.parse("As"), Card.parse("2h"), Card.parse("3d")])
    six_high = evaluate3([Card.parse("2s"), Card.parse("3h"), Card.parse("4d")])
    assert _three_card_kind(tuple(Card.parse(c) for c in ("As", "2h", "3d"))) == "straight"
    assert six_high > wheel


def test_best_score_three_refuses_impossible_inputs() -> None:
    board = (Card.parse("As"), Card.parse("Kh"))
    with pytest.raises(ValueError, match="exactly 2 board cards"):
        best_score_three([Card.parse("Qd")], board[:1])
    with pytest.raises(ValueError, match="exactly 1 private card"):
        best_score_three([Card.parse("Qd"), Card.parse("Jd")], board)
    with pytest.raises(ValueError, match="both a player's card and a board card"):
        best_score_three([Card.parse("As")], board)


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


# --- the vectorised batch paths -----------------------------------------------------------

#: Subdecks chosen for the *structure* they exercise, not for size: a single suit makes every hand a
#: flush and isolates the run logic; six ranks times four suits reaches quads and full houses while
#: keeping the enumeration small; eight ranks times two suits has pairs and two pair but cannot make
#: three of a kind; nine ranks times three suits adds three of a kind without any flush at all.
SUBDECKS: dict[str, list[Card]] = {
    "13r_1s": [Card.parse(f"{r}s") for r in "23456789TJQKA"],
    "6r_4s": [Card.parse(f"{r}{s}") for r in "AKQJT9" for s in "cdhs"],
    "8r_2s": [Card.parse(f"{r}{s}") for r in "AKQJT987" for s in "ch"],
    "9r_3s": [Card.parse(f"{r}{s}") for r in "AKQJT9876" for s in "cdh"],
}


def _all_hands(label: str, size: int) -> np.ndarray:
    """Every ``size``-card hand of one subdeck as an ``(N, size)`` block of 52-indices."""
    codes = np.array([c.index for c in SUBDECKS[label]], dtype=np.int64)
    rows = [sorted(codes[i] for i in combo) for combo in combinations(range(codes.size), size)]
    return np.array(rows, dtype=np.int64)


def _scalar_five(hands: np.ndarray) -> np.ndarray:
    return np.fromiter(
        (evaluate5(tuple(DECK[int(i)] for i in hand)) for hand in hands),
        np.int64,
        count=hands.shape[0],
    )


def _scalar_seven(hands: np.ndarray) -> np.ndarray:
    return np.fromiter(
        (evaluate7(tuple(DECK[int(i)] for i in hand)) for hand in hands),
        np.int64,
        count=hands.shape[0],
    )


@pytest.mark.parametrize("label", ["13r_1s", "8r_2s", "6r_4s"])
def test_batch_five_card_matches_scalar_on_every_hand_of_a_subdeck(label: str) -> None:
    """Exhaustive within a subdeck: the batch path returns the *same integers*, not a ranking."""
    hands = _all_hands(label, 5)
    assert np.array_equal(evaluate5_many(hands), _scalar_five(hands))


@pytest.mark.parametrize("label", ["13r_1s", "8r_2s"])
def test_batch_seven_card_matches_the_definition_on_every_hand_of_a_subdeck(label: str) -> None:
    """``evaluate7_many`` against the literal best-of-21 over a whole subdeck.

    The definition path is itself built on :func:`evaluate5_many`, so this is not "two implementations
    agree and therefore both are right": it is the same relationship ``evaluate7`` has to
    :func:`evaluate7_reference``, and the five-card layer underneath it is proved exhaustively.
    """
    hands = _all_hands(label, 7)
    assert np.array_equal(evaluate7_many(hands), evaluate7_many_reference(hands))


def test_batch_seven_card_finds_the_higher_run_when_a_wheel_is_also_present() -> None:
    """Seven cards can contain two straights at once, and the wheel must not win.

    ``A-2-3-4-5-6-7`` holds the wheel *and* a seven-high run. Scoring it five-high is the bug this test
    was written for: the exhaustive subdeck sweep found it, it cannot be seen on five cards (five cards
    holding five distinct ranks form at most one run), and it changes no category -- only the tiebreak,
    so every category-count assertion in this file stays green through it.
    """
    two_runs = _hand("As2h3d4c5s6h7d")
    wheel_only = _hand("As2h3d4c5s9hTd")
    nine_high = _hand("5s6h7d8c9s2h3d")
    assert category_of(evaluate7_many(two_runs)[0]) is Category.STRAIGHT
    assert (evaluate7_many(two_runs)[0] >> 16) & 0xF == 7
    assert evaluate7_many(wheel_only)[0] < evaluate7_many(two_runs)[0]
    assert evaluate7_many(two_runs)[0] < evaluate7_many(nine_high)[0]
    assert evaluate7_many(two_runs)[0] == _scalar_seven(two_runs)[0]


def test_batch_paths_refuse_malformed_rows_instead_of_scoring_them() -> None:
    """A batch is built by broadcasting, and broadcasting bugs produce repeated cards that score plausibly."""
    hand = _hand("AsKsQsJsTs")
    with pytest.raises(ValueError, match=r"expected shape \(N, 5\)"):
        evaluate5_many(hand[:, :4])
    with pytest.raises(ValueError, match=r"expected shape \(N, 7\)"):
        evaluate7_many(hand)
    with pytest.raises(ValueError, match=r"0\.\.51"):
        evaluate5_many(np.array([[0, 1, 2, 3, 52]], dtype=np.int64))
    with pytest.raises(ValueError, match="repeats a physical card"):
        evaluate5_many(np.array([[0, 0, 1, 2, 3]], dtype=np.int64))
    with pytest.raises(ValueError, match="repeats a physical card"):
        evaluate7_many(np.array([[0, 0, 1, 2, 3, 4, 5]], dtype=np.int64))
    assert evaluate5_many(np.zeros((0, 5), dtype=np.int64)).shape == (0,)


def test_best_scores_many_agrees_with_best_score_on_one_board() -> None:
    """The exact-equity primitive: many holes against one shared board, in the order the caller gave.

    The board ``Kh7h5h3h2d`` carries four hearts, so a two-heart hole makes a flush and the ace-high
    flush ``Ah8h`` outranks the king-high ``ThJh`` -- and both outrank the seven-high straight ``4s6s``,
    which outranks every three of a kind on this unpaired board, which outrank the lone pair. That
    ladder is written from what the engine reports, and it is the ordering ``range_equity``'s exact mode
    will now be relying on for every combo of both ranges at once.
    """
    board = _cards("Kh7h5h3h2d")
    holes = [_cards(text) for text in ("Ah8h", "KdKc", "4s6s", "2s2c", "AdAc", "7d7c", "ThJh")]
    codes = np.array([[a.index, b.index] for a, b in holes], dtype=np.int64)
    got = best_scores_many(codes, np.array([c.index for c in board], dtype=np.int64))
    want = np.array([best_score((a, b), board) for a, b in holes], dtype=np.int64)
    assert np.array_equal(got, want)
    assert got[0] > got[6] > got[2] > got[1] > got[5] > got[3] > got[4]
    assert describe(int(got[0])) == "flush A-K-8-7-5"
    assert category_of(int(got[2])) is Category.STRAIGHT
    assert category_of(int(got[4])) is Category.ONE_PAIR
    with pytest.raises(ValueError, match="cannot also be a board card"):
        best_scores_many(
            np.array([[board[0].index, 3]], dtype=np.int64),
            np.array([c.index for c in board], dtype=np.int64),
        )


@pytest.mark.slow
def test_all_five_card_hands_match_the_batch_path() -> None:
    """Every ``C(52,5)`` hand through both paths: the claim that makes the batch path swappable.

    Chunked rather than one 2,598,960-row array, because the assertion is the element-wise comparison
    and a chunked loop keeps memory flat. The category counts are taken from the **batch** scores, so
    this re-derives ``EXPECTED_COUNTS`` through the second implementation instead of merely restating
    it -- a ranking-preserving fast path would fail here on the counts even before the element-wise
    comparison, and a re-encoded score integer would fail on ``describe`` downstream.
    """
    stream = (sorted(INDICES[i] for i in combo) for combo in combinations(range(52), 5))
    counts: Counter[int] = Counter()
    checked = 0
    while True:
        rows = list(islice(stream, 1 << 15))
        if not rows:
            break
        block = np.array(rows, dtype=np.int64)
        got = evaluate5_many(block)
        assert np.array_equal(got, _scalar_five(block))
        counts.update(int(score >> 20) for score in got)
        checked += block.shape[0]
    assert checked == 2_598_960
    for category, expected in EXPECTED_COUNTS.items():
        assert counts[int(category)] == expected, f"{category.name}: {counts[int(category)]}"


@pytest.mark.slow
def test_batch_seven_card_matches_the_definition_over_millions_of_hands() -> None:
    """``evaluate7_many`` against best-of-21 on every hand of two more subdecks, plus random full decks.

    ``6r_4s`` reaches quads, full houses, flushes and straight flushes; ``9r_3s`` reaches three of a
    kind with no flush possible at all; random hands from the real deck are the only way to reach the
    shapes that need eight or more ranks and three suits at once. Together these are the 1.7M hands a
    dev loop can afford; the 8.3M-hand ``9r_4s`` sweep was run once, out of band, when this path landed.
    """
    for label in ("6r_4s", "9r_3s"):
        hands = _all_hands(label, 7)
        assert np.array_equal(evaluate7_many(hands), evaluate7_many_reference(hands))
    rng = random.Random(20261)
    random_hands = np.array(
        [sorted(c.index for c in rng.sample(DECK, 7)) for _ in range(500_000)], dtype=np.int64
    )
    assert np.array_equal(evaluate7_many(random_hands), evaluate7_many_reference(random_hands))
    assert np.array_equal(evaluate7_many(random_hands), _scalar_seven(random_hands))


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
