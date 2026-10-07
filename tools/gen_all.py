#!/usr/bin/env python3
"""Regenerate ``data/gen`` — or verify that the committed tree already matches the engine.

    python tools/gen_all.py                 # write, except the slow steps below
    python tools/gen_all.py --check         # CI: fail on any byte difference
    python tools/gen_all.py --only tables --only glossary
    python tools/gen_all.py --skip solver   # local loop, when you did not touch the solver
    python tools/gen_all.py --check --include-slow   # the scheduled tier: re-derive everything

Why ``--check`` is a byte-diff and not a hash dance: generation is deterministic by construction
(``pokergto.artifacts.dumps`` sorts keys, pins float quantisation, writes no timestamps into artifact
bodies, and the solvers run under fixed seeds). So a rebuild of unchanged inputs changes nothing, and
anything that does change is a real change someone must read.

Order matters and is fixed: glossary -> ranges -> solver -> preflop -> tables -> quizzes -> index ->
manifest. The preflop matrix is read by nothing here but is placed with the computation that produces it;
the index counts authored artifacts, so it has to run after them; the manifest fingerprints everything, so
it is always last.

``SLOW_STEPS`` is the one exception to "everything re-runs", and it is a measured decision rather than a
convenience: re-deriving the 20,000-board preflop matrix costs 465-499 s, while its per-push proof is a 23-second
re-derivation of one batch (``tools/gen_preflop.py --verify``) plus the identity checks the artifact carries.
A skipped step carries its committed bytes into the tree it produces, so the manifest and the staleness scan
keep telling the truth about the rest of the tree. See ``adr/0008``.
"""

from __future__ import annotations

import argparse
import filecmp
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path

from _bootstrap import REPO_ROOT, bootstrap_path, ok

bootstrap_path()

import gen_curriculum_index  # noqa: E402
import gen_glossary  # noqa: E402
import gen_tables  # noqa: E402
from pokergto import __version__  # noqa: E402
from pokergto.artifacts import GEN_DIR  # noqa: E402

TOOLS = REPO_ROOT / "tools"
SCHEMA_VERSION = "1.0.0"

Step = Callable[[Path], list[Path]]


def _step_glossary(out: Path) -> list[Path]:
    src = REPO_ROOT / "data" / "src" / "glossary.yaml"
    if not src.exists():
        return []
    terms = gen_glossary.load(src)
    problems = gen_glossary.check(
        terms, curriculum_path=REPO_ROOT / "data" / "src" / "curriculum.yaml"
    )
    if problems:
        raise SystemExit("glossary invalid: " + "; ".join(problems[:5]))
    target = out / "glossary.json"
    from pokergto.artifacts import write_artifact

    write_artifact(target, gen_glossary.to_artifact(terms), schema="glossary")
    return [target]


def _step_tables(out: Path) -> list[Path]:
    return gen_tables.generate(out)


def _step_ranges(out: Path) -> list[Path]:
    script = TOOLS / "gen_ranges.py"
    if not script.exists():
        return []
    _run(script, "--out", str(out))
    return sorted((out / "ranges").glob("*.json"))


def _step_solver(out: Path) -> list[Path]:
    script = TOOLS / "run_solver.py"
    if not script.exists():
        return []
    _run(script, "--out", str(out / "solver"))
    return sorted((out / "solver").glob("*.json"))


def _step_preflop(out: Path) -> list[Path]:
    """The board-sampled preflop all-in matrix (``adr/0007``).

    A measured 465-499 s at the committed 20,000 boards, which is why this step is a member of ``SLOW_STEPS`` and is
    not re-derived by default. It is a registered step rather than a manually-run script because the manifest
    has to fingerprint it and ``compare()`` has to know a generator produces it.
    """
    script = TOOLS / "gen_preflop.py"
    if not script.exists():  # pragma: no cover
        return []
    _run(script, "--out", str(out))
    return sorted((out / "preflop").glob("*.json"))


def _step_quizzes(out: Path) -> list[Path]:
    """Quiz items whose answers the engine computed from authored domains.

    Runs before ``index`` because the index counts authored artifacts, and a landing page reporting "0
    questions" next to a bank of 19 would be a lie of omission.
    """
    from gen_quizzes import BANK, generate

    if not BANK.exists():
        return []
    return generate(out)


