# 1. Generated data artifacts are the single source of truth for every number

Status: accepted (2026-10-06)

## Context

This repository states thousands of numbers: minimum defense frequencies, bluff-to-value ratios,
equity tables, exploitability values, range percentages, ICM thresholds. They appear in 92 lessons,
in two languages, and in a browser trainer. A bilingual curriculum that hand-types its own
numbers diverges from itself within a handful of edits — and a curriculum whose numbers disagree
is not a teaching resource, it is a collection of assertions.

There is a second, sharper reason. The engine in `src/pokergto/` is one of the things being
learned. If a lesson's table were maintained by hand, a bug in the code and a bug in the prose
could disagree forever and nobody would notice.

## Decision

1. `src/pokergto/**` computes. `tools/gen_all.py` writes the results into `data/gen/**` as JSON,
   deterministically, and **`data/gen` is committed to the repository**.
2. Lesson prose contains **no hand-typed number**. Every table sits inside an
   `<!-- BEGIN AUTO:id --> … <!-- END AUTO:id -->` block, whose content is produced by
   `tools/inject_doc_tables.py` from `data/gen/tables/*`.
3. The trainer consumes those same artifacts through one loader (`trainer/src/lib/data.ts`).
   It never re-implements poker mathematics in JavaScript.
4. CI runs `gen_all.py --check`, which regenerates into a temporary directory and fails on any
   byte difference against the committed tree.

## Consequences

**Positive**

- A solver or math change becomes a *reviewable diff of numbers* in one pull request, touching
  both languages and the trainer at once.
- Docs and code cannot silently disagree; they are the same value rendered twice.
- The trainer is testable with no backend: fixtures are the committed artifacts.

**Negative, and how it is bounded**

- Regeneration churn: a small numerical change can rewrite many JSON lines. Mitigations:
  determinism by construction (fixed seeds, `sort_keys=True`, `ensure_ascii=False`, pinned float
  formatting, **no timestamps inside artifact bodies**), `--only <dir>` partial regeneration,
  `.gitattributes` marking `data/gen/**` as generated, and a review rule that a solver change
  producing a diff larger than 2000 lines gets manual spot-review instead of a rubber stamp.
- Contributors must understand that editing a number in prose is a category error. `CONTRIBUTING.md`
  states it, and `inject_doc_tables.py --check` enforces it.

## Alternatives rejected

- **Numbers written by hand in markdown.** The status quo of the genre, and the exact failure mode
  this exists to avoid.
- **Generate artifacts at build/deploy time, do not commit them.** Then the published numbers are
  not in version control: no diff review, no reproducibility for a cited claim, and a curriculum
  that can change without a commit. Reproducibility is a pedagogical promise here, not a nicety.
- **Have the trainer recompute the math in TypeScript.** Two independent implementations of the
  same claim is strictly worse than one: it doubles the bug surface and makes disagreement possible.
