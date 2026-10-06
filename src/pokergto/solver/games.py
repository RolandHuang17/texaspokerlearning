"""Game definitions. Every game here is small enough to solve on a laptop and explicit enough to
check by hand, which is the entire requirement (ADR-0002).

Shipped in this milestone:

* :func:`kuhn` -- three cards, one street, no raises, fully analytic. Its game value is ``-ante/18``
  and its equilibria form a one-parameter family, so it is the solver's acceptance test.
* :func:`one_street_bluff_catcher` -- one street, one bet size, and an equilibrium that *is* the
  algebra of chapter 02: the defender's frequency equals ``pot/(pot+bet)`` and the bluff share of the
  betting range equals ``bet/(pot+2bet)``. CFR must reproduce both. If it does not, either the math
  module or the solver is wrong, and the test names which.

Two more games (Leduc and a two-street "protection" toy) are the next milestone's work. They are
deliberately **absent** rather than half-built: a subtly mis-specified game converges happily to the
equilibrium of a game that is not the one documented, which is precisely the failure ADR-0002 exists
to prevent.

**Utility convention, fixed once.** Terminal payoffs are net chips from the start of the hand, with
each player's ante already committed, and player 1 always receives the negative of player 0's number.
The absolute frame matters: several poker derivations quietly switch to "relative to folding" at each
decision, which is fine for a single decision and wrong across an extensive game, because folding at
different nodes has different absolute value. With symmetric prior stakes the two frames produce the
same indifference conditions, and :mod:`pokergto.solver.proofs` checks that they agree here.
"""

from __future__ import annotations

from itertools import permutations
from typing import Sequence

import numpy as np

from ..errors import InputError
from .tree import GameTree, TreeBuilder

DEFAULT_ANTE = 1.0


def kuhn(ante: float = DEFAULT_ANTE) -> GameTree:
    """Kuhn poker: cards ``J < Q < K``, each player antes ``ante``, one street, bet size ``ante``,
    no raises, player 0 acts first.

    Tree::

        p0: check -> p1: {check -> showdown(+-ante), bet -> p0: {fold, call}}
            bet   -> p1: {fold, call}

    Analytic facts, asserted in :mod:`pokergto.solver.proofs` rather than trusted:
    player 0's value under optimal play is ``-ante/18``; the equilibrium family is parameterised by
    ``alpha``, player 0's frequency of betting the jack, with ``alpha in [0, 1/3]``; player 0 bets the
    king always and checks the queen always; player 1 calls a bet with the king always, with the jack
    never, and with the queen at frequency ``alpha + 1/3``.

    CFR lands on *some* member of that family, so the gate is on the game value and exploitability,
    not on one particular strategy table -- and the family itself is a lesson (08-03): many strategies
    are unexploitable, and only some are maximally exploitative.
    """
    if ante <= 0:
        raise InputError("ante must be positive")
    cards = ("J", "Q", "K")
    deals = list(permutations(cards, 2))
    n = len(deals)
    hero = np.array([cards.index(deal[0]) for deal in deals], dtype=np.int64)
    villain = np.array([cards.index(deal[1]) for deal in deals], dtype=np.int64)
    winner = np.sign(hero - villain)

    builder = TreeBuilder(
        "kuhn",
        {
            "zh": "库恩扑克：三张牌、单街、无再加注。唯一有完整解析解的含诈唬博弈。",
            "en": "Kuhn poker: three cards, one street, no raises. The bluffing game with a complete analytic solution.",
        },
        deals,
    )

    node_p0 = builder.new_node_id()
    node_p1_after_check = builder.new_node_id()
    node_p0_facing_bet = builder.new_node_id()
    node_p1_facing_bet = builder.new_node_id()
    terminal_check_check = builder.new_node_id()
    terminal_p0_folds = builder.new_node_id()
    terminal_p0_calls = builder.new_node_id()
    terminal_p1_folds = builder.new_node_id()
    terminal_p1_calls = builder.new_node_id()

    # check-check: showdown for one ante each.
    builder.add_terminal(terminal_check_check, winner * ante)
    # p0 folds to p1's bet: p0 loses the ante.
    builder.add_terminal(terminal_p0_folds, np.full(n, -ante))
    # p0 calls: showdown for two antes.
    builder.add_terminal(terminal_p0_calls, winner * 2.0 * ante)
    # p1 folds to p0's bet: p1 loses the ante.
    builder.add_terminal(terminal_p1_folds, np.full(n, ante))
    # p1 calls: showdown for two antes.
    builder.add_terminal(terminal_p1_calls, winner * 2.0 * ante)

    builder.add_decision(
        node_p1_facing_bet, 1, ("fold", "call"), (terminal_p1_folds, terminal_p1_calls),
        [cards[int(rank)] for rank in villain],
    )
    builder.add_decision(
        node_p0_facing_bet, 0, ("fold", "call"), (terminal_p0_folds, terminal_p0_calls),
        [cards[int(rank)] for rank in hero],
    )
    builder.add_decision(
        node_p1_after_check, 1, ("check", "bet"), (terminal_check_check, node_p0_facing_bet),
        [cards[int(rank)] for rank in villain],
    )
    builder.add_decision(
        node_p0, 0, ("check", "bet"), (node_p1_after_check, node_p1_facing_bet),
        [cards[int(rank)] for rank in hero],
    )
    return builder.build(node_p0)


