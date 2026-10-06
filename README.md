# texaspokerlearning — a bilingual, runnable GTO curriculum

**Stop guessing. Derive.**

An open, Chinese/English curriculum for no-limit Texas Hold'em that teaches the modern game from
derivable principles instead of memorised charts — with a Python engine that computes every number the
lessons cite, a CFR solver whose output is gated against analytic anchors, and a static trainer that
reads the same artifacts the docs do.

[![CI](https://github.com/RolandHuang17/texaspokerlearning/actions/workflows/ci.yml/badge.svg)](https://github.com/RolandHuang17/texaspokerlearning/actions/workflows/ci.yml)
[![Docs](https://github.com/RolandHuang17/texaspokerlearning/actions/workflows/pages.yml/badge.svg)](https://rolandhuang17.github.io/texaspokerlearning/)
[![code: MIT](https://img.shields.io/badge/code-MIT-green)](LICENSE)
[![content: CC BY--SA--4.0](https://img.shields.io/badge/content-CC_BY--SA--4.0-blue)](LICENSE-docs.md)
[![Python: 3.11+](https://img.shields.io/badge/python-3.11%2B-informational)](pyproject.toml)

中文入口：[README.zh.md](README.zh.md) · 在线阅读：
<https://rolandhuang17.github.io/texaspokerlearning/>

---

## Who this is for

You know the rules. You have real table time behind you. You can name a continuation bet and a
three-bet, and you also know that you mostly decide by feel — board texture "feels" wet, an opponent
"seems" capped, a shove is "probably" thin. Somewhere between you and the next level is the fact that
each of those words is a number, and that the number can be derived rather than quoted.

This repository is built for exactly that transition. It is not a beginner's course and it is not a
tip list.

## The one idea this repository is built on

**Nothing here is asserted. Everything here is recomputable.**

```
src/pokergto/**  computes  ->  data/gen/**.json  (committed)  ->  docs/{en,zh} and the trainer consume it
```

Three consequences you can verify rather than take on faith:

- **No number is typed into a lesson.** Tables sit inside `<!-- BEGIN AUTO:id -->` markers filled by
  `tools/inject_doc_tables.py`. `tools/gen_all.py --check` regenerates the whole tree and fails on a
  single differing byte, so a lesson's figure and the code that produced it cannot drift apart.
- **Solver output must be proved before it may be cited.** Kuhn's game value is analytically
  `-ante/18`; our run reaches `-0.055556` with exploitability `1.08e-05` chips per hand. A game with
  no entry in `src/pokergto/solver/proofs.py` produces no artifact, and a lesson citing an
  unvalidated game cannot reach `ready` status. This is not decoration: one real bug in this solver
  (an action probability folded in twice) converged to exploitability `0.89` while looking perfectly
  stable, and only the analytic anchor exposed it.
- **Every strategy claim states its origin.** `provenance` is a required schema field with
  `kind ∈ {derived, reference, external}`, and `external` accepts only four licences. Ranges traced,
  retyped or screenshotted from PioSolver, GTO Wizard, GTO+, Upswing or any paid course are refused by
  the validator, not by politeness. Claims that are neither derived nor licence-clean render
  `UNVERIFIED / 未核验` in both languages, in the page, not in a footnote.

### The loop that makes this more than a formula collection

Chapter 02 derives two closed forms from one equation — you must defend `pot/(pot+bet)`, and bluffs
must be `bet/(pot+2bet)` of your betting range. Chapter 08 hands the same spot to CFR, which has no
idea what the answer is. They agree, to digits, on every size:

| Bet size | Defense CFR found | `pot/(pot+bet)` | Bluff share found | `bet/(pot+2bet)` | Exploitability |
|---|---|---|---|---|---|
| 1/3 pot | 75.01% | 75.00% | 20.003% | 20.000% | 1.41e-05 |
| 1/2 pot | 66.667% | 66.67% | 25.000% | 25.000% | 9.34e-07 |
| 1x pot | 50.01% | 50.00% | 33.337% | 33.333% | 4.33e-05 |

*Generated from `data/gen/solver/*.json` by `tools/gen_tables.py`; the same numbers appear in
`table.08-04.solver-vs-algebra`.*

**Why it matters:** the two halves of the curriculum validate each other. Get the algebra wrong and
the solver disagrees; get the solver wrong and the algebra disagrees. Neither side has to be trusted.

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
pip install -e ".[dev,docs]"

# every number in the curriculum, at your command line
PYTHONPATH=src python -m pokergto odds
PYTHONPATH=src python -m pokergto mdf --pot 10 --bet 5 --opponents 2
PYTHONPATH=src python -m pokergto equity AhAs 7d2s --mode exact      # ~3 minutes: 1,712,304 runouts
PYTHONPATH=src python -m pokergto range "22+,ATs+,KJs+" --lang zh
PYTHONPATH=src python -m pokergto icm --chips 5000,3000,2000 --payouts 6000,3000,1500

python -m pytest -q                                  # 91 tests, incl. the 2,598,960-hand enumeration
python -m mkdocs serve                               # http://127.0.0.1:8000
```

Windows and Anaconda are first-class: `setup/install.ps1` bootstraps, `setup/doctor.py` diagnoses
read-only, and `python -m <tool>` is the documented form because pip's console scripts land off `PATH`
there. The CLI reconfigures stdout to UTF-8 so Chinese lesson text does not turn to mojibake.

## What is taught, and where it stands

**15 chapters, 92 lessons, authored in Chinese and English simultaneously.** The spine and every
lesson id live in `data/src/curriculum.yaml`; `ROADMAP.md` holds the milestone plan. Chapter counts are
structural (they do not change), so this table is safe to cite:

| Ch. | Track | Lessons | What it delivers |
|---|---|---|---|
| 00 Orientation | shared | 3 | How to use a derivable curriculum; derivation over memorisation; toolchain |
| 01 Combinatorics & Equity | shared | 7 | 1,326 combos → 169 classes; blockers; exact vs Monte Carlo equity; the evaluator; reading a 13×13 grid |
| **02 The Math of One Decision** | shared | 8 | **The derivation core:** break-even, pot odds, MDF, bluff-to-value, fold equity, one EV template, thin value, sizing asymmetry |
| **03 Range Advantage** | shared | 9 | Equity advantage vs **nut** advantage, capped ranges, texture, SPR and commitment |
| **04 Bet Sizing** | shared | 7 | Sizing governance: why 1/3 pot exists, why overbets exist, polarized vs merged, protection vs value |
| 05 Preflop (cash) | cash | 6 | RFI, big-blind defense, three- and four-bet ranges, squeeze, 100bb consequences |
| 06 Postflop (cash) | cash | 9 | Continuation-bet frequencies by texture, check-raise, floats and probes, double barrel, river value and bluffing |
| 07 Multiway | shared, exploits | 4 | Why the algebra changes with player count — derived, not quoted |
| 08 Toy Solvers | shared | 7 | Game trees, regret matching, CFR on Kuhn, convergence and exploitability, CFR+ |
| 09 Cash practice | cash, exploits | 5 | Node locking, plans not charts, hand-review workflow, leak audit |
| 10 Heads-up / BvB | HU | 5 | Two-player algebra, wide ranges, button dynamics, transfer to a full ring |
| 11 MTT core | MTT | 6 | What tournament math changes, stack zones, antes, bubble dynamics |
| 12 ICM & push/fold | MTT | 6 | The two-action model, Nash ranges, ICM vs chip EV, bubble factors, final table |
| 13 Population & exploitation | exploits | 6 | Where GTO stops being right: measuring a population and deviating without self-destructing |
| 14 Capstone | shared | 4 | The full loop, your own training plan, what GTO does not tell you |

Milestones M0–M2 are complete (engine, artifacts, bilingual gates, CI, solver with its proof
registry); M3–M5 are in progress, and `ROADMAP.md` records which chapters are currently drafted in
which language. A lesson is `ready` only when both languages exist and pass the parity gate — so the
statuses are machine-checked, not aspirational.

## What this repository will not pretend to be

Honesty about scope is part of the method, so:

- **No 6-max postflop solver.** Real ones need C++ and GPUs; a Python one that could not be verified
  would teach wrong things with the authority of code. Preflop is solved exactly where it is
  tractable; postflop is taught by derivation — which is a better teacher than a chart you cannot
  question. See `adr/0002`.
- **No solver screenshots, no scraped charts, no course transcriptions.** See `NOTICE`.
- **Multiway figures that folklore states with confidence** (continuation-bet frequencies collapsing
  from roughly 65% to single digits, bluff-to-value tightening to 1:6) are carried as `reference` +
  UNVERIFIED until the multiway model reproduces them from arithmetic. `07-01` explains the
  independence assumption and card removal before it reaches for any such number.
- **This is not real-time assistance.** No site integration, no hand-history scraping, no in-play
  advice. Using external assistance against human opponents is cheating, violates every site's terms,
  and is out of scope by principle rather than by omission — see `SECURITY.md`.

## Layout

```
src/pokergto/   engine: cards, evaluator, equity, ranges, odds, ev, spr, variance, icm
  theory/       the derivable principles lessons cite (range vs nut advantage, frequency balance, multiway)
  solver/       game trees, CFR and CFR+, best response and exploitability, the proof registry
docs/en|zh/     the 92-lesson spine, mirrored path-for-path and section-for-section; ROADMAP.md
                records how many are authored, and data/gen/index.en.json holds the machine count
data/schema/    JSON Schemas — the frozen contract for every artifact
data/src/       authored YAML: glossary, curriculum spine, spots, hands, quizzes
data/gen/       generated, committed, byte-deterministic artifacts
tools/          generators and the CI gates, incl. negative tests that prove the gates fail
trainer/        static Vue 3 + Vite consumer of data/gen (milestone M3)
.github/        CI matrix, Pages, releases, templates, dependabot
adr/            five decisions that are expensive to reverse, with the alternatives they rejected
```

## Contributing

Start with [CONTRIBUTING.md](CONTRIBUTING.md) (中文：[CONTRIBUTING.zh.md](CONTRIBUTING.zh.md)).
The two rules that are not style preferences: **every number is generated**, and **every lesson is
bilingual in the same pull request**. The most useful issue you can file is a
**Derivation request** — "this number is asserted somewhere and I cannot see why it is true".

Three contributions are especially wanted: a derivation gap in a lesson you could not follow, a
`reference` artifact that could be upgraded to `derived` by wiring it to `theory/*`, and a live hand
with its decision points and their costs.

## License

- **Code** (`src/**`, `tools/**`, `trainer/**`, `setup/**`, `.github/**`): [MIT](LICENSE)
- **Curriculum and data** (`docs/**`, `data/**`, root prose): [CC BY-SA 4.0](LICENSE-docs.md)
- **Why the split, and the provenance pledge**: [NOTICE](NOTICE)

If you reuse the curriculum, keep the `provenance` blocks intact and say what you changed. A derived
or reference chart with its provenance stripped is not a compliant redistribution.

## Star history is flattering; a corrected number is better

If you find an arithmetic or logical error, please open an issue or a pull request — the engine is the
authority, so a wrong claim in prose is a bug in code and gets fixed as one. Two were caught during
development and are recorded in `CHANGELOG.md` and in the tests that now pin them: a bluff-to-value
table that had been written with the MDF column in its place, and a multiway defense exponent of `N−1`
where the derivation gives `1/N`.

Educational content about a game of incomplete information. It does not constitute advice to gamble,
and nothing here promises a win rate: the value is the method.