def _step_index(out: Path) -> list[Path]:
    """Curriculum index artifacts, plus the generated nav the mkdocs build reads.

    ``gen_curriculum_index.main`` writes ``data/gen/nav.yml`` alongside the JSON indexes, and the
    ``mkdocs_nav`` build hook feeds it to mkdocs -- mkdocs has no ``!include`` constructor, so the nav
    cannot be pulled into ``mkdocs.yml`` directly. The fragment lists only lessons whose file exists in
    that language, so an unauthored spine entry does not turn ``mkdocs build --strict`` into a
    missing-nav-target error.
    """
    src = REPO_ROOT / "data" / "src" / "curriculum.yaml"
    if not src.exists():
        return []
    argv = ["--out", str(out), "--docs", str(REPO_ROOT / "docs")]
    gen_curriculum_index.main(argv)
    written = [
        out / f"index.{locale}.json"
        for locale in ("en", "zh")
        if (out / f"index.{locale}.json").exists()
    ]
    written.extend(path for path in (out / "nav.yml",) if path.exists())
    return written


def _step_manifest(out: Path) -> list[Path]:
    from pokergto.artifacts import write_manifest

    files: list[tuple[str, Path, str | None]] = []
    for path in sorted(out.rglob("*.json")):
        if path.name == "manifest.json":
            continue
        kind = _kind_by_name(path)
        files.append((kind, path, _schema_for(path)))
    write_manifest(
        files,
        engine_version=__version__,
        schema_version=SCHEMA_VERSION,
        root=out,
    )
    return [out / "manifest.json"]


_HEX40 = re.compile(r"^[0-9a-f]{40}$")


def _environment_note() -> str:
    """What machine produced this tree, for the build log only.

    The manifest used to carry these fields, which made a committed artifact a function of the
    interpreter and the commit rather than of its inputs: ``gen_all --check`` then failed on every new
    commit and on every CI python version. Provenance is still worth seeing -- it just does not belong
    in a byte-compared file.
    """
    try:
        import numpy

        numeric = getattr(numpy, "__version__", "unknown")
    except Exception:  # pragma: no cover - numpy is a hard dependency
        numeric = "unavailable"
    interpreter = ".".join(str(part) for part in sys.version_info[:3])
    return f"python {interpreter}, numpy {numeric}, git {_git_sha() or 'no-commit'}"


def _git_sha() -> str | None:
    """Current commit, or None. Never raises.

    The output is validated because ``git rev-parse HEAD`` in a repository with no commits prints the
    literal string ``HEAD`` on stdout and an error on stderr. Recording that as a provenance field
    would put a fake sha in a committed artifact -- the exact kind of confident-but-wrong number this
    repository is built to refuse.
    """
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True, check=False
    )
    candidate = result.stdout.strip()
    return candidate if _HEX40.match(candidate) else None


def _kind_by_name(path: Path) -> str:
    parents = list(path.parts)
    if "tables" in parents:
        return "table"
    if "ranges" in parents:
        return "range_chart"
    if "matrices" in parents:
        return "pushfold_matrix"
    if "preflop" in parents:
        return "preflop_matrix"
    if "solver" in parents:
        return "solver_run"
    if "spots" in parents:
        return "spot"
    if "quizzes" in parents:
        return "quiz"
    if "hands" in parents:
        return "hand_example"
    if path.name == "glossary.json":
        return "glossary"
    if path.name.startswith("index."):
        return "curriculum_index"
    return "index"


def _schema_for(path: Path) -> str | None:
    mapping = {
        "tables": "table",
        "ranges": "range_chart",
        "matrices": "range_chart",
        "preflop": "preflop_matrix",
        "solver": "solver_run",
        "spots": "spot",
        "quizzes": "quiz",
        "hands": "hand_example",
    }
    for directory, schema in mapping.items():
        if directory in path.parts:
            return schema
    if path.name == "glossary.json":
        return "glossary"
    if path.name.startswith("index."):
        return "index"
    return None


