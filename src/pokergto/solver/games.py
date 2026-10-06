"""Game definitions. Every game here is small enough to solve on a laptop and explicit enough to
check by hand, which is the entire requirement (ADR-0002).

Shipped in this milestone:

* :func:`kuhn` -- three cards, one street, no raises, fully analytic. Its game value is ``-ante/18``
  and its equilibria form a one-parameter family, so it is the solver's acceptance test.
* :func:`one_street_bluff_catcher` -- one street, one bet size, and an equilibrium that *is* the
  algebra of chapter 02: the defender's frequency equals ``pot/(pot+bet)`` and the bluff share of the
  betting range equals ``bet/(pot+2bet)``. CFR must reproduce both. If it does not, either the math
  module or the solver is wrong, and the test names which.

* :func:`leduc` -- six cards, two betting streets, one bet and one raise per street. The benchmark game of
  the CFR literature, and the first game here too big for the per-deal recursion: its anchor is not a
  closed form (there isn't one) but exploitability, the value bracket that exact best responses imply, and
  dominance facts that must survive into the solved strategy.

A two-street "protection" toy is the remaining entry in `adr/0002`'s table and it is deliberately
**absent** rather than half-built: a subtly mis-specified game converges happily to the equilibrium of a
game that is not the one documented, which is precisely the failure ADR-0002 exists to prevent. Shipping it
means writing its gate in the same pull request.

**Utility convention, fixed once.** Terminal payoffs are net chips from the start of the hand, with
each player's ante already committed, and player 1 always receives the negative of player 0's number.
The absolute frame matters: several poker derivations quietly switch to "relative to folding" at each
decision, which is fine for a single decision and wrong across an extensive game, because folding at
different nodes has different absolute value. With symmetric prior stakes the two frames produce the
same indifference conditions, and :mod:`pokergto.solver.proofs` checks that they agree here.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from itertools import permutations

import numpy as np

from ..cards import Card
from ..errors import InputError, InvariantError
from ..evaluator import best_score_three
from .tree import GameTree, TreeBuilder

DEFAULT_ANTE = 1.0

#: A decision reached less often than this is off the equilibrium path, and a solved strategy says
#: nothing trustworthy about behaviour there. One hand in a hundred thousand is a stated convention, not a
#: measurement: the point is that the claim below is only made about decisions a player actually faces.
#: See :func:`pokergto.solver.exploitability.infoset_reach` for why exploitability cannot see the rest.
REACH_FLOOR = 1e-5


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
        node_p1_facing_bet,
        1,
        ("fold", "call"),
        (terminal_p1_folds, terminal_p1_calls),
        [cards[int(rank)] for rank in villain],
    )
    builder.add_decision(
        node_p0_facing_bet,
        0,
        ("fold", "call"),
        (terminal_p0_folds, terminal_p0_calls),
        [cards[int(rank)] for rank in hero],
    )
    builder.add_decision(
        node_p1_after_check,
        1,
        ("check", "bet"),
        (terminal_check_check, node_p0_facing_bet),
        [cards[int(rank)] for rank in villain],
    )
    builder.add_decision(
        node_p0,
        0,
        ("check", "bet"),
        (node_p1_after_check, node_p1_facing_bet),
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

    builder.add_decision(
        node_p1, 1, ("fold", "call"), (terminal_fold, terminal_call), ["catcher", "catcher"]
    )
    builder.add_decision(node_p0, 0, ("check", "bet"), (terminal_showdown, node_p1), ["nut", "air"])
    return builder.build(node_p0)


#: Leduc's deck: three ranks in two suits, six cards, four of which get dealt.
LEDUC_RANKS = ("J", "Q", "K")
LEDUC_SUITS = ("s", "h")


def leduc(ante: float = 1.0, bet_flop: float = 2.0, bet_turn: float = 4.0, cap: int = 2) -> GameTree:
    """Leduc hold'em: six cards, two betting streets, one bet and one raise per street.

    **The rules, stated completely, because a subtly wrong tree converges just as happily as a right one
    -- to the equilibrium of a game nobody documented.**

    * Deck: ``J``, ``Q``, ``K`` in two suits. Each player is dealt one private card and the board carries
      two, one revealed before each street. Two cards stay unseen.
    * Both players ante ``ante``, so ``2 * ante`` is dead money before anyone looks at a card.
    * Street one bets ``bet_flop``, street two bets ``bet_turn``. Player 0 acts first on both streets.
    * At most ``cap`` aggressive actions per street, where a bet and a raise each count and a check and a
      call do not. With ``cap = 2`` a street can take exactly these sequences::

            check-check
            check-bet-fold    check-bet-call    check-bet-raise-fold    check-bet-raise-call
            bet-fold          bet-call          bet-raise-fold          bet-raise-call

    * A fold pays what the folder committed to the other player. At showdown both players have committed
      the same amount and the winner takes it; equal scores split, which is a reachable outcome here
      rather than a defensive branch -- on board ``Js Jh`` with ``Qh`` for the player holding ``Qd``,
      both hold jack-pairs with a queen kicker.

    **What is provable about it.** Leduc has no closed-form equilibrium to check against, so the gates
    registered in :mod:`pokergto.solver.proofs` are the ones that do not need one: exploitability below
    the threshold, the value bracket ``-BR(1) <= v <= BR(0)`` that follows from the same exact best
    responses, dominance facts that must survive into the solved strategy (nobody folds a hand beating
    everything the opponent could hold), and byte-identical reruns. No published Leduc strategy table or
    game value is copied into this repository and no lesson cites one; the numbers come from solving
    *this* tree, whose exact rules are above.

    The tree is 360 deals, 85 public nodes -- 36 decision, 49 terminal -- and 3,780 information sets, all
    of them counted from the built object rather than derived by hand. It is also the first game here too
    large for the per-deal recursion in :mod:`pokergto.solver.cfr` to solve inside a minute, which is what
    :mod:`pokergto.solver.vector` is for -- and why that file has to clear these same gates before it is
    allowed to write artifacts.
    """
    if ante <= 0:
        raise InputError("ante must be positive")
    if bet_flop <= 0 or bet_turn <= 0:
        raise InputError("bet sizes must be positive")
    if cap < 1:
        raise InputError("cap must allow at least one aggressive action")

    hands = [Card.parse(f"{rank}{suit}") for rank in LEDUC_RANKS for suit in LEDUC_SUITS]
    codes = [card.code for card in hands]
    # One deal per ordered assignment: player 0's card, player 1's card, the flop card, the turn card.
    # The turn is part of the deal from the start even though nobody sees it on street one; deals that
    # differ only in it share an information set there, which is how the hidden card becomes a probability
    # rather than a special case.
    positions = list(permutations(range(len(hands)), 4))
    deals: list[tuple[str, str, str, str]] = [tuple(codes[i] for i in position) for position in positions]  # type: ignore[misc]
    n = len(deals)

    winner = np.zeros(n, dtype=np.float64)
    for row, (first, second, flop, turn) in enumerate(positions):
        board = (hands[flop], hands[turn])
        score_first = best_score_three((hands[first],), board)
        score_second = best_score_three((hands[second],), board)
        winner[row] = float(np.sign(score_first - score_second))

    builder = TreeBuilder(
        "leduc",
        {
            "zh": "Leduc 扑克：六张牌、两条街、每街最多一注一加注。CFR 文献的基准博弈，规则在本仓库完整写出，"
            "不靠引用外部定义。",
            "en": "Leduc hold'em: six cards, two streets, one bet and one raise per street. The benchmark "
            "game of the CFR literature, specified here in full rather than by reference.",
        },
        deals,
    )

    def visible(actor: int, depth: int) -> list[str]:
        """The information-set key: the actor's own card plus the board cards already revealed.

        Our public nodes index *betting sequences* only, not which cards came up, so the seen board has to
        be part of the key. Two deals that differ only in an unseen card therefore collapse into one
        information set, which is the whole point.
        """
        return [f"{deal[actor]}|{''.join(deal[2:2 + depth])}" for deal in deals]

    def terminal_fold(folder: int, committed: tuple[float, float]) -> int:
        node_id = builder.new_node_id()
        amount = committed[folder]
        builder.add_terminal(node_id, np.full(n, -amount if folder == 0 else amount))
        return node_id

    def terminal_showdown(committed: tuple[float, float]) -> int:
        node_id = builder.new_node_id()
        amount = max(committed)
        if abs(committed[0] - committed[1]) > 1e-12:
            raise InvariantError("a showdown needs equal commitments")
        builder.add_terminal(node_id, winner * amount)
        return node_id

    def street_end(depth: int, committed: tuple[float, float]) -> int:
        if depth == 2:
            return terminal_showdown(committed)
        return betting(2, 0, committed, 0, False, 0)

    def betting(
        depth: int,
        actor: int,
        committed: tuple[float, float],
        aggressive: int,
        facing: bool,
        actions: int,
    ) -> int:
        """One public decision node. Children are built first so ids are assigned bottom-up."""
        stake = bet_flop if depth == 1 else bet_turn
        legal: tuple[str, ...] = (
            (("fold", "call", "raise") if aggressive < cap else ("fold", "call"))
            if facing
            else ("check", "bet")
        )
        children: list[int] = []
        for action in legal:
            if action == "fold":
                children.append(terminal_fold(actor, committed))
                continue
            if action == "call":
                level = max(committed)
                children.append(street_end(depth, (level, level)))
                continue
            if action == "check":
                # The second check closes the street; the first one passes the action over.
                children.append(
                    street_end(depth, committed) if actions else betting(
                        depth, 1 - actor, committed, aggressive, False, 1
                    )
                )
                continue
            raised_to = committed[1 - actor] + stake
            following = (raised_to, committed[1]) if actor == 0 else (committed[0], raised_to)
            children.append(
                betting(depth, 1 - actor, following, aggressive + 1, True, actions + 1)
            )

        node_id = builder.new_node_id()
        builder.add_decision(node_id, actor, legal, children, visible(actor, depth))
        return node_id

    root = betting(1, 0, (ante, ante), 0, False, 0)
    return builder.build(root)


@dataclass(frozen=True, slots=True)
class LeducDominance:
    """Information sets whose acting hand is decided before the opponent ever acts.

    ``nut`` holds the labels where the actor beats **every** private card the opponent could hold on that
    board; ``worst`` holds the labels where the actor loses to every one of them. Both are statements
    about the three cards on the table, so they are checkable without solving anything -- which is exactly
    why they make good gates: a solver that folds the nuts or calls with a guaranteed loser has a sign
    error somewhere in the payoff bookkeeping, and no amount of convergence evidence will show it.
    """

    nut: tuple[str, ...]
    worst: tuple[str, ...]

    @property
    def total(self) -> int:
        return len(self.nut) + len(self.worst)


def leduc_dominance(tree: GameTree) -> LeducDominance:
    """Classify a :func:`leduc` tree's information sets as strictly-best or strictly-worst.

    Reads the labels :func:`leduc` writes (``node:player:private|board``), so it is coupled to that
    format by construction -- it belongs next to the builder for that reason. Only the turn street is
    classified: on the flop street the second board card has not been revealed, so no hand there is decided
    and any claim would be about a hand the player does not hold yet.
    """
    hands = [Card.parse(f"{rank}{suit}") for rank in LEDUC_RANKS for suit in LEDUC_SUITS]
    nut: list[str] = []
    worst: list[str] = []
    for label in tree.infoset_labels:
        _, _, key = label.split(":", 2)
        private, seen = key.split("|")
        if len(seen) != 4:
            continue
        holder = Card.parse(private)
        board = (Card.parse(seen[:2]), Card.parse(seen[2:]))
        own = best_score_three((holder,), board)
        others = [
            best_score_three((candidate,), board)
            for candidate in hands
            if candidate != holder and candidate not in board
        ]
        if not others:
            continue
        if own > max(others):
            nut.append(label)
        elif own < min(others):
            worst.append(label)
    return LeducDominance(nut=tuple(nut), worst=tuple(worst))


GAME_BUILDERS: dict[str, tuple[str, Sequence[str]]] = {
    "kuhn": ("kuhn", ("ante",)),
    "toy_1street": ("one_street_bluff_catcher", ("pot", "bet_size")),
    "leduc": ("leduc", ("ante", "bet_flop", "bet_turn", "cap")),
}
