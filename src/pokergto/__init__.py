"""pokergto — the engine behind a bilingual, derivable GTO curriculum.

The rule that keeps this package honest (ADR-0002): if a lesson states a number, that number is
produced here. Nothing in ``docs/`` or ``trainer/`` does arithmetic of its own.
"""

from __future__ import annotations

from .cards import (
    ALL_COMBOS,
    GRID_RANKS,
    HAND_CLASSES_169,
    Card,
    Rank,
    Suit,
    class_key,
    combos_for_class,
    parse_cards,
    standard_deck,
)
from .equity import EquityResult, draw_probability, hand_equity, range_equity, vs_random
from .errors import (
    BudgetExceeded,
    InputError,
    InvariantError,
    NotationError,
    PokerGtoError,
    ProofGateError,
    ProvenanceError,
    SchemaDriftError,
)
from .evaluator import Category, best_score, describe, evaluate5, evaluate7, showdown
from .matrix13 import ORIENTATION, Grid13, cell_for_class, class_for_cell
from .notation import expand, parse, to_spec
from .ranges import Range, from_chart
from .spr import (
    all_in_equity_needed,
    commit_threshold_equity,
    implied_odds_break_even_equity,
    max_profitable_commit_fraction,
    spr,
)

__version__ = "0.1.0"

__all__ = [
    "ALL_COMBOS",
    "BudgetExceeded",
    "Card",
    "Category",
    "EquityResult",
    "GRID_RANKS",
    "Grid13",
    "HAND_CLASSES_169",
    "InputError",
    "InvariantError",
    "NotationError",
    "ORIENTATION",
    "PokerGtoError",
    "ProofGateError",
    "ProvenanceError",
    "Range",
    "Rank",
    "SchemaDriftError",
    "Suit",
    "__version__",
    "all_in_equity_needed",
    "best_score",
    "cell_for_class",
    "class_for_cell",
    "class_key",
    "combos_for_class",
    "commit_threshold_equity",
    "describe",
    "draw_probability",
    "evaluate5",
    "evaluate7",
    "expand",
    "from_chart",
    "hand_equity",
    "implied_odds_break_even_equity",
    "max_profitable_commit_fraction",
    "parse",
    "parse_cards",
    "range_equity",
    "showdown",
    "spr",
    "standard_deck",
    "to_spec",
    "vs_random",
]
