# Contributing

Thank you for wanting to make poker teaching verifiable instead of authoritative.

This repository teaches no-limit hold'em from derivable principles. That single premise decides most
of the conventions below: a contribution is strong when a reader can recompute it, and weak when it
asks to be trusted.

- Site: <https://rolandhuang17.github.io/texaspokerlearning/>
- Trainer: <https://rolandhuang17.github.io/texaspokerlearning/trainer/> (milestone M3 onward)
- Chinese guide: [CONTRIBUTING.zh.md](CONTRIBUTING.zh.md)
- Decisions and their reasoning: [adr/](adr/)
- Behaviour expectations: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)

## 30 seconds, from a clean clone

```bash
python -m venv .venv
# Windows PowerShell:  .venv\Scripts\Activate.ps1
source .venv/bin/activate
pip install -e ".[dev,docs]"

python -m pytest -q -m "not slow"     # the fast loop, 20k+ assertions
python -m ruff check .                # use python -m if the console scripts are not on PATH
python -m mkdocs build --strict
```

Windows note: `pip` may install console scripts to a user `Scripts` directory that is not on `PATH`,
so prefer `python -m ruff`, `python -m mkdocs`, `python -m pytest`. `setup/install.ps1` handles the
whole bootstrap, and `setup/doctor.py` diagnoses it read-only.

## The four public surfaces, and what a breaking change means

Version numbers promise that these four things keep their shape. Nothing else is public.

1. Engine signatures -- the functions in `src/pokergto/**`.
2. Artifact contracts -- the JSON Schemas in `data/schema/**`.
3. Lesson ids -- the identifiers in `data/src/curriculum.yaml`. **Never renumber.** A citation,
   a deep link, or another lesson's prerequisite list must not break under an edit. Adding is fine.
4. CLI report shape -- the output of `poker --json` and `--report`.

| Change | Bump |
|---|---|
| Schema breaking, lesson id removed or renamed, engine function removed | MAJOR |
| New lesson, chapter, engine module, artifact kind, solver game | MINOR |
| Text, arithmetic that preserves meaning, translation, bug fix inside a contract | PATCH |

A version-bumping pull request must add a `### Added` / `### Fixed` block under `[Unreleased]` in
`CHANGELOG.md`. `tools/check_release_notes.py` and `release.yml` enforce it.

## Two rules that are not style preferences

### 1. Every number is generated

`tools/gen_all.py` computes `data/gen/**`, and lessons cite those artifacts through AUTO markers.
`tools/gen_all.py --check` is a byte comparison against a clean regeneration; if it fails, the
committed tree no longer describes what the engine produces.

So: **edit the generator, never the artifact.** And do not type a number into a lesson that a
generator could produce -- if you find yourself writing a table by hand, that is a signal that a
builder is missing in `tools/gen_tables.py`.

### 2. Every lesson is bilingual from birth

`docs/en/<chapter>/<lesson>.md` and `docs/zh/<chapter>/<lesson>.md`, same path, same 15 sections,
same AUTO ids, **in the same pull request**. `tools/check_bilingual.py` proves structure; the
translation being faithful rather than machine-shaped is a human review item, and the pull request
template asks you to say which sections you were unsure about.

Chinese is written first, because the terminology decisions (`data/src/glossary.yaml`) are where the
teaching happens. `docs/development/bilingual-style.md` covers the details.

## Three contribution paths

### Fix or write a lesson

```bash
# 1. Register the lesson if it is new: id, slug, bilingual titles, prerequisites, per-language status
$EDITOR data/src/curriculum.yaml
python tools/gen_curriculum_index.py --allow-unauthored

# 2. Copy the template. Its H2 text must match the 15 lesson_template strings exactly.
cp docs/_template/lesson.md.tmpl docs/zh/<chapter-slug>/<slug>.md
cp docs/_template/lesson.md.tmpl docs/en/<chapter-slug>/<slug>.md

# 3. Compute every number you intend to cite before writing the sentence that contains it
PYTHONPATH=src python -m pokergto odds
PYTHONPATH=src python -m pokergto mdf --pot 10 --bet 5 --opponents 2
PYTHONPATH=src python -m pokergto equity AhAs 7d2s --mode auto

# 4. Fill AUTO blocks, then run the gates
python tools/inject_doc_tables.py --file docs/zh/<chapter-slug>/<slug>.md
python tools/inject_doc_tables.py --file docs/en/<chapter-slug>/<slug>.md
python tools/check_bilingual.py && python -m mkdocs build --strict
```

