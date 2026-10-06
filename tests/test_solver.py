"""Solver correctness against anchors the solver itself cannot influence.

This file is how ADR-0002 ("solver claims are gated by proof") is enforced in code. Three independent
mechanisms, each with a distinct failure it catches:

1. **Analytic value.** Kuhn's game value is ``-1/18`` and its equilibria form a one-parameter family.
   The family check is deliberately a *membership* test: an earlier draft of this repository asserted
   "always open a bet with the king", which is an equilibrium selection rather than a necessity, and
   our own CFR+ run found a legitimate equilibrium near 64% that would have failed it. A test that
   encodes a wrong theory cannot catch a wrong solver.
2. **Closed-form cross-validation.** The one-street game's equilibrium *is* chapter 02's algebra: the
   defense frequency equals ``pot/(pot+bet)``, the bluff share equals ``bet/(pot+2bet)``, and the game
   value equals ``pot*bet/(2(pot+bet))``. If either the math module or the solver is wrong, this fails.
3. **Property tests.** Best response against brute-force enumeration over pure strategies; the
   definition ``exploitability = (BR(0)+BR(1))/2``; regret matching's normalisation; determinism at a
   fixed iteration count.

Two bugs found in this repository during development are named in comments where they would be caught.
Both were silent: a squashed reach probability converged to exploitability ~0.89 and value +0.57 while
looking stable, and applying regret updates at the opponent's information sets kept Kuhn away from
its analytic value forever.
"""

from __future__ import annotations

import itertools
from collections import Counter
from fractions import Fraction

import numpy as np
import pytest

from pokergto.artifacts import GEN_DIR, read_artifact
from pokergto.errors import InvariantError
from pokergto.odds import bluff_fraction_at_indifference, minimum_defense_frequency
from pokergto.solver import proofs
from pokergto.solver.cfr import CFRSolver, solve
from pokergto.solver.exploitability import (
    best_response_value,
    expected_value,
    exploitability,
    infoset_reach,
)
from pokergto.solver.games import (
    REACH_FLOOR,
    kuhn,
    leduc,
    leduc_dominance,
    one_street_bluff_catcher,
)
from pokergto.solver.proofs import KUHN, PUBLISHED_PROOFS, entry_for, verify
from pokergto.solver.tree import (
    DecisionNode,
    GameTree,
    TreeBuilder,
    pad_strategy,
    regret_matching,
)
from pokergto.solver.vector import solve_vector

pytestmark = pytest.mark.solver


def _purify(base: np.ndarray, infosets: list[int], choices: tuple[int, ...]) -> np.ndarray:
    """Copy ``base`` with the given information sets forced to pure actions."""
    matrix = base.copy()
    for infoset, choice in zip(infosets, choices, strict=True):
        matrix[infoset] = 0.0
        matrix[infoset][choice] = 1.0
    return matrix


def _kuhn_reference_strategy(tree: GameTree) -> np.ndarray:
    """The textbook Kuhn profile at ``alpha = 1/3``, as a strategy matrix.

    Not used as an oracle for convergence -- it is used as a fixed opponent against which best
    responses are computed and then brute-forced, which needs no theory at all.
    """
    labels = {label: index for index, label in enumerate(tree.infoset_labels)}
    alpha = float(Fraction(1, 3))
    matrix = np.zeros((tree.n_infosets, 2))
    profile = {
        "0:0:J": (1 - alpha, alpha),
        "0:0:Q": (1.0, 0.0),
        "0:0:K": (0.0, 1.0),
        "2:0:J": (1.0, 0.0),
        "2:0:Q": (float(Fraction(1, 3)), float(Fraction(2, 3))),
        "2:0:K": (0.0, 1.0),
        "1:1:J": (float(Fraction(2, 3)), float(Fraction(1, 3))),
        "1:1:Q": (1.0, 0.0),
        "1:1:K": (0.0, 1.0),
        "3:1:J": (1.0, 0.0),
        "3:1:Q": (float(Fraction(1, 3)), float(Fraction(2, 3))),
        "3:1:K": (0.0, 1.0),
    }
    for label, row in profile.items():
        matrix[labels[label]] = row
    return matrix


# --- structure ------------------------------------------------------------------------


def test_kuhn_tree_has_the_canonical_shape() -> None:
    summary = kuhn().summary()
    assert summary == {
        "deals": 6,
        "nodes": 9,
        "decision_nodes": 4,
        "terminal_nodes": 5,
        "infosets": 12,
    }


def test_every_registered_game_has_normalised_chance_weights() -> None:
    for name, entry in PUBLISHED_PROOFS.items():
        tree = entry.build()
        assert abs(float(tree.deal_prob.sum()) - 1.0) < 1e-12, name


