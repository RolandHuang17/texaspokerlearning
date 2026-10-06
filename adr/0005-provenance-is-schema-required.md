# 5. Provenance is a required schema field, so an unattributed claim cannot validate

Status: accepted (2026-10-06)

## Context

Two failure modes are endemic to open poker education, and both are integrity failures rather than
quality failures.

The first is **copyright**. The best postflop ranges in the world are the output of commercial
solvers and paid courses, and the overwhelming majority of "free GTO content" on the internet is
somebody retyping a GTO Wizard screenshot. A repository that wants to be both free and legitimate
cannot do that, and a policy sentence saying "please don't" is not a control.

The second is **folklore**. Poker strategy is full of numbers that are repeated with total
confidence and no derivation — "defend 75% against a one-third-pot bet", "bluff-to-value tightens
to 1:6 three-way". Some are exactly right and derivable; some are approximately right under
assumptions nobody states; some are wrong. A learner who cannot tell which category a claim is in
has not been taught poker, they have been taught to trust.

## Decision

Every strategy-bearing artifact in `data/**` carries a `provenance` object, and the JSON schema
makes it a **required** property. `tools/check_provenance.py` fails the build on its absence.

```json
"provenance": {
  "kind": "derived | reference | external",
  "derivation_ref": "src/pokergto/odds.py#defense_frequency  |  solver/proofs.py#kuhn",
  "solver_run": "data/gen/solver/toy1street_run_0001.json",
  "verified": false,
  "confidence": "high | medium | low",
  "license": "CC-BY-SA-4.0",
  "upstream": null,
  "note": { "zh": "…", "en": "…" }
}
```

**`kind` semantics**

- `derived` — produced by `src/pokergto/theory/**` or `src/pokergto/solver/**`, with
  `derivation_ref` resolving to a real symbol or a proof entry. The strongest class, and where the
  bulk of the repository lives.
- `reference` — hand-authored illustrative content owned by this repository. Permitted only where
  it is **independently checkable**: range validity, EV consistency, MDF algebra, sum-to-one
  frequencies. Rendered with a visible badge so readers know it was authored, not computed.
- `external` — requires `upstream` **and** a `license` value present in
  `data/src/licensing_manifest.yaml`. Accepted licence values are `CC0-1.0`, `CC-BY-4.0`,
  `CC-BY-SA-4.0`, and `public-domain-math`. Anything proprietary is rejected at validation time,
  not at review time.

**The UNVERIFIED discipline is mechanical.** `verified` defaults to `false`, and only three
transitions set it `true`: a pointer into `solver/proofs.py`; a closed-form derivation in
`theory/**` with an executing test; or an external source with a manifest-listed compatible licence.
Anything else renders a `UNVERIFIED / 未核验` admonition in **both** languages and is listed in the
artifact's `unverified_claims` array.

Concretely, right now: the widely-cited multiway continuation-bet collapse (about 65% heads-up,
30% three-way, 15% four-way, 8% five-plus) and the accompanying bluff-to-value tightening are
carried as `reference` + UNVERIFIED, and stay there until `theory/multiway.py` and the
fixed-action three-player toy reproduce them from `d = 1 - (B/(P+B))^(1/N)` plus who-can-win
combinatorics. They are not copied from anywhere, and they are not presented as fact.

The README for `data/` states the editable-source → generated-artifact direction, and
`CODEOWNERS` routes all of `data/src/**` to a human reviewer, because provenance is a judgement
and judgements need an owner.

## Consequences

- Adding a chart from a commercial solver is not a policy violation a reviewer might miss; it is a
  validation error that stops the build. Same for a bare numeric claim.
- Some honest content carries a visible UNVERIFIED badge, which looks worse than a confident
  assertion and is more valuable. The badge doubles as a to-do list: the fastest way to contribute
  is to convert one `reference` artifact into a `derived` one.
- Modeling assumptions must be written down rather than implied. The multiway MDF formula assumes
  defenders act independently, which card removal makes false in practice; the artifact and the
  lesson both state that, because a stated assumption is a smaller lie than an unstated one.

## Alternatives rejected

- **A CONTRIBUTING sentence saying "cite your sources."** This is the norm in the genre and it is
  precisely why the genre is full of unattributed solver screenshots. Prose is not a control.
- **A `sources: [url]` free-text field.** Records provenance without making it checkable: a
  proprietary URL would validate just as happily as a CC0 one.
- **Deleting every unverifiable claim.** Then the multiway chapters become vacuous, and the learner
  gets no model of what a real 4-way pot plays like. Marked-and-honest beats absent.