A lesson is not `ready` because you finished writing it. It is `ready` because
`python tools/check_bilingual.py` reports zero missing twins, zero section drift, and zero AUTO ids
in one language and not the other -- and because each of its numbers resolves to an artifact.

### Add or fix engine code

```bash
python -m pytest tests/test_<module>.py          # start here; tests/ mirrors src/
python -m pytest -q --cov=pokergto --cov-report=term-missing
python -m mypy                                    # src/pokergto is strict
python -m ruff check . && python -m ruff format .
```

Two invariants never regress, and both exist because they were once broken:

- `evaluate7` is a *proved* fast path, not the definition. The definition of the game -- best of the
  C(7,5) sub-hands -- is `evaluate7_reference`, kept separately so the optimisation can be measured
  against it over 20,000 random boards.
- Monte Carlo results carry their own error bar. A number without `stderr` is not a measurement.

### Add or change solver results

Solver work is not ordinary code work here. **A number produced by an unverified solver is worse than
no number**: it is wrong, and it is dressed as mathematics. `adr/0002` is the full argument; the
mechanics are:

1. Add the game in `src/pokergto/solver/games.py`.
2. Register it in `src/pokergto/solver/proofs.py` with a validation anchor -- a closed form, a
   published benchmark, or a cross-check against an independent calculation.
3. `python tools/run_solver.py --game <name>` must pass every gate. A game with no entry in
   `PUBLISHED_PROOFS` produces no artifact, and a lesson citing a game that is not there cannot reach
   `status: ready`.

`python tools/cost_probe.py` fails the build when a solve exceeds its runtime or memory budget, which
is what stops "just one more street" from making the project unrunnable on a laptop. A full 6-max
postflop solve is deliberately out of scope; `adr/0002` explains what is computed instead and why.

## Declaring where a range came from

Before you add any range, chart, or numeric strategy claim: **no solver output or course content
owned by anyone else.** Not copied, not retyped, not traced from a screenshot -- `NOTICE` lists the
tools, and the ban is mechanical rather than polite: an artifact that cannot state a permitted
provenance fails `tools/check_provenance.py`, and `data/src/**` requires a human sign-off.

Write the `provenance` block in the YAML under `data/src/` and regenerate. If the honest answer is
"this is a reference chart an author built, not a solve", say exactly that -- `provenance.kind` has a
value for it. If the answer is "I do not know where this number came from", that is the most useful
thing you could report: open the **Range provenance** issue, and until it resolves the artifact
carries a visible `UNVERIFIED` badge in both languages. A badge that readers can see is worth more
than a confident number neither of us can defend.

## Question you are allowed to ask

> "I know roughly how to play this spot but not why. Teach me the why."

That is the **Derivation request** issue template, it is the highest-value issue type here, and it is
never too basic. If a lesson reads well but does not convince you, that is a defect report, not a you
problem.

## Style, briefly

- English and Chinese prose follow `docs/development/bilingual-style.md`. English identifiers, no
  transliteration of names or abbreviations.
- Comments explain why. Do not describe syntax in comments, and do not narrate what the next line
  obviously does.
- No emoji in commits, code, or docs.
- Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`), imperative, about
  72 characters.

## Opening a pull request

Branch from `main`, keep it focused, and run the fast loop before pushing:

```bash
python -m pytest -q -m "not slow"
python -m ruff check . && python -m mypy
python tools/check_bilingual.py
python tools/inject_doc_tables.py --check
python tools/gen_all.py --check
python -m mkdocs build --strict
```

`pre-commit run --all-files` mirrors these locally; CI runs the same commands as a backstop.

If a gate cannot pass yet, say why in the pull request rather than adding `|| true`. An assertion
that cannot fail is not an assertion -- the same rule that stops a lesson asserting an unverifiable
number stops CI asserting a check that was made to pass.

## Recognition

Contributions are credited in `CHANGELOG.md` per release. If you fixed a numeric claim that had been
wrong in a lesson, that entry names you, because finding it is the hard part.
