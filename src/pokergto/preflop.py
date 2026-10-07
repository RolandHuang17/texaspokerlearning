"""Preflop all-in equities by sampling boards, not deals.

A preflop equity matrix is the object chapters 05, 10, 11 and 12 would cite, and ``adr/0006`` established
that computing it *exactly* is out of budget: one class cell costs 141-180 s measured, and the full
169x169 grid is about 740 hours. This module is the response -- an estimator that is sampled only in the
board, so every cell in the matrix is exact conditional on the boards it was computed over.

Why conditioning on the board is the right axis to sample along:

* The deal variance disappears. For a fixed board, every legal, mutually disjoint (hero, villain) combo
  pair is enumerated and compared -- there is no "did we happen to draw the strong combos this iteration"
  noise at all. What is left is board variance, which is one random draw per board rather than per pair,
  so a few thousand boards buy a lot of accuracy: measured 0.0030 mean standard error over all 28,561
  ordered cells at 20,000 boards, against 0.0103 at 2,000, shrinking as 1/sqrt(K) as it should.
* The work is shared. Seven-card evaluation is the expensive part, and a hole pair's score depends only on
  (hole, board). Scoring all 1,326 holes against a board once serves every one of the 14,365 unordered
  class cells simultaneously, instead of paying twice per sample per cell. Measured: 22 ms per board for
  the whole matrix pass, which is 7.3 minutes for 20,000 boards.
* The estimator is a ratio of sums, so its error bar comes from **independent batches of boards**.
  A binomial formula on the comparison count would be wrong here by an order of magnitude, because
  comparisons that share a board are not independent -- the tie structure, the legality filter and the
  card removal are all fixed for a given board.

The three exact cells this was validated against (``pokergto.equity.range_equity(..., mode="exact")``
with the budget raised, 142-178 s each, measured 2026-10-07): ``AA`` v ``KK`` 0.8194605047, ``AKo`` v
``QQ`` 0.4324233606, ``72o`` v ``22`` 0.3258923844. At 20,000 boards the deviations were 1.5, 0.6 and
1.2 standard errors -- no sign of bias, and the magnitude is what sampling noise should be.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

import numpy as np

from .cards import ALL_COMBOS, HAND_CLASSES_169, class_key, combo_cards
from .equity import conflict_mask, score_matrix
from .errors import InputError

#: Every ordered class pair is a cell, including the ``169`` diagonal ones: ``AA`` against ``AA`` is a
#: real deal (``AhAd`` versus ``AsAc``), and its equity is 0.5 by symmetry rather than an empty slot.
#: The grid therefore has ``169 x 169 = 28,561`` populated cells, not 169 x 168 -- asserted in the tests.
N_CLASSES: Final = len(HAND_CLASSES_169)

#: The 1,326 hole-card combos as ``(N, 2)`` 52-card indices, in :data:`pokergto.cards.ALL_COMBOS` order.
COMBO_CODES = np.array(ALL_COMBOS, dtype=np.int64)

#: Which of the 169 classes each combo belongs to, indexed like :data:`COMBO_CODES`.
COMBO_CLASS = np.array(
    [HAND_CLASSES_169.index(class_key(*combo_cards(combo))) for combo in ALL_COMBOS], dtype=np.int64
)

#: Pairs of combos that share a physical card. Board independent, so this is computed once: such a pair is
#: never dealable, and counting it would silently weight an impossible deal.
NONDEALABLE = conflict_mask(COMBO_CODES, COMBO_CODES)

#: Class-index pair for every ordered slot, used to scatter pair counts into the matrix in one pass.
_CLASS_CELLS = COMBO_CLASS[:, None] * N_CLASSES + COMBO_CLASS[None, :]


@dataclass(frozen=True, slots=True)
class PreflopMatrix:
    """Board-sampled all-in equities over the 169 classes, with the error bars carried beside them.

    ``equity[i, j]`` is hero class ``i``'s share of the pot all-in preflop against villain class ``j``.
    ``stderr`` is the independent-batch standard error of that number and ``pairs_stderr`` the same for the
    denominator -- both are carried because a sampled quantity that reports no error is a guess formatted
    like a fact, and because the denominator is what says how much comparison work backs a cell. The
    denominator's dispersion is also the one that has to be believed when checking pair counts against
    closed-form combinatorics: comparisons that share a board are correlated, so a binomial formula on the
    pair count understates the spread by more than three times (measured: a 1.6-sigma deviation by the exact
    variance reads 6.2 sigma under the binomial assumption).
    """

    equity: np.ndarray
    stderr: np.ndarray
    pairs: np.ndarray
    pairs_stderr: np.ndarray
    boards: int
    batches: int
    seed: int
    #: ``(batches, 3, 169, 169)`` wins / ties / pair counts per batch, kept so that a *derived* quantity --
    #: an equity against a range rather than against one class -- gets its error bar from the same
    #: independent batches. Averaging a row and quoting sqrt(sum of squared sigmas) would be decorative:
    #: every cell in a row shares the same boards, so they are strongly correlated and the true spread is
    #: wider than that formula claims.
    panels: np.ndarray

    def equity_against(self, weights: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Each class's equity against an opponent distribution, with a batch-derived error bar.

        ``weights`` is over the 169 classes and need not be normalised -- the ratio of sums normalises
        itself, the way ``range_equity`` weights by combos rather than by cells. The result is what a preflop
        threshold decision compares against, and the second array is its honest standard error: computed by
        re-deriving the whole weighted quantity inside each independent batch, not by combining the per-cell
        sigmas as if the cells were independent draws.
        """
        if weights.shape != (N_CLASSES,):
            raise InputError(f"expected {N_CLASSES} class weights, got shape {weights.shape}")
        total = self._contract(self.panels.sum(axis=0), weights)
        per_batch = np.stack([self._contract(batch, weights) for batch in self.panels])
        # `_contract` returns a ratio, so the reported quantity is the batches' mean and its error is
        # std / sqrt(batches). `pairs_stderr` multiplies by sqrt(batches) instead, because a total is a sum:
        # copying one scaling into the other inflates an equity error bar by exactly the batch count, which is
        # what this line got wrong the first time and what the one-hot identity in tests/test_preflop.py now
        # pins from both directions.
        spread = per_batch.std(axis=0, ddof=1) / np.sqrt(self.panels.shape[0])
        return total, spread

    @staticmethod
    def _contract(panel: np.ndarray, weights: np.ndarray) -> np.ndarray:
        """Ratio of weighted sums for one batch (or for all of them): hero equity per hero class."""
        wins, ties, totals = panel[0], panel[1], panel[2]
        numerator = (wins + 0.5 * ties) @ weights
        denominator = totals @ weights
        return np.where(denominator > 0, numerator / np.maximum(denominator, 1.0), np.nan)

    def cell(self, hero_class: str, villain_class: str) -> tuple[float, float]:
        """``(equity, standard error)`` for one ordered class pair."""
        for key in (hero_class, villain_class):
            if key not in HAND_CLASSES_169:
                raise InputError(f"unknown hand class {key!r}")
        i, j = HAND_CLASSES_169.index(hero_class), HAND_CLASSES_169.index(villain_class)
        return float(self.equity[i, j]), float(self.stderr[i, j])


