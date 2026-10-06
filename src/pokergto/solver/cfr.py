"""Counterfactual regret minimisation, in the textbook form, for the games in
:mod:`pokergto.solver.games`.

This implementation is deliberately the *slow, obviously correct* one: it recurses over
``(node, deal)`` pairs and folds reach probabilities into the updates the way every CFR tutorial does.
Kuhn then converges to its analytic value ``-1/18`` and the one-street game reproduces the closed
forms of chapter 02, which is what this milestone requires (ADR-0002). A vector form that carries a
vector over deals at each public node is one to two orders of magnitude faster and belongs to the next
milestone -- and this file is the oracle it will be validated against, because a vectorised CFR has
ways to be quietly wrong that this form does not.

That sentence is not hypothetical. An earlier vector-form version of this file multiplied the acting
player's action probability both into the reach vector *and* outside the recursive call, squaring the
opponent's probabilities at every opponent node. Convergence stalled at a fixed point that was not an
equilibrium, and only Kuhn's analytic value exposed it. The exploitability gate in
:mod:`pokergto.solver.proofs` is what turns that class of bug into a build failure instead of a
confident wrong number inside a lesson.

The algorithm, in the order lesson 08-02 teaches it:

1. **Regret matching.** The current strategy is proportional to positive accumulated regret; uniform
   when nothing has been learned yet.
2. **One traversal per player per iteration** (alternating updates), accumulating
   ``regret[I][a] += pi_opp * chance * (utility(a) - utility(node))``.
3. **Average.** ``strategy_sum[I][a] += weight * pi_self * sigma(a)``. The *average* strategy
   converges; the current one oscillates. That is the most counter-intuitive fact in CFR, and the
   reason exploitability is always measured on the average.

Nothing here samples: every deal of every traversal is exact, so an iteration count is reproducible
bit-for-bit across machines, which is what makes committing solver artifacts meaningful (ADR-0001).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Literal

import numpy as np

from ..errors import InvariantError
from .tree import DecisionNode, GameTree, TerminalNode, regret_matching


@dataclass(slots=True)
class SolveResult:
    """Everything a solver artifact records, and everything the observation deck animates."""

    tree_name: str
    algorithm: str
    iterations: int
    average_strategy: list[np.ndarray]
    current_strategy: list[np.ndarray]
    curve: list[tuple[int, float]] = field(default_factory=list)
    elapsed_seconds: float = 0.0
    exploitability: float = float("nan")
    game_value: float = float("nan")
    infoset_labels: list[str] = field(default_factory=list)
    infoset_actions: list[list[str]] = field(default_factory=list)

    def strategy_report(self) -> dict[str, dict[str, float]]:
        """``infoset label -> action -> average frequency``, rounded for artifact writing."""
        report: dict[str, dict[str, float]] = {}
        for index, label in enumerate(self.infoset_labels):
            actions = self.infoset_actions[index]
            row = self.average_strategy[index]
            report[label] = {action: round(float(value), 6) for action, value in zip(actions, row, strict=True)}
        return report


class CFRSolver:
    """One instance per game. Call :meth:`run`, then read :attr:`SolveResult.exploitability`."""

    def __init__(
        self,
        tree: GameTree,
        *,
        plus: bool = False,
        weighting: Literal["uniform", "linear"] | None = None,
    ) -> None:
        if not tree.n_infosets:
            raise InvariantError("game has no information sets")
        self.tree = tree
        self.plus = plus
        self.weighting: Literal["uniform", "linear"] = weighting or ("linear" if plus else "uniform")
        self.regrets = [np.zeros(int(count)) for count in tree.infoset_actions]
        self.strategy_sum = [np.zeros(int(count)) for count in tree.infoset_actions]
        self.iteration = 0

    # --- strategies -------------------------------------------------------------------

    def current_strategy(self) -> list[np.ndarray]:
        return [regret_matching(row[None, :])[0] for row in self.regrets]

    def average_strategy(self) -> list[np.ndarray]:
        out: list[np.ndarray] = []
        for row in self.strategy_sum:
            total = row.sum()
            out.append(row / total if total > 0 else np.full(row.shape, 1.0 / row.shape[0]))
        return out

    def current_matrix(self) -> np.ndarray:
        return _pad(self.current_strategy(), self.tree)

    def average_matrix(self) -> np.ndarray:
        return _pad(self.average_strategy(), self.tree)

    # --- traversal --------------------------------------------------------------------

    def _cfr(
        self,
        node_id: int,
        deal: int,
        reach_self: float,
        reach_opp: float,
        player: int,
        sigma_by_infoset: list[np.ndarray],
    ) -> float:
        """Expected utility for ``player`` at this node, given the two reach probabilities.

        The opponent's reach multiplies the *regret update* and never the returned utility; our own
        reach multiplies the strategy-sum update only. Those two asymmetries are the whole meaning of
        "counterfactual", and getting them backwards is the bug this function is written to make
        visible.
        """
        node = self.tree.nodes[node_id]
        if isinstance(node, TerminalNode):
            payoff = float(node.payoff[deal])
            return payoff if player == 0 else -payoff
        assert isinstance(node, DecisionNode)
        infoset = int(node.infosets[deal])
        sigma = sigma_by_infoset[infoset]
        count = len(node.children)
        utilities = np.zeros(count)
        for action, child in enumerate(node.children):
            if node.player == player:
                utilities[action] = self._cfr(
                    child, deal, reach_self * float(sigma[action]), reach_opp, player, sigma_by_infoset
                )
            else:
                utilities[action] = self._cfr(
                    child, deal, reach_self, reach_opp * float(sigma[action]), player, sigma_by_infoset
                )
        node_utility = float(np.dot(sigma[:count], utilities))
        if node.player == player:
            # Alternating updates mean exactly one player's rows are touched per traversal. Updating at
            # the opponent's node as well is a real bug this line prevents: the utilities returned up
            # this call are from *our* perspective, so writing them into the opponent's regrets mixes
            # signs and quietly destroys convergence.
            weight = reach_opp * float(self.tree.deal_prob[deal])
            regret_row = self.regrets[infoset]
            regret_row[:count] += weight * (utilities - node_utility)
            if self.plus:
                np.maximum(regret_row, 0.0, out=regret_row)
            own_weight = float(self.iteration) if self.weighting == "linear" else 1.0
            self.strategy_sum[infoset][:count] += own_weight * reach_self * sigma[:count]
        return node_utility

    def step(self, player: int) -> None:
        """One traversal updating only ``player``'s regrets and strategy sums."""
        sigma_by_infoset = self.current_strategy()
        for deal in range(self.tree.n_deals):
            self._cfr(self.tree.root, deal, 1.0, 1.0, player, sigma_by_infoset)

    def run(self, iterations: int, *, measure_every: int = 0) -> SolveResult:
        """``iterations`` iterations, each an alternating pair of full traversals."""
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
            algorithm="cfr_plus" if self.plus else "cfr",
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


def _pad(rows: list[np.ndarray], tree: GameTree) -> np.ndarray:
    """Stack per-infoset strategies into ``(n_infosets, max_actions)``, zero-padding ragged rows.

    Padding rather than dropping is required because callers gather by row (information set) and index
    by column (action); a shifted row would pair an action with the wrong strategy.
    """
    width = int(max(tree.infoset_actions))
    matrix = np.zeros((tree.n_infosets, width))
    for index, row in enumerate(rows):
        matrix[index, : row.shape[0]] = row
    return matrix


def _actions_per_infoset(tree: GameTree) -> list[list[str]]:
    labels: list[list[str]] = [[] for _ in range(tree.n_infosets)]
    for node in tree.nodes:
        if isinstance(node, DecisionNode):
            for infoset in np.unique(node.infosets):
                labels[int(infoset)] = list(node.actions)
    return labels


def solve(tree: GameTree, iterations: int = 10_000, *, plus: bool = False, measure_every: int = 0) -> SolveResult:
    """Functional entry point used by lessons, tests and ``tools/run_solver.py``."""
    return CFRSolver(tree, plus=plus).run(iterations, measure_every=measure_every)
