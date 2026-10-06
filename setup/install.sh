#!/usr/bin/env bash
# Bootstrap this repository on Windows (Git Bash) or any POSIX shell.
#
# What it does, in order: find a Python >= 3.11, preflight the pyproject metadata claim, create .venv,
# install the package editable with the dev and docs extras, print the read-only environment report
# (setup/doctor.py), register the git hooks and run them once, install the trainer's node dependencies
# if trainer/ exists, then print the next steps. What it never does: sudo, global pip installs, or
# touching data/gen -- regeneration is a decision you make deliberately, not a side effect of
# installing.
#
# Design note: every tool call goes through "$VENV_PY -m <module>", never a bare command name. On
# Windows, pip puts console scripts in %APPDATA%\Python\Python312\Scripts, which is usually not on
# PATH, so a bootstrap that ended by running `mkdocs` or `poker` would fail for an environmental
# reason and teach the reader that the docs are wrong. Same reason this script calls setup/doctor.py
# itself rather than asking you to.
#
# Usage:
#   bash setup/install.sh              # Git Bash on Windows, or Linux/macOS
#   bash setup/install.sh --no-trainer # skip npm ci even if trainer/ exists
#   bash setup/install.sh --python /c/py312/python.exe

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

VENV=".venv"
WANT_TRAINER=1
PYTHON_BIN="${PYTHON:-}"
prev_arg=""

say() { printf '\033[1m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[33mwarn:\033[0m %s\n' "$*" >&2; }

for arg in "$@"; do
  case "$arg" in
    --no-trainer) WANT_TRAINER=0 ;;
    --help | -h)
      sed -n '2,20p' "${BASH_SOURCE[0]}"
      exit 0
      ;;
    *)
      if [ "$prev_arg" = "--python" ]; then
        PYTHON_BIN="$arg"
      elif [ "$arg" != "--python" ]; then
        warn "ignoring unknown argument: $arg"
      fi
      ;;
  esac
  prev_arg="$arg"
done

# --- pick an interpreter ------------------------------------------------------------------------
# Every candidate is asked to actually print a version, not just exist. Verified reason: on this
# machine `command -v python3.12` succeeds while the entry is a stub pointing at a missing
# c:\python312\python.exe, so a naive "does the command exist" test picks a broken interpreter and the
# failure shows up twenty steps later as a pip error. Windows Store aliases fail the same way.
python_is_usable() {
  local candidate="$1"
  local version
  command -v "$candidate" >/dev/null 2>&1 || return 1
  version="$("$candidate" -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null)" || return 1
  case "$version" in
    3.1[1-9] | 3.[2-9][0-9]) return 0 ;; # 3.11 and up, per pyproject requires-python
    *) return 1 ;;
  esac
}

find_python() {
  local candidate
  for candidate in "$PYTHON_BIN" python python3 python3.12 python3.11; do
    [ -n "$candidate" ] || continue
    if python_is_usable "$candidate"; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  return 1
}

if ! PY="$(find_python)"; then
  warn "no Python >= 3.11 found. pyproject sets requires-python >= 3.11."
  warn "Install one (winget install Python.Python.3.12, or conda create -n pokergto python=3.12) and re-run."
  exit 1
fi

say "using interpreter: $PY ($("$PY" -c 'import sys; print(sys.version.split()[0], sys.executable)'))"

# --- fail early on a repository-state problem, not a pip one ------------------------------------
# pyproject declares readme = "README.md"; if that file is absent, `pip install -e .` dies inside
# metadata generation with an error that names neither the file nor the cause. Checked here so the
# message is about the real problem.
if [ -f pyproject.toml ]; then
  declared_readme="$(grep -E '^[[:space:]]*readme[[:space:]]*=' pyproject.toml | head -1 |
    sed -E 's/.*=[[:space:]]*"([^"]*)".*/\1/')"
  if [ -n "$declared_readme" ] && [ ! -f "$declared_readme" ]; then
    warn "pyproject.toml declares readme = \"$declared_readme\" but $REPO_ROOT/$declared_readme does not exist."
    warn "pip install -e . will fail on metadata generation. Create the file (or drop the declaration);"
    warn "this is a repository-state issue, not an environment issue, and no amount of reinstalling fixes it."
    exit 1
  fi
