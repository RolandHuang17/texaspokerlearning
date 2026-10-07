# 2. Solver correctness is gated by proof, not by plausibility

Status: accepted (2026-10-06), **partially superseded by
[ADR-0006](0006-exact-enumeration-is-bounded-by-measurement.md)** (2026-10-07). Rule A, the 6-max
postflop cut and the other five games stand unchanged. What ADR-0006 retracts is one premise and one
sentence: Rule B's justification for the preflop row ("no future streets, so it is tractable exactly")
and the claim that "preflop **is** solved exactly". The row's game is still on the list; what it is
solved *from* is an open question that ADR-0006 leaves to a later record.

## Context

The project teaches that "play by feel" is the thing being replaced. A solver that is subtly wrong
replaces it with something worse: **a wrong answer wearing the authority of code.** A learner cannot
audit CFR output by intuition — that is precisely the skill they do not yet have.

The temptation in this domain is to reach for a real no-limit hold'em solver: 6-max, 100bb stacks,
full postflop trees with variable bet sizes. That is what PioSolver and GTO Wizard do, and it is
what a "serious" repository would appear to do.

## Decision

Two rules, enforced together.

### Rule A — no claim ships unless it is provable in-repo

Every solver artifact is validated by at least one of four mechanisms, all of which run in CI:

1. **Closed-form cross-validation.** The 1-street toy game is built so that its own equilibrium
   *is* the algebra taught in chapter 02: at the converged average strategy, the bluffing hand must
   be EV-indifferent, the defender's frequency must equal `pot/(pot+bet)`, and the bluff-to-value
   split must equal `s/(1+2s)` for bet size `s`. The solver asserts these against
   `src/pokergto/odds.py`. If either the math module or the solver is wrong, CI fails. The two
   halves of the repository validate each other.
2. **Exploitability thresholds.** `solver/exploitability.py` computes an exact best-response value;
   every artifact records its exploitability and it must fall below the threshold registered in
   `solver/proofs.py`, and must not increase with iterations.
3. **Known analytic results.** Kuhn poker's game value is `-1/18` chips per hand and its
   equilibrium family is parameterised by the first player's jack-bluffing frequency
   `alpha in [0, 1/3]`, with the second player calling queens at `alpha + 1/3`. Landing on any
   member of that family, with that value, is a hard check. Published benchmark game values are
   cited as `external` with `license: public-domain-math`.
4. **Property and metamorphic tests.** Regret sums are non-negative and normalised; zero-sum
   identities hold (`BR_1 + BR_2` equals the game value at equilibrium); strategy is invariant under
   infoset renaming and child-ordering; **a fixed seed reproduces bit-identical output**.

A lesson may cite a game as `status: ready` only if that game appears in `solver/proofs.py`.

### Rule B — the solver solves six small games, not one big one

| Game | Why it is here | Anchor |
|---|---|---|
| Kuhn poker | Fully analytic; smallest game with bluffing | `-1/18` |
| 1-street toy (bucketed hand, check/bet ½·¾·pot/all-in) | The bridge between chapter 02's algebra and an equilibrium | Rule A.1 |
| Leduc hold'em | Canonical research benchmark, 2 streets, real card abstraction | exploitability → 0 |
| 2-street "ruddy" toy | Where protection and the no-bluff-on-earlier-street result appear | exploitability → 0 |
| 1326-combo preflop model, fixed sizes | The real object cash and MTT preflop need; no future streets, so it is tractable exactly | exploitability → 0 |
| Push/fold Nash, 10–20bb, 2–6 seats, antes, optional ICM | Highest rigour per unit complexity in the whole project | zero-sum identity + independent reference |

**Explicitly cut: a full 6-max postflop NLHE solver.** Producing one in pure Python/numpy is not
feasible at useful accuracy, its output could not be validated against anything, and multiway
postflop has no tractable exact solution. Rather than ship something unverifiable, preflop is
solved exactly and postflop is taught in *structured form* — range-vs-range equity, MDF balance,
indifference conditions, and `theory/multiway.py` deriving how the algebra changes with player
count. A learner who understands why `d = 1 - (B/(P+B))^(1/N)` needs no 6-max chart.

Also cut: GPU/C extensions, Monte-Carlo sampling of private cards in the CFR inner loop, external
solver formats, abstraction ladders, and browser-side WASM CFR. One tree format, two CFR variants,
six games. `tools/cost_probe.py` fails CI if any game exceeds its runtime/memory budget, which is
what stops this scope from sliding silently.

## Consequences

- The curriculum's most rigorous material is where proofs are cheapest: push/fold and preflop are
  provable; "solved" 6-max postflop is not, so it is not claimed.
- Some lessons teach a *toy* result rather than the exact NLHE answer. They say so, and mark the
  distance between toy and reality as part of the lesson (chapter 08-07: reading solver output
  without memorising it).
- Contributors touching the solver must extend `solver/proofs.py` in the same pull request, and
  `solver-regression.yml` runs on a schedule because it is too expensive for every commit.

## Alternatives rejected

- **Ship a 6-max postflop solver anyway.** Unverifiable, therefore actively harmful.
- **Import published range charts as "ground truth" and skip the solver.** That is the memorisation
  model this project exists to replace, and it is a copyright problem too (see `NOTICE`).
- **Trust CFR output because it converged.** Convergence to *something* is guaranteed; convergence
  to *the right thing* requires a best-response calculation. Exploitability is the gate, not the
  iteration count.
