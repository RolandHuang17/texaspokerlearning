"""Game trees in vector form: the representation the whole solver shares.

A two-player extensive game with chance is stored as

* a list of **deals** -- every possible assignment of hidden and public cards, each with its prior
  probability;
* a **public tree** of decision and terminal nodes. A decision node knows which player acts, its
  action labels, and, for every deal, which information set that deal puts the acting player in;
* terminal nodes carry a payoff vector over deals, in chips, for player 0 (player 1 gets the
  negative, because every game here is zero-sum).

Why vector form instead of recursing over deals: with a tree of ~40 public nodes and ~360 deals,
per-deal recursion costs ~14,000 Python operations per iteration and Leduc becomes a ten-minute run.
Carrying a vector over deals costs ~40 numpy operations per iteration instead, so the same solve
finishes in seconds. The payoff is real and the cost is honesty about indexing: a deal that cannot
reach a node is handled by its zero reach, never by a special case.

An information set is ``(node, acting player's private cards)`` -- the public part is already encoded
by the node, which is exactly why a learner can see that "I know the board, I don't know your hand"
and nothing more.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

import numpy as np

from ..errors import InvariantError

#: Player index used for terminal-node markers. A terminal node has no acting player.
TERMINAL = -1


@dataclass(slots=True)
class DecisionNode:
    node_id: int
    player: int
    actions: tuple[str, ...]
    children: tuple[int, ...]
    #: Information set index per deal. Same index for deals that differ only in the opponent's cards.
    infosets: np.ndarray = field(default_factory=lambda: np.zeros(0, dtype=np.int64))

    @property
    def is_terminal(self) -> bool:
        return False


@dataclass(slots=True)
class TerminalNode:
    node_id: int
    actions: tuple[str, ...]
    #: Chips won by player 0 for each deal. Player 1's payoff is the negative.
    payoff: np.ndarray = field(default_factory=lambda: np.zeros(0, dtype=np.float64))

    @property
    def is_terminal(self) -> bool:
        return True


Node = DecisionNode | TerminalNode


@dataclass(slots=True)
class GameTree:
    """An assembled, index-consistent game. Build one with :mod:`pokergto.solver.games`."""

    name: str
    description: dict[str, str]
    nodes: list[Node]
    root: int
    deal_prob: np.ndarray
    infoset_player: np.ndarray
    infoset_actions: np.ndarray
    #: For reporting: the acting player's private key per (infoset), as a stable string.
    infoset_labels: list[str] = field(default_factory=list)

    @property
    def n_deals(self) -> int:
        return int(self.deal_prob.shape[0])

    @property
    def n_infosets(self) -> int:
        return int(self.infoset_player.shape[0])

    def validate(self) -> None:
        """Structural checks. Cheap to run, and every one of them has a failure mode that would
        otherwise show up as a solver converging to a wrong answer.
        """
        if abs(float(self.deal_prob.sum()) - 1.0) > 1e-9:
            raise InvariantError(
                f"{self.name}: deal probabilities sum to {self.deal_prob.sum()}, not 1"
            )
        if np.any(self.deal_prob < 0):
            raise InvariantError(f"{self.name}: negative deal probability")
        for node in self.nodes:
            if isinstance(node, TerminalNode):
                if node.payoff.shape != (self.n_deals,):
                    raise InvariantError(
                        f"{self.name}: terminal {node.node_id} payoff shape {node.payoff.shape}"
                    )
                continue
            if node.infosets.shape != (self.n_deals,):
                raise InvariantError(
                    f"{self.name}: decision {node.node_id} infoset shape {node.infosets.shape}"
                )
            if len(node.children) != len(node.actions):
                raise InvariantError(f"{self.name}: node {node.node_id} actions/children mismatch")
            if np.any(node.infosets < 0) or np.any(node.infosets >= self.n_infosets):
                raise InvariantError(
                    f"{self.name}: node {node.node_id} has an out-of-range infoset id"
                )
            acting = self.infoset_player[node.infosets]
            if not np.all(acting == node.player):
                raise InvariantError(
                    f"{self.name}: node {node.node_id} says player {node.player} acts, but its "
                    "information sets are registered to "
                    f"{sorted(set(int(p) for p in np.unique(acting)))}"
                )
        for infoset, count in enumerate(self.infoset_actions):
            if count < 2:
                raise InvariantError(
                    f"infoset {infoset} has {count} actions; a decision needs at least two"
                )
        self._check_reachability()

    def _check_reachability(self) -> None:
        seen = set[int]()
        stack = [self.root]
        while stack:
            node_id = stack.pop()
            if node_id in seen:
                continue
            seen.add(node_id)
            node = self.nodes[node_id]
            if isinstance(node, TerminalNode):
                continue
            stack.extend(node.children)
        if len(seen) != len(self.nodes):
            unreachable = sorted(set(range(len(self.nodes))) - seen)
            raise InvariantError(f"{self.name}: nodes {unreachable} are unreachable from the root")

    def infoset_of(self, node_id: int, deal: int) -> int:
        node = self.nodes[node_id]
        if isinstance(node, TerminalNode):
            raise InvariantError("terminal nodes have no information set")
        return int(node.infosets[deal])

    def decision_nodes(self) -> list[DecisionNode]:
        return [node for node in self.nodes if isinstance(node, DecisionNode)]

    def summary(self) -> dict[str, int]:
        return {
            "deals": self.n_deals,
            "nodes": len(self.nodes),
            "decision_nodes": len(self.decision_nodes()),
            "terminal_nodes": len(self.nodes) - len(self.decision_nodes()),
            "infosets": self.n_infosets,
        }


class TreeBuilder:
    """Incremental tree construction with automatic information-set numbering.

    The numbering rule is the one place a bug can silently merge two decisions that should be
    separate, so it lives here, once, keyed on ``(node, player, private label)``.
    """

    def __init__(
        self,
        name: str,
        description: dict[str, str],
        deals: Sequence[tuple[str, ...]],
        deal_prob: np.ndarray | None = None,
    ) -> None:
        self.name = name
        self.description = description
        #: Each deal is a tuple of stable labels: private cards for each player, then public cards.
        self.deals = list(deals)
        self.n_deals = len(self.deals)
        self.deal_prob = (
            np.full(self.n_deals, 1.0 / self.n_deals, dtype=np.float64)
            if deal_prob is None
            else np.asarray(deal_prob, dtype=np.float64)
        )
        self.nodes: list[Node] = []
        self._infoset_ids: dict[tuple[int, int, str], int] = {}
        self._infoset_player: list[int] = []
        self._infoset_actions: list[int] = []
        self._infoset_labels: list[str] = []

    def new_node_id(self) -> int:
        self.nodes.append(None)  # type: ignore[arg-type]
        return len(self.nodes) - 1

    def add_terminal(self, node_id: int, payoff: Sequence[float] | np.ndarray) -> None:
        self.nodes[node_id] = TerminalNode(
            node_id=node_id, actions=(), payoff=np.asarray(payoff, dtype=np.float64)
        )

    def add_decision(
        self,
        node_id: int,
        player: int,
        actions: Sequence[str],
        children: Sequence[int],
        private_key: Sequence[str],
    ) -> DecisionNode:
        """Register a decision node. ``private_key[d]`` is the acting player's own information for
        deal ``d`` -- never the opponent's, never anything public.
        """
        if len(actions) != len(children):
            raise InvariantError("one child per action")
        infosets = np.zeros(self.n_deals, dtype=np.int64)
        for index, key in enumerate(private_key):
            identity = (node_id, player, key)
            infoset = self._infoset_ids.get(identity)
            if infoset is None:
                infoset = len(self._infoset_ids)
                self._infoset_ids[identity] = infoset
                self._infoset_player.append(player)
                self._infoset_actions.append(len(actions))
                self._infoset_labels.append(f"{node_id}:{player}:{key}")
            elif self._infoset_actions[infoset] != len(actions):
                raise InvariantError(
                    f"infoset {infoset} ({self._infoset_labels[infoset]}) registered with "
                    f"{self._infoset_actions[infoset]} actions, now asked for {len(actions)}"
                )
            infosets[index] = infoset
        node = DecisionNode(
            node_id=node_id,
            player=player,
            actions=tuple(actions),
            children=tuple(int(child) for child in children),
            infosets=infosets,
        )
        self.nodes[node_id] = node
        return node

    def build(self, root: int) -> GameTree:
        tree = GameTree(
            name=self.name,
            description=self.description,
            nodes=self.nodes,
            root=root,
            deal_prob=self.deal_prob,
            infoset_player=np.asarray(self._infoset_player, dtype=np.int64),
            infoset_actions=np.asarray(self._infoset_actions, dtype=np.int64),
            infoset_labels=self._infoset_labels,
        )
        tree.validate()
        return tree


def pad_strategy(rows: Sequence[np.ndarray], tree: GameTree) -> np.ndarray:
    """Stack per-infoset strategies into ``(n_infosets, max_actions)``, zero-padding ragged rows.

    Padding rather than dropping is required because every consumer gathers by row (information set) and
    indexes by column (action); a shifted row would pair an action with the wrong strategy. The width is
    the tree's maximum, so a row that is shorter than the widest node's action list is not "actions with
    probability zero" -- :mod:`pokergto.solver.vector` fills its own padding with an even split precisely
    so that a read which forgot to mask cannot turn "no such action" into "this action is never played".
    """
    width = int(max(tree.infoset_actions))
    matrix = np.zeros((tree.n_infosets, width))
    for index, row in enumerate(rows):
        matrix[index, : row.shape[0]] = row
    return matrix


def regret_matching(regrets: np.ndarray) -> np.ndarray:
    """Current strategy from cumulative regrets: positive part, normalised; uniform if all zero.

    This is the entire idea of CFR, in five lines, which is why lesson 08-02 asks the learner to
    write it before the lesson shows it.
    """
    positive = np.clip(regrets, 0.0, None)
    totals = positive.sum(axis=1, keepdims=True)
    where = totals > 0.0
    uniform = np.full_like(regrets, 1.0 / max(regrets.shape[1], 1))
    return np.where(where, positive / np.where(where, totals, 1.0), uniform)
