# Architecture decision records

An ADR records a decision that is expensive to reverse, together with the alternatives that were
considered and rejected. Code shows *what* the repository does; these files show *why* it could not
have been otherwise — which is the same distinction the curriculum draws between playing by feel and
playing by derivation.

**Changing any decision below requires a new ADR that supersedes the old one**, not an edit of the
old text. Superseded records stay in the directory with `Status: superseded by ADR-00NN`.

| # | Decision | Controls |
|---|---|---|
| [1](0001-generated-data-artifacts-as-single-source-of-truth.md) | Generated `data/gen/**` artifacts are the single source of truth for every number | `tools/gen_all.py`, `tools/inject_doc_tables.py`, every AUTO block |
| [2](0002-cfr-correctness-is-gated-by-proof.md) | Solver claims require proof; the solver handles six small games, and a full 6-max postflop solve is deliberately cut | `src/pokergto/solver/**`, `data/gen/solver/**`, lesson `status: ready` |
| [3](0003-licensing-split-mit-code-ccbysa-content.md) | MIT for code, CC BY-SA 4.0 for curriculum and data | `LICENSE`, `LICENSE-docs.md`, `NOTICE`, `CITATION.cff` |
| [4](0004-static-trainer-consumes-artifacts-only.md) | The trainer is a static artifact consumer: no backend, no re-derived math, no live solving | `trainer/**`, `tools/sync_trainer_data.py` |
| [5](0005-provenance-is-schema-required.md) | `provenance` is a required schema field, so an unattributed claim cannot validate | `data/schema/*`, `tools/check_provenance.py`, `NOTICE` |

Decisions **D1–D7** referenced elsewhere in the documentation map to these records as:
D1/D2 → ADR-0001, D3/D6 → ADR-0005 and ADR-0002, D4 → the bilingual rules in
`docs/development/bilingual-style.md` plus `tools/check_bilingual.py`, D5 → `CONTRIBUTING.md`
(engine code lives in `src/pokergto`, build glue lives in `tools`), D7 → ADR-0002.
