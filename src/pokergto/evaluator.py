"""Hand evaluation: who wins, as a single integer with a total order.

Design notes that matter for teaching, not just for speed:

* ``evaluate5`` returns one integer built as ``category << 20 | t1<<16 | t2<<12 | t3<<8 | t4<<4 | t5``.
  Four bits hold a rank (2..14), five tiebreak slots, nine categories. So ``a > b`` **is**
  "a beats b", with no tuple comparison and no special cases at the call site.
* ``evaluate7`` is a direct seven-card algorithm, and ``evaluate7_reference`` is the literal
  definition of the game -- the best of the C(7,5) = 21 sub-hands. The fast path exists so exact
  preflop enumeration is affordable, and it is therefore the part of this file that must be *proved*
  rather than read. ``tests/test_evaluator.py`` pins all 2,598,960 five-card hands on the slow path,
  cross-checks fast against reference over 20,000 random seven-card boards, and names the wheel
  (A-5-4-3-2) in a test of its own because that is the bug every evaluator eventually ships.
* ``evaluate5_many`` / ``evaluate7_many`` are the same two rules over ``(N, 5)`` and ``(N, 7)`` blocks
  of 52-card indices, and they return the **same integers** the scalar functions do. Measured on the
  laptop this was developed on: 1,028,474 five-card hands/s against 62,118 scalar (16.6x) and 313,984
  seven-card hands/s against 46,296 (6.8x). ``evaluate7_many_reference`` keeps the literal definition
  in vectorised form as the oracle, at 39,305 hands/s. The 6.8x, not the 16.6x, is what a table
  generator feels, because every equity call evaluates seven cards -- and best-of-21 in a vector
  (39,305/s) is *slower* than the scalar direct algorithm (46,296/s), which is why the direct rules
  are duplicated here instead of "just call the definition 21 times".
* The wheel (A-5-4-3-2) is a straight with high card five, and only the ace moves. This is the
  single most common evaluator bug, so it is called out in a test with a name. On seven cards the
  wheel can also *coexist* with a higher run -- ``A-2-3-4-5-6-7`` is seven-high -- and the batch path
  got that wrong until the exhaustive subdeck sweep caught it, so both facts are tested by name.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Sequence
from enum import IntEnum
from functools import lru_cache
from itertools import combinations
from typing import cast

import numpy as np

from .cards import Card, Suit

#: C(7,5) = 21 sub-hands. Computed once, over positions, not cards.
_SEVEN_FIVE_SPLITS: tuple[tuple[int, ...], ...] = tuple(combinations(range(7), 5))

#: The same table as an index array, for :func:`evaluate7_many_reference`.
_SEVEN_FIVE_SPLITS_ARRAY = np.array(_SEVEN_FIVE_SPLITS, dtype=np.intp)

#: Which five of the available cards to keep, at the arities :func:`best_scores_many` accepts. A river
#: is absent because it has a direct algorithm; the five-card entry is the identity, because a hand plus
#: a full board already is exactly one hand.
_SUB_HAND_SPLITS: dict[int, np.ndarray] = {
    5: np.array([tuple(range(5))], dtype=np.intp),
    6: np.array(tuple(combinations(range(6), 5)), dtype=np.intp),
}

#: Rows the vectorised path processes at a time. Chosen by measurement (``tools/cost_probe.py``):
#: large enough that numpy's per-call overhead stops mattering, small enough that the temporaries --
#: the 52-bin count is the widest -- stay a few megabytes and the loop stays inside cache.
BATCH_CHUNK = 1 << 14

#: Rank values along the 0..12 axis of the count table :func:`evaluate5_many` builds.
_RANK_VALUES = np.arange(2, 15, dtype=np.int64)


class Category(IntEnum):
    HIGH_CARD = 0
    ONE_PAIR = 1
    TWO_PAIR = 2
    THREE_OF_A_KIND = 3
    STRAIGHT = 4
    FLUSH = 5
    FULL_HOUSE = 6
    FOUR_OF_A_KIND = 7
    STRAIGHT_FLUSH = 8

    @property
    def zh(self) -> str:
        return _ZH[self]

    @property
    def en(self) -> str:
        return _EN[self]


_ZH: dict[Category, str] = {
    Category.HIGH_CARD: "高牌",
    Category.ONE_PAIR: "一对",
    Category.TWO_PAIR: "两对",
    Category.THREE_OF_A_KIND: "三条",
    Category.STRAIGHT: "顺子",
    Category.FLUSH: "同花",
    Category.FULL_HOUSE: "葫芦",
    Category.FOUR_OF_A_KIND: "四条",
    Category.STRAIGHT_FLUSH: "同花顺",
}

_EN: dict[Category, str] = {
    Category.HIGH_CARD: "high card",
    Category.ONE_PAIR: "one pair",
    Category.TWO_PAIR: "two pair",
    Category.THREE_OF_A_KIND: "three of a kind",
    Category.STRAIGHT: "straight",
    Category.FLUSH: "flush",
    Category.FULL_HOUSE: "full house",
    Category.FOUR_OF_A_KIND: "four of a kind",
    Category.STRAIGHT_FLUSH: "straight flush",
}

_ROYAL_FLUSH = "royal flush"
_ROYAL_FLUSH_ZH = "皇家同花顺"


def _pack(category: Category, tiebreak: Sequence[int]) -> int:
    padded = list(tiebreak[:5]) + [0] * (5 - len(tiebreak[:5]))
    score = int(category) << 20
    for shift, value in zip((16, 12, 8, 4, 0), padded, strict=True):
        if value >= 16:  # pragma: no cover - ranks are 2..14 by construction
            raise ValueError(f"tiebreak slot overflow: {value}")
        score |= value << shift
    return score


def evaluate5(cards: Sequence[Card]) -> int:
    """Total-ordered score of exactly five cards. Higher wins; equal scores are a genuine tie."""
    if len(cards) != 5:
        raise ValueError(f"evaluate5 needs exactly 5 cards, got {len(cards)}")
    counts = Counter(c.rank.value for c in cards)
    ranks_desc = sorted(counts, reverse=True)
    is_flush = len({c.suit for c in cards}) == 1

    straight_high = _straight_high_from(set(counts))

    # groups sorted by (count, rank) descending so quads/trips/pairs come first, and within equal
    # count the higher rank wins.
    groups = sorted(counts.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)
    pattern = [count for _, count in groups]
    ordered_ranks = [rank for rank, _ in groups]

    if is_flush and straight_high is not None:
        if straight_high == 14:
            return _pack(Category.STRAIGHT_FLUSH, [14])
        return _pack(Category.STRAIGHT_FLUSH, [straight_high])
    if pattern[0] == 4:
        return _pack(Category.FOUR_OF_A_KIND, ordered_ranks)
    if pattern[:2] == [3, 2]:
        return _pack(Category.FULL_HOUSE, ordered_ranks)
    if is_flush:
        return _pack(Category.FLUSH, ranks_desc)
    if straight_high is not None:
        return _pack(Category.STRAIGHT, [straight_high])
    if pattern[0] == 3:
        return _pack(Category.THREE_OF_A_KIND, ordered_ranks)
    if pattern[:2] == [2, 2]:
        return _pack(Category.TWO_PAIR, ordered_ranks)
    if pattern[0] == 2:
        return _pack(Category.ONE_PAIR, ordered_ranks)
    return _pack(Category.HIGH_CARD, ranks_desc)


def evaluate7(cards: Sequence[Card]) -> int:
    """Best five-card score available from exactly seven cards.

    Implemented directly rather than as "the best of 21 sub-hands", because twenty-one evaluations
    per board makes exact preflop enumeration (1,712,304 boards for one matchup) a ten-minute job and
    would quietly push every equity lesson onto Monte Carlo. The 21-combination definition is kept as
    :func:`evaluate7_reference` and the two are cross-checked over thousands of random boards in
    ``tests/test_evaluator.py``: this is the optimisation that must be proved, not trusted.
    """
    if len(cards) == 5:
        return evaluate5(cards)
    if len(cards) == 6:
        return max(evaluate5([cards[i] for i in split]) for split in combinations(range(6), 5))
    if len(cards) == 7:
        return _evaluate7_direct(cards)
    raise ValueError(f"evaluate7 needs 5, 6 or 7 cards, got {len(cards)}")


def evaluate7_reference(cards: Sequence[Card]) -> int:
    """The definition of the game, executed literally: the max over all C(7,5) sub-hands. Slow, and
    the oracle the fast path is tested against.
    """
    if len(cards) == 5:
        return evaluate5(cards)
    if len(cards) == 6:
        return max(evaluate5([cards[i] for i in split]) for split in combinations(range(6), 5))
    if len(cards) == 7:
        return max(evaluate5([cards[i] for i in split]) for split in _SEVEN_FIVE_SPLITS)
    raise ValueError(f"evaluate7_reference needs 5, 6 or 7 cards, got {len(cards)}")


def _straight_high_from(values: set[int]) -> int | None:
    """Highest card of a straight available among these ranks, or None.

    An ace also counts as a one, so the wheel (5-4-3-2-A) is found and scored as high-five. This
    mirror-of-the-ace rule is the most common evaluator bug in existence; it has its own test.
    """
    search = set(values)
    if 14 in search:
        search.add(1)
    for high in range(14, 4, -1):
        if all((high - offset) in search for offset in range(5)):
            return high
    return None


def _rank_counts(cards: np.ndarray, per_hand: int) -> tuple[np.ndarray, np.ndarray]:
    """Per-row card counts for a batch: ``(N, 13)`` by rank and ``(N, 13, 4)`` by rank and suit.

    ``np.bincount`` of ``row * 52 + index`` builds a dense histogram for every hand in one pass, with
    no Python loop over hands and no loop over cards. A bin above 1 means the caller supplied the same
    physical card twice, and that is refused here rather than scored, because every rule downstream
    reads these numbers as *card* counts -- "four of a kind" means four distinct cards of one rank, and
    two copies of the ace of spades would otherwise satisfy it.
    """
    n = cards.shape[0]
    rows = np.repeat(np.arange(n, dtype=np.int64), per_hand)
    counts_52 = np.bincount(rows * 52 + cards.reshape(-1), minlength=n * 52).reshape(n, 52)
    if counts_52.max() > 1:
        raise ValueError(
            "a batch hand repeats a physical card; 52-indices must be distinct per row"
        )
    by_rank_suit = counts_52.reshape(n, 13, 4)
    return by_rank_suit.sum(axis=2, dtype=np.int64), by_rank_suit


def _descending(values: np.ndarray) -> np.ndarray:
    """Sort each row high to low. Zero padding sinks to the end, which is what the callers want: they
    read the first few columns and ignore the rest, exactly like slicing a sorted Python list.
    """
    return np.flip(np.sort(values, axis=-1), axis=-1)


def _hide(ranked: np.ndarray, hidden: np.ndarray) -> np.ndarray:
    """Remove up to ``k`` named rank values from each descending row and re-descend.

    This is the vectorised form of ``[r for r in ranks_desc if r != triple][:2]``, and the re-sort is
    what makes it honest: masking an entry in place leaves a hole in the middle of the row, and a hole
    reads as a zero kicker. A ``0`` in ``hidden`` hides nothing that matters, because the padding of
    every ``ranked`` table is already zero.
    """
    keep = ~((ranked[:, :, None] == hidden[:, None, :]).any(axis=2))
    return _descending(np.where(keep, ranked, 0))


def _rank_slots(counts: np.ndarray) -> np.ndarray:
    """Per-hand tiebreak slots in :func:`evaluate5`'s order, from a ``(N, 13)`` rank-count table.

    ``counts * 16 + rank_value`` turns the sort key into one integer whose high nibble is the
    multiplicity and whose low nibble is the rank, so a single sort reproduces
    ``sorted(counts.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)``: a count step is worth 16
    and a rank is worth at most 14, so count dominates rank and the low nibble breaks ties the way the
    scalar lambda does. Keys below 16 belong to absent ranks and are zeroed, which is the same padding
    :func:`_pack` applies.
    """
    ordered = _descending(counts * 16 + _RANK_VALUES)
    return np.where(ordered >= 16, ordered & 15, 0).astype(np.int64)


def _straight_high_present(present: np.ndarray) -> np.ndarray:
    """Straight top card per row, or 0. ``present`` is a ``(N, 13)`` "rank occurs" mask.

    Ten windows, each a whole-array test, run low to high so the highest window wins. The wheel is an
    eleventh window because the ace sits at index 12 while its one-guards sit at 0..3, and it is applied
    only when no other window matched -- which is the vectorised form of ``_straight_high_from`` scanning
    from fourteen downwards. On five cards that distinction is invisible (five cards holding five
    distinct ranks form at most one run), but on seven, ``A-2-3-4-5-6-7`` contains both a wheel and a
    seven-high run and must be scored seven-high; a test that only ever passed five cards would have
    shipped that error.
    """
    high = np.zeros(present.shape[0], dtype=np.int64)
    for top_index in range(4, 13):
        window = present[:, top_index - 4 : top_index + 1].all(axis=1)
        high = np.where(window, top_index + 2, high)
    wheel = present[:, 12] & present[:, 0] & present[:, 1] & present[:, 2] & present[:, 3]
    return np.where(wheel & (high == 0), 5, high)


def _pack_many(category: np.ndarray, slots: np.ndarray) -> np.ndarray:
    """:func:`_pack` for a whole batch: ``(N,)`` categories, ``(N, 5)`` tiebreak slots.

    The cast is numpy's fault, not a smell: ``ndarray`` without dtype parameters makes every binary
    operation ``Any`` to mypy, and this repository turned ``disallow_any_generics`` off deliberately
    (see ``pyproject.toml``) rather than annotate every array twice.
    """
    return cast(
        "np.ndarray",
        (category << 20)
        | (slots[:, 0] << 16)
        | (slots[:, 1] << 12)
        | (slots[:, 2] << 8)
        | (slots[:, 3] << 4)
        | slots[:, 4],
    )


def _run_slots(straight_high: np.ndarray, like: np.ndarray) -> np.ndarray:
    """``[high, 0, 0, 0, 0]`` for a straight or straight flush.

    A run is named by its top card alone: :func:`_pack` is handed ``[straight_high]`` in the scalar
    path, so the four remaining slots must stay zero rather than fill with whatever else is in the
    hand. Two wheels ``A-5-4-3-2`` tie regardless of the suits of the five, and that is this line.
    """
    slots = np.zeros_like(like)
    slots[:, 0] = straight_high
    return slots


def _evaluate5_chunk(hands: np.ndarray) -> np.ndarray:
    """Vectorised core for one ``(N, 5)`` block of distinct 52-indices. See :func:`evaluate5_many`."""
    counts, by_rank_suit = _rank_counts(hands, 5)
    present = counts > 0
    flush = (by_rank_suit.sum(axis=1) == 5).any(axis=1)
    straight_high = _straight_high_present(present)

    # The same ladder evaluate5 walks, in the same order, so np.select's first-match rule reproduces
    # its sequence of early returns rather than re-deriving a category from a different reading.
    has_four = (counts == 4).any(axis=1)
    has_three = (counts == 3).any(axis=1)
    has_two = (counts == 2).any(axis=1)
    pairs = (counts == 2).sum(axis=1)
    category = np.select(
        [
            flush & (straight_high > 0),
            has_four,
            has_three & has_two,
            flush,
            straight_high > 0,
            has_three,
            pairs == 2,
            pairs == 1,
        ],
        [8, 7, 6, 5, 4, 3, 2, 1],
        default=0,
    ).astype(np.int64)

    slots = _rank_slots(counts)
    runs = (category == 8) | (category == 4)
    slots = np.where(runs[:, None], _run_slots(straight_high, slots), slots)
    return _pack_many(category, slots)


def evaluate5_many(hands: Sequence[Sequence[int]] | np.ndarray) -> np.ndarray:
    """Vectorised :func:`evaluate5`. ``(N, 5)`` 52-card indices in, ``(N,)`` scores out.

    The scores are the **same integers** ``evaluate5`` returns, not an order-equivalent re-encoding, so
    the two are interchangeable at the call site and :func:`describe` works on either. That is the claim
    ``tests/test_evaluator.py`` pins by enumerating all ``C(52,5) = 2,598,960`` hands and comparing
    element-wise; a merely order-preserving fast path would pass every equity test and still corrupt
    every committed table, because tables store these integers.

    Input is deck indices (``Card.index``, ``cards.ALL_COMBOS``), not :class:`~pokergto.cards.Card`
    objects: the callers this exists for -- exact equity and the preflop matrices -- already hold
    indices, and building ``Card`` objects is most of the cost the scalar path pays. Rows must be five
    *distinct* indices; a repeated card is refused rather than scored, because four-of-a-kind-looking
    counts are what a broadcasting bug produces and the wrong answer is plausible.
    """
    return _evaluate_many(hands, 5, _evaluate5_chunk)


def _evaluate7_chunk(cards: np.ndarray) -> np.ndarray:
    """Vectorised core for one ``(N, 7)`` block of distinct 52-indices, mirroring
    :func:`_evaluate7_direct`'s decision order. See :func:`evaluate7_many`.
    """
    counts, by_rank_suit = _rank_counts(cards, 7)
    n = cards.shape[0]
    by_suit_rank = by_rank_suit.transpose(0, 2, 1)  # (N, 4, 13): is this rank in this suit
    flush_suit = by_suit_rank.sum(axis=2) >= 5

    # Two suits cannot both hold five of seven cards, because 5 + 5 > 7. That single counting fact is
    # what makes the two lines below selections rather than collisions: multiplying by ``flush_suit``
    # picks the one flush suit instead of adding two together, and looking for a run in all four suits
    # is safe because a suit of four cards contains no five-card window.
    flush_values = np.where(by_suit_rank > 0, _RANK_VALUES, 0) * flush_suit[:, :, None]
    flush_top = _descending(flush_values.sum(axis=1, dtype=np.int64))

    straight_high = _straight_high_present(counts > 0)
    sf_high = _straight_high_present((by_suit_rank > 0).reshape(-1, 13)).reshape(n, 4).max(axis=1)

    # ``trip`` is the highest rank holding three or more, and ``boat_pair`` the highest *other* rank
    # holding two or more, which is how _evaluate7_direct reads its (count, rank)-ordered ``next()``
    # calls: with quads already claimed by a higher-priority rung, a second set of trips legitimately
    # supplies the pair. ``second_pair`` likewise excludes ``high_pair``, so three pairs on the board
    # become the two best of them plus the third as kicker.
    distinct = _descending(np.where(counts > 0, _RANK_VALUES, 0))
    quad = np.where(counts == 4, _RANK_VALUES, 0).max(axis=1)
    trip = np.where(counts >= 3, _RANK_VALUES, 0).max(axis=1)
    high_pair = np.where(counts >= 2, _RANK_VALUES, 0).max(axis=1)
    second_pair = _descending(
        np.where((counts >= 2) & (high_pair[:, None] != _RANK_VALUES), _RANK_VALUES, 0)
    )[:, 0]
    boat_pair = np.where((counts >= 2) & (trip[:, None] != _RANK_VALUES), _RANK_VALUES, 0).max(
        axis=1
    )
    zero = np.zeros(n, dtype=np.int64)
    five = distinct[:, :5]

    ladder = [
        (
            high_pair > 0,
            np.column_stack([high_pair, _hide(distinct, high_pair[:, None])[:, :3], zero]),
        ),
        (
            second_pair > 0,
            np.column_stack(
                [
                    high_pair,
                    second_pair,
                    _hide(distinct, np.column_stack([high_pair, second_pair]))[:, :1],
                    zero,
                    zero,
                ]
            ),
        ),
        (trip > 0, np.column_stack([trip, _hide(distinct, trip[:, None])[:, :2], zero, zero])),
        (straight_high > 0, _run_slots(straight_high, five)),
        (flush_suit.any(axis=1), flush_top[:, :5]),
        (
            (trip > 0) & (boat_pair > 0),
            np.column_stack([trip, boat_pair, zero, zero, zero]),
        ),
        (
            quad > 0,
            np.column_stack([quad, _hide(distinct, quad[:, None])[:, :1], zero, zero, zero]),
        ),
        (sf_high > 0, _run_slots(sf_high, five)),
    ]

    # One walk up the category ladder, weak to strong, so the category and its tiebreak slots are
    # produced by the same predicate. Two independent encodings of the same rules -- which is what a
    # ``np.select`` alongside a second ``np.select`` would be -- can disagree, and a disagreement
    # between a hand's name and its score is exactly the bug that survives a category-count test.
    slots = five
    category = np.zeros(n, dtype=np.int64)
    for value, (mask, candidate) in enumerate(ladder, start=1):
        slots = np.where(mask[:, None], candidate, slots)
        category = np.where(mask, value, category)
    return _pack_many(category, slots)


def evaluate7_many(hands: Sequence[Sequence[int]] | np.ndarray) -> np.ndarray:
    """Vectorised :func:`evaluate7`: ``(N, 7)`` 52-card indices in, ``(N,)`` scores out.

    This is the one place in the codebase where a fast algorithm is *not* the definition, so the oracle
    sits next to it: :func:`evaluate7_many_reference` computes the literal best-of-21 from
    :func:`evaluate5_many`, whose own path is exhaustively proved over every five-card hand. The two are
    compared over every hand of several subdecks and over millions of random boards in
    ``tests/test_evaluator.py``. Measured at the time of writing, the reference form is *slower* than
    the scalar :func:`evaluate7` (43,204 vs 45,389 hands/s), because 21 five-card evaluations divided by
    an 18x vector speed-up is a wash -- which is the whole reason this function exists.
    """
    return _evaluate_many(hands, 7, _evaluate7_chunk)


def evaluate7_many_reference(hands: Sequence[Sequence[int]] | np.ndarray) -> np.ndarray:
    """The definition, vectorised: the maximum over each hand's C(7,5) = 21 five-card sub-hands.

    Slow by construction, and correct by construction -- it inherits everything from
    :func:`evaluate5_many`. It exists to be the oracle :func:`evaluate7_many` is proved against, and it
    is the same relationship :func:`evaluate7_reference` has to :func:`evaluate7`.
    """
    codes = np.asarray(hands, dtype=np.int64)
    if codes.ndim != 2 or codes.shape[1] != 7:
        raise ValueError(f"expected shape (N, 7) of 52-card indices, got {codes.shape}")
    if codes.size and (codes.min() < 0 or codes.max() > 51):
        raise ValueError("card indices must be in 0..51")
    out = np.empty(codes.shape[0], dtype=np.int64)
    for start in range(0, codes.shape[0], BATCH_CHUNK):
        block = codes[start : start + BATCH_CHUNK]
        subhands = block[:, _SEVEN_FIVE_SPLITS_ARRAY].reshape(-1, 5)
        out[start : start + BATCH_CHUNK] = (
            evaluate5_many(subhands).reshape(block.shape[0], 21).max(axis=1)
        )
    return out


def _evaluate_many(
    hands: Sequence[Sequence[int]] | np.ndarray,
    per_hand: int,
    chunk: Callable[[np.ndarray], np.ndarray],
) -> np.ndarray:
    """Shape and range validation, then ``chunk`` over rows of at most :data:`BATCH_CHUNK`."""
    codes = np.asarray(hands, dtype=np.int64)
    if codes.ndim != 2 or codes.shape[1] != per_hand:
        raise ValueError(f"expected shape (N, {per_hand}) of 52-card indices, got {codes.shape}")
    if codes.size and (codes.min() < 0 or codes.max() > 51):
        raise ValueError("card indices must be in 0..51")
    if codes.shape[0] == 0:
        return np.zeros(0, dtype=np.int64)
    if codes.shape[0] <= BATCH_CHUNK:
        return chunk(codes)
    out = np.empty(codes.shape[0], dtype=np.int64)
    for start in range(0, codes.shape[0], BATCH_CHUNK):
        out[start : start + BATCH_CHUNK] = chunk(codes[start : start + BATCH_CHUNK])
    return out


def best_scores_many(
    holes: Sequence[Sequence[int]] | np.ndarray, board: Sequence[int] | np.ndarray
) -> np.ndarray:
    """Best five-card score for many hole cards against one shared board of three to five cards.

    ``(N, 2)`` holes and a three-to-five-card board, both 52-card indices. This is the shape a range
    query wants: score every surviving combo of the range against the board in one call instead of
    building ``N`` tuples of :class:`~pokergto.cards.Card` objects.

    Seven cards (a river) go through :func:`evaluate7_many`, the proved direct algorithm. Five and six
    cards go through the literal definition instead, because no direct algorithm exists at those
    arities and the price is small: ``C(6,5) = 6`` five-card evaluations per hand at the measured
    1,028,474 hands/s, which scores a whole 1,081-combo ceiling sweep on a flop in about four
    milliseconds.
    """
    hole_codes = np.asarray(holes, dtype=np.int64)
    board_codes = np.asarray(board, dtype=np.int64)
    if hole_codes.ndim != 2 or hole_codes.shape[1] != 2:
        raise ValueError(f"expected hole cards of shape (N, 2), got {hole_codes.shape}")
    if board_codes.ndim != 1 or not 3 <= board_codes.shape[0] <= 5:
        raise ValueError(f"expected 3 to 5 board cards, got shape {board_codes.shape}")
    if np.isin(hole_codes, board_codes).any():
        raise ValueError("a hole card cannot also be a board card; drop the combo before scoring")
    shared = np.broadcast_to(board_codes, (hole_codes.shape[0], board_codes.shape[0]))
    cards = np.concatenate([hole_codes, shared], axis=1)
    if cards.shape[1] == 7:
        return evaluate7_many(cards)
    splits = _SUB_HAND_SPLITS[cards.shape[1]]
    subhands = cards[:, splits].reshape(-1, 5)
    return cast("np.ndarray", evaluate5_many(subhands).reshape(cards.shape[0], -1).max(axis=1))


def _evaluate7_direct(cards: Sequence[Card]) -> int:
    counts = Counter(c.rank.value for c in cards)
    by_suit: dict[Suit, list[int]] = {}
    for card in cards:
        by_suit.setdefault(card.suit, []).append(card.rank.value)

    flush_suits = [suit for suit, ranks in by_suit.items() if len(ranks) >= 5]

    # 1. Straight flush: only a suit holding five cards can produce one. Checked first, because it
    #    outranks everything below and is invisible to the "is there a flush" test alone.
    for suit in flush_suits:
        high = _straight_high_from(set(by_suit[suit]))
        if high is not None:
            return _pack(Category.STRAIGHT_FLUSH, [high])

    ranks_desc = sorted(counts, reverse=True)
    ordered = sorted(counts.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)
    top_count = ordered[0][1]
    triple_rank = next((rank for rank, size in ordered if size >= 3), None)
    pair_rank = next((rank for rank, size in ordered if size >= 2 and rank != triple_rank), None)

    if top_count >= 4:
        quad = ordered[0][0]
        kicker = max((rank for rank in counts if rank != quad), default=0)
        return _pack(Category.FOUR_OF_A_KIND, [quad, kicker])

    if triple_rank is not None and pair_rank is not None:
        # With two sets of triples the higher one is the triple and the lower becomes the pair,
        # which falls out of `ordered` being sorted by (count, rank) already.
        return _pack(Category.FULL_HOUSE, [triple_rank, pair_rank])

    if flush_suits:
        return _pack(Category.FLUSH, sorted(by_suit[flush_suits[0]], reverse=True)[:5])

    straight_high = _straight_high_from(set(counts))
    if straight_high is not None:
        return _pack(Category.STRAIGHT, [straight_high])

    if triple_rank is not None:
        kickers = [rank for rank in ranks_desc if rank != triple_rank][:2]
        return _pack(Category.THREE_OF_A_KIND, [triple_rank, *kickers])

    pairs = sorted((rank for rank, size in counts.items() if size >= 2), reverse=True)
    if len(pairs) >= 2:
        kicker = max((rank for rank in ranks_desc if rank not in pairs[:2]), default=0)
        return _pack(Category.TWO_PAIR, [pairs[0], pairs[1], kicker])
    if len(pairs) == 1:
        kickers = [rank for rank in ranks_desc if rank != pairs[0]][:3]
        return _pack(Category.ONE_PAIR, [pairs[0], *kickers])
    return _pack(Category.HIGH_CARD, ranks_desc[:5])


#: The only three-card run that is not named by its own top card.
_WHEEL_LOW = 3


def _straight_high_from_three(values: set[int]) -> int | None:
    """High card of a three-card straight, or ``None``.

    ``A-2-3`` is a straight and it is **three-high**: inside the wheel the ace plays as a one, so the top
    card of the run is the three. Naming it five-high the way :func:`evaluate5` names ``A-5-4-3-2`` would
    make ``A-2-3`` and ``2-3-4`` compare equal, which is not a rule anyone plays by.
    """
    if len(values) != 3:
        return None
    ordered = sorted(values)
    if ordered[2] - ordered[0] == 2:
        return ordered[2]
    if ordered == [2, 3, 14]:
        return _WHEEL_LOW
    return None


def evaluate3(cards: Sequence[Card]) -> int:
    """Total-ordered score of exactly three cards, packed with the same integers as :func:`evaluate5`.

    Leduc hold'em deals one private card each against a two-card board, so its showdown is a three-card
    comparison and :func:`evaluate5` cannot express it. The category ladder is reused verbatim --
    ``STRAIGHT_FLUSH > FLUSH > STRAIGHT > ONE_PAIR > HIGH_CARD`` -- because Leduc is a hold'em variant and
    its rules say hold'em's ordering restricted to the hands that can exist, not three-card poker's
    ordering (where a straight outranks a flush because the deck is different).

    Which categories a deck can actually reach is a fact to enumerate rather than assume, and on Leduc's
    six-card deck (J, Q, K in two suits) three of a kind cannot occur because no rank has a third copy,
    and every flush is automatically a straight because the only three-card flush is J-Q-K of one suit.
    The two orderings that differ between conventions therefore never fire here; ``tests/test_evaluator.py``
    walks all C(6,3) boards to pin that claim instead of trusting this paragraph.
    """
    if len(cards) != 3:
        raise ValueError(f"evaluate3 needs exactly 3 cards, got {len(cards)}")
    counts = Counter(c.rank.value for c in cards)
    ranks_desc = sorted(counts, reverse=True)
    is_flush = len({c.suit for c in cards}) == 1
    straight_high = _straight_high_from_three(set(counts))
    groups = sorted(counts.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)
    pattern = [count for _, count in groups]
    ordered_ranks = [rank for rank, _ in groups]

    if pattern[0] == 3:
        return _pack(Category.THREE_OF_A_KIND, ordered_ranks)
    if is_flush and straight_high is not None:
        return _pack(Category.STRAIGHT_FLUSH, [straight_high])
    if is_flush:
        return _pack(Category.FLUSH, ranks_desc)
    if straight_high is not None:
        return _pack(Category.STRAIGHT, [straight_high])
    if pattern[0] == 2:
        pair_rank, *kickers = ordered_ranks
        return _pack(Category.ONE_PAIR, [pair_rank, *kickers])
    return _pack(Category.HIGH_CARD, ranks_desc)


def best_score_three(private: Sequence[Card], board: Sequence[Card]) -> int:
    """Showdown score for a one-private-card, two-board-card game such as Leduc hold'em."""
    private_cards = tuple(private)
    board_cards = tuple(board)
    if len(private_cards) != 1:
        raise ValueError(
            f"a three-card showdown takes exactly 1 private card, got {len(private_cards)}"
        )
    if len(board_cards) != 2:
        raise ValueError(
            f"a three-card showdown takes exactly 2 board cards, got {len(board_cards)}"
        )
    if private_cards[0] in board_cards:
        raise ValueError(f"{private_cards[0].code} cannot be both a player's card and a board card")
    return evaluate3([*private_cards, *board_cards])


