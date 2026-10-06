"""The 13x13 grid: how every range chart in this repository is drawn and indexed.

Orientation is pinned once, repo-wide, and encoded as a literal string that travels with every
generated chart artifact:

* rows and columns run ``A, K, Q, J, T, 9, 8, 7, 6, 5, 4, 3, 2`` (descending);
* the diagonal is pocket pairs;
* the **upper** triangle is suited, the **lower** triangle is offsuit.

A cell holds a **frequency in [0, 1]**, not a combo count. Combo counts always come from
:data:`pokergto.cards` via :mod:`pokergto.ranges`, so exactly one place in the codebase can be wrong
about how many ``AKo`` combos exist.

The interesting invariant is not symmetry, it is *mirror equivalence*: the two triangles are the
same rank structure, differing only in suitedness. So mirroring a pure-suited chart across the
diagonal must produce the identical chart with ``s`` replaced by ``o``. ``tests/test_matrix13.py``
pins that, because an orientation bug in a chart is invisible to the eye and catastrophic downstream.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Final

import numpy as np

from .cards import GRID_RANKS
from .errors import InputError

#: The single legal orientation. Baked into data/schema/range_chart.schema.json as a const.
ORIENTATION: Final[str] = "akqjt98765432-desc-diagonal-pairs-upper-suited"

AXIS: Final[tuple[str, ...]] = tuple(rank.char for rank in GRID_RANKS)

#: Combo count of each cell under the pinned orientation.
CELL_COMBOS: Final[np.ndarray] = np.array(
    [[6 if i == j else (4 if i < j else 12) for j in range(13)] for i in range(13)],
    dtype=np.int64,
)


def class_for_cell(row: int, col: int) -> str:
    """Grid position -> 169 class key."""
    if not (0 <= row < 13 and 0 <= col < 13):
        raise InputError(f"cell ({row},{col}) outside the 13x13 grid")
    high, low = AXIS[row], AXIS[col]
    if row == col:
        return f"{high}{low}"
    if row < col:
        return f"{high}{low}s"
    return f"{low}{high}o"


def cell_for_class(key: str) -> tuple[int, int]:
    """169 class key -> grid position, honouring the pinned orientation."""
    if key not in _CLASS_TO_CELL:
        raise InputError(f"unknown hand class {key!r}")
    return _CLASS_TO_CELL[key]


_CLASS_TO_CELL: dict[str, tuple[int, int]] = {}
for _row in range(13):
    for _col in range(13):
        _CLASS_TO_CELL[class_for_cell(_row, _col)] = (_row, _col)

if len(_CLASS_TO_CELL) != 169:  # pragma: no cover
    raise InputError(f"grid indexing produced {len(_CLASS_TO_CELL)} classes, expected 169")


class Grid13:
    """A 13x13 frequency grid. Values are per-class frequencies, never combo counts."""

    __slots__ = ("values",)

    def __init__(self, values: np.ndarray | None = None) -> None:
        if values is None:
            values = np.zeros((13, 13), dtype=np.float64)
        if values.shape != (13, 13):
            raise InputError(f"grid must be 13x13, got {values.shape}")
        self.values = values.astype(np.float64, copy=False)

    # --- constructors ---------------------------------------------------------------

    @classmethod
    def zeros(cls) -> Grid13:
        return cls()

    @classmethod
    def full(cls) -> Grid13:
        return cls(np.ones((13, 13), dtype=np.float64))

    @classmethod
    def from_range(cls, rng: Any) -> Grid13:
        grid = cls()
        for key, frequency in rng.frequency_map().items():
            row, col = cell_for_class(key)
            grid.values[row, col] = frequency
        return grid

    @classmethod
    def from_chart(cls, artifact: Mapping[str, Any]) -> Grid13:
        if artifact.get("orientation") != ORIENTATION:
            raise InputError(
                f"chart {artifact.get('id')!r} has orientation {artifact.get('orientation')!r}, "
                f"this repository only reads {ORIENTATION!r}"
            )
        grid = cls()
        for key, frequency in artifact["weights"].items():
            row, col = cell_for_class(key)
            grid.values[row, col] = float(frequency)
        return grid

    @classmethod
    def from_numpy(cls, array: np.ndarray) -> Grid13:
        return cls(array)

    # --- accessors --------------------------------------------------------------------

    def cell(self, key: str) -> float:
        row, col = cell_for_class(key)
        return float(self.values[row, col])

    def set_cell(self, key: str, value: float) -> None:
        if not 0.0 <= value <= 1.0:
            raise InputError(f"frequency must be within [0,1], got {value}")
        row, col = cell_for_class(key)
        self.values[row, col] = value

    def to_numpy(self) -> np.ndarray:
        return self.values.copy()

    def combos(self) -> float:
        """Weighted combo total. A fully-included grid is exactly 1326."""
        return float(np.sum(self.values * CELL_COMBOS))

    def range_percentage(self) -> float:
        return 100.0 * self.combos() / 1326.0

    def mirror(self) -> Grid13:
        """Reflect across the diagonal: suited becomes offsuit and vice versa, ranks unchanged."""
        return Grid13(self.values.T.copy())

    def classes(self) -> dict[str, float]:
        out: dict[str, float] = {}
        for row in range(13):
            for col in range(13):
                value = float(self.values[row, col])
                if value > 0.0:
                    out[class_for_cell(row, col)] = value
        return out

    def to_chart(self, *, digits: int = 6) -> dict[str, Any]:
        """The payload half of a ``range_chart`` artifact, with combo counts taken from the module
        constants rather than trusted from a caller.
        """
        return {
            "orientation": ORIENTATION,
            "rows": list(AXIS),
            "columns": list(AXIS),
            "cell_combos": {
                class_for_cell(i, j): int(CELL_COMBOS[i, j]) for i in range(13) for j in range(13)
            },
            "weights": {key: round(value, digits) for key, value in sorted(self.classes().items())},
        }

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Grid13):
            return NotImplemented
        return bool(np.allclose(self.values, other.values))

    # Explicitly unhashable: the grid wraps a mutable numpy array, so Python's default
    # "eq without hash" suppression is the correct behaviour and stating it here says so.
    __hash__ = None  # type: ignore[assignment]

    def __repr__(self) -> str:
        return f"Grid13(combos={self.combos():.3f}, classes={len(self.classes())})"
