# `data/` — the contract between the engine, the lessons and the trainer

Three directories, three different rules about who may edit what.

```
data/
├── schema/   JSON Schema for every artifact kind. FROZEN FIRST.
├── src/      Authored YAML. Human-reviewed. This is what you edit.
└── gen/      Generated JSON. Committed, byte-deterministic, machine-owned. Never hand-edit.
```

The direction of data flow is one-way: `src/` + `src/pokergto/**` → `gen/` → docs and trainer.
See `adr/0001-generated-data-artifacts-as-single-source-of-truth.md`.

## Regenerating

```bash
python tools/gen_all.py                     # write data/gen from data/src plus engine computation
python tools/gen_all.py --check             # regenerate into a temp dir and fail on any byte diff
python tools/gen_all.py --only tables/glossary
python tools/gen_all.py --check --include-slow   # the scheduled tier: re-derive the slow steps too
```

`--check` is what CI runs. If it fails, you edited something in `gen/` by hand, or you changed
engine code without committing the regenerated artifacts. Both are real mistakes; the message says
which one it found.

## `gen/` contents

| Directory | What is in it | Cost to re-derive |
|---|---|---|
| `glossary.json` | The generated terminology authority, from `src/glossary.yaml`. | seconds |
| `ranges/*.json` | 13x13 charts whose frequencies the engine derived from a stated cut (an MDF floor, an equity-needed-to-call). | seconds |
| `solver/*.json` | Recorded CFR solves: strategies, exploitability curve, proof entry. | ~90 s |
| `preflop/*.json` | The board-sampled preflop all-in matrix (169x169 equities **with a per-cell standard error**), plus the `sampling` block that makes it checkable. | **465-499 s, so this step is slow-tiered** |
| `tables/*.json` | Every numeric table lessons embed through an AUTO block. | ~4 min (one table enumerates 2,598,960 hands) |
| `quizzes/*.json` | Drill items whose answers the engine computed, never typed. | seconds |
| `index.*.json`, `nav.yml` | The curriculum index and the mkdocs nav fragment. | seconds |
| `manifest.json` | sha256, kind and size per artifact. Content only -- no clock, no commit sha. | seconds |

## What `--check` proves, and at which tier

One row above costs more than the rest put together, and `adr/0008` is the record of what happens then.
`preflop` is a `SLOW_STEPS` member of `tools/gen_all.py`: on an ordinary run its committed bytes are **carried
into** the tree being compared rather than exempted from it, so the manifest still fingerprints a complete tree
and a missing matrix is a hard failure instead of a quiet hole. Per push, CI then re-derives the part of that
artifact one batch determines -- `python tools/gen_preflop.py --verify`, about 23 seconds, which rebuilds batch 0
of the declared seed, compares its digest to `sampling.first_batch_sha256`, and re-derives every identity the file
claims from the cells themselves. The full 20,000-board re-derivation is
`.github/workflows/solver-regression.yml`'s job (weekly, plus `--include-slow` locally).

So: CI proves the matrix's bytes on a schedule and proves its *engine* on every push. Nothing here should be
read as "CI proves every committed artifact is byte-identical to a fresh generation" -- the sentence is false for
`preflop/` and true for everything else, and where the boundary sits is written into the workflow that runs it.

## `src/` contents

| File | What it is |
|---|---|
| `glossary.yaml` | The bilingual terminology authority. Chinese poker terms have no standard, so this file *is* the standard: `zh`, `en`, `abbrev`, `avoid` (rejected synonyms), `note_zh` (the ruling explained). A lesson that uses an unregistered term fails CI. |
| `curriculum.yaml` | The spine: 15 chapters, 92 lessons, ids, tags, prerequisites, per-language status. Lesson ids are permanent — never renumber. |
| `board_taxonomy.yaml` | Texture classes with the `pokergto.board` predicate that assigns them, so "wet board" always means a stated rule. |
| `licensing_manifest.yaml` | One record per external source, with `license` and `why_permitted`. |
| `spots/*.yaml` | Decision spots: seat, line, stacks, board, strategy, per-hand EV. |
| `hands/*.yaml` | Live-hand teaching examples with decision points. Format is ours; there is no site hand-history parser on purpose (see `NOTICE`). |
| `quizzes/*.yaml` | Authored drill items. Numeric ones are generated with **computed** answers; `tools/check_quiz_answers.py` recomputes every key. |

## The provenance rule, in one place

Every strategy-bearing artifact carries `provenance` with `kind` in
`derived` | `reference` | `external`. It is a **required schema property**, so a claim with no
origin does not validate — this is a control, not a guideline. Read
`adr/0005-provenance-is-schema-required.md` and the repo root `NOTICE` before adding anything.

The short version: no chart traced, retyped, or screenshotted from PioSolver, GTO Wizard, GTO+,
Upswing, or any paid course. Ranges are either computed here, authored here and independently
checkable, or cited from a licence listed in `licensing_manifest.yaml`. Claims that are none of
those render `UNVERIFIED / 未核验` in both languages and appear in `unverified_claims`.

## `gen/` and determinism

`gen_all.py` writes with `sort_keys=True`, `ensure_ascii=False`, a pinned float format, fixed seeds,
and **no timestamps inside artifact bodies**. That makes `--check` a pure byte-diff.
`manifest.json` records sha256, kind and size per file and is the only file allowed to churn.
`.gitattributes` marks `data/gen/**` as generated so diffs collapse by default while staying
reviewable.

A solver change that produces more than ~2000 changed lines is flagged for manual spot review in
`CONTRIBUTING.md` rather than rubber-stamped.
