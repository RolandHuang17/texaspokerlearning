# Solver proof policy

> **Single-language by design:** these are contributor-facing engineering docs, and the
> bilingual-same-PR rule applies to curriculum content only (see adr/0005).

A learner cannot audit CFR output by intuition — auditing it is the skill they are here to acquire.
So the rule that replaces intuition is not "the numbers look right" and not "it converged". It is
ADR-0002: **convergence to *something* is guaranteed by the algorithm; convergence to *the right
thing* has to be demonstrated**, and the demonstration lives in the repository where CI can run it.

## Rule A: no solver claim ships unless it is provable in-repo

Every solver artifact must be validated by at least one of four mechanisms. All four are designed to
run in CI, and `src/pokergto/solver/proofs.py` is where each one is registered.

**1. Closed-form cross-validation.** The 1-street toy game is constructed so that its own equilibrium
*is* the algebra taught in chapter 02. At the converged average strategy, the bluffing hand must be
EV-indifferent, the defender's call frequency must equal `pot/(pot+bet)`, and the bluff share of the
betting range must equal `bet/(pot+2bet)`. `proofs._one_street_entry` asserts exactly those against
`pokergto.odds.minimum_defense_frequency` and `pokergto.odds.bluff_fraction_at_indifference` — not
against a copy of the formula, against the module the chapters teach from. If either half of the
repository is wrong, CI fails, and it fails naming which. This is the loop that makes the math core
and the solver each other's test.

**2. Exploitability thresholds.** `src/pokergto/solver/exploitability.py` computes an exact best
response, and `exploitability = (BR(0) + BR(1)) / 2` in chips per hand (the half-sum convention,
stated because the "total" convention also exists and mixing them silently halves every comparison).
Best response must commit to one action per *information set*, aggregating over every deal that shares
it; argmax per deal measures "how well would a cheat who sees your cards do", which is not a property
of the strategy at all. Every artifact records its exploitability, it must be at or below
`ProofEntry.exploitability_threshold`, and it must not increase with iterations. Current gates: Kuhn
`5e-5` at 20,000 CFR+ iterations, the one-street toys `2e-4` at 4,000, Leduc `1e-5` at 10,000. Those
numbers come from observed convergence, not from wishfulness: plain CFR reaches about `3e-3` in Kuhn's
budget and CFR+ about `1e-5`, so the gates sit a decade below what a correct run achieves and a decade
above what a broken one did during development (a squashed-reach bug stalled at 0.89, and no sane
threshold admits that).

**3. Known analytic results.** Kuhn poker's game value is `-1/18` chips per hand at `ante = 1.0`
(`proofs.KUHN_VALUE`, computed as `-Fraction(1, 18) * ANTE`, not typed as a decimal), and its
equilibrium family is parameterised by player 0's jack-bluffing frequency `alpha` in `[0, 1/3]`, with
player 1 calling the king always and the queen never. Landing on *any* member of that family with that
value is a hard check: `assert_jack_bluff_in_family` asserts membership, not a particular value,
because demanding one specific member would be testing the implementation's path rather than game
theory. Published benchmark values for tiny games are cited as `external` with
`license: public-domain-math` and a record in `data/src/licensing_manifest.yaml` (see
[data provenance](./data-provenance.md)).

**4. Property and metamorphic tests.** Regret sums non-negative and normalised; the zero-sum identity
(`BR(0) + BR(1)` equals the game value at equilibrium — `exploitability.zero_sum_residual` is the
in-repo handle for it); strategy invariant under infoset renaming and child ordering; a fixed seed
reproduces bit-identical output.

### The `ready` rule

> **A lesson may not carry `status: ready` in either language if it cites a game that is absent from
> `src/pokergto/solver/proofs.py`.**

Mechanically: `proofs.PUBLISHED_PROOFS` is the registry, `entry_for(game)` raises `ProofGateError` for
anything unlisted, and `require_validated(game)` is the handle meant to be called by generators and by
the docs gate. `tools/run_solver.py` refuses to write an artifact for a game with no entry, so the
artifact a `ready` lesson would cite cannot be produced at all. The chain is: no proof entry → no
artifact → nothing to cite → `ready` impossible. `data/schema/common.schema.json#/$defs/status` says
the same thing in the contract itself.

Contributors who touch the solver must extend `proofs.py` **in the same pull request**, with a real
anchor. "It converged" is not an anchor.

## Rule B: six small games, not one big one

