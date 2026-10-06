"""Exception hierarchy for pokergto.

Errors are typed because the curriculum distinguishes three things a naive tool collapses into
"Exception": a malformed input the learner should be taught to recognise, an unsatisfiable request
(a computation whose budget is too large to be exact), and an internal invariant violation (which
means the library is wrong, not the user).
"""

from __future__ import annotations


class PokerGtoError(Exception):
    """Base class for every error raised by this package."""


class InputError(PokerGtoError):
    """The caller supplied something malformed: a bad card string, an illegal range, a wrong arity."""


class NotationError(InputError):
    """A range specification could not be parsed, or parsed to an empty/contradictory set."""


class BudgetExceeded(PokerGtoError):
    """A request is well-formed but too large to serve exactly.

    Raised by exact enumeration paths. The message always names the cheaper alternative, because
    in a teaching library "no, but here is how to ask differently" is the whole point.
    """


class InvariantError(PokerGtoError):
    """An internal assertion that should be impossible failed. Please file an issue."""


class ProvenanceError(PokerGtoError):
    """An artifact violates the provenance contract (see adr/0005 and NOTICE)."""


class ProofGateError(PokerGtoError):
    """A solver result is not registered in solver/proofs.py, so it may not back a ready lesson."""


class SchemaDriftError(PokerGtoError):
    """A committed generated artifact differs from what the engine now produces."""
