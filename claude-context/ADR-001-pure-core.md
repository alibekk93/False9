# ADR-001 — Pure simulation core, isolated from pygame

Status: Accepted
Date: 2026-08-22

## Context
The game's central design claim is that the career ceiling emerges from an honest world
model rather than a hidden cheat. That claim must be verifiable. Separately, balancing a
160-week career requires running thousands of careers headlessly, which is impossible if
the simulation is entangled with the renderer.

## Options
- Conventional pygame game loop with state mutated in place by screen code.
- Core/UI split with a mutable state object shared between them.
- Pure core: frozen state, `step(state, action, rng) -> StepResult`, UI as a consumer.

## Decision
Pure core. `src/false_nine/core/` imports only the standard library, performs no I/O, and returns
new state objects. All randomness flows through seeded named substreams in `core/rng.py`.

## Consequences
- A full 160-week career runs headless in under 400 ms; `tools/sim.py` becomes the primary
  balancing instrument.
- Determinism is testable, so `(seed, action_log)` is a complete save and a complete bug
  report.
- The "no hidden cheat" claim becomes auditable by a test rather than a promise.
- Costs: allocation churn from `dataclasses.replace` (irrelevant at this scale), and a
  discipline burden — the temptation to reach into state from a screen must be refused.
- Forbids: any pygame, file, network, or clock access inside `src/false_nine/core/`. Enforced by
  `tests/test_boundaries.py`.
