# Local development, Windows first

> **Single-language by design:** these are contributor-facing engineering docs, and the
> bilingual-same-PR rule applies to curriculum content only (see adr/0005).

Every command below was run on the machine this repository started on: Windows 11 + Git Bash,
Python 3.12.13 (Anaconda base at `D:\annaconda`), Node 20.15.1, ruff 0.16.10, mypy 1.10.0,
pytest 7.4.4, mkdocs 1.6.1, mkdocs-material 9.7.7, pre-commit 4.6.2. Where a command does not work
here, that is written down rather than smoothed over.

## The one rule that makes everything else work

**Invoke tools as modules: `python -m ruff`, `python -m mkdocs`, `python -m pytest`,
`python -m mypy`, `python -m pre_commit`.**

This is not a style preference. On this machine `pip` placed its console scripts in
`C:\Users\roland\AppData\Roaming\Python\Python312\Scripts`, and that directory is **not** on `PATH`
(`PATH` carries `C:\Users\roland\AppData\Roaming\npm`, which is a different directory that only
holds Node globals). So the bare commands fail:

```text
$ ruff --version
bash: ruff: command not found
$ mkdocs --version
bash: mkdocs: command not found
```

`python -m <tool>` ignores that whole mess: it runs the module that is actually importable by the
interpreter you are standing on, so there is no chance of executing a script whose shebang points at
a different Python than the one holding `numpy`.

Optional fix, if you want the bare names — add the Scripts directory to `PATH`:

```powershell
# PowerShell, user scope, permanent
[Environment]::SetEnvironmentVariable(
  "Path",
  [Environment]::GetEnvironmentVariable("Path", "User") +
    ";$env:APPDATA\Python\Python312\Scripts",
  "User")
```

In Git Bash, for the current shell only:

```bash
export PATH="$PATH:$HOME/AppData/Roaming/Python/Python312/Scripts"
```

Do this only after `python -m` works, so you can tell which of the two problems you fixed. A
`.pth`-free `PATH` edit changes the shell, not the repository, so nothing here depends on it.

## Bootstrap

Fresh clone, Git Bash. `setup/install.sh` does exactly this, and `setup/install.ps1` does it in
PowerShell.

```bash
python -m venv .venv
source .venv/Scripts/activate           # Git Bash; in PowerShell: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev,docs]"  # pyproject is the single source of tool configuration
python setup/doctor.py                  # read-only environment report, exits non-zero on failure
```

If you would rather not create a virtual environment — reasonable when you are already inside an
Anaconda environment and only want to run the checks — `requirements-dev.txt` mirrors the `dev` and
`docs` extras for a plain `python -m pip install -r requirements-dev.txt`. The two lists must stay
in sync; `ci.yml` has a step that fails when they diverge.

`poker`, the CLI entry point, is only importable after the editable install. Before that, the tools
in `tools/` still work, because each one calls `_bootstrap.bootstrap_path()` and prepends `src/` to
`sys.path`. That is deliberate: the first command a new contributor runs should not be able to fail
for an environmental reason.

```bash
python -m pokergto mdf --pot 1 --bet 0.5         # works with the editable install
python -m pokergto mdf --pot 1 --bet 0.5 --lang zh
```

There is no `poker solve` yet: `tools/run_solver.py` and `src/pokergto/solver/proofs.py` are M2
work, and `src/pokergto/solver/` currently holds `tree.py`, `games.py`, `cfr.py` and
`exploitability.py` only.

## UTF-8, because the second language is Chinese

Windows consoles still default to a legacy code page, which turns Chinese output into mojibake on a
machine whose locale is not `zh-CN`.

- The CLI already handles itself: `pokergto.cli.main` calls `stream.reconfigure(encoding="utf-8")`
  on stdout and stderr, so `python -m pokergto --lang zh` prints correct Chinese without you
  touching system settings. `_bootstrap.utf8_stdio()` exists for tools that want the same thing.
- For anything that writes Chinese without going through those entry points — `type`, `cat`, a
  redirected file — the terminal code page is what matters. `chcp 65001` (cmd), or
  `[Console]::OutputEncoding = [System.Text.Encoding]::UTF8` (PowerShell), or a terminal profile
  setting, all work. It is a per-terminal fix, which is why the code-level reconfigure is the
  default and this is the note.