| Game | Why it is here | Anchor |
|---|---|---|
| Kuhn poker | smallest game with bluffing, fully analytic | `-1/18` + equilibrium family |
| 1-street bluff-catcher, bet sizes ⅓ / ½ / pot | the bridge between chapter 02's algebra and an equilibrium | mechanism 1 |
| Leduc hold'em | canonical research benchmark, 2 streets, real card abstraction | exploitability → 0 |
| 2-street "ruddy" toy | protection, and the no-bluff-on-earlier-street result | exploitability → 0 |
| 1326-combo preflop model, fixed sizes | the real object cash and MTT preflop need | exactness **retracted** by adr/0006 (~740 h measured-rate for the matrix); payoff table sampled over boards and validated against exact cells, per adr/0007 |
| Push/fold Nash, 10–20bb, 2–6 seats, antes, optional ICM | highest rigour per unit complexity in the project | zero-sum identity + independent reference |

As of this writing `games.py` ships **three** of them (`kuhn`, `one_street_bluff_catcher`, `leduc`) and
`PUBLISHED_PROOFS` has seven entries (Kuhn, the one-street toy at five sizes, and Leduc). Leduc had to earn
its row: it has no closed form, so its gates are the three mechanisms that need none -- the best-response
value bracket, dominance at the information sets the solved strategy actually reaches, and exploitability.
The two-street toy with an analytic anchor is still absent rather than half-built: a subtly mis-specified
game converges happily to the equilibrium of a game that is not the one documented, which is exactly the
failure ADR-0002 exists to prevent.

### The cut, and the reasoning

**A full 6-max no-limit postflop NLHE solver is cut.** Not deferred — cut.

Producing one in pure Python/numpy is not feasible at useful accuracy; its output could not be
validated against anything, since there is no analytic 6-max postflop answer to compare with and
importing a commercial solver's output as "ground truth" is both the memorisation model this project
argues against and a copyright problem (`NOTICE`); and multiway postflop has no tractable exact
solution, so "close enough" would be a claim with no evidence under it. An unverifiable solver is not
a weaker version of a useful one, it is worse than none: it attaches the authority of code to a guess.

What replaces it: postflop is taught in structured form — range-vs-range equity, MDF balance,
indifference conditions, and `src/pokergto/theory/multiway.py` deriving how the algebra changes with
player count from `d = 1 - (B/(P+B))^(1/N)`. A learner who understands that exponent needs no 6-max
chart.

Preflop was going to be the exception — "solved exactly, because there are no future streets" — and that
is the one sentence in this policy that adr/0006 retracts. There are no future *decisions*, but there are
still five future *cards*: every preflop all-in cell enumerates `C(52,5) = 2,598,960` boards, and the
vectorised evaluator that was built to settle the question made the enumeration 4.8x to 20.4x faster, not
three orders of magnitude faster. The full exact 169x169 matrix prices out at about 740 hours on the
machine this project is developed on. So preflop is not claimed as solved exactly: adr/0007 chose the
sampled-payoff route and measured it (20,000 boards is the whole 169x169 grid in 7.3 minutes at a 0.0030
mean standard error, agreeing with three exactly-enumerated cells within 0.5 to 1.9 of its own sigmas at the
8,000-board validation size; the committed 20,000-board artifact sits at -1.79, +0.34 and +3.49 with both signs
present, and two fresh seeds at the same budget land inside 1.14).
Its boundary gate is measured and passed -- at 20,000 boards and two seeds, no class changes call/fold verdict
at the 0.5 line or at the big blind's MDF line facing a 2.5x open (closest class QQ, 9.6 sigmas away). The
artifact exists now: `data/gen/preflop/preflop.all-in-matrix.json`, with its sampling fields required by
`data/schema/preflop_matrix.schema.json` and its verification tiered by adr/0008. What chapters 05 and 10-12
still need from it is authored, not generated: a range-level number and its error bar come from a generator run
that has the per-batch panels in memory (the panels are not committed), and the range in question is lesson
content. Inventing an opening range to get a pretty matrix first is the thing adr/0005 exists to forbid.

Also cut, for the same reason: GPU/C extensions, Monte-Carlo sampling of private cards inside the CFR
inner loop, external solver formats, abstraction ladders, browser-side WASM CFR. One tree format, two
CFR implementations, and only the games that `proofs.PUBLISHED_PROOFS` can vouch for -- seven entries
today, listed in the next section.

## Current state, honestly

What is wired and running, so a contributor does not have to take a documented rule on faith:

- `tools/run_solver.py` generates `data/gen/solver/**` for every entry in `PUBLISHED_PROOFS`, and
  `run_solver.py --check` compares bytes against the committed artifacts. `gen_all.py`'s `solver` step
  calls it.
