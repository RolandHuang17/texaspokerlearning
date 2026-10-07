# 8. Sampled artifacts are tiered by measured cost

Status: accepted (2026-10-07). Implements a rule [ADR-0002](0002-cfr-correctness-is-gated-by-proof.md) already
published -- "`solver-regression.yml` runs on a schedule because it is too expensive for every commit" -- which
described a workflow file that did not exist, and extends it from solver runs to the first committed *sampled*
data artifact, [ADR-0007](0007-sampled-payoffs-not-sampled-traversals.md)'s preflop matrix.

## Context

`tools/gen_all.py --check` is the repository's byte-diff gate, and `ci.yml` runs it on every push and every
pull request. Until now every step in it cost seconds. The preflop matrix costs a measured **465-499 s** (23-25 ms
per board over 20,000 boards, depending on machine load; 2026-10-07), and two obvious answers are both wrong.

- **Pay it per push.** The data job goes from a couple of minutes to about ten, for a number nobody touched.
  A gate that charges eight minutes of waiting per commit gets routed around, and `--skip` on a byte-reproducibility
  gate is how a committed artifact becomes a fossil.
- **Leave the artifact out of `STEPS` and generate it by hand.** Then `compare()` reports it as "stale artifact
  committed with no generator producing it", because that is literally true. The gate turns red, or the artifact
  becomes uncommittable, and the repository loses the thing ADR-0007 was written to make citable.

Two cheaper-sounding tricks fail on inspection. **Path filtering** ("only re-derive when `preflop.py` changed")
misses the inputs that actually move the bytes: an edit to `artifacts.py`'s quantisation, a numpy bump, or a change
to the evaluator all change the artifact without touching a matching path -- a filter would report green while the
committed numbers stopped being what the engine produces. **A statistical drift test** needs a threshold, and a
threshold tuned until it passes is a decoration. The existing `tools/cost_probe.py` matrix probe made that concrete:
it samples 600 boards from `seed=202610071`, which is the committed artifact's own seed, so its boards are a
*nested subset* of the committed ones -- comparing an artifact against a subsample of itself proves nothing.

## The decision

1. **Per push, every non-sampled artifact is still byte-compared, and slow steps carry their committed bytes
   into the tree being checked.** `SLOW_STEPS` in `tools/gen_all.py` names the step and the directories it owns;
   `_carry_over()` copies them into the rebuild. That keeps the manifest complete (it fingerprints a whole tree,
   so a missing matrix would otherwise make the rebuilt manifest differ and read as a real change) and keeps the
   staleness scan honest. A skipped step whose artifact is **absent** is a hard failure: skipped must never read
   as deleted.
2. **Per push, a sampled artifact proves what one batch determines.** `tools/gen_preflop.py --verify` re-runs
   batch 0 of the artifact's own declared `seed`/`boards_per_batch` (1,000 boards, a measured 23 s), hashes the
   integer wins/ties/pair-count panel, and compares it byte for byte with `sampling.first_batch_sha256`. The
   digest is the exact kind of check, not a statistical one: no threshold to argue about, and it moves if the
   evaluator, the pair enumeration, the legality filter, the RNG arithmetic or the serialisation moves. The same
   command re-derives every identity the file claims from its committed cells -- zero-sum, the exact diagonal,
   the ordered-cell count, the declared decimal precision, the summary statistics, the closed-form comparison
   count, and the distance from the exhaustively enumerated anchor cells.
3. **The schedule re-derives the full board set.** `.github/workflows/solver-regression.yml` runs
   `gen_all.py --check --include-slow` (the whole tree, matrix included) plus `run_solver.py --check`,
   `cost_probe.py` and the `slow` test tier, weekly and on `workflow_dispatch`.
4. **Any future sampled artifact inherits the rule**: register the step, put it in `SLOW_STEPS` with its measured
   cost in the comment, and give it a per-push proof that is exact rather than statistical. The push/fold and ICM
   matrices will be sampled artifacts, so this is not a one-off accommodation.
5. **The scope of each tier is stated wherever it is invoked.** No document, workflow comment or artifact body may
   claim "CI proves every committed artifact is byte-identical to a fresh generation" without naming which tier
   proves it. `ci.yml` says what its own step does not prove, in the comment above it.

## What each tier does and does not prove

Per push: the engine still produces batch 0 of this artifact's numbers; the artifact's cells satisfy every
identity it declares; the artifact is on disk, valid against `data/schema`, and fingerprinted in the manifest;
every *other* artifact in the tree is byte-compared.

Per push, not proven: that the other nineteen batches' boards are the ones written down. A weekly full
re-derivation and `pytest -m slow` cover that, and anyone doubting a number can run it.

A hand-edit to a committed cell is caught by re-derivation to the extent that it breaks an identity; an edit
crafted to preserve all of them is out of scope here. This is a defence against drift and accidents, not against
a determined forgery -- the digest and the weekly re-derivation are what a forgery would have to beat.

## Consequences

- The data job pays about 23 s more per push, and the wait for a full-tree re-derivation moves from "every
  commit" to "Mondays, or when you ask".
- `adr/0002`'s and `docs/development/adr.md`'s claim about a scheduled regression workflow became true on the day
  it was written down, roughly eight thousand commits of intent later. A record that names an enforcing artifact
  should be checked for the artifact's existence, which is now what
  `tests/test_preflop_artifact.py::test_the_slow_step_is_registered_everywhere_its_artifact_is_named` does for
  this one class of wiring.
- Sampling metadata is schema-required, not conventional: `data/schema/preflop_matrix.schema.json` refuses an
  artifact with no `sampling` block, and refuses one whose declared precision does not match the digits it
  actually stores.
- The committed matrix carries `equity` and `stderr` for all 28,561 ordered cells, and deliberately not the
  per-batch panels (20 x 3 x 169 x 169 = 1.7M numbers) or the per-cell denominators. The consequence is a rule
  rather than an optimisation: **a range-level number cannot be recomputed from this artifact**, so it must be
  emitted by a generator run as its own artifact. That is where chapters 05 and 10-12 will get their numbers.

## Alternatives rejected

- **Commit the per-batch panels** (about 20 MB) so a consumer can derive weighted error bars. Rejected: the
  trainer would then be doing the arithmetic ADR-0004 forbids, and a 20 MB committed artifact is not reviewable.
- **Re-derive the matrix only when `src/pokergto/**` changes.** Rejected for the path-filter reason above.
- **Drop the artifact from `data/gen` and generate it on demand in the docs build.** Rejected: it moves the
  numbers out of the provenance contract entirely, which is ADR-0001's whole subject.
- **Statistical agreement with a small fresh sample.** Rejected: it needs a threshold, and the nested-seed
  discovery above showed how easily the fresh sample is not independent of the committed one.
