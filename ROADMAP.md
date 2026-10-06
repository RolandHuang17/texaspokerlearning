# Roadmap

This repository is built in milestones, and **every milestone ends in a state where CI is green
and the repo is independently publishable**. That is deliberate: the deliverable of an open
educational project is partly the visible history of it getting built.

Dependency graph:

```
M0 ──▶ M1 ──┬─▶ M2 ─▶ M3 ─┐
            │             ├─▶ M5 ─▶ M6 ─▶ M7
            └─▶ M4 ───────┘
```

`M1` blocks everything (it freezes the artifact schema, the provenance rule, and the math core
that later chapters cite). `M2 → M3` is the solver chain: a toy game must be validated before
anything is allowed to display its output.

---

## M0 — Skeleton that passes its own CI ✅

No poker content. The scaffolding is proven *before* there is content to retrofit onto it.

- [x] Root files: `README`(+`.zh`), `LICENSE`/`LICENSE-docs`/`NOTICE`, `CITATION.cff`,
      `CONTRIBUTING`(+`.zh`), `CHANGELOG`, `SECURITY`, `SUPPORT`, `CODE_OF_CONDUCT`, `ROADMAP`
- [x] `pyproject.toml` as the single Python config (ruff / mypy / pytest / coverage / entry point)
- [x] `setup/install.ps1`, `setup/install.sh`, `setup/doctor.py`
- [x] `data/schema/*.schema.json` drafted and enforced (`check_artifact_schema.py`, 14 schemas)
- [x] `.github/workflows`: lint, test, data-drift, docs, bilingual, trainer, pages, release
- [x] `tools/check_bilingual.py` passes on an **empty** docs tree (a `draft` lesson owes no file --
      `tests/test_gates.py` proves both halves of that rule)
- [x] `tools/gen_all.py --check` runs, and compares bytes against a fresh generation

**Exit test:** `pip install -e .` on win32 and ubuntu; `pre-commit run --all-files` green;
a contributor pull request that adds a `docs/zh/` lesson without its `docs/en/` twin fails loudly.

