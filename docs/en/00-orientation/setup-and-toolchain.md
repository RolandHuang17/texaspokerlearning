# Set up the toolchain: the CLI, random seeds and deterministic output

<!-- hands: 3 -->
<!-- terms: solver, determinism, generated-artifact, single-source-of-truth, rng-seed, monte-carlo-simulation, standard-error, sample-size, equity, spr, required-equity, minimum-defense-frequency, icm, combos, expected-value -->

## 本节目标 / Objectives

- Get the engine running locally, and say which invocation form you are actually using
  (`PYTHONPATH=src python -m pokergto ...` today, versus `poker ...` once the install succeeds).
- State the toolchain's two hard rules: always `python -m <tool>`, and every simulated result ships with
  a random seed.
- Explain why the same command must emit byte-identical output on two machines, and name the five
  implementation conventions that hold that property up.
- Read a standard error and a 95% interval, and say when the sample size has to go up.

## 前置知识 / Prerequisites

- `00-01`: the division of labour between curriculum, engine and trainer, and where an AUTO table's
  numbers come from.
- `00-02`: why a number has to be recomputable. This lesson is the one that puts "recompute" on your
  own machine.

## 核心原理 / The principle

Three rules, all of them measured rather than asserted:

1. **Always `python -m <tool>`.** `python -m ruff`, `python -m mkdocs`, `python -m pytest`,
   `python -m mypy`, `python -m pre_commit`, `python -m pokergto`. The bare names do not exist here.
2. **A random seed is part of the number.** Quote a simulated equity together with its `iterations`
   and its `seed`; with only the first, nobody can reproduce it.
3. **Determinism is what makes a gate possible.** `tools/gen_all.py --check` regenerates and compares
   bytes. That comparison only means something if the output is necessarily identical; otherwise it is
   red every morning and unread by Friday.

<!-- provenance: kind=derived verified=true -->
> !!! note "Provenance"
>     Rules 1 and 3 come from `docs/development/local-dev.md` and `adr/0001`; rule 2 comes from the determinism list in `adr/0001` and the implementation of `pokergto.equity`. All three are run live in the examples below.

## 推导 / Derivation

The path from "readers should be able to check us" to "here is what the code must guarantee" involves
no taste.

Suppose a lesson cites `n` tables. Two languages makes that `2n` copies. There are only two ways to
verify them: the reader trusts us, or the reader regenerates and compares. The second option requires
one property: **same code plus same input implies the same bytes.**

While that property holds, `--check` is a gate. The moment it fails, `--check` becomes noise. Four
things destroy it, and each has a written-down countermeasure:

| Breaks byte-equality | Symptom | Convention in this repository |
|---|---|---|
| Unstable key order | same data, different key sequence | `json.dump(..., sort_keys=True)` |
| Escaped CJK | Chinese turns into `\uXXXX`, diffs become unreadable | `ensure_ascii=False`, every file read and written as UTF-8 explicitly |
| Float formatting drift | `0.6666666666666666` next to `0.667` | pinned decimal places, `digits` declared inside the artifact |
| Timestamps in the body | every regeneration reddens the whole file | no timestamps inside artifacts; only `manifest.json` may churn |
| Sampling randomness | a simulated equity differs run to run | the seed is stored in the artifact, so `--check` compares it too |

Two more that are not mathematics but bite anyway: `.gitattributes` forces `eol=lf`, because CRLF drift
alone would break a byte comparison; and Windows consoles default to a legacy code page, which is why
`pokergto.cli.main` calls `stream.reconfigure(encoding="utf-8")` on stdout and stderr before printing
anything — the CLI fixes itself instead of asking you to change your system settings.

The seed rule follows the same logic. A simulated estimate is `ê = (1/N)ΣXᵢ` with standard error about
`√(ê(1−ê)/N)`, so the 95% interval is roughly `ê ± 1.96 × standard error`. Example 5 checks all three
numbers against the engine. Quadrupling N only halves the interval width: precision at the third decimal
is bought with sample size, and nothing else.