fi

# --- virtual environment ------------------------------------------------------------------------
if [ ! -d "$VENV" ]; then
  say "creating $VENV"
  "$PY" -m venv "$VENV"
else
  say "$VENV exists; reusing it (delete it for a clean rebuild)"
fi

if [ -f "$VENV/Scripts/python.exe" ]; then
  VENV_PY="$VENV/Scripts/python.exe"   # Windows layout
else
  VENV_PY="$VENV/bin/python"           # POSIX layout
fi

say "installing pokergto editable with dev + docs extras"
"$VENV_PY" -m pip install --upgrade pip
"$VENV_PY" -m pip install -e ".[dev,docs]"

say "environment report (read-only)"
"$VENV_PY" setup/doctor.py || warn "doctor reported failures -- read the lines above before continuing"

# --- git hooks ------------------------------------------------------------------------------------
# Registering the hooks here is what makes the gates run without anyone remembering to run them.
# It writes only .git/hooks, and it is skipped when pre-commit is not importable.
if [ -d .git ] && "$VENV_PY" -c 'import pre_commit' >/dev/null 2>&1; then
  say "installing pre-commit git hooks"
  "$VENV_PY" -m pre_commit install
  say "running every hook once, over all files"
  "$VENV_PY" -m pre_commit run --all-files ||
    warn "hooks reported failures; some are known M0 gates (see docs/development/local-dev.md)"
fi

# --- trainer --------------------------------------------------------------------------------------
if [ "$WANT_TRAINER" -eq 1 ] && [ -f trainer/package.json ]; then
  if command -v npm >/dev/null 2>&1; then
    say "installing trainer node dependencies (npm ci)"
    (cd trainer && npm ci)
  else
    warn "trainer/package.json exists but npm is not on PATH; skipping npm ci"
  fi
else
  say "trainer: skipped (no trainer/package.json yet, or --no-trainer)"
fi

# --- next steps -----------------------------------------------------------------------------------
if [ -f "$VENV/Scripts/activate" ]; then
  ACTIVATE="source .venv/Scripts/activate"
else
  ACTIVATE="source .venv/bin/activate"
fi

cat <<EOF

Next steps

  1. activate the environment in your shell:
       $ACTIVATE
  2. confirm the tools are reachable through the interpreter:
       python -m ruff check .
       python -m pytest
       python -m mkdocs build --strict
  3. read the two docs that decide how you work here:
       docs/development/local-dev.md         (which commands actually run on this machine)
       docs/development/bilingual-style.md   (both languages, or the pull request is red)
  4. serve the site while you write:
       python -m mkdocs serve                http://127.0.0.1:8000
  5. use the CLI through the module form, which needs no PATH change:
       python -m pokergto mdf --pot 1 --bet 0.5 --lang zh
EOF

# Two Windows-specific facts, stated here because they are the two that make a working install look
# broken. Both are verified on the machine this repository started on and documented in step 3 above.
cat <<'EOF'

Two Windows-specific facts worth knowing now:

  - Bare 'ruff', 'mkdocs' and 'poker' may still be "command not found". pip puts its console scripts
    in %APPDATA%\Python\Python312\Scripts, which is frequently not on PATH. 'python -m <tool>' always
    works because it runs the module the interpreter can already see; adding that directory to PATH is
    optional and per-machine, never per-repository.
  - Chinese CLI output needs a UTF-8 console. The CLI reconfigures its own streams, so '--lang zh'
    prints correctly; 'type', 'cat' and redirected files depend on the terminal code page instead
    (chcp 65001 in cmd, or run python with -X utf8).
EOF
