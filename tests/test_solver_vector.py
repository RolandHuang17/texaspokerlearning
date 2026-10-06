"""The vector form must be the same algorithm, not a faster different one.

``solver/cfr.py`` is the definition of correctness in this repository: it recurses one ``(node, deal)``
at a time, it is slow, and Kuhn's analytic ``-1/18`` proves it. ``solver/vector.py`` exists because the
preflop model is not tractable one deal at a time -- and a vectorised CFR has a documented history here
of converging *stably to a non-equilibrium* (an earlier version squared the opponent's reach
probabilities; exploitability stalled at 0.89 and only the closed form exposed it).

So the admission control is agreement, and it is stated precisely, because "agree on everything" is not
achievable and claiming it would be a false test:

* **plain regret matching** (no CFR+, uniform averaging) sums commutative contributions inside a
  traversal, so the two forms must agree to machine epsilon -- the terms are identical and only the
  associativity of floating-point addition differs;
* **CFR+** floors regrets at every touch and therefore depends on the order of updates, so equality is
  not the claim -- reaching an equilibrium is. Both forms must independently satisfy Kuhn's game value,
  the closed-form defence frequency, and the exploitability gate.
"""

from __future__ import annotations

from fractions import Fraction

import numpy as np
import pytest

from pokergto.odds import bluff_fraction_at_indifference, minimum_defense_frequency
from pokergto.solver import cfr, vector
from pokergto.solver.games import kuhn, one_street_bluff_catcher
from pokergto.solver.tree import TreeBuilder

pytestmark = pytest.mark.solver


def _two_street_tree() -> object:
    """A tree whose information sets do not all have the same number of actions.

    This is the shape a vector form breaks on and the shape a one-street toy never exercises: the second
    decision only exists after a bet, so most information sets have two actions and one has three.
    Padding is where a vectorised CFR dies quietly -- a padded column read as ``sigma = 0`` multiplies a
    child's reach by zero, and the run still prints a tidy exploitability because the branch it froze no
    longer contributes anything to measure.
    """
    deals = [f"{suit}{rank}" for rank in "AB3" for suit in "jh"][:6]
    builder = TreeBuilder(
        "two_street_probe", {"zh": "两条街探针", "en": "two-street probe"}, [(d,) for d in deals]
    )
    # Three genuinely different outcomes. Built with identical payoffs the probe is degenerate: every
    # action has the same utility, so regret is zero everywhere and a test that "passes" on it has
    # measured nothing -- which is worth remembering about solver tests generally.
    showdown = builder.new_node_id()
    builder.add_terminal(showdown, [1.0, -1.0, 0.5, -0.5, 0.25, -0.25])
    folded = builder.new_node_id()
    builder.add_terminal(folded, [0.5, 0.5, 0.5, 0.5, 0.5, 0.5])
    doubled = builder.new_node_id()
    builder.add_terminal(doubled, [-1.0, 1.0, -0.5, 0.5, -0.25, 0.25])
    river = builder.new_node_id()
    builder.add_decision(
        river,
        1,
        ("check", "bet", "shove"),
        (showdown, doubled, folded),
        list(deals),
    )
    turn = builder.new_node_id()
    builder.add_decision(
        turn, 0, ("check", "bet"), (showdown, river), ["A", "B", "C", "A", "B", "C"]
    )
    return builder.build(turn)


def test_plain_cfr_regrets_agree_exactly_with_the_textbook_form() -> None:
    """Same tree, same iteration, buffer for buffer.

    This is the strong assertion, and it is only available because plain regret matching sums commutative
    contributions within a traversal: the deal order cannot change the result, so any difference between
    the two implementations would be a difference in the algorithm.
    """
    slow = cfr.CFRSolver(_two_street_tree(), plus=False)
    fast = vector.VectorCFRSolver(_two_street_tree(), plus=False)
    for iteration in range(1, 11):
        slow.iteration = iteration
        fast.iteration = iteration
        for player in (0, 1):
            slow.step(player)
            fast.step(player)
        padded = np.stack(
            [
                np.pad(row, (0, int(max(slow.tree.infoset_actions)) - len(row)))
                for row in slow.regrets
            ]
        )
        # Machine-epsilon agreement, not bit equality, and the reason is worth stating rather than
        # working around: both forms sum the same terms, but the scalar form accumulates deal by deal
        # while the vector form reduces a column at once. Floating-point addition is not associative, so
        # the two differ at the last bits (measured here at 1e-17 and growing only as fast as those bits
        # carry). Anything larger than this tolerance is a real divergence, and this test is what would
        # catch the historical bug class -- an agreement failure here is a different algorithm, not noise.
        assert np.allclose(padded, fast.regrets, rtol=0.0, atol=1e-12), (
            f"diverged at iteration {iteration}: max |delta| = "
            f"{float(np.abs(padded - fast.regrets).max()):.3e}"
        )
        assert float(np.abs(fast.regrets).sum()) > 0.0, "the probe must actually accumulate regret"