## 直觉 / Intuition

`python -m` is not the formal spelling of a command; it means "let the interpreter I am standing on
import that module". That sidesteps the whole pile of script directories that anything can write into
and nothing can find. Inside Anaconda, inside a venv, or inside CI, you type the same line and get the
same code the same Python actually resolved.

For seeds, the intuition is this: a simulation is not a number, it is one realisation of a random
process. The seed is that realisation's name. A simulated result without its name is like a claim
without its source — it can be believed, but never checked.

## 算例 / Worked examples

**Example 1 — the bare commands do not exist here.** Observed in Git Bash at the repository root:

```bash
ruff --version
mkdocs --version
poker --version
```

All three: `command not found`. As modules:

```bash
python -m ruff --version        # ruff 0.16.10
python -m mkdocs --version      # python -m mkdocs, version 1.6.1 from ...site-packages\mkdocs (Python 3.12)
python -m pytest --version      # pytest 7.4.4
python -m mypy --version        # mypy 1.10.0 (compiled: yes)
```

The reason is recorded in `docs/development/local-dev.md`: pip put its console scripts in
`...\AppData\Roaming\Python\Python312\Scripts`, and that directory is not on `PATH`.
`python setup/doctor.py` says it out loud as a WARN:
`WARN console scripts on PATH ... is NOT on PATH -- use python -m ruff, python -m mkdocs, python -m pytest`.

**Example 2 — before installing, check whether the engine can even be imported.** Observed:

```bash
python -c "import pokergto"        # ModuleNotFoundError: No module named 'pokergto'
python -m pip show pokergto        # WARNING: Package(s) not found: pokergto
```

So no editable install has been done on this machine. Two ways forward:

```bash
PYTHONPATH=src python -m pokergto mdf --pot 10 --bet 5 --opponents 2   # works right now
python -m pip install -e ".[dev,docs]"                                  # needed before `poker` exists
```

The second route is currently blocked by a purely mechanical detail: `pyproject.toml` declares
`readme = "README.md"` and there is no `README.md` at the root, which is exactly what
`python setup/doctor.py` reports as `FAIL pyproject readme ... pip install -e . will fail while
building metadata`. The way to proceed without touching the repository is to skip the metadata build
entirely: `python -m pip install -r requirements-dev.txt` — that mirror file exists precisely for this
path, and a `ci.yml` step keeps the two lists from diverging. Once the install succeeds, `poker xxx`
becomes the short form of `python -m pokergto xxx`.

The bootstrap sequence is copied from `docs/development/local-dev.md` and nothing in it is invented:

```bash
python -m venv .venv
source .venv/Scripts/activate            # Git Bash; in PowerShell use .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev,docs]"
python setup/doctor.py                   # read-only environment report, non-zero exit on failure
```

`.python-version` pins 3.12 and `pyproject.toml` requires `>=3.11`; `python --version` here returns
3.12.13.

**Example 3 — the output shows its working, not just its verdict.**

```bash
PYTHONPATH=src python -m pokergto mdf --pot 10 --bet 5 --opponents 2
```

```text
bet = 0.500 pot
MDF  = pot/(pot+bet) = 10.000/(10.000+5.000) = 0.6667
     with 2 opponents: d = 1-((bet/(pot+bet))^(1/2)) = 0.4227 each, joint 0.6667 (equals the heads-up MDF)
```

Add `--lang zh` for the Chinese build. It prints correct Chinese with no system setting touched,
because the CLI reconfigures its own streams — a detail that genuinely bites on Windows and is recorded
in `local-dev.md`.

**Example 4 — the engine refuses, and explains why.** Ask for exact preflop range-versus-range equity:

```bash
PYTHONPATH=src python -m pokergto equity AA --range-villain "88+,AKs,AQs" --mode exact
```

