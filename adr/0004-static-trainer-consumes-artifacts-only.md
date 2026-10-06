# 4. The trainer is a static artifact consumer — no backend, no re-derived math, no live solving

Status: accepted (2026-10-06)

## Context

An interactive trainer is where "play by feel" actually gets rewired: you paint a range, and the
repository should be able to tell you how much that mistake costs in bb/100. The obvious ways to
build one each carry a hidden cost:

- A server-side app with accounts and progress tracking needs hosting, secrets, and maintenance
  that a solo educational repository will not sustain.
- Recomputing poker mathematics in JavaScript creates a second implementation of every claim, so
  the docs and the trainer can now disagree with each other, which is the exact failure mode
  ADR-0001 was written to eliminate.
- Running CFR in the browser (WASM) is impressive and teaches the learner nothing that the Python
  CLI does not already teach them — while making the trainer slow and the dependency story ugly.

## Decision

The trainer is a **static single-page application** (Vue 3 + Vite, deployed to GitHub Pages under
`/trainer/`) whose only input is the committed artifacts in `data/gen/**`.

1. **No backend, no accounts, no network calls at runtime.** Progress is stored locally in the
   browser. There is nothing to secure, no bill, and the site cannot go down.
2. **One loader.** Every artifact read goes through `trainer/src/lib/artifacts.ts`, with types
   derived from `data/schema/*.schema.json`. Ad-hoc `fetch` of a data file is not permitted.
3. **No mathematics re-derived in TypeScript**, with one narrow exception: the odds/MDF slider may
   interpolate a *committed* table, and `tools/check_quiz_answers.py` proves the trainer's answer
   keys equal the engine's computed ones.
4. **Solver screens play recorded runs**, not live CFR: exploitability-vs-iteration CSVs and
   average-strategy JSON produced by `tools/run_solver.py`.
5. **Data sync is versioned.** `tools/sync_trainer_data.py` copies `data/gen` into
   `trainer/public/data` (gitignored) and writes `trainer/src/generated/manifest.ts` with each
   file's sha256 plus `schema_version` and `engine_version`. The build **fails** on version skew,
   so a stale trainer cannot be deployed quietly.

## Consequences

- The trainer and the docs cannot disagree, because they read the same bytes.
- The trainer is testable without a browser: vitest against fixtures exported by the Python engine.
- Learners cannot ask the browser to solve a new spot. That is a feature with a cost: the answer to
  "what about my weird spot?" is `poker solve …` on the CLI, which is more honest anyway — the
  browser version would hide the approximation being made.
- Choosing Vue over Svelte trades ~40 kB of shipped JavaScript for the maintainer's ability to keep
  editing it. Decided in favour of the maintainer; the architecture, contracts, screens, and CI all
  survive a future swap because none of them touch framework choice.

## Alternatives rejected

- **Next.js / Astro with a server route.** A backend surface with no backend need.
- **WebAssembly CFR in the browser.** Cost without pedagogy.
- **Reimplementing equity/MDF in TypeScript for snappier sliders.** Two implementations, one truth.
- **Accounts and cloud progress.** Privacy cost, hosting cost, and no learning benefit.
