# Architecture decisions, summarised

> **Single-language by design:** these are contributor-facing engineering docs, and the
> bilingual-same-PR rule applies to curriculum content only (see adr/0005).

The canonical records are `adr/0001`…`adr/0005` at the repository root:
<https://github.com/RolandHuang17/texaspokerlearning/tree/main/adr>. They live there, and not under
`docs/`, because an ADR is part of the engineering contract alongside `pyproject.toml`, `NOTICE` and
`LICENSE` — it must be readable by someone who has only cloned the code and never built the site, and
`docs/**` is licensed CC BY-SA 4.0 as curriculum content while these records are read as decisions
about the code. This page exists because mkdocs cannot link outside `docs_dir`, so a reader on the
site gets a summary here and a pointer to the originals. Summaries are not authoritative: when this
page and a record disagree, the record wins, and this page is the bug.

Changing any decision requires a **new** ADR that supersedes the old one; superseded records stay in
the directory marked `Status: superseded by ADR-00NN`. Do not edit history into agreement.

## ADR-0001 — Generated data artifacts are the single source of truth for every number

`src/pokergto/**` computes, `tools/gen_all.py` writes the results into `data/gen/**` as
byte-deterministic JSON, and **that tree is committed**. Lesson prose contains no hand-typed number:
every table sits inside an AUTO block whose content `tools/inject_doc_tables.py` renders from
`data/gen/tables/*`, and the trainer reads the same artifacts through one loader rather than
re-implementing poker mathematics in TypeScript. Determinism is by construction — keys sorted,
`ensure_ascii=False`, floats quantised to 12 decimals, fixed seeds, no timestamps inside artifact
bodies — which is what makes `gen_all.py --check` a pure byte diff and a solver change a reviewable
diff of numbers rather than noise. The rejected alternatives are the interesting part: numbers typed
by hand (the genre's default, and the exact failure being replaced) and generate-at-build-time-never-commit
(which would put the published numbers outside version control, so a cited claim could not be
reproduced). Bounded cost: regeneration churn, mitigated by `--only`, `.gitattributes` marking
`data/gen/**` generated, and a review rule that a solver diff over 2,000 lines gets manual spot review.

## ADR-0002 — Solver correctness is gated by proof, not by plausibility

Two rules enforced together. Rule A: every solver artifact is validated by at least one of four
in-repo mechanisms — closed-form cross-validation against `pokergto.odds`, exact exploitability
thresholds, known analytic results (Kuhn's `-1/18` and its `alpha ∈ [0, 1/3]` equilibrium family), and
property/metamorphic tests including bit-identical reproducibility under a fixed seed — and a lesson
may reach `status: ready` only if the game it cites is registered in `src/pokergto/solver/proofs.py`.
Rule B: the solver handles six small games and **explicitly cuts a full 6-max postflop NLHE solver**,
because one could not be produced at useful accuracy in pure Python, could not be validated against
anything, and multiway postflop has no tractable exact solution; GPU/C extensions, Monte-Carlo
sampling in the CFR inner loop, external solver formats, abstraction ladders and browser-side WASM CFR
are cut on the same reasoning. See [solver proof policy](./solver-proof-policy.md) for the authoring
rules that fall out of this.

## ADR-0003 — Two licences: MIT for code, CC BY-SA 4.0 for curriculum and data

`LICENSE` (MIT) covers `src/**`, `tools/**`, `setup/**`, `trainer/**`, `.github/**`; `LICENSE-docs.md`
(CC BY-SA 4.0) covers `docs/**`, `data/**` and the narrative root files (`README*.md`, `ROADMAP.md`,
`CONTRIBUTING*.md`, `adr/**`); `NOTICE` states the split and the no-proprietary-solver-output rule, and
`CITATION.cff` lists both licences so attribution is machine-readable. The reason a single licence
cannot work is that it has to pick a side: MIT everywhere would let anyone republish the lessons as
their own course, CC BY-SA everywhere would burden someone vendoring `evaluator.py` with copyleft on
prose. ShareAlike is chosen deliberately — enclosing this curriculum inside a paid course whose changes
never return is the paywall the repository argues against. Practical consequence: GitHub's licence
detection reports MIT only, so `NOTICE` and the README's licence section must carry the second licence
explicitly. CC BY-NC was rejected as not a free-content licence.

## ADR-0004 — The trainer is a static artifact consumer

Vue 3 + Vite, deployed to GitHub Pages under `/trainer/`, with `data/gen/**` as its only input. No
backend, no accounts, no runtime network calls (progress stays in the browser), one loader
(`trainer/src/lib/artifacts.ts`) with types derived from `data/schema/*.schema.json`, and no
mathematics re-derived in TypeScript except interpolation of a committed table for the odds/MDF slider.
Solver screens play *recorded* runs, not live CFR. `tools/sync_trainer_data.py` copies `data/gen` into
`trainer/public/data` (gitignored) and writes a manifest of sha256 plus `schema_version` and
`engine_version`, and the build fails on version skew so a stale trainer cannot be deployed quietly.
What this gives up is stated rather than hidden: a learner cannot ask the browser to solve a new spot,
and the answer to "what about my weird spot?" is the CLI — which is the more honest answer, because the
browser version would hide the approximation being made. Next.js with a server route, WASM CFR,
TypeScript re-derivation and cloud progress were all rejected.

## ADR-0005 — Provenance is a schema-required field, so an unattributed claim cannot validate

Every strategy-bearing artifact in `data/**` carries a `provenance` object with
`kind ∈ {derived, reference, external}`, `verified`, `confidence`, `license`, `upstream`, and the JSON
Schema makes it **required**, so a chart with no origin fails validation instead of failing review.
`verified` defaults to `false` and only three transitions set it true: a pointer into
`solver/proofs.py`, a closed-form derivation in `theory/**` with an executing test, or an external
source with a manifest-listed compatible licence. Everything else renders `UNVERIFIED / 未核验` in both
languages and is listed in the artifact's `unverified_claims`. This exists because the two endemic
failures of free poker education — retyped commercial solver charts, and confident folklore — are
integrity failures, and prose that says "please cite your sources" is not a control. See
[data provenance](./data-provenance.md) for the mechanics and the ban list.

## Where each decision is enforced

| Record | Enforcing artefacts |
|---|---|
| 0001 | `tools/gen_all.py --check`, `tools/inject_doc_tables.py --check`, `data/gen/manifest.json`, `.gitattributes` |
| 0002 | `src/pokergto/solver/proofs.py`, `src/pokergto/solver/exploitability.py`, `status: ready` checks in `tools/check_bilingual.py`, `workflows/solver-regression.yml` |
| 0003 | `LICENSE`, `LICENSE-docs.md`, `NOTICE`, `CITATION.cff`, `.github/PULL_REQUEST_TEMPLATE.md` |
| 0004 | `trainer/src/lib/artifacts.ts`, `tools/sync_trainer_data.py`, `workflows/trainer` job in `ci.yml`, `workflows/pages.yml` |
| 0005 | `data/schema/common.schema.json#/$defs/provenance`, `tools/check_provenance.py`, `CODEOWNERS` on `data/src/**` |