No number. You get `exact equity needs about 176,729,280 evaluations (2598960 runouts x 68 combos)`,
plus the instruction to use `mode='mc'` and accept a reported error bar. **Knowing when a tool refuses
you matters more than knowing one more subcommand.** Preflop is not beyond exact computation entirely:
one hand against one hand enumerates 1,712,304 runouts (Example 5).

**Example 5 — byte-identical runs, and how wide the bar is.** Same command, three times:

```bash
for i in 1 2 3; do PYTHONPATH=src python -m pokergto odds --json | sha256sum; done
```

All three digests are identical, beginning `1cbfa6b7456e28ad9d813a338296736b` (take your own output as
the authority on the rest). Seeded simulation behaves the same way: running
`equity AhAs 7d2s --iterations 60000 --seed 1 --json` twice gives one digest, and switching to
`--seed 2` changes it — the estimate moves from 88.43% to 88.22%.

The exact value for the same two hands: `--mode exact` returns `equity = 0.881937`,
`iterations = 1712304`, `stderr = 0.0`.

| Run | Point estimate | Standard error | 95% interval |
|---|---|---|---|
| `--iterations 20000 --seed 0` (defaults) | 88.04% | — | ±0.45%, covers 88.19% |
| `--iterations 60000 --seed 1` | 88.4258% | 0.00130605 | [88.1699%, 88.6818%], covers 88.19% |
| `--iterations 60000 --seed 2` | 88.22% | — | ±0.26%, covers 88.19% |
| `--mode exact` | 88.1937% | 0 | a single point |

The 60,000-run estimate sits 0.2321 percentage points from the truth — 1.78 standard errors. The
interval contains the exact value while the point estimate is not it. That is the entire argument for
publishing intervals: the default 20,000 runs are already 0.15 points off, and they do not look it.

## 生成表 / Generated tables

All three tables serve the claim above: anything recomputable gets recomputed. The first puts a rule of
thumb and an exact value in the same row so the gap is visible; the second is the SPR curve; the third
is the solver checking itself against algebra.

<!-- BEGIN AUTO:table.01-03.draw-probability-exact-vs-rule -->
| Outs | Exact, next card | Rule of 2 | Exact, two cards | Rule of 4 |
|---:|---:|---:|---:|---:|
|    3 |            6.38% |     6.00% |           12.49% |    12.00% |
|    4 |            8.51% |     8.00% |           16.47% |    16.00% |
|    5 |           10.64% |    10.00% |           20.35% |    20.00% |
|    6 |           12.77% |    12.00% |           24.14% |    24.00% |
|    8 |           17.02% |    16.00% |           31.45% |    32.00% |
|    9 |           19.15% |    18.00% |           34.97% |    36.00% |
|   10 |           21.28% |    20.00% |           38.39% |    40.00% |
|   12 |           25.53% |    24.00% |           44.96% |    48.00% |
|   15 |           31.91% |    30.00% |           54.12% |    60.00% |

<!-- provenance: kind=derived verified=true -->
!!! unverified "Provenance: derived in this repository · verified · confidence high"
    Derived at: `pokergto.equity#draw_probability`

<!-- generated by: tools/gen_tables.py from pokergto.equity::draw_probability -->
<!-- END AUTO:table.01-03.draw-probability-exact-vs-rule -->

<!-- BEGIN AUTO:table.03-07.spr-commitment -->
|  SPR | Equity to commit |
|---:|---:|
| 0.25 |           16.67% |
|  0.5 |           25.00% |
|    1 |           33.33% |
|  1.5 |           37.50% |
|    2 |           40.00% |
|    3 |           42.86% |
|    4 |           44.44% |
|    6 |           46.15% |
|   13 |           48.15% |
|   20 |           48.78% |

<!-- provenance: kind=derived verified=true -->
!!! unverified "Provenance: derived in this repository · verified · confidence high"
    Derived at: `pokergto.spr#all_in_equity_needed_from_spr`

<!-- generated by: tools/gen_tables.py from pokergto.spr::spr_commitment_table -->
<!-- END AUTO:table.03-07.spr-commitment -->

