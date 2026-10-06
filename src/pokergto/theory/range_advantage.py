"""Range advantage and nut advantage: two different quantities, one lesson each.

The distinction is the hinge of chapter 03, and it is easy to state badly. Both numbers describe whose
hands are good on a board; they answer different questions, and the strategies they license are
different:

* **equity (range) advantage** -- whose distribution wins more often against the other's. Drives who
  can bet *often*.
* **nut advantage** -- whose distribution contains the hands that are best *when the money goes in*.
  Drives who can bet *big*, because a large bet is a threat to be raised.

A board can give one player the equity advantage and the other the nut advantage, which is why "I think
I'm ahead on this flop" is not yet a strategy statement. The classic case is a low-connected flop where
the caller's range has more two-pair and straight combos while the preflop raiser's range has more
overcards: the raiser may still hold the equity edge while the caller owns the nut-heavy tail.

Both are computed here from combos and the evaluator, so neither is a matter of opinion -- and both are
stated with their limits: nut advantage is exact on a completed board and, on earlier streets, is
computed against the best hand *currently* achievable rather than the best hand after all runouts.
That understates it, and the docstring of :func:`nut_advantage` says by how much the definition differs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ..cards import Card
from ..equity import range_equity
from ..errors import InputError
from ..evaluator import best_score
from ..ranges import Range

__all__ = ["Advantage", "advantage", "equity_advantage", "is_capped", "nut_advantage"]


@dataclass(frozen=True, slots=True)
class Advantage:
    """The three facts a sizing decision rests on, computed for one board."""

    board: tuple[str, ...]
    hero_equity: float
    villain_equity: float
    hero_nut_share: float
    villain_nut_share: float
    hero_combos: float
    villain_combos: float

    @property
    def equity_edge(self) -> float:
        return self.hero_equity - self.villain_equity

    @property
    def nut_edge(self) -> float:
        return self.hero_nut_share - self.villain_nut_share

    @property
    def who_can_bet_often(self) -> str:
        return "hero" if self.equity_edge > 0 else ("villain" if self.equity_edge < 0 else "either")

    @property
    def who_can_bet_big(self) -> str:
        """The nut-advantaged side, and only when the edges genuinely disagree.

        Reported separately from :attr:`who_can_bet_often` precisely because collapsing them into one
        verdict is the error this module exists to make visible.
        """
        if abs(self.nut_edge) < 1e-9:
            return "either"
        return "hero" if self.nut_edge > 0 else "villain"


def equity_advantage(
    hero: Range,
    villain: Range,
    board: tuple[Card, ...],
    *,
    mode: Literal["exact", "mc", "auto"] = "auto",
    iterations: int = 20_000,
    seed: int = 0,
) -> tuple[float, float]:
    """All-in equity of each distribution on this board. ``mode`` follows ``range_equity``."""
    if hero.is_empty() or villain.is_empty():
        raise InputError("an empty range has no advantage to measure")
    result = range_equity(hero, villain, board, mode=mode, iterations=iterations, seed=seed)
    return result.equity, 1.0 - result.equity


def nut_advantage(
    hero: Range,
    villain: Range,
    board: tuple[Card, ...],
    *,
    near_nuts: int = 0,
) -> tuple[float, float]:
    """Share of each range's combos that sit at the top of the hand-strength ordering on this board.

    Definition used: the best score any combo of either range achieves on ``board`` is the reference;
    a combo counts as nut-tier when it is within ``near_nuts`` steps below it, where a step is one rank
    in the evaluator's total order. With ``near_nuts=0`` this is the literal nuts.

    On an incomplete board the reference is the best hand *currently* reachable, not the best hand
    after every runout, so the shares are upper-biased for the player who is already holding a made
    hand and lower-biased for the one drawing. That difference is exactly what lesson 03-03 is about,
    and the artifact records it as an assumption rather than passing the number off as exact.
    """
    if not 3 <= len(board) <= 5:
        raise InputError("board must be 3 to 5 cards")

    def scores(rng: Range) -> list[tuple[int, float]]:
        return [
            (best_score((first, second), board), weight)
            for first, second, weight in rng
            if weight > 0
        ]

    hero_scores, villain_scores = scores(hero), scores(villain)
    if not hero_scores or not villain_scores:
        raise InputError("both ranges need combos")
    top = max(score for score, _weight in hero_scores + villain_scores)
    cutoff = top - near_nuts

    def share(pairs: list[tuple[int, float]]) -> float:
        total = sum(weight for _score, weight in pairs)
        hits = sum(weight for score, weight in pairs if score >= cutoff)
        return hits / total if total else 0.0

    return share(hero_scores), share(villain_scores)


def is_capped(rng: Range, board: tuple[Card, ...], *, tolerance: int = 2) -> bool:
    """Whether a range's best possible holding sits clearly below the reachable ceiling.

    A capped range cannot hold the nuts, which removes the threat that licenses big bets and raises.
    That is why "your range is capped here" is a *sizing* conclusion and not a hand-strength one, and
    why chapter 03 leads into chapter 04.
    """
    if not 3 <= len(board) <= 5:
        raise InputError("board must be 3 to 5 cards")
    pairs = [
        (best_score((first, second), board), weight) for first, second, weight in rng if weight > 0
    ]
    if not pairs:
        raise InputError("range has no combos")
    # The ceiling is the best hand any two cards could make on this board, taken over all 1326 combos
    # rather than only the ones this range holds: capped means "not in *my* range", not "not
    # achievable in principle".
    from ..cards import ALL_COMBOS
    from ..cards import Card as _Card

    ceiling = max(
        best_score((_Card.from_index(a), _Card.from_index(b)), board) for a, b in ALL_COMBOS
    )
    return max(score for score, _weight in pairs) < ceiling - tolerance


def advantage(
    hero: Range,
    villain: Range,
    board: tuple[Card, ...],
    *,
    mode: Literal["exact", "mc", "auto"] = "auto",
    iterations: int = 20_000,
    seed: int = 0,
    near_nuts: int = 0,
) -> Advantage:
    """One call, all three numbers, for a lesson's worked example."""
    hero_equity, villain_equity = equity_advantage(
        hero,
        villain,
        board,
        mode=mode,
        iterations=iterations,
        seed=seed,
    )
    hero_nut, villain_nut = nut_advantage(hero, villain, board, near_nuts=near_nuts)
    return Advantage(
        board=tuple(card.code for card in board),
        hero_equity=hero_equity,
        villain_equity=villain_equity,
        hero_nut_share=hero_nut,
        villain_nut_share=villain_nut,
        hero_combos=hero.total_combos(),
        villain_combos=villain.total_combos(),
    )
