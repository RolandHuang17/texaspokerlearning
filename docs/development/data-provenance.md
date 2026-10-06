# Data provenance

> **Single-language by design:** these are contributor-facing engineering docs, and the
> bilingual-same-PR rule applies to curriculum content only (see adr/0005).

Provenance is not a citation style here. It is a required JSON Schema property, so **an unattributed
strategy claim cannot validate**, and a pull request that contains one is red rather than "should have
been caught in review". Read `adr/0005-provenance-is-schema-required.md` and `NOTICE` first; this file
is the how-to that follows from them.

The two failures this exists to prevent are copyright and folklore. Commercial solver output is not
reusable here at any price, and a confident number with no derivation is not teachable here at any
price. Both are treated as build errors, because a policy sentence is not a control.

## The three `provenance.kind` values

| `kind` | Meaning | Extra requirements | Badge a reader sees |
|---|---|---|---|
| `derived` | produced by `src/pokergto/theory/**` or `src/pokergto/solver/**` in this repository | must carry `derivation_ref` **or** `solver_run` | "derived in this repository / 本仓库推导" |
| `reference` | hand-authored illustrative content owned by this repository | permitted only where it is independently checkable (range validity, EV consistency, MDF algebra, frequencies summing to one); `note` is required by `Provenance.reference()` | "author reference chart / 作者自建的参考范围" |
| `external` | a cited outside source | `upstream` non-null **and** a record in `data/src/licensing_manifest.yaml` whose `license` is on the allow-list | "external source / 外部来源" |

Every provenance block must contain all five keys `kind`, `verified`, `confidence`, `license`,
`upstream` — `tools/check_provenance.py::PROVENANCE_KEYS`, mirrored by
`data/schema/common.schema.json#/$defs/provenance`. Optional keys are `derivation_ref`, `solver_run`,
`assumptions`, `note`.

`license` is a closed list, and the closure is the point: `CC0-1.0`, `CC-BY-4.0`, `CC-BY-SA-4.0`,
`MIT`, `public-domain-math`, `fair-use-commentary`. A proprietary value is not "declined", it is
invalid, and adding one to the list requires editing `common.schema.json` and `NOTICE` together.

Build blocks with `pokergto.artifacts.Provenance` rather than by hand — one classmethod per kind
(`Provenance.derived`, `Provenance.reference`, `Provenance.external`), so a call site cannot forget to
say where a number came from:

```python
from pokergto.artifacts import Provenance

provenance = Provenance.derived(
    "pokergto.odds#minimum_defense_frequency",
    assumptions=["defenders act independently; card removal makes that approximate"],
)
```

## The UNVERIFIED mechanics

`verified` defaults to `false`, and it is `false` for almost everything at the start of every
milestone. Three transitions set it true, and `tools/check_provenance.py` checks that each one points
at something that actually exists:

1. a `derivation_ref` that resolves to a real symbol in `src/pokergto` (or a real file path);
2. a `solver_run` whose file exists in `data/gen/solver/`, for a game registered in
   `src/pokergto/solver/proofs.py`;
3. an `external` upstream with a licence recorded in `data/src/licensing_manifest.yaml`.

`verified: true` additionally requires `confidence: high`, and `check_provenance` *demotes* a verified
badge that points at nothing — an unverifiable claim wearing a verified badge is worse than an
unverified one, because it teaches readers to trust the badge.

Two pointer forms resolve, and nothing else does:

- `pokergto.<module>#<symbol>` — the module is imported and the attribute path is walked. Every part
  must exist, so `pokergto.odds#minimum_defense_frequency` is fine and a renamed function fails.
- `src/<path>.py` — a path check only. **The part after `#` is not resolved in this form**, so
  `src/pokergto/solver/proofs.py#kuhn` proves the file exists, not that `kuhn` is in it. Prefer the
  `pokergto.…#symbol` form whenever the symbol is reachable as an attribute.

Anything not verified renders a badge, mechanically, in both languages.
`pokergto.render.provenance_block` emits the `!!! unverified` admonition and
`tools/inject_doc_tables.py` writes the `<!-- provenance: kind=… verified=… -->` marker above it;
`check_provenance.py` counts markers against AUTO blocks, so deleting a badge by hand-editing a
lesson is a build failure rather than a silent lie. Claims that need explaining get an entry in the
artifact's `unverified_claims` array (`pokergto.artifacts.unverified_claim`, whose fields are
`claim`, `why_unverified`, `path_to_verified`, each a `zh`/`en` pair): the badge is also the to-do
list.

The concrete example to copy, because it is the one the project is currently honest about: the
widely-cited multiway continuation-bet collapse (about 65% heads-up, 30% three-way, 15% four-way, 8%
five-plus) and the accompanying bluff-to-value tightening are carried as `reference` + UNVERIFIED.
They are not copied from anywhere and they are not presented as fact, and they stay that way until
`src/pokergto/theory/multiway.py` derives them from `d = 1 - (B/(P+B))^(1/N)` plus who-can-win
combinatorics (M5 work). The multiway table that *is* derived
(`table.07-01.multiway-defense`) records its own independence assumption in
`provenance.assumptions`, in both languages, because a named assumption is a smaller lie than an
implied one.

`python tools/check_provenance.py` passes today; `--strict` additionally fails if *any* artifact is
still unverified, which is the gate a later milestone turns on, not one to run at M0.

## Adding a chart

Decide which artifact it is, then follow the one path that has a generator.

**A numeric table the engine can compute (the normal case).**

