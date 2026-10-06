"""A deliberately naive five- and seven-card evaluator, written to be read rather than to be fast.

This exists only as a test oracle. It implements the rules of poker in the order a rulebook does --
classify, then compare -- with tuples instead of bit packing, and no shared code with
:mod:`pokergto.evaluator`. If both implementations agree on all 2,598,960 five-card hands, the
probability that the same misunderstanding sits in both is low enough to ship.

Keeping it in ``tests/`` and not in ``src/`` is the point: production code must not be able to depend
on the oracle.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from itertools import combinations

from pokergto.cards import Card

_STRAIGHT_WHEEL = {14, 5, 4, 3, 2}


def _ranks(cards: Sequence[Card]) -> list[int]:
    return sorted((card.rank.value for card in cards), reverse=True)


def classify(cards: Sequence[Card]) -> tuple[int, tuple[int, ...]]:
    """``(category, tiebreak)`` using the ordering HIGH_CARD=0 .. STRAIGHT_FLUSH=8."""
    if len(cards) != 5:
        raise ValueError("the reference evaluator classifies exactly five cards")
    ranks = _ranks(cards)
    counts = Counter(ranks)
    by_count = sorted(counts.items(), key=lambda item: (item[1], item[0]), reverse=True)
    pattern = [count for _, count in by_count]
    ordered = [rank for rank, _ in by_count]
    flush = len({card.suit for card in cards}) == 1
    distinct = sorted(set(ranks), reverse=True)
    straight_high: int | None = None
    if len(distinct) == 5:
        # The high card of a run is its top card, not its bottom. 6-5-4-3-2 is a six-high straight;
        # reading distinct[4] here would rank it below every three-of-a-kind comparison path and make
        # the oracle disagree with the fast evaluator in a way that looks like the fast one's fault.
        if distinct[0] - distinct[4] == 4:
            straight_high = distinct[0]
        elif set(distinct) == _STRAIGHT_WHEEL:
            straight_high = 5
    if flush and straight_high is not None:
        return 8, (straight_high,)
    if pattern[0] == 4:
        return 7, tuple(ordered)
    if pattern[:2] == [3, 2]:
        return 6, tuple(ordered)
    if flush:
        return 5, tuple(ranks)
    if straight_high is not None:
        return 4, (straight_high,)
    if pattern[0] == 3:
        return 3, tuple(ordered)
    if pattern[:2] == [2, 2]:
        return 2, tuple(ordered)
    if pattern[0] == 2:
        return 1, tuple(ordered)
    return 0, tuple(ranks)


def naive_evaluate5(cards: Sequence[Card]) -> tuple[int, tuple[int, ...]]:
    return classify(cards)


def naive_evaluate7(cards: Sequence[Card]) -> tuple[int, tuple[int, ...]]:
    """Best of the C(7,5) sub-hands, selected by comparing ``(category, tiebreak)`` tuples directly.

    No cleverness, so a reviewer can check it against the rules of the game in one read.
    """
    if len(cards) not in (5, 6, 7):
        raise ValueError("expected 5, 6 or 7 cards")
    return max(
        classify([cards[index] for index in split]) for split in combinations(range(len(cards)), 5)
    )