- The portable, process-scoped version: `python -X utf8 setup/doctor.py`, or
  `PYTHONUTF8=1 python -m pytest`. This affects only the interpreter you just launched.
- Font rendering in the terminal is a separate problem from encoding. If Chinese shows as boxes, the
  console font is the cause, not the bytes.

Every `.md`, `.yaml` and `.json` file in this repository is read and written as UTF-8 explicitly —
there is no `open(path).read()` anywhere in `src/` or `tools/` — so a Windows GBK default cannot
corrupt a file on commit. `.editorconfig` exists to make editors do the same, and
`.gitattributes` forces `eol=lf` because CRLF drift would break the byte-diff gate below.

## The daily loop

| Command | What it proves |
|---|---|
| `python -m ruff check . --no-cache` | lint, including the docstring and type-annotation rules in `pyproject.toml` |
| `python -m ruff format --check .` | formatting identity, without reformatting |
| `python -m mypy` | strict typing of `src/pokergto` (`files` is set in pyproject, so no path argument needed) |
| `python -m pytest` | engine tests (`testpaths = ["tests"]`) |
| `python -m pytest -m "not slow"` | the fast subset CI runs on every push |
| `python -m mkdocs build --strict` | the docs site builds with no broken links and no warnings |
| `python -m mkdocs serve` | live preview at `http://127.0.0.1:8000` |
| `python -m pre_commit run --all-files` | every gate below, in one shot |

`mypy` never gets a path argument: `files = ["src/pokergto"]` in `pyproject.toml` is the decision, and
`tools/` plus `tests/` are type-checked loosely on purpose (build glue and assertions).

**The verified state of this repository at the time of writing**, so nobody reads the table above as a
promise that these are green:

- `python -m ruff check . --no-cache` reports **335 findings** across `src/pokergto/**` and
  `tools/**`. The bulk is pydocstyle (`D102`, `D103`, `D105`, `D205`, `D209`), then `UP035`
  (deprecated `typing` imports, 17), `PLC0415` (imports inside functions, 16 — deliberate in
  `artifacts._registry()` and `gen_tables.build_hand_class_counts()`), `RUF001`/`RUF002` (35 + 5 —
  fullwidth `，、：` inside Chinese captions and docstrings flagged as "ambiguous unicode"), and 7
  `F401` unused imports. The `RUF001`/`RUF002` cluster is a configuration question, not a code
  question: in a bilingual repository the flagged characters are the content. Either the rule gets
  `ruff.lint.allowed-confusables` or a per-file ignore for the Chinese string sites, or the noise
  teaches contributors to skim the rest.
- `python -m ruff format --check .` would reformat **24 of 48** files, i.e. the codebase is not
  currently format-clean and the `ruff-format` pre-commit hook will rewrite files the first time it
  runs on them.
- `python -m mypy` reports **59 errors in 14 files**, concentrated in the new `src/pokergto/solver/**`
  (`Missing type parameters for generic type "ndarray"` — 32 `type-arg` errors under numpy 1.26
  stubs), plus two real ones in `cli.py:244` (the `# type: ignore[union-attr]` on
  `stream.reconfigure` is unused/wrong for this mypy version).
- `python -m pytest` collects **nothing** and exits 5: there is no `tests/` directory yet. pytest also
  warns that `testpaths` points at a missing directory.

So: `mkdocs build --strict` and the five `tools/check_*` / `gen_all --check` gates are green here;
`ruff`, `ruff format`, `mypy` and `pytest` are not, and the reason is M0/M2 content that is still being
authored, not a broken toolchain. CI reflects this (`ci.yml` says which job is gated and which is
reporting).


## The gates, and what each one costs

Run these after touching `src/pokergto`, `data/`, or `docs/`.

```bash
python tools/check_artifact_schema.py         # every data/gen artifact validates against data/schema
python tools/check_provenance.py              # every claim states its origin; proprietary licences rejected
python tools/check_bilingual.py               # en/zh mirror, template order, AUTO ids, term registration
python tools/inject_doc_tables.py --check     # no hand-edited number inside an AUTO block
python tools/gen_all.py --check --skip solver # committed data/gen == what the engine produces now
```