*Status: the win32 half is verified (editable install, all gates, full pytest on the author's machine).
The ubuntu half and `pre-commit` are CI-only -- the hook environments need package downloads that were
not available in the authoring environment, so this box is honest about being unverified locally rather
than claimed.*

## M1 — Math core + the first bilingual proof point ✅ ← first publishable state

- [x] `cards`, `evaluator` (+ naive cross-check reference), `equity` (exact + seeded MC),
      `notation`, `matrix13`, `ranges`, `board`, `odds`, `ev`, `spr`, `variance`
- [x] `artifacts`, `registry`, `render`, `cli`; `tools/gen_tables.py`,
      `tools/inject_doc_tables.py`
- [x] `data/src/glossary.yaml` v1 (237 terms) and `data/src/curriculum.yaml` v1 (15 chapters,
      all 92 lessons registered)
- [x] Chapters **00 Orientation** (3), **01 Combinatorics & Equity** (7),
      **02 The Math of One Decision** (8) complete in both languages -- 18 lessons / 36 files, every
      one `status: ready`, with at least two live hands verified by counting them rather than trusting
      the declaration

**Exit test:** a learner computes MDF and range equity from the CLI; the AUTO-table drift check
catches a hand-edited number; `status: ready` starts to mean something. *All three are asserted in
`tests/` and exercised by the `data` and `bilingual` CI jobs.*

## M2 — Toy games: Kuhn + the 1-street model ✅

- [x] `solver/tree.py`, `cfr.py`, `games.py`, `exploitability.py`, `proofs.py`
      (CFR+ is a mode of `CFRSolver`, not a separate module: `plus=True` switches regret-matching+ and
      iteration-weighted averaging, which is what `tests/test_solver.py` compares against textbook CFR)
- [x] Kuhn converges to game value `-1/18`; the 1-street toys assert bluff-indifference and MDF
      equality against `odds.py` -- the solver and the math chapters become each other's test
- [x] `tools/run_solver.py` writes `data/gen/solver/**` only for games registered in
      `PUBLISHED_PROOFS`, and `tools/cost_probe.py` enforces a per-family runtime and memory budget
- [x] Chapter **08 Toy Solvers** lessons 01–04 bilingual, each with generated AUTO tables

## M3 — CFR+, Leduc, and the visible differentiator  ← strongest early announcement

- [ ] `cfr_plus.py`; Leduc, ruddy and 2-street toys; per-game exploitability CSV
- [ ] GitHub Pages live: docs at root, trainer at `/trainer/`
- [ ] Trainer stood up as a **pure artifact consumer**: solver observation deck, 13×13 viewer,
      odds/MDF slider. Intentionally *no* range grading yet — the EV oracle lands in M4.

## M4 — Preflop engine, cash theory, and graded drills

- [ ] 1326-combo preflop model (HU and 6-max, fixed sizes); `solver/pushfold.py` Nash
- [ ] `theory/range_advantage`, `sizing`, `polarization`, `blockers`, `protection`, `frequencies`
- [ ] Chapters **03 Range Advantage**, **04 Bet Sizing**, **05 Preflop (Cash)**,
      **10 Heads-Up / BvB** bilingual (27 lessons)
- [ ] Trainer scores a painted range in **bb/100 of EV lost versus the spot artifact**, not just
      right/wrong

## M5 — Multiway, cash postflop, MTT  ← last point where the curriculum is cheap to change

- [ ] `theory/multiway.py` + a fixed-action 3-player toy that turns the multiway frequency
      collapse into a `derived` artifact instead of folklore
- [ ] `icm.py`, `variance.py` completed; `gen_pushfold_matrix.py` over M × seats × antes × payouts
- [ ] Chapters **06 Postflop (Cash)**, **07 Multiway**, **11 MTT I**, **12 ICM & push/fold**
      bilingual (25 lessons; 74 of 92 cumulative)

## M6 — Exploitation, drills at scale, trainer feature-complete  ← the 1.0 candidate

- [ ] `theory/exploitation.py`: re-score a *fixed* population model against the equilibrium and
      report its exploitability in bb/100, reusing `solver/exploitability.py` (no new solver)
- [ ] Chapters **09 Cash Practice**, **13 Population & Exploitation**, **14 Capstone**
- [ ] Quiz pipeline: authored bank + generated numeric variants with *computed* answers
      (`check_quiz_answers.py` refuses a hand-typed answer key)
- [ ] Remaining trainer screens: quiz, live-hand replay, push/fold drill, progress dashboard

## M7 — 1.0 hardening, no new topics

- [ ] Performance pass on `evaluator` and range-vs-range equity
- [ ] Coverage ≥ 90% on engine + theory; API reference via docstrings
- [ ] Learner dry run: a non-author follows README → first graded drill end to end on win32 and
      ubuntu without asking a question
- [ ] Terminology sweep against `glossary.yaml` in both languages

## M8 — Post-1.0 depth (only if each item clears its cost guard)

- [ ] Equity realization vs SPR as a computed quantity rather than a rule of thumb
- [ ] A 2-street 1326-combo toy, if `tools/cost_probe.py` still passes
- [ ] Balanced exploitation: how much to deviate when the read is 70% right

---

## Deliberately not planned

A real 6-max postflop NLHE solver, browser-side CFR/WASM, external solver format import, live
hand-history scraping, accounts or a backend, PWA/offline, and an AI "GTO coach" chat feature.
Each is argued in `adr/0002-cfr-correctness-is-gated-by-proof.md` and `NOTICE`.

## Good first issues

Look for the `good-first-issue` label. The three recurring shapes are the easiest to pick up:
a lesson with fewer than two live-hand examples, a glossary term whose `avoid` list is empty,
and a `reference` artifact that could be upgraded to `derived` by wiring it to `theory/*`.
