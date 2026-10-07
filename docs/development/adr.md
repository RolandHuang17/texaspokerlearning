# Architecture decisions, summarised

> **Single-language by design:** these are contributor-facing engineering docs, and the
> bilingual-same-PR rule applies to curriculum content only (see adr/0005).

The canonical records are `adr/0001`…`adr/0007` at the repository root:
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

**Correction, 2026-10-07:** Rule B's preflop row was justified by "no future streets, so it is tractable
exactly", and that premise was priced after the record was written. A preflop all-in still enumerates
`C(52,5) = 2,598,960` boards per cell, the vectorised evaluator speeds the enumeration 4.8-20.4x, and the
full exact 169x169 matrix still measures out at about **740 hours** on the development laptop. The row's
game remains; its exactness does not, and what replaces it is an open question. See `adr/0006` (the
canonical record) and its summary below.

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
backend, no accounts, no network calls to anything but its own static bundle (progress stays in the
browser), one loader (`trainer/src/lib/data.ts`) with hand-written types that mirror
`data/schema/*.schema.json`, and no mathematics re-derived in TypeScript: the odds/MDF control steps
over rows of a committed table, so every number it shows is a cell of an artifact.
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

## ADR-0006 — Exactness is bounded by measured cost, not by ambition

Supersedes part of ADR-0002 on one point: a claim that a computation is "tractable exactly" has to survive
being priced. The preflop all-in matrix was written into Rule B on the reasoning that no future streets
means a tractable enumeration, and the reasoning was sound about the tree and wrong about the deal: every
cell still runs the board out to five cards. Priced after the vectorised evaluator landed, on the
development laptop (py3.12, Windows, numpy 2.x, 2026-10-07): `evaluate5_many` 1,028,474 hands/s against
62,118 scalar (16.6x), `evaluate7_many` 313,984 against 46,296 (6.8x), the widest exact flop enumeration
37.9 s to 7.84 s, exact preflop hand-versus-hand 353.8 s to 17.3 s — and the full 169x169 exact matrix
5.87x10^11 evaluations, **~740 hours**. Three findings are part of the record because they changed the
code: vectorising the *definition* (best-of-21 in one array) is slower than the scalar algorithm;
batching one board at a time made the most common exact call eight times *slower*; and the fix was to
batch across boards, which is what produced the 20x. So affordability is declared and re-measured in
`tools/cost_probe.py` (a throughput floor, a wall-clock ceiling on the widest cited enumeration, and that
enumeration's committed number re-derived on every run), `EXACT_EVAL_BUDGET` stays at 4,000,000
evaluations because a 740-hour artifact is not reproducible by a reviewer, and no lesson may cite a
preflop matrix as `derived` until a later record chooses what replaces it — the three costed options
(exact marquee cells plus a declared Monte-Carlo matrix, a reduced preflop game solved exactly, or no
preflop solve at all) are written out in `adr/0006`. That choice has since been made: see ADR-0007.

## ADR-0007 — Sampled payoffs are allowed, sampled traversals are not

Closes `adr/0006`'s open question with its option A, and pins down a boundary ADR-0002 left ambiguous: it
cut "Monte-Carlo sampling of private cards in the CFR inner loop" without saying what a preflop solve may do
about the *payoff table* underneath it. The answer is that the table may be sampled and the traversal may
not — terminal utilities for an all-in may come from a declared board sample, while regret sums, strategy
sums and exploitability stay exact over whatever table they are given.

The mechanism is what made option A affordable enough to consider at all. Sampling a *deal* per cell prices
at 17.9 hours for the grid (measured 8,900 samples/s), because it pays for two noises at once: which combos
are in play, and which board comes. Combo choice is not the hard part — for a fixed board every dealable pair
can be enumerated — so `pokergto.preflop` samples only boards, scores all 1,326 holes per board in one
`evaluate7_many` pass, and is exact conditional on that board set. Measured: 22 ms per board, so 20,000
boards is the whole 169x169 grid in 7.3 minutes with a 0.0030 mean standard error, against three cells
computed exactly (`AA` v `KK` = 0.8194605047 and two others, 142-178 s each) within 0.5 to 1.9 of its own
sigmas. Two cautions are part of the record rather than footnotes. A binomial error bar on the comparison
count understates the true spread by about 3.2x, because pairs sharing a board are correlated — the first
version of the validation test made that mistake and called a real 1.6-sigma deviation "6.2 sigma", so the
test now checks the empirical error bar against a closed-form hypergeometric one. And being sampled is not
the same as being usable: a range boundary compares an equity to a threshold, so before chapters 05, 10, 11
and 12 print a range, the number of classes whose verdict changes between two independent seeds has to be
measured. It has been: at 20,000 boards, two seeds, all 169 classes, **zero classes change verdict** at the
0.5 line against a random hand and zero at the big blind's MDF line (0.7273) facing a 2.5x open, where the
closest class -- QQ -- sits 9.6 standard errors from the line. So the committed budget is 20,000 boards and
the open piece is the artifact itself, not the statistics behind it. A chapter needing a tighter spot (a
3-bet shove, say) re-runs that measurement instead of borrowing this one.

## Where each decision is enforced

| Record | Enforcing artefacts |
|---|---|
| 0001 | `tools/gen_all.py --check`, `tools/inject_doc_tables.py --check`, `data/gen/manifest.json`, `.gitattributes` |
| 0002 | `src/pokergto/solver/proofs.py`, `src/pokergto/solver/exploitability.py`, `status: ready` checks in `tools/check_bilingual.py`, `workflows/solver-regression.yml` |
| 0003 | `LICENSE`, `LICENSE-docs.md`, `NOTICE`, `CITATION.cff`, `.github/PULL_REQUEST_TEMPLATE.md` |
| 0004 | `trainer/src/lib/data.ts`, `tools/sync_trainer_data.py`, `workflows/trainer` job in `ci.yml`, `workflows/pages.yml` |
| 0005 | `data/schema/common.schema.json#/$defs/provenance`, `tools/check_provenance.py`, `CODEOWNERS` on `data/src/**` |
| 0006 | `tools/cost_probe.py` (evaluator throughput floor, exact-enumeration ceiling, re-derived equity), `EXACT_EVAL_BUDGET` in `src/pokergto/equity.py`, `tests/test_evaluator.py` |
| 0007 | `src/pokergto/preflop.py`, `tests/test_preflop.py` (identities, closed-form pair counts, agreement with exact cells); the sampling fields a `data/gen/preflop/**` artifact will have to carry |

