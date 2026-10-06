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
from fractions import Fraction

import numpy as np
import pytest

from pokergto.artifacts import GEN_DIR, read_artifact
from pokergto.errors import InvariantError
from pokergto.odds import bluff_fraction_at_indifference, minimum_defense_frequency
from pokergto.solver.cfr import CFRSolver, solve
from pokergto.solver.exploitability import best_response_value, expected_value, exploitability
from pokergto.solver.games import kuhn, one_street_bluff_catcher
from pokergto.solver.proofs import KUHN, PUBLISHED_PROOFS, entry_for, verify
from pokergto.solver.tree import DecisionNode, GameTree, TreeBuilder, regret_matching

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
    "bet_size", [float(Fraction(1, 4)), float(Fraction(1, 3)), 0.5, 1.0, 2.0],
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
    assert artifact["algorithm"] == entry.algorithm
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
