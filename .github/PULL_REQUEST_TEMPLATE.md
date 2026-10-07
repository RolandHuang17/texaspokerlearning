<!--
One licence line, one bilingual checkbox, and the gates with their measured costs.
This file is named as an enforcing artifact in adr/0003 and docs/development/bilingual-style.md, so
it has to stay a checklist someone can actually fail, not a welcome message.
-->

## Which side of the licence line is this change on

- [ ] **Code** (`src/**`, `tools/**`, `trainer/**`, `.github/**`) -- MIT, and I understand a fork may
      close-source it.
- [ ] **Curriculum or data** (`docs/**`, `data/**`, `adr/**`, root narrative `.md`) -- CC BY-SA 4.0, so
      a fork that republishes it must attribute and share alike.

Both, in one pull request? Say which commits are which. The two licences are a deliberate split
(`adr/0003`), not packaging, so a mixed diff costs a reviewer real time unless it is labelled.

## What changed, and where the number came from

One paragraph. If the change cites a number, name the artifact that carries it
(`data/gen/tables/...`, `data/gen/solver/...`, `data/gen/preflop/...`) or the engine function that
computed it. If the honest answer is "I do not know where this number came from", that is the most
useful thing you can report -- open a **Range provenance** issue instead of writing the sentence, and
let the artifact keep its visible `UNVERIFIED` badge until it resolves.

- [ ] Nothing here is a range chart, frequency table or solve trace taken from PioSolver, GTO Wizard,
      GTO+, Upswing, Run It Once, or any other paid or proprietary source (`NOTICE`).
- [ ] Every strategy claim I added carries a `provenance` block whose `derivation_ref` / `solver_run` /
      `upstream` resolves to something in this repository.
- [ ] No lesson says `ready`, "solved", or "optimal" beyond what `src/pokergto/solver/proofs.py` can
      vouch for.

## Bilingual parity (required)

- [ ] Every lesson I touched exists in **both** `docs/en/**` and `docs/zh/**`, same path, same 15
      sections, same AUTO ids, **in this pull request**.

Chinese is authored first, because the terminology rulings live in `data/src/glossary.yaml`. Then
answer this in your own words -- it is the part a script cannot check:

> Which sections' translation are you unsure about, and what is the alternative reading?

Machine-shaped Chinese that parses but does not teach is the failure mode this repository is most
exposed to. An honest "section 7 reads stiff" is worth more than a clean diff.

## Gates, and what they cost

Run what applies; paste the failing line rather than describing it. Measured on the development
laptop (Python 3.12, numpy 1.26.4, 2026-10-07):

| Command | Cost |
|---|---|
| `python -m pytest -m "not slow" -q` | 2:49 |
| `python -m pytest -q` (full, incl. the 2,598,960-hand enumeration and the matrix re-derivation) | 21:47 |
| `python tools/check_bilingual.py` / `check_provenance.py` / `check_artifact_schema.py` / `check_docs_links.py` | seconds |
| `python tools/inject_doc_tables.py --check` | seconds |
| `python -m mkdocs build --strict` | ~5 s |
| `python tools/gen_all.py --check` | 2:03 |
| `python tools/gen_all.py --check --include-slow` (re-derives the preflop matrix) | ~11 min |
| `python tools/gen_preflop.py --verify` | 23 s |
| `python tools/cost_probe.py` | ~2 min |
| `python -m ruff check .` / `python -m mypy` | seconds |

- [ ] If I changed `src/pokergto/**`, I regenerated `data/gen/**` (`python tools/gen_all.py`) and
      committed it **in this pull request**. `gen_all.py --check` fails otherwise, with the diff.
- [ ] If my change moves a measured cost, I updated `tools/cost_probe.py` and the number in this file,
      rather than letting a budget drift silently (`adr/0006`, `adr/0008`).
- [ ] If I added a slow step or a sampled artifact, I said which tier proves it per push and which one
      proves it on the schedule. Silence here is how "CI verifies it" stops meaning anything.

## Translation review note (for the human reading this)

- [ ] Provenance / licence judgement present -- this is the part `CODEOWNERS` routes to a human on
      purpose; an automated merge would make it unsound.
- [ ] Chinese prose read by a person, not only by `check_bilingual.py`.