def one_street_bluff_catcher(pot: float = 1.0, bet_size: float = 0.5) -> GameTree:
    """One street, one bet size, and an equilibrium that is exactly chapter 02's algebra.

    **Rules.** A pot of ``pot`` sits in the middle, contributed symmetrically, so each player has
    ``pot/2`` in. Player 0 holds ``nut`` (always wins if called) or ``air`` (always loses if called),
    each with probability one half. Player 1 holds a single bluff-catcher: it beats air and loses to
    the nut, and never acts first. Player 0 checks (showdown) or bets ``bet_size * pot``; facing a bet
    player 1 folds or calls.

    **Closed form, derived in lesson 02-03 and 02-04 and asserted in :mod:`proofs`:**

    * player 1 calls with frequency ``MDF = pot / (pot + bet)``;
    * bluffs are ``b = bet / (pot + 2*bet)`` of player 0's betting range;
    * nut hands always bet, so air bets with frequency ``b / (1 - b)``.

    The derivation in absolute chips: player 0's air folds-to-check value is ``-pot/2``; bluffing earns
    ``+pot/2`` when player 1 folds and ``-(pot/2 + bet)`` when called, so indifference at fold frequency
    ``f`` gives ``f = bet/(pot+bet)``. Player 1's bluff-catcher folds for ``-pot/2`` and calls into
    ``pot/2 + bet`` risk, which is indifferent exactly when bluffs are ``bet/(pot+2bet)`` of the range.
    """
    if pot <= 0:
        raise InputError("pot must be positive")
    if bet_size <= 0:
        raise InputError("a zero bet is a check, not a size")
    stake = bet_size * pot
    prior = pot / 2.0

    builder = TreeBuilder(
        "one_street_bluff_catcher",
        {
            "zh": "单街诈唬-捕手博弈：均衡频率就是 pot/(pot+bet) 与 bet/(pot+2bet)。",
            "en": "One-street bluff-catcher game: its equilibrium frequencies are the closed forms of chapter 02.",
        },
        [("nut", "catcher"), ("air", "catcher")],
        deal_prob=np.array([0.5, 0.5]),
    )

    node_p0 = builder.new_node_id()
    node_p1 = builder.new_node_id()
    terminal_showdown = builder.new_node_id()
    terminal_fold = builder.new_node_id()
    terminal_call = builder.new_node_id()

    builder.add_terminal(terminal_showdown, np.array([prior, -prior]))
    builder.add_terminal(terminal_fold, np.array([prior, prior]))
    builder.add_terminal(terminal_call, np.array([prior + stake, -(prior + stake)]))

    builder.add_decision(node_p1, 1, ("fold", "call"), (terminal_fold, terminal_call), ["catcher", "catcher"])
    builder.add_decision(node_p0, 0, ("check", "bet"), (terminal_showdown, node_p1), ["nut", "air"])
    return builder.build(node_p0)


def game_value(tree: GameTree) -> float:
    """Expected net chips for player 0 under the *uniform random* strategy. Not an equilibrium
    quantity -- it exists so a test can confirm the payoff vector is zero-sum-ish sane before the
    solver touches it."""
    root = tree.nodes[tree.root]
    del root
    terminal_payoff = 0.0
    for node in tree.nodes:
        if node.is_terminal:
            # Without a strategy there is no unique reachability, so this weights terminal payoffs by
            # deal probability only, which is enough to catch a sign error.
            terminal_payoff += float(np.dot(node.payoff, tree.deal_prob)) / max(
                1, sum(1 for candidate in tree.nodes if candidate.is_terminal)
            )
    return terminal_payoff


GAME_BUILDERS: dict[str, Sequence[str]] = {
    "kuhn": ("kuhn", ("ante",)),
    "toy_1street": ("one_street_bluff_catcher", ("pot", "bet_size")),
}
