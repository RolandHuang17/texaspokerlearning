"""Equity: exact enumeration where it is affordable, Monte Carlo where it is not, and never a
silent switch between the two.

``EquityResult`` carries ``stderr`` as a first-class field. That is not decoration: a Monte Carlo
number without its error bar is a guess formatted like a fact, and lesson 01-04 exists to make
learners feel the difference. Every generated table containing an MC value records the seed and the
iteration count, so the number can be reproduced or refuted.

Cost is the other half of the design:

* **Exact** means enumerating every runout, and the count depends on how many cards the caller has
  committed: after a three-card board there are ``C(49,2) = 1176`` completions if the board is all
  we know, ``C(47,2) = 1081`` once one player's two hole cards are known too, and ``C(45,2) = 990``
  once both hands are known (44 on a known turn). The evaluation count is
  ``runouts x (hero_combos + villain_combos)``, so exact is cheap for a few combos and absurd for a
  real range. :func:`range_equity` raises :class:`~pokergto.errors.BudgetExceeded` with the number
  and the alternative rather than hanging or quietly degrading. That number counts *evaluations* only:
  each runout then compares the two surviving score vectors, which for a full range against a full range
  on a flop is ``1081 x 1081 = 1,168,561`` pairwise comparisons against ``1081 + 1081`` evaluations. The
  guard is therefore a statement about evaluation work, not a wall-clock promise, and the measured
  ``tools/cost_probe.py`` numbers are the ones to quote for time.
* **Monte Carlo** samples a *(combo pair, runout)* from the correct joint distribution in one shot,
  so cost is ``O(iterations)`` regardless of how wide the ranges are. Conflicting combos (both
  players holding the same physical card) are excluded from the sampling distribution, which is the
  part of this calculation most often got wrong.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from itertools import combinations
from typing import Literal

import numpy as np

from .cards import ALL_COMBOS, Card, standard_deck
from .errors import BudgetExceeded, InputError
from .evaluator import best_score, evaluate7_many
from .ranges import Range

#: Evaluations ``mode="auto"`` will spend. Deliberately far below ``EXACT_EVAL_BUDGET``: preflop
#: exact equity is 1,712,304 runouts and takes about three minutes, which is a fine thing for a
#: learner to *choose* and a bad thing to happen by default.
AUTO_EXACT_BUDGET = 250_000

#: Evaluations allowed before exact enumeration refuses to run. Sized so exact tests stay inside the
#: <60s dev loop; tools/cost_probe.py is the solver-side equivalent.
EXACT_EVAL_BUDGET = 4_000_000

#: Seven-card rows handed to the vectorised evaluator per call. The exact path scores every legal
#: (board, combo) pair in blocks this size, which is what makes the batch path worth its fixed per-call
#: cost even for a two-combo matchup over 1,712,304 boards: at one call per board the fixed cost made
#: hand-vs-hand exact equity eight times *slower*, and hand-vs-hand is the most common exact call in the
#: curriculum. One megabyte-scale block per call keeps the setup amortised and the working set bounded.
EVAL_BLOCK_ROWS = 1 << 20

Board = tuple[Card, ...]
_Z95 = 1.959963984540054


@dataclass(frozen=True, slots=True)
class EquityResult:
    """Share-of-pot equity, decomposed. ``equity == wins + ties/2`` is asserted, not assumed:
    split pots are exactly where hand strength and equity part company.
    """

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
        returning it that way is better than returning a misleading zero.
        """
        if self.exact:
            return (self.equity, self.equity)
        margin = _Z95 * self.stderr
        return (max(0.0, self.equity - margin), min(1.0, self.equity + margin))

    def __str__(self) -> str:
        mode = "exact" if self.exact else f"mc(n={self.iterations},seed={self.seed})"
        error = "" if self.exact else f" +/-{100 * _Z95 * self.stderr:.2f}%"
        return f"{100 * self.equity:.2f}% [W{100 * self.wins:.1f}/T{100 * self.ties:.1f}] ({mode}){error}"


def _remaining_cards(used: Sequence[Card]) -> list[Card]:
    taken = {c.index for c in used}
    return [c for c in standard_deck() if c.index not in taken]


def runout_boards(board: Board, *, known_hands: Sequence[Sequence[Card]] = ()) -> list[Board]:
    """Every completion of a 0..4 card board to five cards, given the hole cards in play.

    The number of completions sets the exact-mode cost. For a flop: ``C(49,2)=1176`` when the board
    is all we know, ``C(47,2)=1081`` once one hand is excluded as well (which is the same number as
    "how many hands can my opponent hold"), ``C(45,2)=990`` once both hands are excluded, and 44 on
    a known turn. Preflop with both hands known it is ``C(48,5)=1712304``.
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
    than a Python set loop because real ranges make that loop 1.7M iterations.
    """
    conflicts = np.zeros((len(hero_combos), len(villain_combos)), dtype=bool)
    for hero_slot in range(2):
        for villain_slot in range(2):
            conflicts |= (
                hero_combos[:, hero_slot][:, None] == villain_combos[:, villain_slot][None, :]
            )
    return conflicts