- `ProofEntry.algorithm` and `ProofEntry.implementation` are both bound: `run_solver.run_entry` builds
  `CFRSolver` or `VectorCFRSolver` according to the latter and passes `plus=` from the former, and the
  artifact's `algorithm` string must equal `entry.expected_algorithm`. So neither field is a caption --
  an artifact cannot describe arithmetic that did not run.
- `tools/cost_probe.py` enforces a per-family wall-clock and memory budget, and CI runs it. A family
  with no declared budget fails the probe rather than passing silently.
- `tests/test_solver.py` carries the `solver` marker: the canonical Kuhn shape and its analytic
  `-1/18`, CFR+ beating CFR at equal iterations, best response checked against a brute force over pure
  strategies, solver frequencies against the closed forms per bet size, byte-identical reruns, Leduc's
  tree shape and payoff bookkeeping, and two proof gates demonstrated to be able to fail.

What is *not* here yet, stated because the gap is where the next work is:

- Seven proof entries exist -- Kuhn, the 1-street toys at one-third, half, three-quarter, pot and
  double-pot (overbet) sizing, and Leduc -- from three families. There is no two-street game with an
  analytic anchor yet, so the solved cross-street numbers on offer are Leduc's, and Leduc is six cards with
  one size per street: it cannot be quoted as a hold'em line, and no lesson cites it as one.
- `tests/test_solver_vector.py` is the admission control, and what it requires is stated precisely because
  "the two implementations agree" is not achievable in general. Under plain regret matching the two are
  **bit-identical** -- zero difference in game value and average strategy on all seven entries, because the
  traversal sums the same terms. Under CFR+ they are not, and cannot be: `cfr.py` recurses deal by deal so
  it floors an information set between deals, `vector.py` sums a node's deals and floors once. What is
  required instead is that each form independently satisfies every registered gate, which is what the test
  parametrized over `PUBLISHED_PROOFS` checks.
- The vector form is now a producer, and the measurement it was written for exists. Leduc -- 360 deals, 36
  decision nodes, 3,780 information sets -- costs the per-deal recursion 0.23 s per iteration and the
  public-tree form 0.003 s: 68x at 50 iterations, 77x at 200, and 35 s for the 10,000 that its gate
  registers against roughly 38 minutes. Kuhn and the one-street toys are still produced by `cfr.py`,
  because on six and twelve deals the vector form's advantage is fixed-overhead noise (3.1x and 1.1x).
  The 1,326-combo preflop model was where the remaining doubt about that speedup belonged, and the doubt
  is now settled in the other direction: adr/0006 prices the whole enumeration, not just the traversal.
- The evaluator has the same two-implementation shape as the solver, and the same rule applies to it:
  `evaluate5_many` / `evaluate7_many` are producers only because they return the *identical integers* the
  scalar paths return, checked over every hand of five structurally chosen subdecks and millions of random
  boards, with a throughput floor in `tools/cost_probe.py`. `evaluate7_many_reference` keeps the literal
  best-of-21 definition beside the fast form as its oracle.
- Push/fold Nash and the 1326-combo preflop model are unimplemented. The preflop matrix the four chapters
  needed has since been committed as a sampled artifact (`data/gen/preflop/preflop.all-in-matrix.json`,
  adr/0007 and adr/0008), so the reason those chapters are still unauthored is no longer "there is no number
  base" -- it is that the ranges on top of the numbers are lesson content, and inventing an opening range to
  fill a table is the exact thing adr/0005 forbids. One mechanical consequence is worth knowing before
  authoring: the matrix commits equities, standard errors and the sampling declaration but not the per-batch
  panels, so a range-weighted equity and its error bar must be emitted by a generator run, not derived from
  the committed file.
- Three-player and ICM payoffs are not representable today. `tree.TerminalNode` stores one number per deal
  -- player 0's, with player 1 taking the negative -- and `exploitability.py` averages two best responses.
  Both conventions are correct for zero-sum and wrong for a three-way pot or an ICM tournament, so those
  rows of ADR-0002's table need a general-sum payoff vector and a Nash-conv measure before they can be
  gated, not just a new game function.

## What this means for a lesson author

Cite a solver result only for a game in `PUBLISHED_PROOFS`, and cite the artifact, not a screenshot of
the artifact. A lesson that teaches a *toy* result rather than the exact NLHE answer says so and makes
the distance between toy and reality part of the lesson — chapter 08-07 ("reading solver output without
memorising it") exists for that purpose. `status: ready` claims that both languages are complete and
that every number in the page is generated; if the evidence is not in `proofs.py`, the correct status
is `draft`, and `draft` is not an insult — it is the label that keeps the curriculum trustworthy.
