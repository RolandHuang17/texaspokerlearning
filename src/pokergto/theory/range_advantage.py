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

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from ..cards import ALL_COMBOS, Card
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
    a combo counts as nut-tier when it is within ``near_nuts`` below it, measured in units of the
    evaluator's packed integer score. With ``near_nuts=0`` this is the literal nuts.

    The unit matters and is not a hand type. Adjacent distinct strengths on a three-card board can sit
    16 integers apart, so ``near_nuts=1,2,3`` all return the ``near_nuts=0`` share; a "small" tolerance
    here is not a small margin, and "second-nuts" cannot be defined with this parameter.

    A range handed to this function must already exclude the board. It cannot detect the collision
    itself, because "the best hand in range" and "how many combos are in range" are both computed off
    the combo list it receives -- so ``AKs`` written on ``AhKsQh`` would be counted four ways when only
    two of those hands are dealt, and the share would be wrong in a direction that never looks wrong.
    :func:`pokergto.notation.parse` takes an ``exclude`` parameter for exactly this; callers are
    expected to use it, and ``table.03-01`` / ``table.03-02`` do.

    On an incomplete board the reference is the best hand *currently* reachable, not the best hand
    after every runout, so the shares are upper-biased for the player who is already holding a made
    hand and lower-biased for the one drawing. That difference is exactly what lesson 03-03 is about,
    and the artifact records it as an assumption rather than passing the number off as exact.
    """
    if not 3 <= len(board) <= 5:
        raise InputError("board must be 3 to 5 cards")
    _assert_board_excluded(hero, villain, board=board, where="nut_advantage")

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


def _assert_board_excluded(
    *ranges: Range, board: Sequence[Card], where: str
) -> None:
    """Refuse a range that still contains a board card.

    Two columns of an advantage number can be computed against different denominators without this:
    :func:`pokergto.equity.range_equity` masks colliding combos internally, while a nut share divides by
    the combos it was handed. The result is a table where equity is honest and the share beside it is
    inflated -- by a factor that never looks like an error. Failing at the boundary is the only fix that
    does not depend on the caller remembering, and one already forgot.
    """
    dead = {card.index for card in board}
    for position, rng in enumerate(ranges):
        for first, second, weight in rng:
            if weight > 0 and (first.index in dead or second.index in dead):
                raise InputError(
                    f"{where}: range {position} still holds {first.code}{second.code}, a card on the "
                    f"board. Narrow it with Range.with_removed(*board) or notation.parse(spec, "
                    "exclude=board); nut shares and combo counts divide by what the range contains."
                )


def is_capped(rng: Range, board: tuple[Card, ...], *, tolerance: int = 0) -> bool:
    """Whether the range holds the best hand this board can deal at all.

    ``tolerance`` is in units of the evaluator's packed integer score, the same unit
    :func:`nut_advantage`'s ``near_nuts`` uses, so the default says what it means: capped means the
    nuts are absent. Adjacent distinct hand strengths are tens or thousands of integers apart, which
    means a positive tolerance answers a much softer question than it sounds like -- "is it a clear
    margin below the ceiling" has to be asked with a number measured against the gaps, not with 1 or 2.

    The ceiling is the best hand any two cards could make here, taken over all 1326 combos rather than
    only the ones this range holds: capped means "not in *my* range", not "not achievable in principle".
    """
    if not 3 <= len(board) <= 5:
        raise InputError("board must be 3 to 5 cards")
    pairs = [
        (best_score((first, second), board), weight) for first, second, weight in rng if weight > 0
    ]
    if not pairs:
        raise InputError("range has no combos")
    _assert_board_excluded(rng, board=board, where="is_capped")

    ceiling = max(
        best_score((Card.from_index(a), Card.from_index(b)), board) for a, b in ALL_COMBOS
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
    # The equity path narrows itself -- ``range_equity`` masks combos colliding with the board -- but
    # the nut share divides by whatever it is handed, so the same narrowing has to happen here or the
    # two columns of one Advantage answer two different questions.
    hero_clean = hero.with_removed(*board)
    villain_clean = villain.with_removed(*board)
    hero_nut, villain_nut = nut_advantage(hero_clean, villain_clean, board, near_nuts=near_nuts)
    return Advantage(
        board=tuple(card.code for card in board),
        hero_equity=hero_equity,
        villain_equity=villain_equity,
        hero_nut_share=hero_nut,
        villain_nut_share=villain_nut,
        hero_combos=hero_clean.total_combos(),
        villain_combos=villain_clean.total_combos(),
    )
