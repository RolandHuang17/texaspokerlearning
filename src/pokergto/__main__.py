"""`python -m pokergto ...` entry point.

On Windows the ``poker`` console script often lands in a Scripts directory that is not on
PATH, so the module form is the documented default in the README and in setup/doctor.py.
"""

from __future__ import annotations

import sys

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