def test_two_nodes_sharing_a_private_key_stay_two_information_sets() -> None:
    """The silent-merge guard.

    An information set is ``(node, private)``. If a builder ever collapsed two decision points that
    share a private key, the solver would converge happily on a game with fewer decisions than
    documented -- which is to say, on a different game.
    """
    builder = TreeBuilder("probe", {"zh": "probe", "en": "probe"}, [("A",), ("B",)])
    terminal = builder.new_node_id()
    builder.add_terminal(terminal, [1.0, -1.0])
    first = builder.new_node_id()
    second = builder.new_node_id()
    builder.add_decision(second, 0, ("x", "y"), (terminal, terminal), ["A", "B"])
    builder.add_decision(first, 0, ("x", "y"), (terminal, second), ["A", "B"])
    tree = builder.build(first)
    assert tree.n_infosets == 4


def test_builder_rejects_conflicting_action_counts_for_one_information_set() -> None:
    builder = TreeBuilder("probe", {"zh": "", "en": ""}, [("A",)])
    terminal = builder.new_node_id()
    builder.add_terminal(terminal, [1.0])
    node = builder.new_node_id()
    builder.add_decision(node, 0, ("x", "y"), (terminal, terminal), ["A"])
    with pytest.raises(InvariantError):
        builder.add_decision(node, 0, ("x", "y", "z"), (terminal, terminal, terminal), ["A"])


def test_regret_matching_positive_part_and_uniform_fallback() -> None:
    assert np.allclose(regret_matching(np.array([[-3.0, 0.0, 5.0]])), [[0.0, 0.0, 1.0]])
    assert np.allclose(regret_matching(np.zeros((1, 4))), np.full((1, 4), 0.25))
    positive = regret_matching(np.array([[1.0, 3.0]]))
    assert abs(float(positive.sum()) - 1.0) < 1e-12


# --- Kuhn against its analytic solution -------------------------------------------------


@pytest.mark.parametrize("plus", [False, True], ids=["cfr", "cfr_plus"])
def test_kuhn_reaches_the_analytic_game_value(plus: bool) -> None:
    result = CFRSolver(kuhn(), plus=plus).run(600)
    assert result.game_value == pytest.approx(-1 / 18, abs=2e-3)
    assert result.exploitability < 5e-2


def test_cfr_plus_is_more_converged_than_cfr_at_the_same_budget() -> None:
    """Only the direction is asserted. A pinned ratio would be measuring a laptop, not game theory."""
    plain = CFRSolver(kuhn(), plus=False).run(200).exploitability
    plus = CFRSolver(kuhn(), plus=True).run(200).exploitability
    assert plus < plain


def test_dominance_holds_and_the_jack_bluff_stays_inside_the_family() -> None:
    tree = kuhn()
    report = CFRSolver(tree, plus=True).run(4000).strategy_report()
    assert report["2:0:K"]["call"] > 0.99
    assert report["3:1:K"]["call"] > 0.99
    assert report["2:0:J"]["call"] < 0.01
    assert report["3:1:J"]["call"] < 0.01
    assert 0.0 - 1e-9 <= report["0:0:J"]["bet"] <= 1 / 3 + 1e-9


def test_the_proof_gate_can_fail() -> None:
    """A gate nobody has seen reject anything is decoration.

    Here a jack-bluff frequency of 0.9 is pushed into the average strategy -- legal as a strategy,
    outside the analytic family ``[0, 1/3]``, so not an equilibrium. The registry must say so.
    """
    tree = kuhn()
    solver = CFRSolver(tree, plus=True)
    result = solver.run(40)
    labels = {label: index for index, label in enumerate(tree.infoset_labels)}
    forced = result.average_strategy[:]
    jack = labels["0:0:J"]
    forced[jack] = np.array([0.1, 0.9])
    result.average_strategy = forced
    records = verify(KUHN, tree, result)
    family = [record for record in records if "jack_bluff_in_family" in str(record["detail"])]
    assert family, "the family assertion is registered"
    assert not family[0]["pass"], "a frequency outside [0, 1/3] must fail the gate"


# --- best response, checked by exhaustion ----------------------------------------------


