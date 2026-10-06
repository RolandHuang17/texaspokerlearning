#!/usr/bin/env python3
"""Read-only environment report for this repository.

``doctor`` answers one question -- "is this machine able to run the project's own gates" -- and takes no
side effect to make the answer nicer. It installs nothing, writes nothing, regenerates nothing, and
does not touch ``data/gen`` or ``docs/``. Every check is a read, or a subprocess that prints a version.

That contract matters here more than in a typical project: this repository's correctness story is
byte-exact generated artifacts (adr/0001), so a diagnostic tool that quietly re-rendered a table would
be worse than no diagnostic tool at all. If you find yourself wanting ``doctor.py`` to fix something,
that is ``setup/install.ps1`` or ``setup/install.sh`` talking, not this file.

Usage::

    python setup/doctor.py          # human-readable; exit 1 on any FAIL
    python setup/doctor.py --json   # machine-readable, for CI logs
    python -X utf8 setup/doctor.py  # if the console code page is not UTF-8

Exit codes: 0 when nothing failed; 1 when at least one check failed; 2 when the repository root could
not be located. WARN states are reported but never move the exit code -- they are things this project
can be built without today (Node, a PATH entry for console scripts).
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"

#: Module entry points the contributor docs tell you to use. Deliberately the ``-m`` form: bare
#: ``ruff`` and ``mkdocs`` are not on PATH on a Windows user-site install, which is the most common
#: "the docs are lying to me" report this project would otherwise receive.
REQUIRED_MODULES: tuple[tuple[str, str], ...] = (
    ("ruff", "lint"),
    ("mypy", "strict type check of src/pokergto"),
    ("pytest", "test suite"),
    ("mkdocs", "docs site build"),
    ("pre_commit", "the gate runner"),
)

PASS = "PASS"
WARN = "WARN"
FAIL = "FAIL"


@dataclass(slots=True)
class Check:
    """One line of the report: a name, a level, and the evidence behind it."""

    name: str
    level: str
    detail: str

    def as_dict(self) -> dict[str, str]:
        """Serialise for ``--json``, so a CI log can be read by a machine as well as a human."""
        return {"name": self.name, "level": self.level, "detail": self.detail}


def _probe_module(module: str, purpose: str) -> Check:
    """Ask the *current* interpreter whether ``python -m <module> --version`` runs.

    Importing alone would be enough to answer "is it there", but the version string is the part a
    contributor compares against the docs, so the subprocess earns its fraction of a second.
    """
    try:
        proc = subprocess.run(
            [sys.executable, "-m", module, "--version"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as error:  # pragma: no cover - exotic environments
        return Check(module, FAIL, f"could not be launched: {error}")
    if proc.returncode != 0:
        missing = importlib.util.find_spec(module) is None
        reason = "not installed in this interpreter" if missing else "installed but exited non-zero"
        return Check(module, FAIL, f"{reason} ({purpose})")
    lines = (proc.stdout or proc.stderr).strip().splitlines()
    version = lines[0] if lines else "ok"
    return Check(module, PASS, f"{version} -- {purpose}")


def check_interpreter() -> Check:
    """Which Python is actually running, and whether it is a version this project supports."""
    version = ".".join(str(part) for part in sys.version_info[:3])
    detail = f"{version} at {sys.executable}"
    if sys.version_info < (3, 11):  # noqa: UP036 - the block exists for interpreters older than the target
        return Check("python", FAIL, f"{detail} -- requires-python is >=3.11")
    return Check("python", PASS, detail)


def check_engine_importable() -> Check:
    """``pokergto`` must import with or without an editable install.

    ``tools/`` puts ``src/`` on ``sys.path`` for exactly this reason, so a contributor who has not
    installed the package yet can still run every generator. The report says which route was taken,
    because "it works only after pip install -e" is a different problem than "it does not work".
    """
    installed = importlib.util.find_spec("pokergto") is not None
    if not installed:
        sys.path.insert(0, str(SRC_DIR))
    try:
        module = importlib.import_module("pokergto")
    except Exception as error:  # a diagnostic reports any failure rather than re-raising it
        return Check("pokergto import", FAIL, f"{type(error).__name__}: {error}")
    version = getattr(module, "__version__", "unknown")
    origin = Path(str(getattr(module, "__file__", "?"))).parent
    via = "installed distribution" if installed else "src/ bootstrap"
    return Check("pokergto import", PASS, f"{version} from {origin} ({via})")


def check_required_modules() -> list[Check]:
    """One line per tool the gates need, all resolved through this same interpreter."""
    return [_probe_module(module, purpose) for module, purpose in REQUIRED_MODULES]


def check_node() -> Check:
    """Node and npm, reported as WARN when absent.

    They gate ``trainer/`` (milestone M3), not the Python or data gates, so a missing Node must not
    turn this report red.
    """
    node = shutil.which("node")
    if node is None:
        return Check("node", WARN, "not on PATH -- trainer/ cannot be built, everything else can")
    proc = subprocess.run([node, "-v"], capture_output=True, text=True, check=False)
    npm = shutil.which("npm")
    detail = f"node {proc.stdout.strip()} at {node}"
    if npm:
        detail = f"{detail}; npm at {npm}"
    return Check("node", PASS, detail)


def check_console_scripts_on_path() -> Check:
    r"""Report the Windows user-site Scripts directory when it is missing from PATH.

    This check exists because of one verified environment: pip put its console scripts into
    ``%APPDATA%\Python\Python312\Scripts``, which was not on PATH, so bare ``ruff`` and ``mkdocs``
    failed while ``python -m ruff`` worked. The documentation's answer is ``python -m`` everywhere;
    this line tells a contributor whether their machine has the same gap and what the optional fix is.
    """
    if os.name != "nt":
        return Check("console scripts on PATH", PASS, "posix: not applicable")
    scripts = Path(os.environ.get("APPDATA", "")) / "Python" / "Python312" / "Scripts"
    if not scripts.is_dir():
        return Check("console scripts on PATH", WARN, f"{scripts} does not exist")
    entries = [entry for entry in os.environ.get("PATH", "").split(os.pathsep) if entry]
    on_path = any(Path(entry).resolve() == scripts for entry in entries)
    if on_path:
        return Check("console scripts on PATH", PASS, f"{scripts} is on PATH")
    return Check(
        "console scripts on PATH",
        WARN,
        f"{scripts} is NOT on PATH -- use `python -m ruff`, `python -m mkdocs`, `python -m pytest`",
    )


def check_schemas() -> Check:
    """Every ``data/schema/*.json`` must parse and declare ``$schema``.

    A schema that does not parse cannot validate anything, and ``tools/check_artifact_schema.py`` would
    then fail at load time rather than on the assertion a reader cares about.
    """
    directory = REPO_ROOT / "data" / "schema"
    if not directory.is_dir():
        return Check("data/schema", FAIL, "directory missing")
    files = sorted(directory.glob("*.json"))
    bad: list[str] = []
    for path in files:
        try:
            payload: Any = json.loads(path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            bad.append(f"{path.name}: {error}")
            continue
        if not isinstance(payload, dict) or "$schema" not in payload:
            bad.append(f"{path.name}: no $schema key")
    if bad:
        return Check(
            "data/schema", FAIL, f"{len(bad)} of {len(files)} invalid: " + "; ".join(bad[:3])
        )
    return Check("data/schema", PASS, f"{len(files)} schemas parse")


def _count_markdown(base: Path) -> int:
    """Number of markdown files under a locale root, or -1 when the root does not exist."""
    return len(sorted(base.rglob("*.md"))) if base.is_dir() else -1


def check_doc_trees() -> list[Check]:
    """Both locale trees exist, and their file counts are compared.

    Only counts, deliberately: the real parity gate is ``tools/check_bilingual.py``, and a diagnostic
    that duplicated its logic would be a second, weaker version of the same claim.
    """
    checks: list[Check] = []
    for locale in ("en", "zh"):
        count = _count_markdown(REPO_ROOT / "docs" / locale)
        target = f"docs/{locale}"
        if count < 0:
            checks.append(Check(target, FAIL, "directory missing"))
        else:
            checks.append(Check(target, PASS, f"{count} markdown files"))
    en = _count_markdown(REPO_ROOT / "docs" / "en")
    zh = _count_markdown(REPO_ROOT / "docs" / "zh")
    if en >= 0 and zh >= 0 and en != zh:
        checks.append(
            Check(
                "docs parity (count only)",
                WARN,
                f"en {en} files, zh {zh} files -- run check_bilingual.py",
            )
        )
    return checks


def check_declared_readme() -> Check:
    """``[project] readme`` in pyproject must point at a file that exists.

    If it does not, ``pip install -e .`` fails during metadata generation with an error that says
    nothing about the real cause, and every contributor spends the same twenty minutes. Read as text
    rather than parsed as TOML on purpose: this check must survive a pyproject.toml that is itself
    broken, which is exactly the situation it is here to diagnose.
    """
    pyproject = REPO_ROOT / "pyproject.toml"
    if not pyproject.is_file():
        return Check("pyproject readme", FAIL, "pyproject.toml missing")
    declared: str | None = None
    for line in pyproject.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("readme") and "=" in stripped:
            declared = stripped.split("=", 1)[1].strip().strip("\"'")
            break
    if declared is None:
        return Check("pyproject readme", WARN, "no readme key declared")
    target = REPO_ROOT / declared
    if not target.is_file():
        return Check(
            "pyproject readme",
            FAIL,
            f"pyproject declares readme = {declared!r} but {target} does not exist; "
            "pip install -e . will fail while building metadata",
        )
    return Check("pyproject readme", PASS, f"{declared} exists")


def check_generated_tree() -> Check:
    """``data/gen`` should exist and hold committed artifacts.

    Empty is not a failure: at M0 there was nothing to generate, and the gates are written to pass on
    an empty tree so that the scaffolding is proven before the content arrives.
    """
    directory = REPO_ROOT / "data" / "gen"
    if not directory.is_dir():
        return Check("data/gen", WARN, "absent -- nothing has been generated yet")
    artifacts = [path for path in directory.rglob("*") if path.is_file()]
    return Check("data/gen", PASS, f"{len(artifacts)} committed artifacts")


def gather() -> list[Check]:
    """Run every check.

    The order is the order a contributor should read the answers: interpreter, package, tooling, then
    the repository's own trees.
    """
    checks = [check_interpreter(), check_engine_importable()]
    checks.extend(check_required_modules())
    checks.append(check_node())
    checks.append(check_console_scripts_on_path())
    checks.append(check_schemas())
    checks.extend(check_doc_trees())
    checks.append(check_declared_readme())
    checks.append(check_generated_tree())
    return checks


def _render(checks: list[Check]) -> str:
    """Column-aligned report. Levels sort the eye before the details do."""
    width = max(len(check.name) for check in checks)
    return "\n".join(
        f"{check.level:4s} {check.name.ljust(width)}  {check.detail}" for check in checks
    )


def main(argv: list[str] | None = None) -> int:
    """Print the report and return the exit code. No writes, in any branch."""
    parser = argparse.ArgumentParser(description="Read-only environment report for pokergto.")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args(argv)

    if not (REPO_ROOT / "pyproject.toml").is_file():
        print(f"FAIL repository root not found above {Path(__file__).resolve()}", file=sys.stderr)
        return 2

    checks = gather()
    failures = [check for check in checks if check.level == FAIL]
    warnings = [check for check in checks if check.level == WARN]

    if args.json:
        print(
            json.dumps(
                {
                    "python": sys.version,
                    "checks": [check.as_dict() for check in checks],
                    "failures": len(failures),
                    "warnings": len(warnings),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1 if failures else 0

    print(_render(checks))
    print(
        f"\n{len(checks) - len(failures) - len(warnings)} pass, {len(warnings)} warn, {len(failures)} fail"
    )
    if failures:
        sys.stdout.flush()  # keep the hint below the report even when stdout is a pipe
        print(
            "Fix: run setup/install.ps1 (Windows) or setup/install.sh, then re-run this.\n"
            "The gates themselves are: python -m ruff check ., python -m mypy, python -m pytest, "
            "python -m mkdocs build --strict.",
            file=sys.stderr,
        )
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
