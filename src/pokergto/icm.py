"""Independent Chip Model: turning chips into money, which is the whole point of a tournament.

Chip EV is the wrong objective function everywhere except cash games. ICM fixes it by pricing a
chip stack as the expected share of the prize pool it buys, under the assumption that every remaining
player is equally skilled and finishes first with probability proportional to chips. That assumption
is the model, not reality: it is why ICM is *conservative* about folding and *aggressive* about
shoving relative to a skilled-player model, and every lesson that uses ICM says so.

The recursion is the standard one, computed exactly over subsets rather than simulated:

``EV[j | R, k] = sum_{i in R} (s_i / S_R) * ( payout[k] if j == i else 0  +  EV[j | R - i, k+1] )``

with the convention that when one player remains they collect the rest of the unpaid prizes.
Complexity is ``O(n * 2^n)``, so nine handed final tables are instant and a fifty-player bubble is
not what this module is for (that is an independent-chip approximation, below).

``data/gen/matrices`` records push/fold ranges computed with and without ICM, so a lesson can show
the *same hand* flipping from a shove to a fold purely because of the payout structure. That is the
most persuasive arithmetic in tournament poker.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache
from typing import Sequence

from .errors import InputError


@dataclass(frozen=True, slots=True)
class IcmResult:
    """Per-player expected prize money, plus the diagnostics a lesson needs to make the point."""

    chips: tuple[int, ...]
    payouts: tuple[float, ...]
    expected_value: tuple[float, ...]
    chip_share: tuple[float, ...]
    prize_pool: float

    @property
    def icm_gap(self) -> tuple[float, ...]:
        """``expected_value / prize_pool - chip_share``. Negative for short stacks and positive for
        big ones: this *is* the bubble, expressed as a number. Chapter 12-04 builds from it."""
        if self.prize_pool <= 0:
            return tuple(0.0 for _ in self.expected_value)
        return tuple(
            value / self.prize_pool - share
            for value, share in zip(self.expected_value, self.chip_share, strict=True)
        )


def _validate(chips: Sequence[int], payouts: Sequence[float]) -> tuple[tuple[int, ...], tuple[float, ...]]:
    stack = tuple(int(c) for c in chips)
    money = tuple(float(p) for p in payouts)
    if len(stack) < 2:
        raise InputError("ICM needs at least two players")
    if any(c <= 0 for c in stack):
        raise InputError("ICM cannot price a zero stack; eliminate that player first")
    if len(money) > len(stack):
        raise InputError("more prizes than players")
    if any(p < 0 for p in money):
        raise InputError("negative prizes are not modelled here")
    if list(money) != sorted(money, reverse=True):
        raise InputError("payouts must be listed in finishing order, highest first")
    return stack, money


def icm_expected_value(chips: Sequence[int], payouts: Sequence[float]) -> tuple[float, ...]:
    """Exact ICM expected prize money for each player, in the order given."""
    stack, money = _validate(chips, payouts)
    n = len(stack)
    # Pad the prize list with zeros so the recursion has one shape to handle.
    prizes = money + (0.0,) * (n - len(money))

    @lru_cache(maxsize=None)
    def solve(remaining: tuple[int, ...], prize_index: int) -> tuple[float, ...]:
        if not remaining:
            return tuple(0.0 for _ in range(n))
        if len(remaining) == 1:
            index = remaining[0]
            outcome = [0.0] * n
            outcome[index] = sum(prizes[prize_index:])
            return tuple(outcome)
        total = sum(stack[i] for i in remaining)
        outcome = [0.0] * n
        for i in remaining:
            probability = stack[i] / total
            rest = tuple(j for j in remaining if j != i)
            following = solve(rest, prize_index + 1)
            for j in remaining:
                outcome[j] += probability * (
                    (prizes[prize_index] if j == i else 0.0) + following[j]
                )
        return tuple(outcome)

    result = solve(tuple(range(n)), 0)
    solve.cache_clear()
    return result


def icm(chips: Sequence[int], payouts: Sequence[float]) -> IcmResult:
    stack, money = _validate(chips, payouts)
    total = sum(stack)
    values = icm_expected_value(stack, money)
    return IcmResult(
        chips=stack,
        payouts=money,
        expected_value=values,
        chip_share=tuple(c / total for c in stack),
        prize_pool=float(sum(money)),
    )


def icm_equity(chips: Sequence[int], payouts: Sequence[float], index: int) -> float:
    """One player's expected share of the prize pool. The quantity a call or fold is compared
    against, and the reason "I have 40% of chips but 32% of money" is a tournament lesson."""
    result = icm(chips, payouts)
    if result.prize_pool <= 0:
        raise InputError("an empty prize pool has no equity to compute")
    return result.expected_value[index] / result.prize_pool


def _padded_prizes(payouts: Sequence[float], n: int) -> tuple[float, ...]:
    money = tuple(float(p) for p in payouts)
    return money + (0.0,) * (n - len(money))


def _value_of_state(
    chips: Sequence[int], payouts: Sequence[float], bust_order: Sequence[int], index: int
) -> float:
    """ICM value of one player after a set of eliminations.

    Convention, stated because it changes the number: eliminated players take the **lowest unpaid
    prizes in bust order**, and the survivors split the top prizes. With no bust-outs this is plain
    ICM; with one it is the difference between "busted for the min cash" and "busted for nothing",
    which is exactly the thing bubble theory is about.
    """
    stack = [int(c) for c in chips]
    prizes = _padded_prizes(payouts, len(stack))
    eliminated = [i for i in bust_order if stack[i] == 0]
    for position, player in enumerate(eliminated):
        if player == index:
            # First bust takes the last paid place, second-last bust the place before it, and so on.
            return prizes[len(stack) - 1 - position]
    alive = [i for i, chips_in_state in enumerate(stack) if chips_in_state > 0]
    if not alive:
        return 0.0
    survivor_prizes = prizes[: len(alive)]
    if not any(p > 0 for p in survivor_prizes):
        return 0.0
    values = icm_expected_value([stack[i] for i in alive], survivor_prizes)
    return values[alive.index(index)]


def fold_or_shove_icm_cost(
    chips: Sequence[int],
    payouts: Sequence[float],
    index: int,
    *,
    equity: float,
) -> dict[str, float]:
    """ICM value of folding versus shoving an entire stack, given hand equity against the caller.

    Models the two terminal outcomes of an all-in against the largest other stack: hero doubles and
    the caller busts, or hero busts. Everything else is assumed to fold. That is the standard
    two-bubble-bubble simplification and it is **not** a general ICM fold/shove solver — multiway
    all-ins need the enumeration in ``solver/pushfold.py``, which is where chapter 12 goes.

    Returns the delta rather than a verdict, so the decision stays in the lesson where it belongs.
    """
    stack = [int(c) for c in chips]
    if not 0.0 <= equity <= 1.0:
        raise InputError("equity must be within [0,1]")
    if index not in range(len(stack)) or stack[index] <= 0:
        raise InputError("hero must have chips")
    opponents = [i for i in range(len(stack)) if i != index and stack[i] > 0]
    if not opponents:
        raise InputError("nobody left to call")
    caller = max(opponents, key=lambda i: stack[i])

    fold_value = _value_of_state(stack, payouts, [], index)

    win_state = list(stack)
    win_state[index] += win_state[caller]
    win_state[caller] = 0
    win_value = _value_of_state(win_state, payouts, [caller], index)

    lose_state = list(stack)
    if lose_state[caller] >= lose_state[index]:
        # Caller covers the shove; hero is eliminated and the caller keeps the difference.
        lose_state[caller] += lose_state[index]
        lose_state[index] = 0
        lose_value = _value_of_state(lose_state, payouts, [index], index)
    else:
        # Hero out-runs the caller's stack: caller busts first, then hero is still alive but the
        # side pot is not modelled here, so this path is refused rather than approximated.
        raise InputError(
            "hero is bigger than the caller; side-pot outcomes are out of scope for this model. "
            "Use solver/pushfold.py for the full enumeration."
        )

    shove_value = equity * win_value + (1 - equity) * lose_value
    return {
        "fold_value": fold_value,
        "shove_value": shove_value,
        "delta": shove_value - fold_value,
        "caller_index": float(caller),
    }


def bubble_factor(chip_share: float, money_share: float) -> float:
    """How much *less* a chip stack is worth in money terms. ``money_share / chip_share``; below 1 for
    short stacks, above 1 for big ones, and the whole of bubble-play psychology in one ratio."""
    if chip_share <= 0:
        raise InputError("chip share must be positive")
    return money_share / chip_share


def independent_chip_share(chips: Sequence[int], index: int) -> float:
    """The chip-proportion baseline ICM is measured against. Exposed as a function so a lesson can
    plot the two curves against each other instead of describing the difference in words."""
    total = sum(int(c) for c in chips)
    if total <= 0:
        raise InputError("no chips in play")
    return int(chips[index]) / total


def payout_structure_from_prize_table(rows: Sequence[tuple[int, float]]) -> tuple[float, ...]:
    """Flatten ``(places, amount)`` pairs into the ordered prize list ICM consumes.

    ``[(1, 5000.0), (2, 3000.0)]`` -> ``(5000.0, 3000.0)``. Repeated places expand, because a table
    saying "places 1-2 pay 1000" is two prizes, not one.
    """
    prizes: list[float] = []
    for places, amount in rows:
        if places <= 0:
            raise InputError(f"invalid place count {places}")
        prizes.extend([float(amount)] * places)
    if prizes != sorted(prizes, reverse=True):
        raise InputError("expanded prize list is not monotonically decreasing")
    return tuple(prizes)


def effective_stack_bb(chips: int, big_blind: int) -> float:
    """Chips to big blinds, because every threshold in this curriculum is stated in bb."""
    if big_blind <= 0:
        raise InputError("big blind must be positive")
    return chips / big_blind


def approximate_icm_by_sampling(
    chips: Sequence[int], payouts: Sequence[float], *, iterations: int = 200_000, seed: int = 0
) -> tuple[float, ...]:
    """A Monte Carlo ICM, for the cases where exact subset enumeration is too many players.

    Included to make the *cost* of exactness visible: it reproduces the exact answer to within a
    reported error, and the lesson is that when exact is affordable, exact is what we ship.
    """
    import random

    stack, money = _validate(chips, payouts)
    total = sum(stack)
    weights = [c / total for c in stack]
    prizes = list(money) + [0.0] * (len(stack) - len(money))
    rng = random.Random(seed)
    tally = [0.0] * len(stack)
    for _ in range(iterations):
        remaining = list(range(len(stack)))
        remaining_chips = list(stack)
        for prize in prizes:
            if not remaining:
                break
            pool = sum(remaining_chips)
            roll = rng.random() * pool
            cumulative = 0.0
            winner = remaining[-1]
            for position, player in enumerate(remaining):
                cumulative += remaining_chips[position] / pool
                if roll <= cumulative:
                    winner = player
                    break
            tally[winner] += prize
            index = remaining.index(winner)
            remaining.pop(index)
            remaining_chips.pop(index)
    del weights
    return tuple(value / iterations for value in tally)
