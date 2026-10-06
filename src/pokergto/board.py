"""Board texture, classified by a rule rather than by feel.

"Wet", "dry", "static", "dynamic" and "paired" are the words poker teaching hides its most important
decisions behind. Here each one is a predicate with a name, so a lesson that says "this board is
dynamic" can be checked, and a generated table can label a board instead of describing it in prose.

The classification is composed from three axes, which is how the solvers actually behave:

1. **suit structure** - ``monochrome`` (all one suit), ``two-tone``, ``rainbow``;
2. **rank structure** - ``paired``, ``connected`` (two board ranks within one step), ``broadway``
   (all ten or higher), ``low`` (all six or lower), and the gap statistic;
3. **derived wetness** - ``dynamic`` when a straight or a flush draw exists for someone, ``static``
   otherwise. This is the axis that decides whether protection matters, and protection is what
   makes small bets correct on dry boards (chapter 04-06).

Composed ids are stable strings, e.g. ``dynamic.two-tone.connected``. ``data/src/board_taxonomy.yaml``
declares the same predicates so the docs can render the rule next to the label.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from .cards import Card
from .errors import InputError


def rank_values(board: Sequence[Card]) -> list[int]:
    return sorted({c.rank.value for c in board})


def max_gap(board: Sequence[Card]) -> int:
    """Largest distance between adjacent distinct board ranks. A high gap is the arithmetic version
    of "nobody really connects with this".

    A one-rank board has no gap, and reports 0 rather than inventing one.
    """
    values = rank_values(board)
    if len(values) < 2:
        return 0
    return max(b - a for a, b in zip(values, values[1:], strict=False))


def is_monochrome(board: Sequence[Card]) -> bool:
    return len({c.suit for c in board}) == 1


def is_two_tone(board: Sequence[Card]) -> bool:
    return len({c.suit for c in board}) == 2


def is_rainbow(board: Sequence[Card]) -> bool:
    return len({c.suit for c in board}) >= 3


def is_paired(board: Sequence[Card]) -> bool:
    return len({c.rank for c in board}) < len(board)


def is_connected(board: Sequence[Card], *, wheel_counts: bool = True) -> bool:
    """Two distinct board ranks within one step of each other.

    ``wheel_counts`` treats A-2 as adjacent, because it is: on A-K-7 the ace pairs nothing but on
    A-5-2 the two and the five connect through the wheel. Turning it off is how you get a board
    classification that disagrees with the card distribution.
    """
    values = rank_values(board)
    for a, b in zip(values, values[1:], strict=False):
        if b - a == 1:
            return True
    if wheel_counts and len(values) >= 2 and values[0] == 2 and values[1] == 3 and 14 in values:
        return True
    return False


def is_broadway(board: Sequence[Card]) -> bool:
    return all(c.rank.value >= 10 for c in board)


def is_low(board: Sequence[Card]) -> bool:
    return all(c.rank.value <= 6 for c in board)


def has_flush_draw_possible(board: Sequence[Card]) -> bool:
    """At least two board cards share a suit, so someone can hold the other two of it."""
    suits = [c.suit for c in board]
    return max(suits.count(s) for s in set(suits)) >= 2


def straight_draw_possible(board: Sequence[Card]) -> bool:
    """Whether the board's ranks sit inside a five-wide window, i.e. a hand can already hold a
    straight draw (open or gutshot).
    """
    values = set(rank_values(board))
    if 14 in values:
        values.add(1)
    for low in range(1, 11):
        window = values & set(range(low, low + 5))
        if len(window) >= 2:
            return True
    return False


@dataclass(frozen=True, slots=True)
class BoardTexture:
    """Everything the classifier decided, kept as data so a table can render it and a test can pin it."""

    board: tuple[str, ...]
    monochrome: bool
    two_tone: bool
    rainbow: bool
    paired: bool
    connected: bool
    broadway: bool
    low: bool
    max_gap: int
    dynamic: bool
    class_id: str

    @property
    def suit_structure(self) -> str:
        if self.monochrome:
            return "monochrome"
        if self.two_tone:
            return "two-tone"
        return "rainbow"

    @property
    def wetness(self) -> str:
        return "dynamic" if self.dynamic else "static"


def classify(board: Sequence[Card]) -> BoardTexture:
    if not 3 <= len(board) <= 5:
        raise InputError(f"a board is 3 to 5 cards, got {len(board)}")
    monochrome = is_monochrome(board)
    two_tone = is_two_tone(board)
    rainbow = is_rainbow(board)
    paired = is_paired(board)
    connected = is_connected(board)
    broadway = is_broadway(board)
    low = is_low(board)
    gap = max_gap(board)
    dynamic = (
        connected
        or (has_flush_draw_possible(board) and not monochrome)
        or straight_draw_possible(board)
    )

    parts = [
        "dynamic" if dynamic else "static",
        "monochrome" if monochrome else ("two-tone" if two_tone else "rainbow"),
    ]
    if paired:
        parts.append("paired")
    if connected and not paired:
        parts.append("connected")
    if broadway:
        parts.append("broadway")
    elif low:
        parts.append("low")
    return BoardTexture(
        board=tuple(c.code for c in board),
        monochrome=monochrome,
        two_tone=two_tone,
        rainbow=rainbow,
        paired=paired,
        connected=connected,
        broadway=broadway,
        low=low,
        max_gap=gap,
        dynamic=dynamic,
        class_id=".".join(parts),
    )


def parse_board(text: str) -> tuple[Card, ...]:
    from .cards import parse_cards

    return parse_cards(text.replace(" ", ""))


def rank_label(board: Sequence[Card]) -> str:
    """Sortable string form used in artifact ids, e.g. ``Kd7s3r`` -> ``kd7s3r``."""
    return "".join(c.code.lower() for c in board)


def rank_alphabet(board: Sequence[Card]) -> str:
    """Rank-only signature, e.g. ``K73``. Groups boards sharing a rank structure across every suit
    permutation, which is how a chapter can discuss "a K-7-3 two-tone" as one object instead of a
    thousand separate ones.
    """
    return "".join(c.rank.char for c in board)
