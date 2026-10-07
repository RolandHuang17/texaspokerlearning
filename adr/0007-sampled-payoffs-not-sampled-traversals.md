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
3. **Being sampled is not the same as being usable, and that is a separate measurement -- it has now been
   made.** A 0.0030 mean stderr is small next to a hand's equity, but a range boundary compares an equity to a
   threshold, so what matters is whether the *decision* flips. Measured at the committed budget of 20,000
   boards, two independent seeds, all 169 classes, comparing each class's all-in equity against an opponent
   distribution weighted by combos:

   | line | classes that change verdict between seeds | within 2 sigma of the line | closest class, in sigma |
   |---|---|---|---|
   | 0.5 against a random hand | **0** | 5 | 0.21 (the quartiles of the margin are 13.2 / 28.1 / 46.0) |
   | MDF 0.7273, big blind facing a 2.5x open | **0** | 0 | QQ at 9.6, then JJ 11.6, AKs 22.0 |

   Zero flips, and no class is anywhere near the noise at the line that actually matters. The budget is
   therefore 20,000 boards (8.3 min measured) rather than the 150,000 that the error bar alone would have
   suggested paying for. This is a property of *this* spot and *this* threshold, so a chapter that needs a
   tighter boundary -- a 3-bet shove, where two classes sit closer in equity -- re-runs the measurement rather
   than borrowing this one. `tests/test_preflop.py` guards the mechanism at a tenth of the budget; the numbers
   above are the artifact's claim.
4. **Exact remains the default where it is payable.** Single preflop matchups (141-180 s per class cell) and
   every flop or turn range enumeration stay exact, and a lesson that can cite an exact cell cites the exact
   cell. The matrix is what is sampled, not the arithmetic around it.

## Consequences

- `src/pokergto/preflop.py` is engine code with eleven tests: the identities that hold at any sample size (a
  class against itself is exactly 0.5 with zero dispersion, `equity[i, j] + equity[j, i] == 1` to the last
  bit, all 28,561 ordered cells populated including the diagonal), determinism under a fixed seed and movement
  under a different one, refusal of sample sizes too small to disperse, the closed-form check of the legality
  filter, the `1 / sqrt(boards)` behaviour of the error bar, and the agreements with exact equity marked
  `slow`.
- The fast suite grows by about 26 s and the slow suite by about 5 min. That is the price of validating a
  sampled estimator against exact arithmetic in CI rather than in conversation.
- `tools/cost_probe.py` gains a board-matrix budget alongside the solver and enumeration budgets (25 ms per
  board measured against an 80 ms ceiling), because this is a cost a future refactor can silently multiply.
- **The error bar of a derived quantity is a separate calculation, and getting it wrong is not
  conservative.** `equity_against` initially scaled a ratio by `sqrt(batches)` -- the correct scaling for the
  pair *count*, which is a sum -- and printed twenty-times-too-wide sigmas. The test that existed at the time
  asserted only that a range sigma is *wider* than the independent-cells formula, which an inflated value
  satisfies, so it passed. It now asserts both ends: a one-hot weight reproduces the stored column's sigma
  exactly, and the aggregate sits strictly between the naive quadrature and a single cell's sigma, under the
  `sqrt(168)` ceiling that perfect board correlation allows. Measured at 600 boards: aggregate/naive 6.15
  mean and 9.92 worst, aggregate sigma 0.0098 against 0.0167 mean per-cell sigma. The corresponding
  `adr/0002` lesson -- an optimisation must be proved, not read -- turns out to apply to error propagation
  too: a number that is only ever checked to be "not too small" will drift upward unnoticed.
- What is left is the artifact itself: `data/gen/preflop/**`, with `seed`, `boards`, `batches`, per-cell
  `stderr` and per-cell pair counts in the schema, generated at the 20,000-board budget this record settled
  on. Chapters 05, 10, 11 and 12 may be authored once it exists; the boundary question that gated them is
  answered above, and a chapter needing a tighter line re-runs that measurement rather than citing this one.
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
