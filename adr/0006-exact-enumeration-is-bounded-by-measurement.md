# 6. Exact enumeration is bounded by measurement, not by ambition

Status: accepted (2026-10-07). Partially supersedes [ADR-0002](0002-cfr-correctness-is-gated-by-proof.md):
its Rule B row for the 1326-combo preflop model, and the sentence "preflop **is** solved exactly", are
retracted. Everything else in ADR-0002 stands, including the 6-max postflop cut and the four proof
mechanisms.

## Context

ADR-0002's Rule B listed six games the solver will handle, and justified the preflop row like this:

> 1326-combo preflop model, fixed sizes | The real object cash and MTT preflop need; **no future
> streets, so it is tractable exactly**

That reasoning was written before anyone priced it. "No future streets" is true and it does remove the
tree, but it does not remove the *deal*: a preflop all-in still runs the board out to five cards, so
every cell of the payoff matrix enumerates `C(52,5) = 2,598,960` boards, or `C(48,5) = 1,712,304` once
four hole cards are known. The matrix is the cheap part; the deal is the whole bill.

The plan for this round said: build the vectorised evaluator first, then decide (the maintainer's
instruction was "先做向量化评估器再说" — build the batch evaluator, then we'll talk). That is what
happened. `evaluator.evaluate5_many` / `evaluate7_many` landed, proved against the scalar paths over
every hand of five subdecks and millions of random boards, and the enumeration paths in
`equity.range_equity` were switched to it. The measured result is below.

## Measurement

Same machine throughout: the author's laptop, Python 3.12, numpy 2.x, Windows, 2026-10-07. Wall clock,
`time.perf_counter`, no other load. These are the numbers `tools/cost_probe.py` now guards.

| Path | Scalar | Vectorised | Speed-up |
|---|---|---|---|
| `evaluate5` | 62,118 hands/s | 1,028,474 hands/s | 16.6x |
| `evaluate7` | 46,296 hands/s | 313,984 hands/s | 6.8x |
| `evaluate7` via best-of-21 in a vector | — | 39,305 hands/s | **0.85x (slower)** |
| exact flop equity, 884 v 442 combos (1,176 runouts) | 37.9 s | 7.84 s | 4.8x |
| exact preflop equity, one hand v one hand (1,712,304 runouts) | 353.8 s | 17.3 s | 20.4x |
| exact preflop class cell `AA(6) v KK(6)` (2,598,960 runouts x 12 combos) | refused by the guard | 141.1 s | — |

Two findings that changed the design, both of which the table above is the evidence for:

* **Vectorising the definition is not vectorising the algorithm.** Evaluating all 21 five-card
  sub-hands in one big vector call (39,305 hands/s) is *slower* than the scalar seven-card algorithm
  (46,296 hands/s), because 21 units of work divided by a 16.6x throughput gain is a wash. The direct
  seven-card rules therefore had to be duplicated in vector form, which is why `evaluate7_many` exists
  next to `evaluate7_many_reference` and why the pair is tested the same way `evaluate7` and
  `evaluate7_reference` are.
* **Per-board batching loses to block batching.** The first version scored one board at a time, and at
  two combos per board numpy's fixed call cost made hand-versus-hand exact equity *eight times slower*
  than the scalar loop (0.81 s against 0.11 s). Scoring every legal (board, combo) pair in one block
  removed the fixed cost and then removed the per-runout Python comparison loop too: 353.8 s to 17.3 s
  on the same enumeration. A throughput claim measured on wide ranges alone would have missed this,
  because the narrow case is the common one in the curriculum.

## Why the preflop matrix is out of budget

Cost of one exact class cell scales with `runouts x (combos_hero + combos_villain)`. Summed over every
unordered class pair, `sum(cA + cB) = 225,780` combos (the 169 classes carry 1,326 combos between them),
so the full exact 169x169 preflop matrix is

    2,598,960 runouts x 225,780 combos = 5.87 x 10^11 evaluations

At the measured real-loop throughput of 221,000 evaluations/s (the `AA v KK` cell: 31.2M evaluations in
141.1 s) that is **2.66 million seconds, about 740 hours, about 31 days** on this laptop, single
threaded, before any CFR iteration runs. The combo-level 1326x1326 object is worse: sharing scores
across holes per board cuts the evaluation term to 2.8 x 10^9, but the head-to-head aggregation then
needs `1081^2` comparisons per board, `3.0 x 10^12` in total.

Cutting the deal space does not rescue it either. Enumerating the 1,712,304 boards that remain once
both hands are known is *per cell*; there are 14,365 unordered class pairs, and 141 s per cell of the
cheapest shape (6+6 combos) is 563 hours even before the wider cells are counted.

So ADR-0002's premise was wrong, and it was wrong in the direction that matters: the object chapters
05, 10, 11 and 12 would cite cannot be produced exactly in this repository.

## Decision

1. **The two sentences are retracted.** "No future streets, so it is tractable exactly" and "preflop is
   solved exactly" are removed from the rule and replaced by the table above. `docs/development/adr.md`
   and `docs/development/solver-proof-policy.md` carry the correction; this record is the authority.
2. **Affordability is a measured property, declared in one place.** `tools/cost_probe.py` now enforces a
   throughput floor for the vectorised evaluator (100,000 seven-card hands/s against 315,843 measured)
   and a wall-clock ceiling on the widest exact enumeration any lesson cites (30 s against 7.84 s
   measured), and it re-derives that enumeration's committed number rather than restating it. A
   speed-up that is not guarded is a speed-up that will be lost in a refactor, and an "exact is
   affordable" claim that is not re-measured is a claim that decays as the code changes.
3. **Exact stays exact where it is affordable, and it is not quietly extended where it is not.** A flop
   range enumeration, a turn enumeration, and a preflop hand-versus-hand matchup are affordable and
   remain `derived` artifacts. A preflop *matrix* is not, so no lesson may cite one as derived until
   there is a decision about what replaces it (see Open question).
4. **`EXACT_EVAL_BUDGET` stays at 4,000,000 evaluations.** It already refuses the matrix cells (the
   `AA v KK` measurement above needed the guard raised deliberately, in a scratch script, not in the
   library). Raising it is a decision about what the repository can regenerate, not a performance tweak,
   because ADR-0001 requires every artifact to be reproducible by a reviewer.

## Open question (blocks lessons 05, 10, 11, 12)

Three replacements were costed against the measured table. None is chosen here, because the choice
changes the epistemic status of four chapters and belongs to the maintainer:

| Option | What preflop becomes | Measured cost | What it costs the project |
|---|---|---|---|
| A. Exact marquee cells plus a declared Monte-Carlo matrix | Hand-picked class matchups exact (141-250 s each, ~40 of them ≈ 2 h); everything else `range_equity(mode="mc")` with seed, iterations and standard error recorded in the artifact | **17.9 h** for 28,561 ordered cells at 20,000 samples each — the Monte-Carlo path still draws and scores one hand per iteration, measured at 8,900 samples/s, so the matrix is 5.7 x 10^8 iterations. Batching it the way the exact path was batched is the obvious follow-on but has not been measured, so it is not in this row. | The matrix is a *sampled* artifact. It stays reproducible (fixed seed) and honest (error bars), but ADR-0002 cuts MC sampling of private cards inside the CFR inner loop, and a preflop solve over a sampled matrix is adjacent to that line. |
| B. A reduced preflop game that *is* affordable exactly | Solve a preflop model over a deliberately small hand space (e.g. 10-30 representative combos per player, buckets with declared membership) and label it a toy in both languages | minutes — Leduc's 10,000-iteration solve is 35 s measured | Honest and provable, but it is not "the real object cash and MTT preflop need"; chapters 05/11 would teach structure from a toy range, not a range a player can memorise. |
| C. No preflop solve | Keep preflop in structured form — the combo arithmetic, MDF and indifference algebra that chapters 01/02 already derive, plus exact flop-conditioned equity — and state that the repository does not solve preflop | 0 | Cheapest and most defensible; loses the "we solved it ourselves" claim for the four chapters and their trainer screens. |

Whichever is chosen becomes ADR-0007, and the lesson set is written under it — not before.

## Consequences

- Chapters 05, 10, 11 and 12 stay `draft` until the open question closes. No preflop range number is
  authored on top of an unaffordable promise.
- The evaluator now has two seven-card implementations and one oracle relationship, which is one more
  pair to keep honest; the exhaustive-and-random cross-checks are in `tests/test_evaluator.py` and the
  throughput floor is in CI, so drift is loud.
- `range_equity`'s cost guard counts *evaluations*. The per-runout comparison term (`hero x villain`)
  is not in it and is larger for wide ranges; wall-clock budgets live here and in
  `tools/cost_probe.py`, not in the guard.

## Alternatives rejected

- **Say the vectorised evaluator unlocked the preflop matrix.** It cut the same enumeration by 4.8x to
  20.4x. The matrix needs three to four orders of magnitude. This is the whole record's point.
- **Raise `EXACT_EVAL_BUDGET` and let it run.** A 740-hour artifact is not regenerable by a reviewer,
  so under ADR-0001 it is not a committed artifact; it is a research run with no reproduction path.
- **Import a commercial solver's preflop matrix and label it `reference`.** Rejected for the same two
  reasons ADR-0002 rejects imported range charts: it is the memorisation model this curriculum argues
  against, and it is a licence problem (`NOTICE`).
- **Ship the matrix from Monte Carlo without saying so in the artifact.** The failure mode this project
  exists to prevent; `EquityResult` carries `stderr` as a first-class field precisely so a sampled
  number cannot masquerade as an exact one.
