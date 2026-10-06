# GTO Academy — English

This is the landing page of the English half of a bilingual curriculum. The Chinese half lives at
[`zh/index.md`](../zh/index.md) and every lesson in it has a twin here at the same path.

## The lesson navigation is generated, not typed

The chapter and lesson list is produced by `tools/gen_curriculum_index.py` from
`data/src/curriculum.yaml` into `data/gen/index.en.json` and `data/gen/nav.yml` (which the
`mkdocs_nav.py` build hook feeds to mkdocs), so the site's table of contents and the curriculum spine
can never disagree. This page holds no hand-typed lesson list: an invented list here would be exactly
the hand-typed assertion that [adr/0001](https://github.com/RolandHuang17/texaspokerlearning/blob/main/adr/0001-generated-data-artifacts-as-single-source-of-truth.md)
exists to forbid. Numbers you see on this site — frequencies, ratios, hand counts — arrive from
`data/gen/` inside AUTO blocks written by `tools/inject_doc_tables.py`.

## Before you read a lesson

Every strategy claim carries a `provenance` block, and one of three kinds: derived in this
repository, authored here as a checkable reference, or external with a recorded licence. Claims that
are none of those render an `UNVERIFIED` badge in both languages. The rules, and the current list of
badged claims, are in [data provenance](../development/data-provenance.md).

Solver output is gated by proof rather than plausibility; see
[solver proof policy](../development/solver-proof-policy.md) for what is validated and for the
6-max postflop solver this project deliberately does not have.

## Contributor-facing engineering docs

| Document | What it settles |
|---|---|
| [Running this locally](../development/local-dev.md) | The commands that work on Windows, and the ones that silently do not |
| [Bilingual style](../development/bilingual-style.md) | File mirroring, the lesson template, the AUTO-block rule, punctuation between CJK and Latin |
| [Data provenance](../development/data-provenance.md) | How to add a chart without shipping an unattributed claim |
| [Solver proof policy](../development/solver-proof-policy.md) | What may be called `ready`, and on what evidence |
| [Architecture decisions](../development/adr.md) | ADR-0001 through ADR-0005 in one paragraph each |

Start with the pull request checklist if you intend to contribute:
[.github/PULL_REQUEST_TEMPLATE.md](https://github.com/RolandHuang17/texaspokerlearning/blob/main/.github/PULL_REQUEST_TEMPLATE.md).
