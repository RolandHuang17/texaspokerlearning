# Bilingual style and the mirroring contract

> **Single-language by design:** these are contributor-facing engineering docs, and the
> bilingual-same-PR rule applies to curriculum content only (see adr/0005).

The curriculum is one document in two languages, not a document and a translation. That distinction
drives every rule below: the file layout exists so a machine can compare the two, and the machine
comparison exists so that a reviewer's attention can go where a machine cannot look — whether the
Chinese explanation actually teaches the thing the English one does.

## Layout

```
docs/
├── en/<chapter-slug>/<lesson-slug>.md
├── zh/<chapter-slug>/<lesson-slug>.md     # identical byte-path, identical file name
└── development/                            # single-language, exempt, shared by both locales
```

- **File names are English, always, in both trees.** `docs/zh/02-the-math-of-one-decision/03-mdf.md`,
  not `docs/zh/02-一手决策的数学/03-防守频率.md`. A Chinese file name would make every tool path a
  unicode-normalisation problem (Windows NFC/NFD differences are real and silent), and it would break
  the one property the parity gate depends on: `docs/en/X` and `docs/zh/X` are the same string.
- `<chapter-slug>` is the chapter's `slug` in `data/src/curriculum.yaml` (e.g.
  `02-the-math-of-one-decision`), and `<lesson-slug>` is the lesson's `slug`. `pokergto.registry`
  builds the expected path for a lesson as `docs/<locale>/<chapter-slug>/<lesson-slug>.md`, in both
  directions: a registered lesson with no file is an error, and a file with no registration is an
  error (`CurriculumRegistry.find_orphans`, surfaced by `tools/gen_curriculum_index.py`).
- **Lesson ids (`NN-NN`) are permanent and are not file names.** Renumbering a lesson id is a
  breaking change to every cross-reference, tag and artifact that cites it; file names may change
  with a redirect-free rename because nothing cites them.
- Chapter landing pages (`index.md`) are exempt from mirroring — declared in
  `check_bilingual.EXEMPT_PATTERNS` alongside `development/`, so an exempt page cannot mask a missing
  lesson file.

## The 15-section lesson template

Every lesson has exactly 15 H2 sections, in this order. The canonical list is `lesson_template` in
`data/src/curriculum.yaml`; `data/schema/curriculum.schema.json` pins the array at
`minItems: 15, maxItems: 15`, so the contract is in the schema rather than in prose. Each entry is a
**bilingual pair**, and the pair is the heading — one section title carries both languages, which is
why a reader cannot land on a Chinese page and find the "Derivation" section missing under a name they
do not read:

| # | Heading |
|---|---|
| 1 | 本节目标 / Objectives |
| 2 | 前置知识 / Prerequisites |
| 3 | 核心原理 / The principle |
| 4 | 推导 / Derivation |
| 5 | 直觉 / Intuition |
| 6 | 算例 / Worked examples |
| 7 | 生成表 / Generated tables |
| 8 | 实战牌局 / Live hands |
| 9 | 范围图 / Range chart |
| 10 | 为何成立、何时失效 / Why it works, when it breaks |
| 11 | 陷阱 / Common mistakes |
| 12 | 练习 / Drills |
| 13 | 自测清单 / Self-check |
| 14 | 来源与置信度 / Provenance and confidence |
| 15 | 术语 / Terms |

Section 7 exists because the tables are generated, section 14 because they must be attributed, and
section 8 because "lots of practical examples" is a gate here (`check_bilingual.py` requires at least
two live-hand examples in a `ready` lesson), not a wish.

What `tools/check_bilingual.py` enforces today, precisely: the **count** of H2 sections must match
between the two files, and the **total count** of H1/H2/H3 headings must match. It does not compare
the headings themselves or their order, even though the bilingual-pair headings would make an exact
string comparison possible — `check_bilingual._template_headings` takes the template as an argument
and ignores it. The module docstring claims "template order", which is not yet implemented; until it
is, section order is a review responsibility. What *is* compared as an ordered list is the AUTO block
id sequence, so tables cannot reorder between languages. `--strict` in mkdocs is a separate gate and
catches a different class of problem (broken links, warnings).

