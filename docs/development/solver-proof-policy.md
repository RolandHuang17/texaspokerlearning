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
`5e-5` at 20,000 CFR+ iterations, the one-street toys `2e-4` at 4,000. Those numbers come from
observed convergence, not from wishfulness: plain CFR reaches about `3e-3` in Kuhn's budget and
CFR+ about `1e-5`, so the gates sit a decade below what a correct run achieves and a decade above what
a broken one did during development (a squashed-reach bug stalled at 0.89, and no sane threshold
admits that).

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
| 1326-combo preflop model, fixed sizes | the real object cash and MTT preflop need; no future streets, so tractable exactly | exploitability → 0 |
| Push/fold Nash, 10–20bb, 2–6 seats, antes, optional ICM | highest rigour per unit complexity in the project | zero-sum identity + independent reference |

As of this writing `games.py` ships **two** of them (`kuhn`, `one_street_bluff_catcher`) and
`PUBLISHED_PROOFS` has four entries (Kuhn plus the three one-street bet sizes). Leduc and the two-street
toy are absent rather than half-built, deliberately: a subtly mis-specified game converges happily to
the equilibrium of a game that is not the one documented, which is exactly the failure ADR-0002 exists
to prevent.

### The cut, and the reasoning

**A full 6-max no-limit postflop NLHE solver is cut.** Not deferred — cut.

Producing one in pure Python/numpy is not feasible at useful accuracy; its output could not be
validated against anything, since there is no analytic 6-max postflop answer to compare with and
importing a commercial solver's output as "ground truth" is both the memorisation model this project
argues against and a copyright problem (`NOTICE`); and multiway postflop has no tractable exact
solution, so "close enough" would be a claim with no evidence under it. An unverifiable solver is not
a weaker version of a useful one, it is worse than none: it attaches the authority of code to a guess.

What replaces it: preflop *is* solved exactly (the 1326-combo model and push/fold Nash), and postflop
is taught in structured form — range-vs-range equity, MDF balance, indifference conditions, and
`src/pokergto/theory/multiway.py` deriving how the algebra changes with player count from
`d = 1 - (B/(P+B))^(1/N)`. A learner who understands that exponent needs no 6-max chart.

Also cut, for the same reason: GPU/C extensions, Monte-Carlo sampling of private cards inside the CFR
inner loop, external solver formats, abstraction ladders, browser-side WASM CFR. One tree format, two
CFR variants, and only the games that `proofs.PUBLISHED_PROOFS` can vouch for -- four today, listed in
the next section.

## Current state, honestly

What is wired and running, so a contributor does not have to take a documented rule on faith:

- `tools/run_solver.py` generates `data/gen/solver/**` for every entry in `PUBLISHED_PROOFS`, and
  `run_solver.py --check` compares bytes against the committed artifacts. `gen_all.py`'s `solver` step
  calls it.
- `ProofEntry.algorithm` is bound: `run_solver.run_entry` builds `CFRSolver(tree, plus=entry.algorithm
  == "cfr_plus")`, so the algorithm field is a constructor argument, not a caption.
- `tools/cost_probe.py` enforces a per-family wall-clock and memory budget, and CI runs it. A family
  with no declared budget fails the probe rather than passing silently.
- `tests/test_solver.py` carries the `solver` marker: the canonical Kuhn shape and its analytic
  `-1/18`, CFR+ beating CFR at equal iterations, best response checked against a brute force over pure
  strategies, solver frequencies against the closed forms per bet size, byte-identical reruns, and a
  proof gate demonstrated to be able to fail.

What is *not* here yet, stated because the gap is where the next work is:

- Five proof entries exist -- Kuhn and the 1-street toys at one-third, half, three-quarter, pot and
  double-pot (overbet) sizing -- all from two families. Nothing in this repository has yet solved a game
  with two *betting* streets: `games.two_street_probe` exists only inside
  ``tests/test_solver_vector.py`` as a padding regression, and Leduc is unwritten, so no lesson may cite
  a two-street solve until `PUBLISHED_PROOFS` does.
- A second implementation exists and is *not* the producer. `solver/vector.py` is the vectorised form the
  preflop model will need; `tests/test_solver_vector.py` holds it to machine-epsilon agreement (1e-17,
  not bit equality: the two forms sum identical terms with different associativity) with the textbook
  form under plain regret matching, and to independent satisfaction of the closed forms under CFR+, where
  flooring order legitimately changes which member of Kuhn's equilibrium family a solver lands in. It
  produces no artifact yet. Until it does, `solver/cfr.py` writes `data/gen/solver`.
- The speedup is measured and it is not yet the point. On the trees that exist -- six deals for Kuhn,
  twelve for the one-street toy -- the vector form runs 3.1x on Kuhn at 20,000 iterations and 1.1x on the
  toy. Both numbers are dominated by fixed per-step Python overhead rather than by the deal loop, so
  nothing here has demonstrated the win the preflop model needs; the phase that solves 1,326 combos is
  where that claim has to be won or dropped.
- Push/fold Nash and the 1326-combo preflop model are unimplemented, which is why chapters 05, 10, 11
  and 12 hold no range charts: an invented opening range would be the exact thing adr/0005 forbids.
- The vectorised tree-walk is not the current implementation. `solver/cfr.py` is the textbook per-deal
  traversal, chosen after it found two bugs the vector form hid; the vector idea is open work with
  Kuhn's `-1/18` as its oracle.

## What this means for a lesson author

Cite a solver result only for a game in `PUBLISHED_PROOFS`, and cite the artifact, not a screenshot of
the artifact. A lesson that teaches a *toy* result rather than the exact NLHE answer says so and makes
the distance between toy and reality part of the lesson — chapter 08-07 ("reading solver output without
memorising it") exists for that purpose. `status: ready` claims that both languages are complete and
that every number in the page is generated; if the evidence is not in `proofs.py`, the correct status
is `draft`, and `draft` is not an insult — it is the label that keeps the curriculum trustworthy.
