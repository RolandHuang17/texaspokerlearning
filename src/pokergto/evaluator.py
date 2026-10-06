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
* The wheel (A-5-4-3-2) is a straight with high card five, and only the ace moves. This is the
  single most common evaluator bug, so it is called out in a test with a name.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from enum import IntEnum
from functools import lru_cache
from itertools import combinations

from .cards import Card, Suit

#: C(7,5) = 21 sub-hands. Computed once, over positions, not cards.
_SEVEN_FIVE_SPLITS: tuple[tuple[int, ...], ...] = tuple(combinations(range(7), 5))


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
