"""Ranges as combo-weighted vectors over the 1326 canonical hole-card combinations.

Why combos and not the 169 classes: a range's behaviour is determined by how many *physical*
combos it contains per class, and those differ by a factor of three (pairs 6, suited 4,
offsuit 12). Averaging over classes instead of combos silently weights ``AKo`` as though it were
as common as ``AA``, which corrupts every aggregate EV derived from it. So:

* ``Range.weights`` is a length-1326 vector over :data:`pokergto.cards.ALL_COMBOS`.
* Class-level views (the 13x13 chart, the 169-entry frequency map) are *derived* from it.
* :class:`pokergto.matrix13.Grid13` stores frequencies only, and combo counts always come from here.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .cards import (
    ALL_COMBOS,
    HAND_CLASSES_169,
    Card,
    class_key,
    combos_for_class,
)
from .errors import InputError, InvariantError

#: Position of each combo inside ALL_COMBOS, for O(1) lookup from a pair of card indices.
_COMBO_POSITION: dict[tuple[int, int], int] = {combo: i for i, combo in enumerate(ALL_COMBOS)}

#: 169 class -> list of combo positions. Built once; 1326 iterations total, not 169 x 1326.
_CLASS_POSITIONS: dict[str, list[int]] = {key: [] for key in HAND_CLASSES_169}
for _position, _combo in enumerate(ALL_COMBOS):
    _key = class_key(Card.from_index(_combo[0]), Card.from_index(_combo[1]))
    _CLASS_POSITIONS[_key].append(_position)

if sum(len(v) for v in _CLASS_POSITIONS.values()) != 1326:  # pragma: no cover
    raise InvariantError("combo/class indexing is inconsistent")


@dataclass(slots=True)
class Range:
    """A combo-weighted distribution over hole cards.

    ``weights[i]`` is the probability that the holder has combo ``ALL_COMBOS[i]``, in [0, 1].
    A class's weight **in combos** is therefore the sum over its positions: pocket aces fully
    included contributes 6, ``AKs`` half-included contributes 2 of its 4.

    Why combos and not the 169 classes: a range's behaviour is determined by how many *physical*
    combos it contains per class, and those differ by a factor of three (pairs 6, suited 4,
    offsuit 12). Averaging over classes instead of combos silently weights ``AKo`` as though it
    were as common as ``AA``, which corrupts every aggregate EV derived from it. Class-level views
    (the 13x13 chart, the 169-entry frequency map) are always derived from this vector, never
    stored beside it.
    """

    weights: np.ndarray = field(default_factory=lambda: np.zeros(1326, dtype=np.float64))
    #: Set when a range was round-tripped through a lossy notation. See notation.to_spec().
    lossy: bool = False

    def __post_init__(self) -> None:
        if self.weights.shape != (1326,):
            raise InputError(f"range weights must have shape (1326,), got {self.weights.shape}")
        if np.any(self.weights < -1e-12) or np.any(self.weights > 1.0 + 1e-12):
            raise InputError("combo weights must be within [0,1]; see combos() for combo counts")
        self.weights = np.clip(self.weights.astype(np.float64, copy=False), 0.0, 1.0)

    # --- constructors ---------------------------------------------------------------

    @classmethod
    def empty(cls) -> Range:
        return cls()

    @classmethod
    def full(cls) -> Range:
        return cls(np.ones(1326, dtype=np.float64))

    @classmethod
    def from_cards(cls, cards: Sequence[Card]) -> Range:
        """Build from one *specific* combo, like ``Ah As``. Ranges answer "how often do I hold this
        class of hand?"; this answers "I hold exactly these two cards", which is what a live hand
        played at the table is.
        """
        if len(cards) != 2:
            raise InputError("a hand is exactly two cards")
        if cards[0].index == cards[1].index:
            raise InputError("a hand cannot contain the same card twice")
        weights = np.zeros(1326, dtype=np.float64)
        weights[combo_positions(cards)] = 1.0
        return cls(weights)

    @classmethod
    def from_classes(cls, entries: Iterable[str] | Mapping[str, float]) -> Range:
        """Build from 169-class keys. A bare key means the class is fully included; a mapping value
        is that class's *frequency*, so ``{"AKs": 0.5}`` holds half of its four combos = 2 combos.
        """
        weights = np.zeros(1326, dtype=np.float64)
        items: Iterable[Any]
        if isinstance(entries, Mapping):
            items = entries.items()
        else:
            items = ((key, 1.0) for key in entries)
        for key, fraction in items:
            if key not in _CLASS_POSITIONS:
                raise InputError(f"unknown hand class {key!r}")
            if not 0.0 <= float(fraction) <= 1.0:
                raise InputError(f"frequency for {key} must be within [0,1], got {fraction}")
            weights[_CLASS_POSITIONS[key]] = float(fraction)
        return cls(weights)

    # --- queries --------------------------------------------------------------------

    def combos(self, key: str | None = None) -> float:
        """Total weight, or the weight of one class."""
        if key is None:
            return float(self.weights.sum())
        return float(self.weights[_CLASS_POSITIONS[key]].sum())

    def total_combos(self) -> float:
        return float(self.weights.sum())

    def weight(self, first: Card, second: Card) -> float:
        position = _COMBO_POSITION.get(
            (min(first.index, second.index), max(first.index, second.index))
        )
        if position is None:
            raise InputError(f"{first}{second} is not a canonical combo")
        return float(self.weights[position])

    def classes(self) -> dict[str, float]:
        """Class -> weight in combos, nonzero entries only."""
        out: dict[str, float] = {}
        for key, positions in _CLASS_POSITIONS.items():
            value = float(self.weights[positions].sum())
            if value > 0.0:
                out[key] = value
        return out

    def frequency_map(self) -> dict[str, float]:
        """Class -> frequency in [0,1] relative to that class's own combo count. This is what a
        13x13 chart cell holds, and what a solver's strategy vector holds.
        """
        out: dict[str, float] = {}
        for key, positions in _CLASS_POSITIONS.items():
            total = combos_for_class(key)
            value = float(self.weights[positions].sum()) / total
            if value > 1e-12:
                out[key] = round(min(value, 1.0), 12)
        return out

    def active_classes(self) -> list[str]:
        return sorted(self.frequency_map(), key=HAND_CLASSES_169.index)

    def is_empty(self) -> bool:
        return bool(np.all(self.weights == 0.0))

    def __bool__(self) -> bool:
        return not self.is_empty()

    def __iter__(self) -> Iterator[tuple[Card, Card, float]]:
        for position, weight in enumerate(self.weights):
            if weight > 0.0:
                first, second = ALL_COMBOS[position]
                yield Card.from_index(first), Card.from_index(second), float(weight)

    # --- algebra --------------------------------------------------------------------

    def union(self, other: Range) -> Range:
        """Element-wise max: 'in either range'. Two ranges each holding one combo of AKs do not
        become two combos of AKs, which is why this is max and not add.
        """
        return Range(np.maximum(self.weights, other.weights))

    def intersect(self, other: Range) -> Range:
        return Range(np.minimum(self.weights, other.weights))

    def complement(self) -> Range:
        return Range(self.full_weight_vector() - self.weights)

    def full_weight_vector(self) -> np.ndarray:
        """1.0 per combo of every class, i.e. the all-combos vector this range is a subset of."""
        return np.ones(1326, dtype=np.float64)

    def subtract(self, other: Range) -> Range:
        return Range(np.clip(self.weights - other.weights, 0.0, None))

    def scaled(self, factor: float) -> Range:
        return Range(self.weights * float(factor))

    def with_removed(self, *cards: Card) -> Range:
        """Card removal, expressed the only way that is safe: zero out combos that contain a
        specified card. A blocker claim that skips this step is arithmetic, not opinion.
        """
        gone = {c.index for c in cards}
        weights = self.weights.copy()
        for position, (first, second) in enumerate(ALL_COMBOS):
            if first in gone or second in gone:
                weights[position] = 0.0
        return Range(weights)

    def normalized(self) -> Range:
        total = self.total_combos()
        if total == 0.0:
            return Range()
        return Range(self.weights / total)

    def equal(self, other: Range, *, tol: float = 1e-9) -> bool:
        return bool(np.max(np.abs(self.weights - other.weights)) <= tol)

    def assert_valid(self, *, tol: float = 1e-9) -> None:
        """The primitive behind the ``frequency_bounds`` check recorded in artifacts."""
        if np.any(self.weights < -tol):
            raise InvariantError("negative weight survived construction")
        for key, positions in _CLASS_POSITIONS.items():
            total = combos_for_class(key)
            value = float(self.weights[positions].sum())
            if value > total + tol:
                raise InvariantError(f"{key} holds {value} combos but only {total} exist")


def from_chart(artifact: Mapping[str, Any]) -> Range:
    """``data/gen/ranges/*.json`` -> Range. Generated charts carry combo-weighted entries plus the
    ``cell_combos`` table so this function never has to trust a hand-typed count.

    A chart cell holds a **frequency relative to that cell's own combos** -- ``0.333333`` in ``84o``
    means a third of its twelve combos, four of them -- and :class:`Range` stores one probability per
    *combo*. The two are the same number, which is the trap: multiplying a cell's frequency by its
    combo count produces a per-combo weight of up to twelve, which is not a probability and which
    ``Range`` refuses. ``combos()`` sums the vector afterwards, so the combo count arrives by itself:
    ``12 x 0.333333 = 3.999996`` is the artifact's own arithmetic, not something to pre-apply here.
    """
    weights = np.zeros(1326, dtype=np.float64)
    orientation = artifact.get("orientation")
    if orientation != "akqjt98765432-desc-diagonal-pairs-upper-suited":
        raise InputError(f"unknown chart orientation {orientation!r} (see matrix13.py)")
    for key, frequency in artifact["weights"].items():
        if key not in _CLASS_POSITIONS:
            raise InputError(f"chart {artifact.get('id')} contains unknown class {key!r}")
        declared = artifact.get("cell_combos", {}).get(key)
        expected = combos_for_class(key)
        if declared is not None and declared != expected:
            raise InputError(
                f"chart {artifact.get('id')} declares {declared} combos for {key}, expected {expected}"
            )
        weights[_CLASS_POSITIONS[key]] = float(frequency)
    return Range(weights)


def to_chart_payload(rng: Range, *, digits: int = 6) -> dict[str, float]:
    """Class -> frequency, rounded for artifact writing. Rounding is centralised here so every
    generator formats numbers identically (ADR-0001 determinism).
    """
    return {key: round(value, digits) for key, value in rng.frequency_map().items() if value > 0.0}


def combo_positions(cards: Sequence[Card]) -> int:
    first, second = cards[0].index, cards[1].index
    position = _COMBO_POSITION.get((min(first, second), max(first, second)))
    if position is None:
        raise InputError(f"{cards[0]}{cards[1]} is not a valid combo")
    return position