def test_best_response_equals_brute_force_over_pure_strategies() -> None:
    """An argmax per *deal* instead of per *information set* fails this test.

    That is the classic best-response bug: it answers "how well could a player who sees your cards
    do", which is not a property of your strategy, and it makes every exploitability number look
    smaller than it is.
    """
    tree = kuhn()
    reference = _kuhn_reference_strategy(tree)
    labels = {label: index for index, label in enumerate(tree.infoset_labels)}

    hero = [labels[f"{node}:0:{card}"] for node in (0, 2) for card in "JQK"]
    brute_hero = max(
        expected_value(tree, _purify(reference, hero, choices))
        for choices in itertools.product((0, 1), repeat=len(hero))
    )
    assert best_response_value(tree, reference, 0) == pytest.approx(brute_hero, abs=1e-9)

    villain = [labels[f"{node}:1:{card}"] for node in (1, 3) for card in "JQK"]
    brute_villain = max(
        -expected_value(tree, _purify(reference, villain, choices))
        for choices in itertools.product((0, 1), repeat=len(villain))
    )
    assert best_response_value(tree, reference, 1) == pytest.approx(brute_villain, abs=1e-9)


def test_exploitability_is_half_the_brute_sum_by_definition() -> None:
    tree = kuhn()
    uniform = np.full((tree.n_infosets, 2), 0.5)
    br0 = best_response_value(tree, uniform, 0)
    br1 = best_response_value(tree, uniform, 1)
    assert exploitability(tree, uniform) == pytest.approx((br0 + br1) / 2, abs=1e-12)
    assert br0 + br1 > 0.0, "a uniform strategy is exploitable in both directions"


def test_a_hand_transcribed_profile_is_verified_not_trusted() -> None:
    """The textbook ``alpha = 1/3`` profile is *claimed*; this test is the receipt either way.

    Transcribing an equilibrium from memory or from a book is exactly how a curriculum accumulates a
    confident wrong number, so the profile used above is measured here rather than excused. What the
    measurement says: it is far better than a uniform strategy, but not unexploitable, which is the
    whole reason the repository computes equilibria instead of copying them. Lesson 08-07 cites this.
    """
    tree = kuhn()
    uniform = np.full((tree.n_infosets, 2), 0.5)
    reference_exploitability = exploitability(tree, _kuhn_reference_strategy(tree))
    assert reference_exploitability < exploitability(tree, uniform) * 0.2
    assert reference_exploitability > 0.0


# --- the closed-form loop between chapter 02 and the solver -----------------------------


@pytest.mark.parametrize(
    "bet_size",
    [float(Fraction(1, 4)), float(Fraction(1, 3)), 0.5, 1.0, 2.0],
    ids=["0p25", "0p333", "0p5", "1p0", "2p0"],
)
def test_one_street_game_reproduces_chapter_02_algebra(bet_size: float) -> None:
    tree = one_street_bluff_catcher(pot=1.0, bet_size=bet_size)
    result = CFRSolver(tree, plus=True).run(4000)
    report = result.strategy_report()

    defense = report["1:1:catcher"]["call"]
    assert defense == pytest.approx(float(minimum_defense_frequency(1.0, bet_size)), abs=2.5e-3)

    nut, air = report["0:0:nut"]["bet"], report["0:0:air"]["bet"]
    assert nut == pytest.approx(1.0, abs=2.5e-3), "the nut hand strictly dominates betting"
    bluff_share = air / (nut + air)
    assert bluff_share == pytest.approx(
        float(bluff_fraction_at_indifference(1.0, bet_size)), abs=2.5e-3
    )
    assert result.game_value == pytest.approx(bet_size / (2.0 * (1.0 + bet_size)), abs=2.5e-3)


@pytest.mark.parametrize("game", sorted(PUBLISHED_PROOFS))
def test_committed_artifacts_agree_with_this_file(game: str) -> None:
    """Lessons cite ``data/gen/solver/*.json``; this re-reads them and re-checks their own records.

    Nothing is re-solved, so the test stays fast while still failing when an artifact is stale, when
    its exploitability drifts above the gate, or when the proof entry name no longer matches.
    """
    entry = entry_for(game)
    path = GEN_DIR / "solver" / f"{game}.json"
    if not path.exists():
        pytest.skip(f"{game}: no committed artifact yet (run tools/run_solver.py)")
    artifact = read_artifact(path, schema="solver_run")
    assert artifact["proof_entry"] == game
    assert artifact["algorithm"] == entry.expected_algorithm
    assert float(artifact["exploitability_bb_per_hand"]) <= entry.exploitability_threshold
    assert artifact["determinism_verified"] is True
    failed = [record for record in artifact["checks"] if not record["pass"]]
    assert not failed, failed


