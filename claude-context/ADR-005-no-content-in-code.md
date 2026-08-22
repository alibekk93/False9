# ADR-005 — All content in JSON, none in Python

Status: Accepted
Date: 2026-08-22

## Context
The bulk of remaining work after the systems land is authoring: ~140 events, ~90 cards,
7 NPC arcs, 10 endings. If content lives in code, every writing pass is a code change,
every writing error is a crash, and the content cannot be validated as a corpus.

## Options
- Events as Python functions (maximum expressiveness).
- A small embedded scripting language.
- Declarative JSON with a tiny condition expression language.

## Decision
JSON with a ~120-line expression evaluator supporting `all`/`any`/`not` and comparison
ops over dotted state paths. No arithmetic, no variables, no function calls.

## Consequences
- Content is validatable as a whole: referential integrity, reachability, weight sums,
  warmth-beat density, unique failure scenes — all checkable in CI.
- Hot-reload of `data/` becomes trivial, so writing iterations are seconds not minutes.
- Complex conditions must be expressed as named computed properties on `GameState`
  (e.g. `state.is_broke`) rather than as inline logic. This is a feature: it forces
  vocabulary to be shared between the code and the writing.
- When a condition genuinely needs arithmetic, that is the signal to add a property —
  not to grow the expression language. Growing it requires a new ADR.