1. Write a builder in `tools/gen_tables.py` returning `_artifact(table_id=…, lesson=…, columns=…,
   rows=…, derivation_ref=…, module=…, function=…)`. Rows come from `pokergto`, never from a literal.
2. Register it in `BUILDERS`. The id must match `data/schema/common.schema.json#/$defs/id`
   (`table.<lesson-id>.<slug>`, e.g. `table.02-03.mdf-vs-sizing`).
3. Put the invariants you believe into `checks` (`mdf_equality`, `ev_matches_direct_calculation`,
   `combo_count`, `frequency_bounds`, …). A check is stored in the artifact and re-run by
   `gen_all.py --check`, so an artifact that stops passing its own invariants is a bug report, not a
   diff.
4. `python tools/gen_tables.py --only <id> --out data/gen`, then
   `python tools/gen_all.py --only tables`.
5. Add the AUTO block pair to **both** lessons, same id, and run `python tools/inject_doc_tables.py`.
6. List the id in the lesson's `table_ids` in `data/src/curriculum.yaml`, and commit `data/gen/` in
   the same pull request.

`python tools/gen_tables.py --list` shows what has builders; an id with no builder has no path into
`data/gen`, and a hand-written JSON file there fails `gen_all.py --check` as "stale artifact committed
with no generator producing it".

**A range chart, a spot, or a hand example.** These are authored YAML under `data/src/`
(`spots/`, `hands/`, `quizzes/`), each record carrying its own `provenance` block. Note the honest
state at the time of writing: `data/src/` does not exist, and neither do
`tools/gen_ranges.py` nor `tools/run_solver.py`, so `gen_all.py`'s `ranges` and `solver` steps are
currently no-ops and a range chart has no generator to feed yet. Authoring one today means authoring
the generator in the same pull request (M4 for preflop ranges, M2 for solver runs), and
`check_artifact_schema.py` will tell you immediately whether the shape is right.

**A derived theory result.** `src/pokergto/theory/**` is where a "why" claim belongs:
`range_advantage.py`, `frequencies.py` and `multiway.py` are cited by lessons and each has a test that
executes the derivation. That combination, and only that combination, earns `verified: true` -- which
is also why three theory modules that were written and then deleted (`sizing`, `polarization`,
`blockers`) are absent: they computed precise-looking numbers from invented exponents, and a test could
only have confirmed the invention.

After any of the above: `python tools/check_artifact_schema.py && python tools/check_provenance.py &&
python tools/gen_all.py --check`.

## `licensing_manifest.yaml`

One record per external source, and it is what makes `kind: external` mean something. Required fields
per record: `id`, `upstream`, `license`, `what_is_taken`, `why_permitted`; optional `retrieved`,
`artifacts_using_it`. `license` must be one of the six accepted values, and `check_provenance.py`
compares each external artifact's `upstream` **string** against the set of `upstream` values in the
manifest — so the artifact and the record must agree byte-for-byte on the upstream name, and a
missing record is a failure with a pointed message.

```yaml
schema_version: 1.0.0
records:
  - id: kuhn-1953
    upstream: "Kuhn (1953), A poker game, Annals of Mathematical Statistics 24(4)"
    license: public-domain-math
    retrieved: null
    what_is_taken:
      zh: 作为验证锚点的博弈值 -1/18 与均衡族结构
      en: the game value -1/18 and the structure of the equilibrium family, as validation anchors
    why_permitted:
      zh: 数学结论不受版权保护；取的是数值，不是表述。
      en: Mathematical results are not copyrightable; the value is taken, the expression is not.
    artifacts_using_it:
      - data/gen/solver/kuhn.json
explicitly_prohibited:
  - zh: 任何商业 solver 的范围图，无论复制、重打、截图还是描摹。
    en: Any range chart from a commercial solver, copied, retyped, screenshotted or traced.
```

Published equilibrium *values* for tiny games — Kuhn's `-1/18`, the shape of its equilibrium family,
Leduc exploitability benchmarks — are mathematics, not protected expression, and are cited as
`external` with `license: public-domain-math`. Taking a value is permitted; taking a *presentation*
of a value is not.

## The ban list

From `NOTICE`, restated as `check_provenance.py::PROPRIETARY_MARKERS`, which scans `data/src/**` and
rejects by name:

- range charts or strategy output from **PioSolver**, **GTO Wizard**, **GTO+**, **Solwars**,
  **Bodrum**, **Slurm**, **Postflop+**, or any other commercial solver — copied, retyped,
  screenshotted, or traced from a UI;
- transcriptions of paid training videos or articles, **including paraphrases close enough to be
  derivative works** — **Upswing**, **Run It Once** and "Raised Run" are named in the scan list, and
  **Monker**'s solved outputs are the canonical example of a range nobody may retype;
- scraped data from paid training sites.

Two consequences authors need to know:

1. There is no hand-history parser and no external solver-format importer in this repository, on
   purpose (ADR-0004, `NOTICE`). Hand examples are authored in `data/src/hands/` in this
   repository's own format.
2. The scan is text matching, so a *prohibition* that names a banned product must contain the word
   `prohibited` or `not permitted` or it is itself reported. That is the escape hatch, and it is
   deliberate: a file that mentions GTO Wizard is either a violation or a ban statement, and the tool
   makes you say which.

`data/src/**` is owned by a human in `CODEOWNERS`, because choosing a `kind` and writing a
`why_permitted` is a judgement, and judgements need an owner.
