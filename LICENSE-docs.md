# Curriculum and data license: CC BY-SA 4.0

This file governs **everything in this repository that is not computer program code**:

- `docs/**` — all lesson prose, derivations, worked examples, tables of explanation
- `data/src/**` — authored YAML: glossary, curriculum spine, spot definitions, hand examples, quizzes
- `data/gen/**` — machine-generated artifacts derived from the above and from `src/pokergto/**`
- `README*.md`, `ROADMAP.md`, `CONTRIBUTING*.md`, `adr/**`

Those files are licensed under **Creative Commons Attribution-ShareAlike 4.0 International**
(https://creativecommons.org/licenses/by-sa/4.0/legalcode).

Code files under `src/pokergto/**`, `tools/**`, `setup/**`, `trainer/**` and `.github/**`
are licensed under the MIT license (`LICENSE`). See `NOTICE` for why the split exists.

## Why BY-SA and not CC0

The curriculum is the actual product of this repository, and its value is the derivations —
the work of deciding *why* each number is what it is and then proving it in code.

- **BY (attribution)** makes authorship citable, which is the point of a public portfolio repo.
  It also lets `CITATION.cff` mean something.
- **SA (share-alike)** stops the curriculum being repackaged into a closed paid course without
  the changes flowing back. This repo exists because paid GTO content is fenced off behind
  subscriptions; a licence that protects that fence would be self-defeating.

CC0 would be more "open" and protect the authorship less. CC BY-NC is not a free-content
licence and would get the repo excluded from open-education listings and awesome-lists.
BY-SA is the deliberate middle. If maximal adoption ever matters more than that, switching to
CC BY-4.0 is a one-line change to this file with no architectural impact.

## Attribution requirements

If you reuse or adapt curriculum content, you must:

1. Name the original author (Roland Huang) and this repository.
2. Indicate what changes were made.
3. Distribute your adaptation under the same CC BY-SA 4.0 licence.
4. Keep the `provenance` metadata of any data artifact you redistribute — a derived or
   reference chart whose provenance block is stripped is not a compliant redistribution.

## What CC BY-SA does not permit

Copying solver output or range charts from commercial tools (PioSolver, GTO Wizard, GTO+,
Upswing Lab, Run It Once, etc.) into this repository is **not** made legal by this licence.
You cannot license what you do not own. See `NOTICE` and `adr/0005-provenance-is-schema-required.md`.