<!-- BEGIN AUTO:table.08-04.solver-vs-algebra -->
|        Size | Solved defence | Algebraic MDF | Solved bluff share | Algebraic bluff share | Exploitability (chips/hand) |
|---:|---:|---:|---:|---:|---:|
| 0.5000x pot |         66.67% |        66.67% |             25.00% |                25.00% |              0.000001 chips |
| 0.3333x pot |         75.01% |        75.00% |             20.00% |                20.00% |              0.000014 chips |
| 1.0000x pot |         50.01% |        50.00% |             33.34% |                33.33% |              0.000043 chips |

<!-- provenance: kind=derived verified=true -->
!!! unverified "Provenance: derived in this repository · verified · confidence high"
    Derived at: `src/pokergto/solver/proofs.py#PUBLISHED_PROOFS`

<!-- generated by: tools/gen_tables.py from pokergto.solver.cfr::solve -->
<!-- END AUTO:table.08-04.solver-vs-algebra -->

The third table is the strongest evidence this lesson can offer. One column is a defense frequency that
CFR iterated out without knowing the answer; the next is the same quantity from one line of algebra;
the last is exploitability. At half pot the solver says 0.666668, the algebra says 0.666667, and
exploitability is 9.3e-07 chips per hand. Two processes that share no assumptions agreeing to the fifth
decimal is what "determinism plus proof as the gate" looks like (`adr/0002`).

One cross-check belongs to this lesson itself: `spr --stack 78 --pot 13` prints 0.4615, and the SPR 6.00
row of the second table prints 46.15%. Same function, two independent routes, matching. That is the
kind of agreement worth demanding.

## 实战牌局 / Live hands

Each hand states which command ran, what it returned, the decision, and the price of the wrong one.
EV uses the one-street form: an all-in call is worth equity × (pot + 2 × risk) − risk.

**Hand 1 (`hand.00-03-spr-commitment-fold`) — 6-max cash, flopped three-bet pot.**
CO opens 2.2bb, Hero three-bets from the button to 6.5bb, CO calls; the small blind folds, so the pot is
13bb. Flop `Jd8h4c`, 95bb effective. CO moves all in.

- Depth first: `spr --stack 95 --pot 13` → `SPR = 95.0/13.0 = 7.308`, and
  `equity needed to commit = SPR/(1+2*SPR) = 0.4680`.
- Then the hand: `equity AQo --range-villain "KK+,AKs" --iterations 60000 --seed 1` → 22.00%
  (`wins` 21.21%, `ties` 1.60%, standard error 0.00169127, 95% interval [21.67%, 22.34%]).
- The test: 22.00% against 46.80%. Not close.
- Arithmetic: the pot after the call is `13 + 95 + 95 = 203`, and `0.4680 × 203 = 95.00` is exactly the
  amount risked — the threshold and the EV formula are the same statement. Substituting 22.00%:
  `0.22 × 203 − 95 = −50.34bb`.
- Decision: fold. The cost of the remembered rule ("AQ is always a call facing a jam") is −50.34bb,
  more than half a buy-in, once.
- Why the seed rule earns its place here: preflop range-versus-range cannot be computed exactly (see
  Example 4), so this 22.00% is sampled, and it must travel with `--iterations 60000 --seed 1`.

**Hand 2 (`hand.00-03-icm-chips-versus-money`) — tournament, three players left.**
Stacks 5000 / 3000 / 2000, payouts 6000 / 3000 / 1500. Hero is the 5000 stack. The 2000 stack shoves;
the pot is 2300 including 300 of blinds, Hero must call 2000 and leaves 3000 behind unexposed.
Hero holds `QcJs`, class `QJs`.

