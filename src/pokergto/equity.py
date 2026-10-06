"""Equity: exact enumeration where it is affordable, Monte Carlo where it is not, and never a
silent switch between the two.

``EquityResult`` carries ``stderr`` as a first-class field. That is not decoration: a Monte Carlo
number without its error bar is a guess formatted like a fact, and lesson 01-04 exists to make
learners feel the difference. Every generated table containing an MC value records the seed and the
iteration count, so the number can be reproduced or refuted.

Cost is the other half of the design:

* **Exact** means enumerating every runout. Once only the board is known a flop has
  ``C(47,2) = 1081`` completions (``C(45,2) = 990`` if the two hole cards are also known, and 44 on
  the turn). The evaluation count is
  ``runouts x (hero_combos + villain_combos)``, so exact is cheap for a few combos and absurd for a
  real range. :func:`range_equity` raises :class:`~pokergto.errors.BudgetExceeded` with the number
  and the alternative rather than hanging or quietly degrading.
* **Monte Carlo** samples a *(combo pair, runout)* from the correct joint distribution in one shot,
  so cost is ``O(iterations)`` regardless of how wide the ranges are. Conflicting combos (both
  players holding the same physical card) are excluded from the sampling distribution, which is the
  part of this calculation most often got wrong.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import combinations
from typing import Literal, Sequence

import numpy as np

from .cards import ALL_COMBOS, Card, standard_deck
from .errors import BudgetExceeded, InputError
from .evaluator import best_score
from .ranges import Range

#: Evaluations ``mode="auto"`` will spend. Deliberately far below ``EXACT_EVAL_BUDGET``: preflop
#: exact equity is 1,712,304 runouts and takes about three minutes, which is a fine thing for a
#: learner to *choose* and a bad thing to happen by default.
AUTO_EXACT_BUDGET = 250_000

#: Evaluations allowed before exact enumeration refuses to run. Sized so exact tests stay inside the
#: <60s dev loop; tools/cost_probe.py is the solver-side equivalent.
EXACT_EVAL_BUDGET = 4_000_000

Board = tuple[Card, ...]
_Z95 = 1.959963984540054


@dataclass(frozen=True, slots=True)
class EquityResult:
    """Share-of-pot equity, decomposed. ``equity == wins + ties/2`` is asserted, not assumed:
    split pots are exactly where hand strength and equity part company."""

    equity: float
    wins: float
    ties: float
    losses: float
    exact: bool
    iterations: int
    seed: int | None = None
    stderr: float = 0.0

    def __post_init__(self) -> None:
        expected = self.wins + self.ties / 2.0
        if abs(expected - self.equity) > 1e-9:
            raise AssertionError(
                f"equity {self.equity} != wins + ties/2 = {expected}; the decomposition is broken"
            )

    @property
    def as_percent(self) -> float:
        return 100.0 * self.equity

    @property
    def error_bar_95(self) -> tuple[float, float]:
        """``equity ± 1.96·stderr``. For an exact result the interval is the point itself, and
        returning it that way is better than returning a misleading zero."""
        if self.exact:
            return (self.equity, self.equity)
        margin = _Z95 * self.stderr
        return (max(0.0, self.equity - margin), min(1.0, self.equity + margin))

    def __str__(self) -> str:
        mode = "exact" if self.exact else f"mc(n={self.iterations},seed={self.seed})"
        error = "" if self.exact else f" +/-{100 * _Z95 * self.stderr:.2f}%"
        return f"{100 * self.equity:.2f}% [W{100*self.wins:.1f}/T{100*self.ties:.1f}] ({mode}){error}"


def _remaining_cards(used: Sequence[Card]) -> list[Card]:
    taken = {c.index for c in used}
    return [c for c in standard_deck() if c.index not in taken]


def runout_boards(board: Board, *, known_hands: Sequence[Sequence[Card]] = ()) -> list[Board]:
    """Every completion of a 0..4 card board to five cards, given the hole cards in play.

    The number of completions sets the exact-mode cost: ``C(47,2)=1081`` for a flop when only the
    board is known, ``C(45,2)=990`` once the two hands are passed in as well, and 44 on a turn.
    """
    if not 0 <= len(board) <= 4:
        raise InputError(f"cannot complete a {len(board)}-card board to five cards")
    used = list(board)
    for hand in known_hands:
        used.extend(hand)
    pool = _remaining_cards(used)
    need = 5 - len(board)
    if need == 0:
        return (tuple(board),)  # type: ignore[return-value]
    return [tuple(board) + combo for combo in combinations(pool, need)]


def _combo_arrays(rng_positions: list[int], weights: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    combos = np.array([ALL_COMBOS[position] for position in rng_positions], dtype=np.int64)
    return combos, weights


def _conflict_mask(hero_combos: np.ndarray, villain_combos: np.ndarray) -> np.ndarray:
    """Vectorised 'these two hands share a physical card'. Written as four equality tests rather
    than a Python set loop because real ranges make that loop 1.7M iterations."""
    conflicts = np.zeros((len(hero_combos), len(villain_combos)), dtype=bool)
    for hero_slot in range(2):
        for villain_slot in range(2):
            conflicts |= hero_combos[:, hero_slot][:, None] == villain_combos[:, villain_slot][None, :]
    return conflicts


def range_equity(
    hero: Range,
    villain: Range,
    board: Board = (),
    *,
    mode: Literal["exact", "mc", "auto"] = "exact",
    iterations: int = 20_000,
    seed: int = 0,
) -> EquityResult:
    """Equity of one range against another on a shared board.

    Weights are per-combo probabilities (see :mod:`pokergto.ranges`), so a half-included class
    contributes half its combos and the aggregate is genuinely a distribution, not a chart.

    ``mode="auto"`` picks exact when the enumeration fits the budget and Monte Carlo when it does
    not, and the returned :class:`EquityResult` says which it used in ``.exact``. That is the one
    permitted convenience, and it is permitted because it is *self-reporting*: silently switching is
    the failure mode, not switching.
    """
    if hero.is_empty() or villain.is_empty():
        raise InputError("an empty range has no equity; that is a question about nothing")
    if len(board) > 4:
        raise InputError("a board of five cards has no equity left to compute")

    hero_positions = [i for i, w in enumerate(hero.weights) if w > 0]
    villain_positions = [j for j, w in enumerate(villain.weights) if w > 0]
    hero_combos, hero_weights = _combo_arrays(hero_positions, hero.weights[hero_positions])
    villain_combos, villain_weights = _combo_arrays(villain_positions, villain.weights[villain_positions])

    allowed = ~_conflict_mask(hero_combos, villain_combos)
    joint = hero_weights[:, None] * villain_weights[None, :]
    joint = joint * allowed
    total_weight = float(joint.sum())
    if total_weight <= 0:
        raise InputError("every hero/villain combo pair conflicts; the two ranges share all cards")

    completions = runout_boards(board)
    single_pair = len(hero_positions) == 1 and len(villain_positions) == 1
    if single_pair:
        # With exactly one combo each, the four hole cards are known, so the runout space shrinks to
        # the boards that cannot contain them: C(48,5) = 1,712,304 preflop instead of C(52,5) =
        # 2,598,960. That exclusion is the difference between an affordable exact answer and one that
        # silently becomes Monte Carlo, which is why it is worth the special case.
        hero_cards = (Card.from_index(int(hero_combos[0][0])), Card.from_index(int(hero_combos[0][1])))
        villain_cards = (
            Card.from_index(int(villain_combos[0][0])),
            Card.from_index(int(villain_combos[0][1])),
        )
        completions = runout_boards(board, known_hands=[hero_cards, villain_cards])
    estimated_cost = len(completions) * (len(hero_positions) + len(villain_positions))
    if mode == "auto":
        mode = "exact" if estimated_cost <= AUTO_EXACT_BUDGET else "mc"

    if mode == "exact":
        # Hole cards vary by combo pair, so the exact path enumerates every runout over the deck
        # minus the board and masks out hands that use a board card. That is the honest definition
        # of exact here, and the cost guard is what makes it safe to attempt.
        if estimated_cost > EXACT_EVAL_BUDGET:
            raise BudgetExceeded(
                f"exact equity needs about {estimated_cost:,} evaluations ({len(completions)} runouts"
                f" x {len(hero_positions) + len(villain_positions)} combos). Preflop with no board is"
                " C(52,5) = 2,598,960 runouts before any filtering, which is why solvers sample it:"
                " pass mode='mc' with iterations=<n> and accept a reported error bar, or use"
                " mode='auto' and read .exact on the result."
            )
        wins = ties = losses = 0.0
        for full_board in completions:
            board_set = {c.index for c in full_board}
            h_mask = np.array([not (set(hc) & board_set) for hc in hero_combos], dtype=bool)
            v_mask = np.array([not (set(vc) & board_set) for vc in villain_combos], dtype=bool)
            if not h_mask.any() or not v_mask.any():
                continue
            hero_scores = np.array(
                [
                    best_score((Card.from_index(int(a)), Card.from_index(int(b))), full_board)
                    for a, b in hero_combos[h_mask]
                ]
            )
            villain_scores = np.array(
                [
                    best_score((Card.from_index(int(a)), Card.from_index(int(b))), full_board)
                    for a, b in villain_combos[v_mask]
                ]
            )
            weights = joint[np.ix_(h_mask, v_mask)]
            diff = hero_scores[:, None] - villain_scores[None, :]
            wins += float(weights[diff > 0].sum())
            ties += float(weights[diff == 0].sum())
            losses += float(weights[diff < 0].sum())
        denominator = wins + ties + losses
        if denominator <= 0:
            raise InputError("exact enumeration found no legal combination")
        return EquityResult(
            equity=(wins + ties / 2.0) / denominator,
            wins=wins / denominator,
            ties=ties / denominator,
            losses=losses / denominator,
            exact=True,
            iterations=len(completions),
        )

    rng = np.random.default_rng(seed)
    flat_pairs = np.argwhere(joint > 0)
    probabilities = joint[flat_pairs[:, 0], flat_pairs[:, 1]]
    probabilities = probabilities / probabilities.sum()
    draws = rng.choice(len(flat_pairs), size=iterations, p=probabilities)
    deck_without_board = np.array([c.index for c in _remaining_cards(board)], dtype=np.int64)
    need = 5 - len(board)

    wins = ties = losses = 0.0
    for sample in draws:
        i, j = int(flat_pairs[sample][0]), int(flat_pairs[sample][1])
        held = set(int(x) for x in hero_combos[i]) | set(int(x) for x in villain_combos[j])
        pool = np.fromiter((c for c in deck_without_board if c not in held), dtype=np.int64)
        runout = rng.choice(pool, size=need, replace=False)
        full_board = tuple(board) + tuple(Card.from_index(int(c)) for c in runout)
        difference = best_score(
            (Card.from_index(int(hero_combos[i][0])), Card.from_index(int(hero_combos[i][1]))), full_board
        ) - best_score(
            (Card.from_index(int(villain_combos[j][0])), Card.from_index(int(villain_combos[j][1]))),
            full_board,
        )
        if difference > 0:
            wins += 1
        elif difference == 0:
            ties += 1
        else:
            losses += 1

    equity = (wins + ties / 2.0) / iterations
    variance = max(equity * (1.0 - equity) / iterations, 1e-15)
    return EquityResult(
        equity=equity,
        wins=wins / iterations,
        ties=ties / iterations,
        losses=losses / iterations,
        exact=False,
        iterations=iterations,
        seed=seed,
        stderr=math.sqrt(variance),
    )


def hand_equity(
    hero: Sequence[Card],
    villain: Sequence[Card],
    board: Board = (),
    *,
    mode: Literal["exact", "mc", "auto"] = "auto",
    iterations: int = 20_000,
    seed: int = 0,
) -> EquityResult:
    """Two specific hands. With a flop this is 1,081 runouts and exact is cheap, so exact is what
    you get; preflop it is 2.6M and ``auto`` falls back to Monte Carlo and *says so* on the result."""
    return range_equity(
        _single_combo_range(hero),
        _single_combo_range(villain),
        board,
        mode=mode,
        iterations=iterations,
        seed=seed,
    )


def _single_combo_range(cards: Sequence[Card]) -> Range:
    if len(cards) != 2:
        raise InputError("a hand is exactly two cards")
    indices = {c.index for c in cards}
    if len(indices) != 2:
        raise InputError("a hand cannot contain the same card twice")
    weights = np.zeros(1326, dtype=np.float64)
    target = (min(indices), max(indices))
    for position, combo in enumerate(ALL_COMBOS):
        if combo == target:
            weights[position] = 1.0
            return Range(weights)
    raise InputError(f"{cards[0]}{cards[1]} is not a valid combo")  # pragma: no cover


def vs_random(range_: Range, board: Board = (), *, iterations: int = 20_000, seed: int = 0) -> EquityResult:
    """Equity against one *random* hand. This is the primitive behind "range advantage": the number
    that says whether a board favours one distribution over another, computed rather than asserted."""
    return range_equity(range_, Range.full(), board, mode="mc", iterations=iterations, seed=seed)


def draw_probability(outs: int, unseen_cards: int, cards_to_come: int = 1) -> float:
    """Exact probability of hitting one of ``outs`` within ``cards_to_come`` deals.

    ``unseen_cards`` is stated explicitly instead of inferred, because "45 or 46 or 47?" is precisely
    where the memorised version of this goes wrong: with two hole cards and a three-card flop there
    are 47 unseen cards, so a nine-out flush draw improves on the turn ``9/47 = 19.15%``, and by the
    river ``1 - C(38,2)/C(47,2) = 34.97%``. The rule of 2 says 18% and the rule of 4 says 36%: one
    under-states, the other over-states, and lesson 01-03 shows both errors next to the exact numbers.
    """
    if cards_to_come not in (1, 2):
        raise InputError("only the next card (1) or turn and river (2) are modelled")
    if outs < 0:
        raise InputError("outs cannot be negative")
    if outs > unseen_cards:
        raise InputError(f"cannot have {outs} outs among {unseen_cards} unseen cards")
    miss = math.comb(unseen_cards - outs, cards_to_come) / math.comb(unseen_cards, cards_to_come)
    return 1.0 - miss


def unseen_after(board: Board, hands: Sequence[Sequence[Card]]) -> int:
    """How many cards nobody is holding and the dealer has not shown."""
    return 52 - len(board) - sum(len(hand) for hand in hands)


def outs_from_enumeration(
    hero: Sequence[Card], board: Board, *, improve_to: str, current_score: int | None = None
) -> list[Card]:
    """Which cards actually improve a hand, by enumeration rather than the usual counting shortcut.

    ``improve_to`` is a member of :class:`pokergto.evaluator.Category`. The classic lesson hidden in
    here: "9 outs" for a flush draw is wrong whenever the board pairs or a straight also arrives.
    Enumeration does not make that mistake, so a learner can watch the count they were taught
    disagree with the count that exists.
    """
    from .evaluator import Category

    if len(hero) != 2:
        raise InputError("needs exactly two hole cards")
    if not 3 <= len(board) <= 4:
        raise InputError("needs a flop or turn board")
    target = Category[improve_to.upper().replace(" ", "_")]
    base = best_score(hero, board) if current_score is None else current_score
    improving: list[Card] = []
    for card in _remaining_cards(list(hero) + list(board)):
        candidate_board = tuple(board) + (card,)
        score = best_score(hero, candidate_board)
        if (score >> 20) >= int(target) and score > base:
            improving.append(card)
    return improving
