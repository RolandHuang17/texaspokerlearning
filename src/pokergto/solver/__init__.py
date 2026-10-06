"""The solver: small games, exact traversal, proof-gated output.

Read :mod:`pokergto.solver.tree` for the representation, :mod:`pokergto.solver.games` for what is
being solved, :mod:`pokergto.solver.cfr` for the algorithm, :mod:`pokergto.solver.exploitability` for
the only measure of "is this an equilibrium yet", and :mod:`pokergto.solver.proofs` for the gate that
decides whether any of it may be cited in a lesson.
"""

from __future__ import annotations

from .cfr import CFRSolver, SolveResult, solve
from .exploitability import best_response_value, expected_value, exploitability
from .games import kuhn, one_street_bluff_catcher
from .proofs import PUBLISHED_PROOFS, ProofEntry, entry_for, is_validated, require_validated, verify
from .tree import DecisionNode, GameTree, TerminalNode, TreeBuilder, regret_matching

__all__ = [
    "PUBLISHED_PROOFS",
    "CFRSolver",
    "DecisionNode",
    "GameTree",
    "ProofEntry",
    "SolveResult",
    "TerminalNode",
    "TreeBuilder",
    "best_response_value",
    "entry_for",
    "expected_value",
    "exploitability",
    "is_validated",
    "kuhn",
    "one_street_bluff_catcher",
    "regret_matching",
    "require_validated",
    "solve",
    "verify",
]