- Chip frame: needs `2000/4300 = 46.51%`.
- What Hero has: `equity QJs --range-villain "22+,A9s+,KTs+,QTs+,AJo+,KQo" --iterations 200000 --seed 1`
  → `equity 0.464533`, `stderr 0.00111522`, 95% interval [46.2347%, 46.6718%], `ties` 1.30%. The same
  call at the default 60,000 gives 0.466758 with interval [46.2766%, 47.0750%].
- Read it honestly: at 200,000 the point estimate is just below the 46.51% threshold and the interval
  top is just above it. At 60,000 the point estimate is above. **In the chip frame this call does not
  have an answer yet — the sample size is refusing to give one.**
- Money frame: `icm --chips 5000,3000,2000 --payouts 6000,3000,1500` prices Hero at 4258.93;
  after winning, `icm --chips 7000,3000 --payouts 6000,3000` prices the seat at 5100.00; after losing,
  `icm --chips 3000,3000,4000 --payouts 6000,3000,1500` prices Hero at 3342.86.
  The threshold solves `e = (4258.93 − 3342.86)/(5100 − 3342.86) = 916.07/1757.14 = 52.13%`.
- Arithmetic: `0.464533 × 5100 + 0.535467 × 3342.86 = 4159.11`, i.e. 99.82 below the 4258.93 of folding.
  The 60,000 estimate points the same way (−95.91).
- Decision: fold. No seed argument, no sample-size excuse: the 5.6-point gap between 46.51% and 52.13%
  is an order of magnitude wider than the error bar. One stated approximation: the 1.30% tie probability
  is folded into equity (the engine defines equity as `P(win) + ½·P(chop)`) rather than modelled as a
  third branch where both players survive.

**Hand 3 (`hand.00-03-rule-of-four-flip`) — cash, flop, depth exactly SPR 6.**
Pot 13bb, 78bb behind each, and Hero holds a clean 12-out draw on the flop (flush draw plus gutshot).

- Depth: `spr --stack 78 --pot 13` → `SPR = 6.000`, equity needed to commit `0.4615`. The SPR 6.00 row
  of `table.03-07.spr-commitment` says the same: 46.15%.
- The shortcut: "outs times four" gives 12 × 4 = 48.00%.
- The exact figure: the 12-out row of `table.01-03.draw-probability-exact-vs-rule` gives 44.96% within
  two cards. Same table: 9 outs is 34.97% against the rule's 36.00%; 6 outs is 24.14% against 24.00%.
- The verdict flips right here: 44.96% < 46.15% < 48.00%. **The shortcut says shove; the exact number
  says do not.**
- Arithmetic: the pot after the commit is `13 + 78 + 78 = 169`. At the true 44.96% that is
  `0.4496 × 169 − 78 = −2.02bb`; the rule had promised `0.48 × 169 − 78 = +3.12bb`. The error is not a
  rounding nuisance, it is a sign error.
- Decision: never take a shortcut within reach of a threshold. Approximations are safe only when the
  margin is far larger than their error, and the tables in this section are exactly the tool that
  measures "far".

## 范围图 / Range chart

An orientation lesson issues no range chart: this lesson's output is a command that runs, not a range to
defend. In strategy lessons `tools/gen_ranges.py` produces `range.*` charts, and the toolchain's role is
that **every chart carries the information needed to reproduce and to sanity-check it**. Look at
`data/gen/ranges/range.02-03.mdf-floor-vs-half-pot.json`: it stores an `orientation` field
(`akqjt98765432-desc-diagonal-pairs-upper-suited`) and a `checks` array whose two entries both report
`pass: true` — every cell's combo count is one of 4/6/12, and frequencies lie inside [0,1]. A chart here
is not only numbers, it is numbers plus the record of what those numbers must satisfy. To see a grid in
the terminal yourself, `PYTHONPATH=src python -m pokergto range "22+,ATs+" --lang zh` does it
(`00-01` Example 4 does exactly that).

## 为何成立、何时失效 / Why it works, when it breaks

**Where `python -m` stops helping:** in a shell with no interpreter activated. Run
`python -c "import sys; print(sys.executable)"` first and find out which Python you are standing on.

