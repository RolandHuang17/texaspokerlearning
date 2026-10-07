# 7. Sampled payoffs are allowed; sampled traversals are not

Status: accepted (2026-10-07). Closes the open question in
[ADR-0006](0006-exact-enumeration-is-bounded-by-measurement.md) by choosing its option A, and amends
[ADR-0002](0002-cfr-correctness-is-gated-by-proof.md) Rule B's cut list, which forbade "Monte-Carlo
sampling of private cards in the CFR inner loop" without saying what happens to the *payoff table* a
preflop solve needs.

## Context

`adr/0006` measured the object chapters 05, 10, 11 and 12 wanted: an exact preflop all-in equity matrix
over the 169 classes is `2,598,960 x 225,780 = 5.87e11` evaluations, about 740 hours on the development
laptop. It left three priced routes and said the choice belonged to the maintainer, because it changes the
epistemic status of four chapters. The maintainer chose **A: exact where the price is payable, sampled
where it is not, with the sampling declared**.

That route needed pricing before it could be written down honestly. The obvious implementation -- sample
`(hero, villain, board)` triples per class cell -- measures at 8,900 samples/s, so 20,000 samples across
28,561 ordered cells is **17.9 hours**: unaffordable, and the same order of magnitude as the exact matrix it
was meant to replace. It is unaffordable because it pays for noise twice. Sampling a deal randomises which
*combos* are in play, but combo choice is not the hard part -- for a fixed board, every combo pair can be
enumerated. The expensive part is the board.

## The mechanism this record adopts

`src/pokergto/preflop.py` samples boards and, for each one, scores all 1,326 holes in a single vectorised
pass and enumerates every dealable pair. Conditional on the board set, each cell is then **exact**: no combo
is sampled, no matchup is skipped, and the only randomness left is which boards were drawn.

Consequences of that choice, measured on the author's laptop (py3.12, numpy 2.x, 2026-10-07):

| boards | wall clock for the whole 169x169 grid | mean stderr over cells | worst stderr |
|---|---|---|---|
| 2,000 | 45 s | 0.0103 | 0.0242 |
| 20,000 | 7.3 min | 0.0030 | 0.0053 |
| 150,000 | ~55 min | ~0.0011 | ~0.0020 |

Against three cells computed exactly (`range_equity(mode="exact")` with the budget raised, 142.6 s, 176.8 s
and 177.5 s): `AA` v `KK` 0.8194605047, `AKo` v `QQ` 0.4324233606, `72o` v `22` 0.3258923844, the sampled
matrix deviates by **0.5 to 1.9 of its own standard errors** at 8,000 boards. That is the agreement
`tests/test_preflop.py::test_the_sampled_matrix_agrees_with_the_exact_cells_within_its_own_error_bars`
enforces, and the assertion is a multiple of the matrix's reported sigma, so the test checks the error bar
as well as the estimate.

The speed-up over per-cell sampling is roughly 150x at equal accuracy, and it comes from one fact: the
seven-card evaluation is shared. `evaluate7_many` scores 1,326 holes against one board for about 22 ms, and
that single pass serves all 14,365 unordered cells.

## Decision

1. **A sampled payoff table may be a `derived` artifact; a sampled traversal may not.** Terminal utilities
   for an all-in may be computed over a declared board sample. The CFR iterations themselves stay
   deterministic over whatever table was produced: regret sums, strategy sums and exploitability are
   computed exactly for the tree they are given. This is the boundary ADR-0002 was reaching for when it cut
   "Monte-Carlo sampling of private cards in the CFR inner loop"; it is written here because the original
   wording left the payoff table ambiguous, and the ambiguity would have been resolved by whoever needed the
   feature last.
2. **A sampled artifact declares its sampling or it does not ship.** The matrix carries `seed`, `boards`,
   `batches`, a per-cell `stderr` and a per-cell pair count. Two rules follow from it, both already enforced
   elsewhere in this repository: the seed is fixed so `tools/gen_all.py --check` remains a byte diff, and the
   error is an *independent-batch* dispersion rather than a binomial formula -- comparisons sharing a board
   are correlated, and treating 47,437 of them as independent trials understates the spread by about 3.2x.
   The first version of the validation test made exactly that mistake and flagged a real 1.6-sigma deviation
   as "6.2 sigma"; the closed-form hypergeometric standard deviation is now asserted against the empirical
   one in the same test.
3. **Being sampled is not the same as being usable, and that is a separate measurement.** A 0.0030 mean
   stderr is small next to a hand's equity, but a range boundary is set by comparing an equity to a
   threshold, so what matters is whether the *decision* flips. Before chapters 05, 10, 11 and 12 print an
   opening or defence range, the number of classes whose call/fold verdict changes between two independent
   seeds has to be measured and recorded in the artifact. If the count is not near zero at the chosen board
   budget, the budget goes up or the range is not published. No lesson is authored on top of an unmeasured
   boundary.
4. **Exact remains the default where it is payable.** Single preflop matchups (141-180 s per class cell) and
   every flop or turn range enumeration stay exact, and a lesson that can cite an exact cell cites the exact
   cell. The matrix is what is sampled, not the arithmetic around it.

## Consequences

- `src/pokergto/preflop.py` is engine code with nine tests: the identities that hold at any sample size
  (a class against itself is exactly 0.5, `equity[i, j] + equity[j, i] == 1` to the last bit, all 28,561
  ordered cells populated including the diagonal), determinism under a fixed seed, refusal of sample sizes
  too small to disperse, the closed-form check of the legality filter, and the two agreements with exact
  equity marked `slow`.
- The fast suite grows by about 26 s and the slow suite by about 5 min. That is the price of validating a
  sampled estimator against exact arithmetic in CI rather than in conversation.
- `tools/cost_probe.py` gains a board-matrix budget alongside the solver and enumeration budgets, because
  this is a cost a future refactor can silently multiply.
- The matrix artifact does not exist yet. This record fixes the mechanism, the boundary and the gate;
  generating `data/gen/preflop/**`, extending the schema for the sampling fields, and measuring boundary
  stability are the next pieces of work, and 05/10/11/12 stay unauthored until all three are done.
- A reader can now see, in one place, which numbers in this repository were enumerated and which were
  sampled -- and the second category is smaller and better labelled than the genre it replaces.

## Alternatives rejected

- **Per-cell Monte Carlo.** Measured 17.9 hours for the grid at 20,000 samples per cell, and it estimates
  each cell independently, so the matrix is not even internally consistent (zero-sum and diagonal
  identities hold only in expectation). Rejected on cost and on structure.
- **Publish the exact marquee cells and skip the matrix.** Cheaper, but it leaves chapters 05, 10, 11 and 12
  with ranges to *describe* and none to *derive*, and describing someone else's range is the memorisation
  model ADR-0001 and ADR-0005 exist to remove.
- **Present the sampled matrix as exact.** The genre error this project is built against: a number wearing
  the authority of code with no statement of its dispersion.
- **Wait for a faster evaluator.** The bottleneck was never the per-hand constant any more; it was sampling
  noise, and the fix was to stop sampling deals. A further 10x in evaluation speed buys the same grid in
  proportionally less time and changes no decision here.
