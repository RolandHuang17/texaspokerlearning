"""Pytest configuration for a repository where the package is importable three ways.

``pip install -e .`` is the documented path, but a contributor on Windows/Anaconda often just runs
``pytest`` in a bare clone. Adding ``src`` here makes that work without an editable install, and it is
the only path manipulation the test suite performs.

The markers declared in ``pyproject.toml`` (``slow``, ``solver``, ``docs``) are what let the dev loop
finish in under a minute while CI still runs the full 2,598,960-hand enumeration.
"""

from __future__ import annotations

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