**Where determinism stops holding**, all of it nameable:

1. Sampled results are not supposed to be byte-identical unless the seed is fixed. The CLI defaults to
   `--seed 0`; what matters is that the seed lands inside the artifact.
2. Exact preflop is infeasible for range-versus-range (Example 4's refusal). Then you hold an estimator,
   and the interval travels with it.
3. Current state of `--check`: `python tools/gen_all.py --check --skip solver` raises
   `NameError: name '_kind_for' is not defined`; the equivalent that works today is
   `python tools/gen_all.py --check --skip manifest`. Also, `--check` is not read-only for the manifest
   step — it does write `data/gen/manifest.json`. Both facts are recorded in
   `docs/development/local-dev.md` rather than smoothed over. After any `--check` run, look at
   `git status --short` and delete the leftover if it appeared.
4. Machine state moves. When this lesson was written, `python -m ruff check . --no-cache` reported 2
   N817 findings, while `local-dev.md` records a historical snapshot of 335. The command is durable;
   the count is a snapshot. Re-run it.
5. `python -m pytest` works now (`-m "not slow"`: 87 passed, 4 deselected, 19.47s), whereas
   `local-dev.md` records that `tests/` did not exist yet and nothing was collected. Same distinction:
   snapshot versus present.

## 陷阱 / Common mistakes

1. **Typing bare commands copied from another platform's docs** — `mkdocs build`, `pytest`,
   `ruff check .`. None resolve here.
   *Cost*: an afternoon spent on "why can't I run something I just installed", when
   `python setup/doctor.py` states in one line that the Scripts directory is not on `PATH`.
2. **Quoting a simulated number without `iterations` and `seed`.**
   *Cost*: in Example 5, 60,000 runs at seed 1 give 88.43% and at seed 2 give 88.22%; both read as "88%",
   so a reader who re-runs gets a different figure that is equally correct, and starts doubting the tool
   instead of the report. The `--check` gate works only because the seed is pinned.
3. **Trusting the third decimal of a simulation to settle a marginal choice.**
   *Cost*: Hand 2, where the 60,000 and 200,000 run estimates change colour across the 46.51% line, while the real
   question (52.13% in money) was never close. Quadrupling N halves the interval: buy precision with
   samples, or switch to `--mode exact`.
4. **Using the shortcut near a threshold.** *Cost*: +3.12bb becomes −2.02bb (Hand 3). The reason
   `table.01-03.draw-probability-exact-vs-rule` exists is to print that 3.04-point spread
   (12 outs: 44.96% exact against 48.00% by rule) in advance.

## 练习 / Drills

- From a clean checkout: `python -m venv .venv` → activate → `python -m pip install -r requirements-dev.txt`
  → `python setup/doctor.py`. Copy every WARN and FAIL into a note and state the cause of each.
- Run `PYTHONPATH=src python -m pokergto range "22+,ATs+" --json | sha256sum` three times. Then change
  `--iterations` on an `equity` command and run it twice more; explain which changes are meaningful and
  which are the point of the exercise.
- Take `equity AhAs 7d2s` at 20,000 / 60,000 / 200,000 iterations, record each point estimate and
  interval, then run `--mode exact` and count how many intervals contain the truth and how many standard
  errors each estimate sits from it.
- Re-run the commands behind Hand 3 (`spr --stack 78 --pot 13` and the 12-out row of the draw table) and
  recompute the −2.02bb yourself.
- Open `data/gen/manifest.json` and explain why `python`, `numpy` and `git_sha` belong in it.

## 自测清单 / Self-check

- [ ] I know this machine wants `python -m <tool>`, and why.
- [ ] I can run the engine with `PYTHONPATH=src` before any editable install exists.
- [ ] I can explain why `--lang zh` prints correct Chinese with no system setting changed.
- [ ] I can name the five conventions behind deterministic output and how each relates to `--check`.
- [ ] I report simulations with sample size and seed, and I use the standard error to decide whether to sample more.
- [ ] I know when the engine refuses me (exact preflop, a five-card board) and how to read the refusal.

## 来源与置信度 / Provenance and confidence

<!-- provenance: kind=derived verified=true -->
Every number and command output below was measured in the repository root on Windows 11 with Git Bash
and Python 3.12.13. No content from a commercial solver or a paid course appears anywhere in this lesson.

| Content | Source type | Location |
|---|---|---|
| The `python -m` rule, the Scripts/PATH story, the UTF-8 story | Verified engineering record | `docs/development/local-dev.md`, plus the `ruff`/`poker` output above |
| Tool versions (ruff 0.16.10, mypy 1.10.0, pytest 7.4.4, mkdocs 1.6.1, node v20.15.1, pre-commit 4.6.2) | Measured | `python -m <tool> --version`; `python setup/doctor.py` |
| `pip install -e .` currently fails (missing `README.md`) | Measured FAIL | the `FAIL pyproject readme` line from `python setup/doctor.py`; `readme` in `pyproject.toml` |
| Byte-identical output for the same command | Measured | three matching `odds --json` digests; two matching `--seed 1` digests, a different one at `--seed 2` |
| 88.1937% exact, 1,712,304 runouts | `derived` | `equity AhAs 7d2s --mode exact`; `src/pokergto/equity.py` |
| 22.00%, 0.464533, 0.466758 and their intervals | `derived` | `equity ... --iterations N --seed 1`; table in Example 5 |
| SPR 7.308 / 6.000 and thresholds 0.4680 / 0.4615 | `derived` | `pokergto spr`; `src/pokergto/spr.py#all_in_equity_needed_from_spr` |
| ICM 4258.93 / 5100.00 / 3342.86 | `derived` | three `pokergto icm` calls; `src/pokergto/icm.py#icm` |
| Solver 0.666668 against algebra 0.666667, exploitability 9.3e-07 | `derived` | `data/gen/tables/table.08-04.solver-vs-algebra.json`; gates in `src/pokergto/solver/proofs.py` |
| The two known `gen_all.py --check` defects | Verified state (engineering side) | `docs/development/local-dev.md`; restated here, that file not modified |
| Why CFR needs proof rather than plausibility | Decision | `adr/0002`; the figures come from this repository's own solver |

## 术语 / Terms

<!-- terms: solver, determinism, generated-artifact, single-source-of-truth, rng-seed, monte-carlo-simulation, standard-error, sample-size, equity, spr, required-equity, minimum-defense-frequency, icm, combos, expected-value -->

| Abbrev | 中文 | English | Meaning in this lesson |
|---|---|---|---|
| — | 求解器 | solver | this repository's own CFR implementation, not a table aid |
| — | 确定性输出 | determinism | same input, same bytes; stronger than "repeatable" |
| — | 生成物 | generated artifact | the JSON under `data/gen/**`, machine-owned, never hand-edited |
| — | 唯一数据源 | single source of truth | each number computed once, referenced everywhere else |
| — | 随机种子 | random seed | the name of one realisation; reported alongside the result |
| — | 蒙特卡洛模拟 | Monte Carlo simulation | an estimate, shipped with an error bar |
| — | 标准误 | standard error | the spread of the estimator, used here to judge sample size |
| — | 样本量 | sample size | number of runs; ×4 buys only a ÷2 interval |
| — | 胜率 | equity | `P(win) + ½·P(chop)`, not the raw win rate |
| SPR | 筹码底池比 | stack-to-pot ratio | the `S/P` inside the all-in threshold |
| — | 所需胜率 | equity needed to call | the other face of the same line |
| MDF | 最低防守频率 | minimum defense frequency | the range quota derived from the same equation |
| ICM | 独立筹码模型 | independent chip model | the model that converts chips into money |
| — | 组合数 | combos | the weighting unit, used here by the chart's own `checks` |
| EV | 期望值 | expected value | the unit in which a wrong play is priced |