def _run(script: Path, *args: str) -> None:
    result = subprocess.run(
        [sys.executable, str(script), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        sys.stderr.write(result.stdout or "")
        sys.stderr.write(result.stderr or "")
        raise SystemExit(f"{script.name} failed with exit {result.returncode}")


#: Order is a dependency, not a preference: the solver writes the runs that ``tables`` reads to build
#: the frequency-comparison tables, and ``index`` counts artifacts, so it must run last but one.
STEPS: list[tuple[str, Step]] = [
    ("glossary", _step_glossary),
    ("ranges", _step_ranges),
    ("solver", _step_solver),
    ("preflop", _step_preflop),
    ("tables", _step_tables),
    ("quizzes", _step_quizzes),
    ("index", _step_index),
    ("manifest", _step_manifest),
]


#: Steps that cannot run partially, and why.
#:
#: ``manifest.json`` is a fingerprint of the whole ``data/gen`` tree. Generating it after a filtered
#: run would describe a tree that does not exist (the temp directory holds only the steps you asked
#: for), so the next ``--check`` would report a phantom diff. Filtering therefore drops the manifest
#: instead of producing a wrong one.
FULL_TREE_ONLY = {"manifest"}


#: Steps that are skipped unless ``--include-slow`` is passed, mapped to the ``data/gen`` directories whose
#: committed bytes are carried into the tree instead.
#:
#: ``preflop`` is here because of one measured number: 465-499 s to re-derive 20,000 boards (23-25 ms per board,
#: 2026-10-07), on a gate -- ``gen_all --check`` -- that runs on every push and every pull request. Paying that
#: per push is not extra rigour, it is a tax that teaches contributors to add ``--skip``, and a skipped gate
#: nobody re-runs is the failure mode ``adr/0002`` already wrote a scheduled job for. So the per-push tier
#: re-derives what one batch determines and compares it byte for byte
#: (``python tools/gen_preflop.py --verify``, about 23 s), and the scheduled
#: ``.github/workflows/solver-regression.yml`` re-derives the whole board set with ``--include-slow``. Recorded
#: in ``adr/0008``.
SLOW_STEPS: dict[str, tuple[str, ...]] = {"preflop": ("preflop",)}


def _carry_over(out: Path, prefixes: tuple[str, ...]) -> list[Path]:
    """Copy a skipped slow step's committed artifacts into the tree being produced, or refuse loudly.

    A copy rather than an exemption, for two reasons that are both about not weakening a gate. The manifest
    fingerprints the whole tree, so a matrix missing from the rebuild would make the rebuilt ``manifest.json``
    disagree with the committed one and read as a real change. And ``compare()`` treats a committed file that no
    generator produces as stale -- true of a skipped step, and a false alarm that would hide the real kind.
    Carrying the bytes over keeps both of those checks telling the truth about everything else in the tree.

    What this must never become is "skipped means deleted". If the committed artifact is not on disk, that is a
    real failure, and it is reported as one instead of being compared away.
    """
    carried: list[Path] = []
    for prefix in prefixes:
        source_dir = GEN_DIR / prefix
        committed = sorted(source_dir.rglob("*.json")) if source_dir.exists() else []
        if not committed:
            raise SystemExit(
                f"data/gen/{prefix} holds no artifact, and its generating step is not being re-derived. "
                f"Run `python tools/gen_all.py --include-slow`, or `python tools/gen_preflop.py --out data/gen`."
            )
        for source in committed:
            target = out / source.relative_to(GEN_DIR)
            if target.resolve() != source.resolve():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
            carried.append(target)
    return carried


def generate(
    out: Path,
    *,
    only: set[str] | None = None,
    skip: set[str] | None = None,
    include_slow: bool = False,
) -> list[Path]:
    filtered = bool(only or skip)
    written: list[Path] = []
    carried: list[Path] = []
    for name, step in STEPS:
        # First question, before any filter: is this a slow step the caller did not explicitly ask for? Answering
        # it after `--only` would let a filtered run skip the carry-over entirely, and the carry-over is what makes
        # "not re-derived" different from "deleted" -- it refuses the run when the committed artifact is absent.
        explicitly_requested = bool(only) and name in only
        if not include_slow and name in SLOW_STEPS and not explicitly_requested:
            carried.extend(_carry_over(out, SLOW_STEPS[name]))
            continue
        if only and name not in only:
            continue
        if skip and name in skip:
            continue
        if filtered and name in FULL_TREE_ONLY:
            continue
        written.extend(step(out))
    if carried:
        print(
            f"note: {len(carried)} artifact(s) carried from data/gen instead of re-derived "
            f"({', '.join(sorted(SLOW_STEPS))}). Their bytes are compared, their engine is not re-run: "
            "`python tools/gen_preflop.py --verify` re-derives one batch on every push, and "
            "`--include-slow` re-derives the full board set. See adr/0008.",
            file=sys.stderr,
        )
    if filtered and not only:
        print(
            "note: manifest step skipped for a filtered run; it fingerprints the whole tree and would "
            "otherwise record a partial one. Run `python tools/gen_all.py` unfiltered before committing.",
            file=sys.stderr,
        )
    return written


def _first_difference(left: Path, right: Path, *, limit: int = 90) -> str:
    """The first line where two artifacts stop agreeing, bounded so a build log stays readable.

    A FAIL that only names a file is useless to anyone who cannot run the generator themselves -- which is
    exactly the situation of a contributor reading a red CI job, and of whoever debugged the first public run
    here. The difference itself is the diagnosis, so print it.
    """
    left_lines = left.read_text(encoding="utf-8").splitlines()
    right_lines = right.read_text(encoding="utf-8").splitlines()
    for index, (a, b) in enumerate(zip(left_lines, right_lines, strict=False)):
        if a != b:
            shown_a = a.strip()[:limit]
            shown_b = b.strip()[:limit]
            return f"line {index + 1}: committed `{shown_a}` against fresh `{shown_b}`"
    if len(left_lines) != len(right_lines):
        return f"line count {len(left_lines)} against {len(right_lines)}"
    return "bytes differ after the last shared line (encoding or trailing newline)"


def compare(committed: Path, rebuilt: Path) -> list[str]:
    problems: list[str] = []
    if not committed.exists():
        return [f"{committed} does not exist but generated output was produced"]
    committed_files = {
        path.relative_to(committed): path for path in committed.rglob("*") if path.is_file()
    }
    rebuilt_files = {
        path.relative_to(rebuilt): path
        for path in rebuilt.rglob("*")
        if path.is_file() and path.suffix in {".json", ".csv", ".svg"}
    }
    for relative in sorted(set(committed_files) - set(rebuilt_files)):
        if relative.suffix not in {".json", ".csv", ".svg"}:
            continue
        problems.append(
            f"stale artifact committed with no generator producing it: data/gen/{relative.as_posix()}"
        )
    for relative in sorted(set(rebuilt_files) - set(committed_files)):
        problems.append(f"generated but not committed: data/gen/{relative.as_posix()}")
    for relative in sorted(set(rebuilt_files) & set(committed_files)):
        if not filecmp.cmp(committed_files[relative], rebuilt_files[relative], shallow=False):
            problems.append(
                f"data/gen/{relative.as_posix()} differs from what the engine produces now "
                f"({_first_difference(committed_files[relative], rebuilt_files[relative])}); "
                "run `python tools/gen_all.py` and commit the result"
            )
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--only", action="append", default=[])
    parser.add_argument("--skip", action="append", default=[])
    parser.add_argument(
        "--include-slow",
        action="store_true",
        help="re-derive SLOW_STEPS too (the preflop matrix: a measured 465-499 s). The scheduled tier does this.",
    )
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args(argv)

    if args.list:
        for name, _ in STEPS:
            print(name)
        return 0

    only = set(args.only) or None
    skip = set(args.skip) or None
    unknown = (only or set()) | (skip or set())
    known = {name for name, _ in STEPS}
    if unknown - known:
        print(
            f"error: unknown step(s) {sorted(unknown - known)}; available: {sorted(known)}",
            file=sys.stderr,
        )
        return 2

    if args.check:
        if only and "manifest" in only:
            print(
                "error: --only manifest cannot be checked: the manifest describes the whole tree. "
                "Run the unfiltered generator.",
                file=sys.stderr,
            )
            return 2
        problems: list[str] = []
        with tempfile.TemporaryDirectory(prefix="pokergto-check-") as tmp:
            rebuilt = Path(tmp) / "gen"
            rebuilt.mkdir(parents=True, exist_ok=True)
            produced = generate(rebuilt, only=only, skip=skip, include_slow=args.include_slow)
            if not produced and not GEN_DIR.exists():
                ok("nothing generated and nothing committed: data gate passes on an empty tree")
                return 0
            if not GEN_DIR.exists():
                problems = [
                    "data/gen does not exist but generators produced output: run tools/gen_all.py"
                ]
            elif only or skip:
                # A partial check compares only what it regenerated. Whole-tree staleness is the
                # unfiltered job's business, so a fast local loop can never report false staleness.
                for path in produced:
                    counterpart = GEN_DIR / path.relative_to(rebuilt)
                    if not counterpart.exists():
                        problems.append(
                            f"data/gen/{path.relative_to(rebuilt).as_posix()} is not committed"
                        )
                    elif counterpart.read_bytes() != path.read_bytes():
                        problems.append(
                            f"data/gen/{path.relative_to(rebuilt).as_posix()} differs from what the "
                            "engine produces now: run `python tools/gen_all.py` and commit the result"
                        )
            else:
                problems = compare(GEN_DIR, rebuilt)
        if problems:
            for problem in problems[:40]:
                print(f"FAIL {problem}", file=sys.stderr)
            if len(problems) > 40:
                print(f"... and {len(problems) - 40} more", file=sys.stderr)
            return 1
        ok("data/gen is byte-identical to a fresh generation")
        return 0

    written = generate(GEN_DIR, only=only, skip=skip, include_slow=args.include_slow)
    ok(f"gen_all: wrote {len(written)} artifacts into data/gen")
    print(f"     built by {_environment_note()}", file=sys.stderr)
    if not written:
        print(
            "     (empty state is expected at M0: add data/src/curriculum.yaml and tables to grow it)",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