def test_solver_is_deterministic_at_a_fixed_iteration_count() -> None:
    """Nothing samples, so the same budget must produce identical bytes.

    This is what makes committing convergence curves meaningful: a rebuild that differs is a code
    change, not a coin flip.
    """
    first = CFRSolver(kuhn(), plus=True).run(120)
    again = CFRSolver(kuhn(), plus=True).run(120)
    assert first.game_value == again.game_value
    assert first.exploitability == again.exploitability
    for row_a, row_b in zip(first.average_strategy, again.average_strategy, strict=True):
        assert np.array_equal(row_a, row_b)


def test_report_shape_is_a_public_surface() -> None:
    """``--report`` output is versioned with the package (CONTRIBUTING.md), so its shape is pinned."""
    tree = kuhn()
    result = solve(tree, 60)
    report = result.strategy_report()
    assert set(report) == set(tree.infoset_labels)
    for label, actions in report.items():
        assert set(actions) <= {"check", "bet", "fold", "call"}, label
        assert abs(sum(actions.values()) - 1.0) < 1e-4, label


def test_decision_nodes_all_register_an_acting_player() -> None:
    """``GameTree.validate`` already checks this; the test exists so a regression names the node."""
    tree = one_street_bluff_catcher(pot=1.0, bet_size=0.5)
    for node in tree.nodes:
        if isinstance(node, DecisionNode):
            assert int(tree.infoset_player[int(node.infosets[0])]) == node.player


# --- Leduc: the two-street family, gated without a closed form -----------------------------

LEDUC_SHAPE = {
    "deals": 360,
    "nodes": 85,
    "decision_nodes": 36,
    "terminal_nodes": 49,
    "infosets": 3780,
}

#: The nine sequences one street of Leduc can take, transcribed from ``games.leduc``'s docstring.
STREET_SEQUENCES = {
    ("check", "check"),
    ("check", "bet", "fold"),
    ("check", "bet", "call"),
    ("check", "bet", "raise", "fold"),
    ("check", "bet", "raise", "call"),
    ("bet", "fold"),
    ("bet", "call"),
    ("bet", "raise", "fold"),
    ("bet", "raise", "call"),
}


def _street_action_sets(tree: GameTree, board_length: int) -> list[tuple[str, ...]]:
    """The legal action sets of every decision node whose acting player sees ``board_length`` cards."""
    found = []
    for node in tree.decision_nodes():
        seen = tree.infoset_labels[int(node.infosets[0])].split("|", 1)[1]
        if len(seen) == board_length:
            found.append(tuple(node.actions))
    return found


def test_leduc_tree_matches_the_shape_its_rules_imply() -> None:
    """A mis-specified game converges just as happily, so the shape is checked against the rules.

    360 deals is ``6 x 5 x 4 x 3``: two private cards and two board cards out of a six-card deck. The
    information-set count is the part worth hand-checking -- 180 on the flop street (six decision nodes,
    each reached by one of six private cards against one of five boards) plus 3,600 on the turn street
    (the same six decision nodes, instantiated once for each of the five ways a flop street can end
    without a fold, against sixty private-and-board combinations).
    """
    assert leduc().summary() == LEDUC_SHAPE


def test_leduc_streets_take_exactly_the_documented_nine_sequences() -> None:
    """The raise cap is a rule, not a mood: each street exposes the same action structure."""
    tree = leduc()
    flop = Counter(_street_action_sets(tree, board_length=2))
    turn = Counter(_street_action_sets(tree, board_length=4))
    assert flop == Counter({("check", "bet"): 2, ("fold", "call", "raise"): 2, ("fold", "call"): 2})
    assert turn == Counter(
        {("check", "bet"): 10, ("fold", "call", "raise"): 10, ("fold", "call"): 10}
    )
    assert len(STREET_SEQUENCES) == 9
    assert sum(1 for sequence in STREET_SEQUENCES if sequence[-1] != "fold") == 5
    # Five fold-free ways to end street one, and the turn tree is built once per each of them.
    assert sum(turn.values()) == 6 * 5


def test_leduc_payoffs_are_pot_conserving() -> None:
    """Every terminal pays one player exactly what the other put in, and never more.

    The absolute frame is the one ``games.py``'s docstring insists on: a terminal number is net chips from
    the start of the hand, so a fold pays the folder's own commitment and a showdown pays the equal amount
    both players reached. A convention that quietly switched to "relative to folding" part-way through the
    tree would still converge, and only bookkeeping checks like this one notice.
    """
    tree = leduc()
    # 1 = ante only, 3 = ante plus one flop bet, 5 = ante plus a flop bet and a raise, 7/9 = those levels
    # plus a turn bet, 11/13 = plus a turn raise. There is no 15, because the cap allows exactly two
    # aggressive actions per street -- which is the number this set is really checking.
    legal = {0.0, 1.0, 3.0, 5.0, 7.0, 9.0, 11.0, 13.0}
    showdowns = 0
    for node in tree.nodes:
        if not node.is_terminal:
            continue
        magnitudes = set(np.round(np.abs(node.payoff), 9))
        assert magnitudes <= legal, f"terminal {node.node_id} pays {sorted(magnitudes)}"
        if len(magnitudes) > 1:
            showdowns += 1
    assert showdowns, "at least one terminal must depend on the cards"


