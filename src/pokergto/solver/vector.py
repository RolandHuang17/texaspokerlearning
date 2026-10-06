"""Vector-form CFR: the same recursion, carried over all deals at once.

:mod:`pokergto.solver.cfr` is the definition of correctness in this repository. It recurses one
``(node, deal)`` pair at a time, which is slow and obviously right, and Kuhn's analytic ``-1/18`` proves
it. This file is the fast form the curriculum eventually needs -- a 1326-combo preflop model is not
tractable one deal at a time -- and the fast form has ways of being wrong that the slow form does not:

* the acting player's action probability belongs **inside** the recursion, into their own reach only.
  Multiplying it outside as well squares the opponent's probabilities, and the iteration then converges
  to something stable that is not an equilibrium;
* regrets and strategy sums may only be written at the *updating* player's information sets, because
  the utilities arriving up the call stack are from that player's perspective;
* padding ragged per-infoset rows with zeros makes a nonexistent action look like an action with
  probability ``0``, which multiplies a child's reach by zero and freezes part of the tree;
* flooring *the whole regret matrix* after a traversal touches a few information sets also floors the
  opponent's rows, which is a different algorithm from the per-row flooring of :mod:`pokergto.solver.cfr`.

The first two are not hypothetical: an earlier vector attempt here stalled at exploitability 0.89 with
a game value of +0.57 and only Kuhn's analytic value exposed it. The fourth was found by this file's own admission run, and the honest version of what it found is less
flattering than a bug. With whole-matrix flooring, every registered gate still passed: plain matching
agreed to ``1e-16``, CFR+ agreed on all four closed-form frequencies per entry, exploitability stayed at
``3e-5`` or better. What disagreed was everything the gates do not look at -- the average strategy over
all 3,780 Leduc information sets drifted up to ``1.1e-2`` between the two implementations. That is the
reason to fix the scope rather than note it: a gate samples a handful of frequencies, and the only thing a
second implementation contributes beyond those samples is the same trajectory. Two solvers that agree on
the four numbers anyone checks and disagree on the rest are one check, not two.

What the two forms can and cannot be required to agree on is stated in
``tests/test_solver_vector.py``, and it is not equality everywhere:

* under plain regret matching the two are **bit-identical** -- same game value, same average strategy,
  difference exactly zero on all six registered proof entries;
* under CFR+ they are **not** bit-identical and cannot be. :mod:`cfr` recurses deal by deal, so it
  floors an information set's row *between* deals, cutting off negative partial sums that have already
  been added; this file sums every deal at a node and floors *once*. The flooring scope now matches
  (touched rows only); the flooring moment cannot, without giving up the vectorisation that is the whole
  point. Both forms therefore satisfy every registered gate on their own, and the gates -- not equality
  between implementations -- are the standard. That is the same conclusion :mod:`cfr` reaches about
  Kuhn's equilibrium family: a solver's job is to land inside the set the math defines, not to reproduce
  another solver's path.

Storage is flat: ``(n_infosets * width)`` buffers indexed by information set, with a per-node column
mask, so a scatter is one ``np.add.at`` over a gathered index array instead of a Python loop over
information sets.
"""

from __future__ import annotations

import time
from typing import Literal

import numpy as np

from ..errors import InvariantError
from .cfr import SolveResult, _actions_per_infoset
from .tree import DecisionNode, GameTree, TerminalNode

__all__ = ["VectorCFRSolver", "solve_vector"]