def best_score(hole: Sequence[Card], board: Sequence[Card]) -> int:
    """Best hand from a player's hole cards plus the board. Accepts 3..5 board cards."""
    all_cards = tuple(hole) + tuple(board)
    if len(hole) != 2:
        raise ValueError(f"expected exactly 2 hole cards, got {len(hole)}")
    if not 3 <= len(board) <= 5:
        raise ValueError(f"expected 3 to 5 board cards, got {len(board)}")
    return evaluate7(all_cards)


@lru_cache(maxsize=1 << 15)
def category_of(score: int) -> Category:
    return Category(score >> 20)


def showdown(hand_a: Sequence[Card], hand_b: Sequence[Card], board: Sequence[Card]) -> int:
    """``-1`` if hand_a wins, ``1`` if hand_b wins, ``0`` if they split. Signature follows the
    comparison convention (like ``sorted``) so that ``showdown(a,b) == -showdown(b,a)``.
    """
    sa = best_score(hand_a, board)
    sb = best_score(hand_b, board)
    if sa == sb:
        return 0
    return -1 if sa > sb else 1


def split_pot(
    hands: Sequence[Sequence[Card]], board: Sequence[Card]
) -> tuple[list[int], list[int]]:
    """Return (winners, all_indices). Winners are the indices sharing the top score.

    Split pots are why "equity" and "hand strength" are different quantities: two hands with the
    same score divide the money, and that tie term is what makes ``equity(r, r) == 0.5`` exactly.
    """
    scores = [best_score(h, board) for h in hands]
    top = max(scores)
    return [i for i, s in enumerate(scores) if s == top], list(range(len(scores)))


def describe(score: int, *, lang: str = "en") -> str:
    """Human-readable hand, e.g. ``two pair, AA77`` / ``两对 A7``. Used by CLI reports, never by
    comparisons — those use the integer.
    """
    category = category_of(score)
    slots = [(score >> shift) & 0xF for shift in (16, 12, 8, 4, 0)]
    zh = lang == "zh"
    name = category.zh if zh else category.en

    def rank_name(value: int) -> str:
        if value == 0:
            return ""
        return {14: "A", 13: "K", 12: "Q", 11: "J", 10: "T"}.get(value, str(value))

    if category is Category.STRAIGHT_FLUSH:
        if slots[0] == 14:
            return _ROYAL_FLUSH_ZH if zh else _ROYAL_FLUSH
        return f"{'同花顺' if zh else 'straight flush'} {rank_name(slots[0])}"
    if category in (Category.FLUSH, Category.HIGH_CARD, Category.STRAIGHT):
        rendered = "-".join(rank_name(s) for s in slots if s)
        return f"{name} {rendered}".strip()
    rendered = " ".join(rank_name(s) for s in slots if s)
    return f"{name} {rendered}".strip()
