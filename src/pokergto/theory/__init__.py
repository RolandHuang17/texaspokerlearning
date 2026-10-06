"""The derivable principles, one module per idea the curriculum cites.

Every function here answers a question a lesson asks in prose, and each lesson's ``derivation_ref``
points back at the symbol that produced its numbers. That is the mechanism behind the repository's
central claim: nothing in the docs is asserted, because anything assertable can be recomputed.

The modules are deliberately *not* a strategy engine. There is no function here that says what to do
with a hand. They compute the quantities that make a decision checkable -- whose range is ahead, what
a board favours, which bet sizes can be justified, whether a frequency pair is balanced -- and then
the learner, or a solver, decides. A repository that shipped "the answer" without the arithmetic would
be a worse version of the paid tools it replaces.
"""

from __future__ import annotations

from .frequencies import (
    balance_bluff_and_value,
    bluff_indifference_gap,
    defense_indifference_gap,
    is_frequency_balanced,
    value_bluff_split,
)
from .multiway import (
    bluff_value_ratio_multiway,
    continuation_fold_requirement,
    joint_defense,
    who_can_win,
)
from .polarization import classify_betting_range, is_polarised, polarised_vs_merged_ev
from .protection import protection_gain, realization_penalty
from .range_advantage import Advantage, advantage, nut_advantage, range_advantage
from .sizing import legal_sizes, sizing_rationale
from .blockers import blocker_report, removal_weight_delta

__all__ = [
    "Advantage",
    "balance_bluff_and_value",
    "blocker_report",
    "bluff_indifference_gap",
    "bluff_value_ratio_multiway",
    "classify_betting_range",
    "continuation_fold_requirement",
    "defense_indifference_gap",
    "is_frequency_balanced",
    "is_polarised",
    "joint_defense",
    "legal_sizes",
    "nut_advantage",
    "polarised_vs_merged_ev",
    "protection_gain",
    "range_advantage",
    "realization_penalty",
    "removal_weight_delta",
    "sizing_rationale",
    "value_bluff_split",
    "who_can_win",
]
