# Security Policy

## What this project is, and its actual attack surface

`texaspokerlearning` is an offline educational codebase: a Python engine, a Markdown
curriculum, and a **static** browser trainer with no backend, no accounts, no database, and no
network calls at runtime. It does not connect to poker sites, does not handle real money, and
does not touch any player's funds or credentials.

The surfaces that a report should target, in descending order of real risk:

| Surface | Risk | Where the mitigation lives |
|---|---|---|
| Trainer rendering of `data/gen/**` | XSS / DOM injection if a generated artifact ever contains attacker-controlled markup | `trainer/src/lib/artifacts.ts` is the only loader; all lesson content flows through it; artifacts are schema-validated before sync |
| `tools/inject_doc_tables.py` | Rewriting arbitrary files if AUTO-block ids escaped their allowlist | ids are matched against `data/gen/tables` keys; unknown id = build failure, not write |
| Dependency supply chain | `numpy`, `PyYAML`, `jsonschema`, `mkdocs-material`, Vue/Vite | `dependabot.yml` weekly; lockfiles committed; CI installs from pins |
| GitHub Pages build | Secret leakage in workflows | no workflow receives secrets; `pages.yml` has `permissions: contents: read, pages: write` only |
| Curriculum content | Harmful gambling advice presented as mathematics | the provenance system is the defence: unverified claims render an UNVERIFIED badge (see NOTICE) |

## Not in scope

- Vulnerabilities in third-party poker rooms or clients.
- Anything requiring you to run the code against a live poker site. **Do not do that.** Using
  external assistance in real time against other players (RTA) violates the terms of service of
  every major site and is cheating against human opponents. This repository teaches strategy;
  it is deliberately not built as a real-time advisor and will not accept contributions that
  turn it into one.
- Automated betting, bot play, or site scraping. These are rejected on principle, not just as
  security scope (see `adr/0004-static-trainer-consumes-artifacts-only.md`).

## Reporting

Open a **private security advisory** at
<https://github.com/RolandHuang17/texaspokerlearning/security/advisories/new>.
For anything else, use a normal issue.

Response targets: acknowledge within 5 business days, assess within 14. This is a solo-maintained
educational project, so "fix" may realistically mean "documented + unlisted from the site" —
you will be told which, and why.

## Note on the engine and float arithmetic

The engine is used to *teach* exactness. Where a value is derived, tests pin it with rational
arithmetic (`fractions.Fraction`) rather than float tolerance wherever possible; where floats are
unavoidable (Monte Carlo, CFR accumulation), the error bar is a first-class field of the result
object, never an assumption. A report showing a place where a documented tolerance is wider than
the claim built on it is welcome.