def test_leduc_dominance_holds_where_the_strategy_actually_goes() -> None:
    """The gate, and the reason it is reach-conditioned rather than absolute.

    A solved average strategy is free to misbehave at information sets the equilibrium never reaches:
    nothing in ``BR(0) + BR(1)`` sees them, because arriving there requires the opponent to play a line
    they do not play. Measured on the committed solve the dominated-action frequencies are ``8e-8`` and
    ``1e-7`` at information sets reached at least once in a hundred thousand hands, and as much as ``0.28``
    at ones reached once in a billion. Both halves are in this test deliberately: the second is why the
    first is phrased the way it is, and a lesson that quotes a frequency at an unreachable node is quoting
    noise.
    """
    tree = leduc()
    result = solve_vector(tree, 2_000, plus=True)
    reach = infoset_reach(tree, pad_strategy(result.average_strategy, tree))
    positions = {label: index for index, label in enumerate(tree.infoset_labels)}
    classes = leduc_dominance(tree)
    assert len(classes.nut) == 360
    assert len(classes.worst) == 720

    def worst_frequency(labels: tuple[str, ...], action: str, floor: float) -> float:
        out = 0.0
        for label in labels:
            index = positions[label]
            if reach[index] < floor:
                continue
            choices = result.infoset_actions[index]
            if action in choices:
                out = max(out, float(result.average_strategy[index][choices.index(action)]))
        return out

    assert worst_frequency(classes.nut, "fold", REACH_FLOOR) == pytest.approx(0.0, abs=1e-5)
    assert worst_frequency(classes.worst, "call", REACH_FLOOR) == pytest.approx(0.0, abs=1e-5)
    reached = sum(1 for label in classes.nut if reach[positions[label]] >= REACH_FLOOR)
    assert 0 < reached < len(classes.nut), "the floor must actually exclude something"


def test_leduc_gate_fails_when_the_strategy_folds_the_nuts() -> None:
    """A gate that cannot fail is not a gate."""
    entry = proofs.entry_for("leduc")
    tree = entry.build()
    result = solve_vector(tree, 200, plus=True)
    reach = infoset_reach(tree, pad_strategy(result.average_strategy, tree))
    positions = {label: index for index, label in enumerate(tree.infoset_labels)}
    # Only the nut information sets where a fold is even an option can violate the gate.
    facing = [
        label
        for label in leduc_dominance(tree).nut
        if "fold" in result.infoset_actions[positions[label]]
        and "call" in result.infoset_actions[positions[label]]
    ]
    assert facing, "Leduc must hand the nut holder a facing-bet decision somewhere"
    target = max(facing, key=lambda label: reach[positions[label]])
    assert reach[positions[target]] >= REACH_FLOOR, target
    index = positions[target]
    choices = result.infoset_actions[index]
    row = result.average_strategy[index].copy()
    row[choices.index("fold")] = 0.5
    row[choices.index("call")] = 0.5
    result.average_strategy[index] = row
    broken = [record for record in proofs.verify(entry, tree, result) if not record["pass"]]
    assert any("nut_never_folded" in str(record["detail"]) for record in broken), broken


def test_infoset_reach_mass_counts_the_decisions_a_hand_go_through() -> None:
    """Summing reach over information sets answers "how many decisions does a hand face, on average".

    Between one and two for Leduc: everybody faces the flop's first decision, and only the lines that get
    there face another. A traversal that counted a subtree twice would show up immediately as a mass above
    the tree's maximum depth.
    """
    tree = leduc()
    result = solve_vector(tree, 200, plus=True)
    reach = infoset_reach(tree, pad_strategy(result.average_strategy, tree))
    root = tree.nodes[tree.root]
    # Every deal reaches the first decision, so the root node's information sets partition probability 1.
    assert float(sum(reach[int(i)] for i in np.unique(root.infosets))) == pytest.approx(
        1.0, abs=1e-9
    )
    # The total is the expected number of decisions a hand goes through: more than one, because a line can
    # keep asking, and never more than the deepest path -- four decisions on the flop and four on the turn.
    assert 1.0 < float(reach.sum()) <= 8.0, float(reach.sum())
