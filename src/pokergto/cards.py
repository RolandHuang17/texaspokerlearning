"""Cards, ranks, suits, and the two canonical encodings this project depends on.

Two encodings matter and they are not interchangeable:

* **52-card index** (0..51) — one physical card. Used for decks, removal, and board literals.
* **1326 combos / 169 classes** — an unordered pair of hole cards, either as a specific 2-card
  combination (a *combo*) or as a rank+suit-shape class (e.g. ``AKs``). 169 classes carry 4, 6 or
  12 combos each: pairs 6, suited 4, offsuit 12, and ``13*6 + 78*4 + 78*12 == 1326``.

The 1326 decomposition is asserted in tests rather than assumed. It is also why ``Grid13`` stores
frequencies only: combo counts come from here, so there is exactly one combinatorial path in the
codebase that could be wrong.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from itertools import combinations
from typing import Final, Iterator, Sequence

from .errors import InputError, InvariantError

RANK_CHARS: Final = "23456789TJQKA"
SUIT_CHARS: Final = "cdhs"


class Rank(Enum):
    """Card rank. ``value`` is the pip value, so aces are high by construction."""

    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14

    @property
    def char(self) -> str:
        return RANK_CHARS[self.value - 2]

    @property
    def index(self) -> int:
        """0 for TWO .. 12 for ACE. This is the 13x13 grid axis order when reversed."""
        return self.value - 2

    @classmethod
    def from_char(cls, ch: str) -> Rank:
        try:
            return cls(RANK_CHARS.index(ch.upper()) + 2)
        except ValueError as exc:
            raise InputError(f"unknown rank {ch!r}; expected one of {RANK_CHARS}") from exc


class Suit(Enum):
    """Card suit. ``value`` is the lowercase character used in board literals like ``Kd7s3r``."""

    CLUB = "c"
    DIAMOND = "d"
    HEART = "h"
    SPADE = "s"

    @property
    def zh(self) -> str:
        return {"c": "梅花", "d": "方块", "h": "红心", "s": "黑桃"}[self.value]

    @property
    def is_red(self) -> bool:
        return self in (Suit.DIAMOND, Suit.HEART)

    @classmethod
    def from_char(cls, ch: str) -> Suit:
        try:
            return cls(ch.lower())
        except ValueError as exc:
            raise InputError(f"unknown suit {ch!r}; expected one of {SUIT_CHARS}") from exc


@dataclass(frozen=True, slots=True)
class Card:
    """One physical card."""

    rank: Rank
    suit: Suit

    @classmethod
    def parse(cls, text: str) -> Card:
        """Accept ``As``, ``AS``, ``10s``, ``Ts``. Two characters is the canonical form."""
        s = text.strip()
        if not s:
            raise InputError("empty card string")
        if s[0] in "1" and s.startswith("10"):
            rank, suit_text = Rank.TEN, s[3:]
        elif s[0].upper() in "A23456789KQJT":
            rank = Rank.from_char(s[0])
            suit_text = s[1:]
        else:
            raise InputError(f"cannot parse card {text!r}")
        if len(suit_text) != 1:
            raise InputError(f"card {text!r} needs exactly one suit character")
        return cls(rank, Suit.from_char(suit_text))

    @property
    def code(self) -> str:
        return f"{self.rank.char}{self.suit.value}"

    @property
    def index(self) -> int:
        """Canonical deck position: rank-major (TWO of clubs is 0), suits in ``cdhs`` order."""
        return self.rank.index * 4 + SUIT_CHARS.index(self.suit.value)

    @classmethod
    def from_index(cls, index: int) -> Card:
        if not 0 <= index < 52:
            raise InputError(f"card index {index} out of range 0..51")
        rank_idx, suit_idx = divmod(index, 4)
        return cls(Rank.from_char(RANK_CHARS[rank_idx]), Suit.from_char(SUIT_CHARS[suit_idx]))

    def __str__(self) -> str:
        return self.code

    def __lt__(self, other: Card) -> bool:
        return (self.rank.value, self.suit.value) < (other.rank.value, other.suit.value)


def parse_cards(text: str, *, sep: str = "") -> tuple[Card, ...]:
    """Parse ``Kd7s3r`` or ``Kd 7s 3r``. Duplicate cards raise rather than silently collapse."""
    tokens = text.split(sep) if sep else [text[i : i + 2] for i in range(0, len(text), 2)]
    cards = tuple(Card.parse(t) for t in tokens if t)
    if len({c.index for c in cards}) != len(cards):
        raise InputError(f"duplicate card in {text!r}: a deck has one of each")
    return cards


def standard_deck() -> tuple[Card, ...]:
    return tuple(Card.from_index(i) for i in range(52))


# --- hole-card encodings ---------------------------------------------------------------

#: Axis order of every 13x13 chart in the repository. Descending rank, ACE first.
GRID_RANKS: Final[tuple[Rank, ...]] = tuple(
    Rank.from_char(c) for c in "AKQJT98765432"
)


def class_key(first: Card, second: Card) -> str:
    """The 169-class key of a hole-card pair: ``AA``, ``AKs``, ``AKo``.

    Higher rank is written first, and ``s``/``o`` is decided by suit equality, never by which card
    was passed first.
    """
    if first.index == second.index:
        raise InputError(f"cannot pair a card with itself: {first}")
    hi, lo = (first, second) if first.rank.value >= second.rank.value else (second, first)
    if hi.rank is lo.rank:
        return f"{hi.rank.char}{lo.rank.char}"
    return f"{hi.rank.char}{lo.rank.char}{'s' if hi.suit is lo.suit else 'o'}"


def combos_for_class(key: str) -> int:
    """6 for a pocket pair, 4 for suited, 12 for offsuit."""
    if len(key) == 2:
        return 6
    if key[2] == "s":
        return 4
    if key[2] == "o":
        return 12
    raise InputError(f"malformed 169 class {key!r}")


def _ordered_class_keys() -> tuple[str, ...]:
    chars = "AKQJT98765432"
    keys: list[str] = [c + c for c in chars]
    keys += [a + b + "s" for i, a in enumerate(chars) for b in chars[i + 1 :]]
    keys += [a + b + "o" for i, a in enumerate(chars) for b in chars[i + 1 :]]
    return tuple(keys)


#: 169 canonical classes, pairs first, then suited, then offsuit, each in descending rank order.
HAND_CLASSES_169: Final[tuple[str, ...]] = _ordered_class_keys()

#: Every unordered pair of distinct cards, in canonical 52-index order. Length 1326.
ALL_COMBOS: Final[tuple[tuple[int, int], ...]] = tuple(combinations(range(52), 2))

if len(ALL_COMBOS) != 1326:  # pragma: no cover - unreachable unless the module is broken
    raise InvariantError(f"combo enumeration produced {len(ALL_COMBOS)}, expected 1326")
if len(HAND_CLASSES_169) != 169:  # pragma: no cover
    raise InvariantError(f"class enumeration produced {len(HAND_CLASSES_169)}, expected 169")


def combo_cards(combo: tuple[int, int]) -> tuple[Card, Card]:
    return (Card.from_index(combo[0]), Card.from_index(combo[1]))


def class_combos(key: str) -> tuple[tuple[int, int], ...]:
    """The physical combos belonging to a 169 class. ``AKs`` has four; ``AKo`` has twelve."""
    if key not in HAND_CLASSES_169:
        raise InputError(f"unknown hand class {key!r}")
    return tuple(c for c in ALL_COMBOS if class_key(*(combo_cards(c))) == key)


def enumerate_combos() -> Iterator[tuple[tuple[int, int], str]]:
    for combo in ALL_COMBOS:
        yield combo, class_key(*combo_cards(combo))


def remove_cards(available: Sequence[int], removed: Sequence[Card]) -> list[int]:
    """Card removal. Explicit, because 'blocker' claims that ignore it are the most common
    arithmetic error in poker content."""
    gone = {c.index for c in removed}
    return [i for i in available if i not in gone]


def suits(cards: Sequence[Card]) -> set[str]:
    return {c.suit.value for c in cards}
