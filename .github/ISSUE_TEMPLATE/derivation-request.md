---
name: Derivation request
description: A lesson reads fine but does not convince you. Ask for the why, not for a chart.
title: "Derive: "
labels:
  - derivation-request
  - enhancement
---

<!--
This is the highest-value issue type in this repository (see CONTRIBUTING.md). "never too basic" is
literal: a lesson whose derivation has a hole is a defect, and the report is the fix's first draft.
-->

## Which lesson, and which step

Lesson path (`docs/en/...` or `docs/zh/...`, or the lesson id like `04-02`) and the section number.

## Where you lose the thread

Quote the sentence or formula, then say where it stops following. One line is enough --
"this exponent appears out of nowhere", "why is the tie worth half here", "the switch from combos to
frequency is doing unstated work".

```
Paste the exact step here.
```

## What would convince you

What you would accept as a derivation: a closed form you can check by hand, a worked numeric example
the engine reproduces, a monotonicity or limiting case, or an experiment you can run in a terminal.

## Can you get the number yourself? (try for five minutes)

If a command exists, the answer stops being an argument. Paste what you ran and what came back:

```bash
PYTHONPATH=src python -m pokergto odds
PYTHONPATH=src python -m pokergto mdf --pot 10 --bet 5 --opponents 2
PYTHONPATH=src python -m pokergto equity AhAs 7d2s --mode auto
```

- [ ] I ran something and it disagreed with the lesson
- [ ] I ran something and it agreed, but I still do not see why
- [ ] There is no command that computes this, which is itself the finding

## If the answer is "a new derivation has to be written"

That lands in `src/pokergto/theory/**`, and the rule there is unforgiving on purpose: a theory module
needs a test that **executes** the derivation, and a lesson may only cite it as `derived` once that
test exists. Three modules (`sizing`, `polarization`, `blockers`) were deleted rather than left
computing precise-looking numbers from invented exponents -- if the honest route is "we cannot derive
this yet", that is a legitimate resolution for this issue, and the lesson gets an `UNVERIFIED` badge
in both languages instead of a confident number.