class VectorCFRSolver:
    """Alternating-update CFR carrying one vector over deals at each public node.

    Same constructor surface as :class:`pokergto.solver.cfr.CFRSolver`, which is what lets the two forms
    be run against each other without either knowing about the other.
    """

    def __init__(
        self,
        tree: GameTree,
        *,
        plus: bool = False,
        weighting: Literal["uniform", "linear"] | None = None,
    ) -> None:
        if not tree.n_infosets:
            raise InvariantError("game has no information sets")
        tree.validate()
        self.tree = tree
        self.plus = plus
        self.weighting: Literal["uniform", "linear"] = weighting or (
            "linear" if plus else "uniform"
        )
        self.width = int(max(tree.infoset_actions))
        self.counts = np.asarray(tree.infoset_actions, dtype=np.int64)
        #: Columns that exist for each information set. Padding must never be read as a zero
        #: probability, which is what fills it in :meth:`current_matrix` is for.
        self.present = (
            np.arange(self.width)[None, :] < self.counts[:, None]
        )  # (n_infosets, width) broadcasting the row's own action count
        self.regrets = np.zeros((tree.n_infosets, self.width))
        self.strategy_sum = np.zeros((tree.n_infosets, self.width))
        self.iteration = 0
        self._children, self._infosets, self._payoffs, self._players = self._compile()

    # --- compilation ------------------------------------------------------------------

    def _compile(
        self,
    ) -> tuple[list[tuple[int, ...]], list[np.ndarray], list[np.ndarray], list[int]]:
        """Flatten the tree so a traversal never touches a Python node object per deal.

        There is deliberately no per-node action mask here. A gather is ``sigma[infosets][:, :width]``,
        which already restricts to the actions that exist at that node, and a mask sized to that same
        width is therefore all-True by construction -- indexing it with ``[:, action]`` selects one
        column of a column-slice and can never mask anything. A guard that is always true is not a
        guard, so the hazard it was written against (a padded column read as ``sigma = 0``, which zeroes
        a child's reach and freezes a subtree while the run still reports a tidy exploitability) is
        handled where it can actually bite: :meth:`current_matrix` fills padded columns with an even
        split, so no read can turn "this action is not here" into "probability zero".
        """
        children: list[tuple[int, ...]] = []
        infosets: list[np.ndarray] = []
        payoffs: list[np.ndarray] = []
        players: list[int] = []
        for node in self.tree.nodes:
            if isinstance(node, TerminalNode):
                children.append(())
                infosets.append(np.zeros(0, dtype=np.int64))
                payoffs.append(np.asarray(node.payoff, dtype=np.float64))
                players.append(-1)
                continue
            assert isinstance(node, DecisionNode)
            children.append(tuple(node.children))
            infosets.append(np.asarray(node.infosets, dtype=np.int64))
            payoffs.append(np.zeros(0, dtype=np.float64))
            players.append(node.player)
        return children, infosets, payoffs, players

    # --- strategies -------------------------------------------------------------------

    def current_matrix(self) -> np.ndarray:
        """Regret-matching strategy as ``(n_infosets, width)``, padding filled to an even split.

        The padding is filled rather than zeroed so that a read which forgot to mask cannot turn "no
        such action" into "probability zero". Correct reads still use the mask.
        """
        positive = np.clip(self.regrets, 0.0, None) * self.present
        totals = positive.sum(axis=1, keepdims=True)
        held = totals > 0.0
        uniform = self.present / self.counts[:, None]
        strategy = np.where(held, positive / np.where(held, totals, 1.0), uniform)
        return np.where(self.present, strategy, 1.0 / self.width)

    def average_matrix(self) -> np.ndarray:
        totals = self.strategy_sum.sum(axis=1, keepdims=True)
        held = totals > 0.0
        uniform = self.present / self.counts[:, None]
        return np.where(held, self.strategy_sum / np.where(held, totals, 1.0), uniform)

    def current_strategy(self) -> list[np.ndarray]:
        return [
            row[: int(count)] for row, count in zip(self.current_matrix(), self.counts, strict=True)
        ]

    def average_strategy(self) -> list[np.ndarray]:
        return [
            row[: int(count)] for row, count in zip(self.average_matrix(), self.counts, strict=True)
        ]

    # --- traversal --------------------------------------------------------------------

    def _walk(
        self,
        node_id: int,
        reach_self: np.ndarray,
        reach_opp: np.ndarray,
        player: int,
        sigma: np.ndarray,
    ) -> np.ndarray:
        """Utility vector for ``player``, one entry per deal.

        ``reach_opp`` scales the regret update and ``reach_self`` scales the strategy-sum update;
        neither scales the returned utility. That asymmetry is the whole content of
        *counterfactual*, and it is identical in the slow form -- which is what makes the two
        comparable value by value.
        """
        if self._players[node_id] < 0:
            payoff = self._payoffs[node_id]
            return payoff if player == 0 else -payoff

        infosets = self._infosets[node_id]
        width = len(self._children[node_id])
        # The slice is the mask: columns beyond this node's action count are not read.
        gather = sigma[infosets][:, :width]
        utilities = np.empty((self.tree.n_deals, width), dtype=np.float64)
        for action, child in enumerate(self._children[node_id]):
            if self._players[node_id] == player:
                utilities[:, action] = self._walk(
                    child, reach_self * gather[:, action], reach_opp, player, sigma
                )
            else:
                utilities[:, action] = self._walk(
                    child, reach_self, reach_opp * gather[:, action], player, sigma
                )
        node_utility: np.ndarray = np.einsum("da,da->d", gather, utilities)

        if self._players[node_id] == player:
            weight = reach_opp * self.tree.deal_prob
            columns = np.arange(width)[None, :]
            flat = (infosets[:, None] * self.width + columns).ravel()
            values = (weight[:, None] * (utilities - node_utility[:, None])).ravel()
            np.add.at(self.regrets.ravel(), flat, values)
            if self.plus:
                # Floor exactly the rows this node touched, and nothing else. Whole-matrix flooring is
                # a different algorithm: it zeroes the *opponent's* negative regrets during our own
                # traversal, which changes the strategy they act on two lines later. Measured before
                # this was fixed, the two forms agreed to 1e-16 under plain regret matching (nothing is
                # floored, so the scope cannot be wrong) and drifted 1.1e-2 in the defender's frequency
                # at two times pot under CFR+ -- while still reporting a tidy exploitability of 1.1e-4,
                # which is exactly the failure mode this file exists to prevent.
                rows = np.unique(infosets)
                self.regrets[rows] = np.maximum(self.regrets[rows], 0.0)
            own_weight = float(self.iteration) if self.weighting == "linear" else 1.0
            np.add.at(
                self.strategy_sum.ravel(),
                flat,
                (own_weight * reach_self[:, None] * gather).ravel(),
            )
        return node_utility

    def step(self, player: int) -> None:
        """One traversal updating only ``player``'s regrets and strategy sums.

        The strategy snapshot is taken once per traversal, exactly as :class:`pokergto.solver.cfr.
        CFRSolver` does it. Recomputing per node would make regret-matching updates land in the middle
        of the same traversal, and the two forms would then differ by an algorithm change rather than by
        a speed change -- which is the one thing this file is not allowed to become.
        """
        ones = np.ones(self.tree.n_deals, dtype=np.float64)
        self._walk(self.tree.root, ones, ones, player, self.current_matrix())

    def run(self, iterations: int, *, measure_every: int = 0) -> SolveResult:
        """``iterations`` iterations, each an alternating pair of full vector traversals."""
        from .exploitability import expected_value, exploitability

        started = time.perf_counter()
        curve: list[tuple[int, float]] = []
        for iteration in range(1, iterations + 1):
            self.iteration = iteration
            self.step(0)
            self.step(1)
            if measure_every and iteration % measure_every == 0:
                curve.append((iteration, exploitability(self.tree, self.average_matrix())))
        final_matrix = self.average_matrix()
        final_exploitability = exploitability(self.tree, final_matrix)
        elapsed = time.perf_counter() - started
        if measure_every and (not curve or curve[-1][0] != iterations):
            curve.append((iterations, final_exploitability))
        return SolveResult(
            tree_name=self.tree.name,
            algorithm="cfr_plus_vector" if self.plus else "cfr_vector",
            iterations=iterations,
            average_strategy=self.average_strategy(),
            current_strategy=self.current_strategy(),
            curve=curve,
            elapsed_seconds=elapsed,
            exploitability=final_exploitability,
            game_value=expected_value(self.tree, final_matrix),
            infoset_labels=list(self.tree.infoset_labels),
            infoset_actions=_actions_per_infoset(self.tree),
        )


def solve_vector(
    tree: GameTree, iterations: int = 10_000, *, plus: bool = False, measure_every: int = 0
) -> SolveResult:
    """Functional entry point, mirroring :func:`pokergto.solver.cfr.solve`."""
    return VectorCFRSolver(tree, plus=plus).run(iterations, measure_every=measure_every)
