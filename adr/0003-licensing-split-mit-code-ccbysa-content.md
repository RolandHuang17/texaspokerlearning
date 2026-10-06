# 3. Two licences: MIT for code, CC BY-SA 4.0 for curriculum and data

Status: accepted (2026-10-06)

## Context

The repository contains two things with different economics. Engine code is infrastructure: someone
building a hand reviewer should be able to vendor `evaluator.py` without reading a lawyer. The
curriculum is the authored product — the work was deciding *why* each number is what it is, then
proving it in code — and its publication is the author's public portfolio.

A single licence has to pick a side. MIT lets anyone republish the lessons as their own course;
CC BY-SA would burden anyone reusing a card evaluator with copyleft on prose.

## Decision

- `LICENSE` — **MIT**, covering `src/**`, `tools/**`, `setup/**`, `trainer/**`, `.github/**`.
- `LICENSE-docs.md` — **CC BY-SA 4.0**, covering `docs/**`, `data/**`, and the narrative root files
  (`README*.md`, `ROADMAP.md`, `CONTRIBUTING*.md`, `adr/**`).
- `NOTICE` — states the split, its rationale, and the "no proprietary solver output" rule.
- `CITATION.cff` — lists both licences so attribution is machine-readable.

**Attribution required** makes the authorship citable, which is the point of publishing it.
**ShareAlike** stops the curriculum being enclosed into a paid course whose changes never return —
the paywall around exactly this knowledge is the thing the repository exists to argue against.

## Consequences

- Contributors must know which side of the line their change falls on; `CONTRIBUTING.md` and the
  pull request template say it in one line each.
- GitHub's licence detection reports MIT from `LICENSE` and cannot display the second licence, so
  `NOTICE` and the README's license section carry it explicitly.
- Switching prose to CC BY-4.0 later (maximal adoption over share-alike protection) is a
  one-file change with no architectural impact. CC BY-NC was rejected: it is not a free-content
  licence and would get the repository excluded from open-education listings.

## Alternatives rejected

- **MIT everywhere.** Cheapest legally, but the curriculum becomes anonymously repackable.
- **CC BY-SA everywhere.** Would infect vendored code; no one can reuse the evaluator cleanly.
- **CC0.** More "open", protects the author less, and forfeits the citation the repo exists to earn.