def _sample_boards(count: int, seed: int) -> np.ndarray:
    """``count`` uniform five-card boards as ``(count, 5)`` 52-card indices, sorted within a row.

    Ranking the 52 uniform keys per row and taking the five smallest is a without-replacement sample that
    numpy can build for every board at once; the sort within the row keeps the output independent of the
    sampling order, which is what makes a fixed seed reproduce byte for byte.
    """
    rng = np.random.default_rng(seed)
    keys = rng.random((count, 52), dtype=np.float64)
    drawn = np.argsort(keys, axis=1, kind="stable")[:, :5]
    return np.sort(drawn, axis=1).astype(np.int64)


def _accumulate(boards: np.ndarray, chunk: int = 200) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Wins, ties and dealable-pair counts by class cell, over one batch of boards."""
    wins = np.zeros(N_CLASSES * N_CLASSES, dtype=np.float64)
    ties = np.zeros(N_CLASSES * N_CLASSES, dtype=np.float64)
    totals = np.zeros(N_CLASSES * N_CLASSES, dtype=np.float64)
    for start in range(0, boards.shape[0], chunk):
        block = boards[start : start + chunk]
        scores, legal = score_matrix(COMBO_CODES, block)
        for row in range(block.shape[0]):
            live = np.flatnonzero(legal[row])
            if live.size == 0:
                continue
            values = scores[row][live]
            allowed = ~NONDEALABLE[np.ix_(live, live)]
            cells = _CLASS_CELLS[np.ix_(live, live)]
            difference = values[:, None] - values[None, :]
            wins += np.bincount(
                cells[(difference > 0) & allowed].ravel(), minlength=N_CLASSES * N_CLASSES
            )
            ties += np.bincount(
                cells[(difference == 0) & allowed].ravel(), minlength=N_CLASSES * N_CLASSES
            )
            totals += np.bincount(cells[allowed].ravel(), minlength=N_CLASSES * N_CLASSES)
    shape = (N_CLASSES, N_CLASSES)
    return wins.reshape(shape), ties.reshape(shape), totals.reshape(shape)


def all_in_matrix(
    boards: int = 20_000, *, seed: int = 202_610_071, batches: int = 20
) -> PreflopMatrix:
    """Board-sampled preflop all-in equity matrix over the 169 classes.

    ``batches`` splits the boards into independent groups so the standard error is a real one: each batch
    yields its own ratio-of-sums, and the reported error is the standard deviation of the batch ratios over
    ``sqrt(batches)``. The guard requires at least a hundred boards per batch -- one batch cannot be
    dispersed at all, and a batch of a handful of boards measures board noise so coarsely that the error bar
    becomes decoration.

    Determinism is by seed, not by accident: the same ``seed``, ``boards`` and ``batches`` reproduce the same
    ``data/gen`` bytes, which is what ADR-0002 asks of any sampled artifact this repository commits.
    """
    if boards < 100:
        raise InputError("under 100 boards the batch error bar is decoration, not measurement")
    if not 2 <= batches <= boards // 100:
        raise InputError(f"batches must be between 2 and boards // 100; got {batches}")
    per_batch = boards // batches
    panels = np.stack(
        [_accumulate(_sample_boards(per_batch, seed + 7919 * index)) for index in range(batches)]
    )
    wins, ties, totals = (panels[:, axis].sum(axis=0) for axis in range(3))
    equity = np.where(totals > 0, (wins + 0.5 * ties) / np.maximum(totals, 1.0), np.nan)
    batch_equity = np.where(
        panels[:, 2] > 0,
        (panels[:, 0] + 0.5 * panels[:, 1]) / np.maximum(panels[:, 2], 1.0),
        np.nan,
    )
    stderr = batch_equity.std(axis=0, ddof=1) / np.sqrt(batches)
    # The total is a sum of `batches` exchangeable batch counts, so its dispersion is the batch spread times
    # sqrt(batches) -- the opposite scaling to a mean, which is easy to get backwards and print an error bar
    # that shrinks as the artifact gets less reliable.
    pairs_stderr = panels[:, 2].std(axis=0, ddof=1) * np.sqrt(batches)
    return PreflopMatrix(
        equity=equity,
        stderr=stderr,
        pairs=totals,
        pairs_stderr=pairs_stderr,
        boards=per_batch * batches,
        batches=batches,
        seed=seed,
        panels=panels,
    )