All five are fast except the last, which re-runs the 2,598,960-hand enumeration in
`gen_tables.build_hand_class_counts`. That enumeration is the point of the project, so it is not
going to be mocked out; but the same cost applies to `gen_all.py` (write mode).

Two things `--check` guarantees, both verified rather than assumed:

1. It is read-only. The manifest step writes into the temporary rebuild directory, never into
   `data/gen/`, so a verification run leaves `git status --short` unchanged. (It used to dirty the
   tree; the guard is `artifacts.write_manifest(..., root=out)` in `gen_all._step_manifest`.)
2. `--check --only manifest` is refused with an explanation instead of silently comparing a partial
   tree, because the manifest fingerprints everything. `FULL_TREE_ONLY` in `tools/gen_all.py` is that
   guard, and `--check` outside it compares the steps it can actually rebuild.

One consequence worth knowing when you bump a version: `manifest.json` holds content only -- digests,
`schema_version`, `engine_version`. Interpreter, numpy and commit sha are printed to the build log by
`gen_all` and are deliberately *not* committed, since a byte-compared artifact must not depend on the
machine that wrote it. Committing without regenerating is therefore fine; committing a generator change
without regenerating is not.

`pre-commit run --all-files` mirrors the CI jobs; if a hook cannot run offline (a hook environment has
to be downloaded), say so in the pull request rather than marking it green.

## Regenerating

```bash
python tools/gen_all.py                       # write everything
python tools/gen_all.py --only tables         # just the numeric tables
python tools/gen_tables.py --list             # the table ids that have builders
python tools/gen_tables.py --only table.02-03.mdf-vs-sizing --out data/gen
python tools/gen_tables.py --skip-expensive    # the loop without the 2.6M-hand enumeration
python tools/inject_doc_tables.py             # fill AUTO blocks in docs/** from data/gen/tables
python tools/inject_doc_tables.py --file docs/zh/02-the-math-of-one-decision/03-mdf.md
```

Order matters and `gen_all.py` enforces it: glossary → tables → ranges → solver → index → manifest.
The index counts authored artifacts, so it runs after them; the manifest fingerprints everything, so
it is last. If you regenerate, commit the regenerated `data/gen/` in the same pull request —
`data-drift.yml` fails otherwise, and it fails with the diff, not with a shrug.

## Docs preview

```bash
python -m mkdocs serve
```

`docs/en/index.md` and `docs/zh/index.md` are the two landing pages; the header dropdown switches
locale. The lesson tree is not in this file: `python tools/gen_all.py --only index` writes
`data/gen/nav.yml` from `data/src/curriculum.yaml`, and the `mkdocs_nav.py` hook hands it to mkdocs at
build time. mkdocs has no `!include` constructor, which is why a hook does the job instead of the config
file -- and why a lesson that exists on disk but is missing from the nav is a curriculum problem, not an
`mkdocs.yml` problem.

## Trainer

`trainer/` is a static Vue 3 + Vite app published under `/trainer/`. It is a *consumer* of
`data/gen` and contains no poker mathematics (ADR-0004), so it must be synced before it is run:

```bash
python tools/sync_trainer_data.py   # copies data/gen -> trainer/public/data, stamps src/generated/manifest.ts
cd trainer
npm ci
npm run dev                          # http://localhost:5173/trainer/
npm run build                        # vue-tsc --noEmit && vite build
```

`tools/sync_trainer_data.py --check` is the CI mode: it compares the copied tree and the stamped
manifest against `data/gen` without writing, so a bundle built against stale artifacts fails instead of
rendering a number an older engine wrote. Both `trainer/public/data/` and
`trainer/src/generated/manifest.ts` are gitignored build products -- if you find them in `git status`,
something added them by mistake, because a committed copy is a second source of truth for every number
in the project.

## If something is broken

```bash
python setup/doctor.py       # what is installed, what imports, what is reachable
python -m pip show pokergto  # is the editable install actually pointing at this checkout?
python -c "import sys; print(sys.executable)"
git status --short           # a --check run must leave the tree clean; if it did not, that is a bug
```

`doctor.py` is read-only by contract: it never installs, never writes, never regenerates. If you
find it changing anything, that is a bug worth an issue.