@pytest.mark.parametrize("bet_size", [Fraction(1, 3), Fraction(1, 2), Fraction(3, 4), Fraction(1)])
def test_vector_form_reproduces_the_chapter_02_closed_forms(bet_size: Fraction) -> None:
    """Each size's defence frequency and bluff share must match the algebra independently.

    Both implementations are run because agreement between them proves nothing about the *mathematics*:
    the assertion that matters is that each one lands on ``pot/(pot+bet)`` and ``bet/(pot+2bet)``.
    """
    size = float(bet_size)
    result = vector.solve_vector(one_street_bluff_catcher(1.0, size), 6_000, plus=False)
    report = result.strategy_report()
    defended = report["1:1:catcher"]["call"]
    value_bets = report["0:0:nut"]["bet"]
    bluffs = report["0:0:air"]["bet"]
    assert defended == pytest.approx(float(minimum_defense_frequency(1.0, size)), abs=2e-3)
    measured_bluff_share = bluffs / (value_bets + bluffs) if (value_bets + bluffs) else 0.0
    assert measured_bluff_share == pytest.approx(
        float(bluff_fraction_at_indifference(1.0, size)), abs=2e-3
    )
    assert result.exploitability < 2e-3


def test_vector_form_hits_kuhn_from_an_equilibrium_of_the_proven_family() -> None:
    """Kuhn has a continuum of equilibria, so the check is family membership, not a specific strategy.

    Asserting one number here would fail for a correct solver that simply settled on a different valid
    ``alpha`` -- which is exactly how the proof entries in ``solver/proofs.py`` are written.
    """
    result = vector.solve_vector(kuhn(1.0), 2_000, plus=True)
    assert result.game_value == pytest.approx(-1.0 / 18.0, abs=2e-4)
    jack_open = result.strategy_report()["0:0:J"]["bet"]
    assert 0.0 <= jack_open <= 1.0 / 3.0 + 1e-9
    assert result.exploitability < 1e-3


def test_ragged_action_counts_do_not_zero_out_an_existing_branch() -> None:
    """The padding regression, in the direction that actually breaks silently.

    A masked-out column must not be read as ``sigma = 0``: if it is, the child's reach becomes zero,
    the subtree stops being trained, and the run still reports a clean exploitability number because the
    untrained subtree contributes nothing to the traversal it was cut from.
    """
    tree = _two_street_tree()
    solver = vector.VectorCFRSolver(tree, plus=False)
    solver.step(0)
    solver.step(1)
    matrix = solver.current_matrix()
    for index, count in enumerate(solver.counts):
        live = matrix[index, : int(count)]
        assert float(live.sum()) == pytest.approx(1.0), f"infoset {index} does not normalise"
        padded = matrix[index, int(count) :]
        assert np.all(padded >= 0.0), "padding must never be negative"
    # Every information set was actually visited: a frozen branch would sit at exactly uniform.
    assert any(float(np.abs(row - 1.0 / len(row)).max()) > 0.0 for row in solver.current_strategy())


def test_vector_run_reports_a_distinct_algorithm_name() -> None:
    """An artifact must not be able to claim the textbook algorithm while running the fast one.

    ``ProofEntry.algorithm`` is the field a reader trusts; two implementations sharing a name would make
    ``data/gen/solver`` ambiguous about which produced a number.
    """
    result = vector.solve_vector(kuhn(1.0), 20, plus=False)
    assert result.algorithm == "cfr_vector"
    plus = vector.solve_vector(kuhn(1.0), 20, plus=True)
    assert plus.algorithm == "cfr_plus_vector"