def _score_matrix(combos: np.ndarray, boards: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Scores and legality for every ``(board, combo)`` pair, in as few vector calls as the block allows.

    Returns ``(scores, legal)``, both shaped ``(n_boards, n_combos)``. A combo that uses a card the board
    already shows is *illegal*: it cannot be dealt, and its seven-card row would repeat a physical card,
    which the evaluator rightly refuses. Those entries are left at zero in ``scores`` and reported by
    ``legal``, so a caller that forgets to mask reads a zero as "worst possible hand" rather than
    crashing -- which is why the mask is returned instead of applied here.

    The dense ``(n_boards, n_combos)`` temporary is affordable because :data:`EXACT_EVAL_BUDGET` caps
    ``n_boards x (hero_combos + villain_combos)``, and so bounds this shape by the same number; the
    broadcast intermediate that builds it is ten times wider (two hole cards against five board cards per
    pair), which the same cap keeps at a few tens of megabytes.
    """
    conflict = (combos[:, None, :, None] == boards[None, :, None, :]).any(axis=(2, 3))

    legal = ~conflict.T
    flat_board, flat_combo = np.nonzero(legal)
    scores = np.zeros(legal.shape, dtype=np.int64)
    for start in range(0, flat_board.size, EVAL_BLOCK_ROWS):
        rows = slice(start, min(start + EVAL_BLOCK_ROWS, flat_board.size))
        cards = np.concatenate([combos[flat_combo[rows]], boards[flat_board[rows]]], axis=1)
        scores[flat_board[rows], flat_combo[rows]] = evaluate7_many(cards)
    return scores, legal


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
    villain_combos, villain_weights = _combo_arrays(
        villain_positions, villain.weights[villain_positions]
    )

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
        hero_cards = (
            Card.from_index(int(hero_combos[0][0])),
            Card.from_index(int(hero_combos[0][1])),
        )
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
        board_codes = np.fromiter(
            (card.index for board_ in completions for card in board_),
            dtype=np.int64,
            count=5 * len(completions),
        ).reshape(len(completions), 5)
        hero_scores, hero_legal = _score_matrix(hero_combos, board_codes)
        villain_scores, villain_legal = _score_matrix(villain_combos, board_codes)
        if single_pair and hero_legal.all() and villain_legal.all():
            # Both hands are on the table, so the runout space was already built from the deck minus
            # those four cards and no combo can ever be illegal. That makes the comparison one
            # whole-array operation rather than a per-runout Python loop. Measured over the same
            # 1,712,304 runouts and 3,424,608 evaluations of ``AhAs`` versus ``7d2s`` preflop: 353.8s
            # with the old per-hand scalar evaluator, 50.8s with vectorised scoring behind the loop,
            # 17.3s with the loop gone. Same 0.8819368523 every time.
            weight = float(joint[0, 0])
            difference = hero_scores[:, 0] - villain_scores[:, 0]
            wins = weight * float((difference > 0).sum())
            ties = weight * float((difference == 0).sum())
            losses = weight * float((difference < 0).sum())
        else:
            for index in range(board_codes.shape[0]):
                h_live = hero_legal[index]
                v_live = villain_legal[index]
                if not h_live.any() or not v_live.any():
                    continue
                weights = joint[np.ix_(h_live, v_live)]
                diff = hero_scores[index][h_live][:, None] - villain_scores[index][v_live][None, :]
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
            (Card.from_index(int(hero_combos[i][0])), Card.from_index(int(hero_combos[i][1]))),
            full_board,
        ) - best_score(
            (
                Card.from_index(int(villain_combos[j][0])),
                Card.from_index(int(villain_combos[j][1])),
            ),
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
    """Two specific hands. With a flop this is 990 runouts and exact is cheap, so exact is what you
    get; preflop it is 1,712,304 and ``auto`` falls back to Monte Carlo and *says so* on the result.
    """
    return range_equity(
        Range.from_cards(hero),
        Range.from_cards(villain),
        board,
        mode=mode,
        iterations=iterations,
        seed=seed,
    )


def vs_random(
    range_: Range, board: Board = (), *, iterations: int = 20_000, seed: int = 0
) -> EquityResult:
    """Equity against one *random* hand. This is the primitive behind "range advantage": the number
    that says whether a board favours one distribution over another, computed rather than asserted.
    """
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