A lesson that adds an "Extra notes" section in Chinese only fails the build, which is the point — an
extra section is how a translation quietly becomes a different document. Chapter landing pages
(`index.md`) and `development/` are exempt from mirroring, declared in `check_bilingual.EXEMPT_PATTERNS`
so an exempt page cannot mask a missing lesson file.

## AUTO blocks: no hand-typed number, in either language

A lesson reserves space for a generated table and never writes its contents. The block is an HTML
comment pair whose id is the artifact's `table.*` id, so it is invisible in the rendered page and
machine-findable in the source:

```text
BEGIN AUTO:table.02-03.mdf-vs-sizing      opened as an HTML comment
END AUTO:table.02-03.mdf-vs-sizing        closed as an HTML comment, same id
```

(The two lines above are the shape, not a working block. A working block wraps each line in
`<!--` `-->`, and this file deliberately does not contain one: `tools/check_provenance.py` counts
`AUTO` opens across every file under `docs/` and demands a provenance marker per block, so a literal
example in a doc would read as an unprovenanced table — and `tools/inject_doc_tables.py` derives a
lesson's locale from the first path segment, so a real block under `docs/development/` would ask
`pokergto.render` for a `development` column header. Document the syntax; do not seed a live block.)

`tools/inject_doc_tables.py` fills the interior from `data/gen/tables/<id>.json`, rendering the
locale that the file's own path implies (`docs/zh/...` gets the Chinese column headers), and writes
three things with it:

- the table itself, padded by `pokergto.render.display_width` so a Chinese header row aligns instead
  of limping;
- `<!-- provenance: kind=... verified=... -->`, which `tools/check_provenance.py` counts against the
  number of AUTO blocks — a hand-deleted badge is a build failure;
- the `!!! unverified` admonition generated by `pokergto.render.provenance_block`, so a chart's
  honesty travels with the chart.

Both languages embed the **same** artifact id. `check_bilingual` asserts the id lists match 1:1 in
content and order, so a table cannot exist in one language and not the other.

`--check` re-renders and compares bytes without writing; CI runs it (`bilingual.yml`,
`data-drift.yml`). The rule this enforces is absolute: if you want a number to change, change the
code that computes it, regenerate, and let the diff show. Editing a digit inside an AUTO block is a
category error, and `python tools/inject_doc_tables.py --check` is the sentence that says so in
public.

Three more machine-read markers live in a lesson, all HTML comments so they never render:

| Marker | Read by | Purpose |
|---|---|---|
| `<!-- hands: 3 -->` | `check_bilingual.py` | a `ready` lesson must render at least two live-hand examples |
| `<!-- terms: mdf, pot-odds -->` | `check_bilingual.py` | every listed term must exist in `data/src/glossary.yaml` |
| `&lt;!-- BEGIN AUTO:id --&gt;` / `&lt;!-- END AUTO:id --&gt;` | `inject_doc_tables.py`, `check_bilingual.py`, `check_provenance.py` | generated content, parity, provenance count |

## Authoring order: Chinese first, both languages in one pull request

`data/src/curriculum.yaml` records `status_zh` and `status_en` per lesson, and
`pokergto.registry.Lesson.is_ready` is `status_zh == "ready" and status_en == "ready"`. There is no
state where one language is "done" and the other is a translation backlog.

Authoring is Chinese-first as a matter of practice, because the terminology authority
(`data/src/glossary.yaml`) is a Chinese document: Chinese poker vocabulary has no standard, so this
repository *is* the standard, and writing the sentence that fixes a term before the term exists in
English is what makes the English side consistent later.

The same-PR rule is enforced by the pull request template (a required checkbox), by `CODEOWNERS`
routing `data/src/**` to a human, and by `check_bilingual.py` refusing a `ready` status whose file
is missing. Deliberately not enforced: any notion of "translate it later". A half-authored lesson
ships as `draft` in both languages, and `draft` is exempt from the file-existence check — which is
exactly what lets this gate pass on an empty repository at M0 instead of only passing when the work
is already finished.

## Mixed CJK and Latin: the actual rules

