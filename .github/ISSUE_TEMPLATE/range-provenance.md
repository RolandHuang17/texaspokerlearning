---
name: Range provenance
description: You cannot say where a range, frequency or number came from. Report it instead of writing it.
title: "Provenance: "
labels:
  - range-provenance
  - question
---

<!--
The most useful issue type after Derivation request. `adr/0005` makes provenance a required schema
field, so an unattributed claim does not fail review -- it fails the build. This template is how a
human catches what a schema cannot: a number that is sourced but not actually checkable.
-->

## What you cannot source

One range, one frequency, one number. Point at it: a lesson path, an artifact path under `data/gen/**`,
or a `data/src/**` record.

## Which kind of answer is needed

- [ ] **Computed here** -- a builder is missing, so the number has no generator. The fix is a builder in
      `tools/gen_tables.py` / `tools/gen_ranges.py` plus a `derivation_ref` into `src/pokergto/**`, and a
      test that executes it. If you find yourself typing a table by hand, that is this finding.
- [ ] **An author's judgement** -- a chart someone built rather than a solve. That is a legitimate
      `provenance.kind: reference`, and it stays visibly `reference`: `verified: false`, confidence
      `medium`, and a note saying who built it on what reasoning.
- [ ] **External source** -- needs a record in `data/src/licensing_manifest.yaml` with a licence on the
      allow-list (`CC0-1.0`, `CC-BY-4.0`, `CC-BY-SA-4.0`, `MIT`, `public-domain-math`,
      `fair-use-commentary`). Note the current state honestly: that manifest does not exist yet and no
      artifact here claims an external origin, so this option means creating the file and its first
      record, not appending to a list.
- [ ] **Nobody knows** -- say so in the issue. The artifact keeps a visible `UNVERIFIED / 未核验` badge in
      both languages, which is worth more than a confident number neither of us can defend.

## The line that is not negotiable

Commercial solver output and paid-course charts may not enter this repository as ground truth, in any
form: not traced, not retyped from a screenshot, not "corrected" by hand. PioSolver, GTO Wizard, GTO+,
Upswing, Run It Once and similar are named in `NOTICE` and are rejected by
`python tools/check_provenance.py` by name as well as by schema.

- [ ] My report does not ask us to import, retype or approximate any of those.

## What would close this issue

```bash
python tools/check_provenance.py
python tools/check_artifact_schema.py
python tools/gen_all.py --only tables   # or ranges / solver, whichever builder you added
```

- [ ] The number now resolves to an artifact or an engine function a reviewer can re-run.
- [ ] Or: the claim was removed/downgraded, and the lesson says plainly what is not known.

A `ready` lesson may not cite a game that is absent from `src/pokergto/solver/proofs.py` (`adr/0002`),
and a sampled number may not exist without its declared seed, boards and error bar
(`adr/0007`, `adr/0008`). If this issue's answer is "we cannot source this", that is a resolved issue --
the badge is the deliverable.
