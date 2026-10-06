"""Variance, risk of ruin and bankroll: why a correct play can still feel terrible.

"Play by feel" fails at the results end as much as the decision end: a learner who cannot separate
*decision quality* from *outcome* will abandon a good line after a downswing. The quantities here are
what make that separation numerical.

Model assumptions, stated because they are load-bearing and frequently violated:

* hands are independent and identically distributed;
* per-hand results are approximately normal with standard deviation ``std``;
* your win rate does not change with your bankroll (it does in real life — game selection, table
  choice and tilt all break the model, which is why the numbers below are floors, not ceilings).

Risk of ruin for such a walk is the classical
``exp(-2 * mean * bankroll / variance_per_hand)``; the Kelly fraction is ``mean / variance``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True, slots=True)
class HandStats:
    """Per-hand mean and standard deviation, in big blinds."""

    mean_bb: float
    std_bb: float
    samples: int = 0

    @classmethod
    def from_results(cls, results_bb: Sequence[float]) -> HandStats:
        if len(results_bb) < 2:
            raise ValueError("need at least two hands to estimate a standard deviation")
        mean = sum(results_bb) / len(results_bb)
        variance = sum((r - mean) ** 2 for r in results_bb) / (len(results_bb) - 1)
        return cls(mean, math.sqrt(variance), len(results_bb))

    @property
    def variance_bb(self) -> float:
        return self.std_bb**2


def bb_per_100(stats: HandStats) -> float:
    return 100.0 * stats.mean_bb


def std_per_100(stats: HandStats) -> float:
    return 100.0 * stats.std_bb


def standard_error(stats: HandStats, hands: int) -> float:
    """Standard error of the *mean* after ``hands`` hands, in bb. A winrate reported without this is
    a story, not a measurement."""
    if hands <= 0:
        raise ValueError("hands must be positive")
    return stats.std_bb / math.sqrt(hands)


def confidence_interval_bb_per_100(stats: HandStats, hands: int, z: float = 1.959963984540054) -> tuple[float, float]:
    se = standard_error(stats, hands)
    centre = bb_per_100(stats)
    margin = z * se * 100.0
    return (centre - margin, centre + margin)


def probability_of_beating_a_field(stats: HandStats, hands: int, target_bb_per_100: float) -> float:
    """P(observed winrate >= target) under the model. ``1 - Phi((target - mean) / (100·se))``.

    This is the least dramatic way to say "you cannot tell yet", which is the most useful thing a
    variance module can tell a learner.
    """
    se = standard_error(stats, hands) * 100.0
    if se == 0:
        return 1.0 if bb_per_100(stats) >= target_bb_per_100 else 0.0
    return _normal_sf((target_bb_per_100 - bb_per_100(stats)) / se)


def _normal_sf(x: float) -> float:
    """1 - Phi(x), via the complementary error function so the tail does not lose precision."""
    return 0.5 * math.erfc(x / math.sqrt(2.0))


def risk_of_ruin(stats: HandStats, bankroll_bb: float) -> float:
    """Classical gambler's-ruin probability for a random walk with normal increments:
    ``exp(-2 * mean * bankroll / variance)``. Zero when there is no edge, because with no edge a
    walk of unbounded horizon is ruined with probability one.

    The lesson in the number itself: halving the ruin probability needs *doubling the bankroll*, not
    increasing it by a bit, because the relationship is exponential in the other direction.
    """
    if bankroll_bb <= 0:
        return 1.0
    if stats.mean_bb <= 0:
        return 1.0
    exponent = -2.0 * stats.mean_bb * bankroll_bb / stats.variance_bb
    return math.exp(exponent)


def required_bankroll_bb(stats: HandStats, max_ruin_probability: float) -> float:
    """Inverse of :func:`risk_of_ruin`: the roll that keeps ruin below ``p``."""
    if not 0 < max_ruin_probability < 1:
        raise ValueError("ruin probability must be strictly between 0 and 1")
    if stats.mean_bb <= 0:
        return math.inf
    return -math.log(max_ruin_probability) * stats.variance_bb / (2.0 * stats.mean_bb)


def kelly_fraction(stats: HandStats) -> float:
    """Continuous Kelly for a random walk: ``mean / variance``. Read it as "the fraction of the roll
    whose growth is maximal", and the reason a full-Kelly player accepts ruin probabilities that a
    quarter-Kelly player would not."""
    if stats.variance_bb == 0:
        return 0.0
    return stats.mean_bb / stats.variance_bb


def drawdown_sigma_bands(stats: HandStats, hands: int) -> dict[str, float]:
    """Typical size of a ``k``-sigma drawdown over a horizon, in bb.

    ``sigma sqrt(hands)`` is the *spread of the outcome*, not the expected maximum drawdown. The
    distinction is a chapter's worth of confusion, so it is named in the key rather than glossed.
    """
    sd = stats.std_bb * math.sqrt(hands)
    return {
        "outcome_spread_1_sigma": sd,
        "outcome_spread_2_sigma": 2 * sd,
        "outcome_spread_3_sigma": 3 * sd,
        "expected_drawdown_scale": stats.std_bb * math.sqrt(hands / (2 * math.pi)),
    }


def rake_adjustment(gross_bb_per_100: float, rake_pct_of_pot: float, avg_pot_bb: float) -> float:
    """Net winrate after rake, per 100 hands: ``gross - 100 * rake_pct * avg_pot``.

    Small-stakes reality check: at 2 NL the rake is a bigger opponent than any player at the table,
    and chapter 01-06 uses this to show why "GTO at 25 NL" can be net-negative while the identical
    line at 200 NL is not.
    """
    return gross_bb_per_100 - 100.0 * rake_pct_of_pot * avg_pot_bb


def hands_for_significance(stats: HandStats, effect_bb_per_100: float, z: float = 1.959963984540054) -> int:
    """Sample size needed to detect a difference of this size at the given confidence. Answers the
    question "how many hands before I am allowed to have an opinion", which is a frequency question
    a learner should be able to answer for themselves."""
    if effect_bb_per_100 == 0:
        raise ValueError("effect size must be non-zero")
    se_needed = abs(effect_bb_per_100) / (z * 100.0)
    return math.ceil((stats.std_bb / se_needed) ** 2)