- **Abbreviations stay Latin.** MDF, EV, ICM, SPR, GTO, bb, VPIP, 3-bet: these are notation, not
  English words, and translating them makes a Chinese lesson impossible to reconcile against any
  other source. On **first use in a lesson** give the Chinese full name with the abbreviation after
  it — `最低防守频率（MDF）` — then use the bare Latin form for the rest of the lesson. The
  glossary's `abbrev` field is what records the sanctioned short form.
- **One half-width space between CJK and Latin or digits.** `使用 MDF 计算`, not `使用MDF计算`. The
  space is what keeps a table column readable when a header mixes scripts, and it is the convention
  the CJK-aware typographers in this project's dependency chain already follow.
- **Punctuation follows the script of the sentence.** Full-width `，。：；！？、` in Chinese prose;
  half-width everywhere inside code, math, paths, and artifact ids. Never half-width in a Chinese
  sentence — `ruff` flags fullwidth punctuation as "ambiguous unicode" (`RUF001`) precisely because
  the two are easy to confuse, and the fix for a bilingual repository is to be deliberate, not to
  silence the rule everywhere.
- **Numbers are always Arabic digits, always with their unit.** `29.29%`, `4:1`, `18 bb/100`. Chinese
  numerals do not appear in generated content, and they should not appear in prose either, because a
  number that cannot be diffed against the artifact that produced it is a number nobody can verify.
- **Card notation is untouched.** `AhAs`, `22+`, `ATs+`, `K7o` are the same bytes in both files;
  `pokergto.notation` parses them and would reject a translated form.

## The `avoid` mechanism

A glossary entry may list rejected synonyms:

```yaml
- id: minimum-defense-frequency
  zh: 最低防守频率
  en: minimum defense frequency
  abbrev: MDF
  avoid:
    - 防守频率      # ambiguous: which frequency? defended how?
    - 最小防守频率   # the drift that makes chapter 02 and chapter 07 disagree
  note_zh: 只指" bluff 无利可图"的下界，不是任何防守动作的频率。
```

`tools/gen_glossary.py::check` turns those lists into build failures:

- an `avoid` entry may not be another term's official `zh` label (that is a disagreement between two
  entries, not a ruling);
- the same rejected synonym may not be owned by two entries — merge them;
- `zh` labels must be unique across terms, because two terms sharing one Chinese label is exactly how
  "defend 75%" and "defend at least 75%" end up meaning different things in different chapters;
- `first_seen` must name a registered lesson, so a term cannot be invented in prose and back-filled.

The payoff is in `check_bilingual.py`: a lesson that uses a term id nobody registered fails CI, and
the Chinese text stops being a place where synonyms can drift in unnoticed.

## The known weak link, stated plainly

`check_bilingual.py` proves structure. Same files, same section count, same section order, same AUTO
ids, same declared terms. **It does not prove that the English text says what the Chinese text
says**, and it never will.

We are not building a semantic-equivalence checker. Three reasons, and they are cost arguments, not
taste arguments:

1. It needs a translation-quality model, which makes the correctness of a free, offline, no-accounts
   educational repository depend on a network call and a model whose behaviour changes without a
   commit in this repository. That contradicts ADR-0004's "nothing at runtime reaches out" and
   SECURITY.md's supply-chain posture.
2. Its failure mode is worse than its value. A similarity score either gates merges (and then
   reviewers optimise the score, and a fluent-but-wrong sentence passes while a correct rephrasing
   fails) or it reports (and then it is noise nobody reads after week two). A check that cannot say
   *which sentence is wrong and why* is not a gate.
3. The part of a lesson most likely to be silently mistranslated is already covered mechanically:
   numbers come from AUTO blocks and cannot differ, terms come from the glossary and must be
   registered, tables and hand counts are compared. What remains is explanation, and explanation is
   what the same-PR rule plus a human reviewer is for.

So the honest control stack is: **machine-check what is decidable, make the rest visible.** The
review checklist for a bilingual lesson pull request is short and it is a human job: does the Chinese
sentence state the same assumption as the English one; does either version claim more than the
provenance block supports; does the abbreviation on first use match the glossary.
