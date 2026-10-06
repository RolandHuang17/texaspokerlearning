"""The derivable principles the curriculum cites, one module per idea.

Every function here answers a question a lesson asks in prose, and a lesson's ``derivation_ref``
points at the symbol that produced its numbers. That is the mechanism behind the repository's
central claim: nothing in ``docs/`` is asserted, because anything assertable can be recomputed.

Three modules ship. They are the ones whose quantities can be computed *exactly* from the cards and
the algebra -- combos, the evaluator, pot odds:

* :mod:`pokergto.theory.frequencies` -- the two indifference conditions a mixed strategy must meet,
  and the signed gap when it does not. This is what
  :mod:`pokergto.solver.proofs` requires the solver to drive to zero.
* :mod:`pokergto.theory.multiway` -- the ``1/N`` defense law, plus the assumption-free counting that
  explains why bluffing collapses as players are added.
* :mod:`pokergto.theory.range_advantage` -- equity advantage and nut advantage as two separate
  numbers, because collapsing them is how "I'm ahead, so I bet big" goes wrong.

Deliberately absent, and that absence is a decision rather than an omission: bet-size *governance*,
polarisation tests, blocker EV and protection-versus-value. Each needs a solver-style answer about a
range's future behaviour -- what the opponent folds, which tail the next card favours -- and this
repository has no validated model of that for full hold'em (see ``adr/0002``: an unverifiable model
would teach wrong things with the authority of code). Those ideas are taught in chapters 03 and 04 by
derivation from the quantities that *are* computable here, and any number in those chapters that comes
from judgement rather than arithmetic carries a ``reference`` provenance and an UNVERIFIED badge.
"""

from __future__ import annotations

from .frequencies import (
    BalanceReport,
    balance_bluff_and_value,
    bluff_indifference_gap,
    defense_indifference_gap,
    is_frequency_balanced,
    value_bluff_split,
)
from .multiway import (
    MultiwayReport,
    bluff_value_ratio,
    continuation_fold_requirement,
    describe,
    joint_defense,
    per_player_defense,
    value_and_air_combos,
    who_can_win,
)
from .range_advantage import Advantage, advantage, equity_advantage, is_capped, nut_advantage

__all__ = [
    "Advantage",
    "BalanceReport",
    "MultiwayReport",
    "advantage",
    "balance_bluff_and_value",
    "bluff_indifference_gap",
    "bluff_value_ratio",
    "continuation_fold_requirement",
    "defense_indifference_gap",
    "describe",
    "equity_advantage",
    "is_capped",
    "is_frequency_balanced",
    "joint_defense",
    "nut_advantage",
    "per_player_defense",
    "value_and_air_combos",
    "value_bluff_split",
    "who_can_win",
]
