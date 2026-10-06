"""Shared plumbing for the build-time tools in this directory.

``tools/`` is not part of the installable package (ADR-0005 / D5): it may import ``pokergto``, but
``pokergto`` must never import it. Keeping that one-way edge is what lets a learner ``pip install``
the engine and still get every documented number.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
TOOLS = REPO_ROOT / "tools"


def bootstrap_path() -> None:
    """Make ``src/`` importable when the package is not installed editable.

    Every tool starts with this instead of requiring contributors to install first, because the first
    command a new contributor runs should not be able to fail for an environmental reason.
    """
    if str(SRC) not in sys.path:
        sys.path.insert(0, str(SRC))


def utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:  # pragma: no cover
            pass


def fail(message: str, *, hint: str | None = None) -> int:
    print(f"FAIL {message}", file=sys.stderr)
    if hint:
        print(f"     {hint}", file=sys.stderr)
    return 1


def ok(message: str) -> None:
    print(f"ok   {message}")
