# CLAUDE.md — False Nine

Operating manual for Claude Code. This file is always in context. Everything else is
loaded on demand from the routing table below.

## What this is

A single-player career management game about a Russian footballer, ages 16 to ~32.
Python + pygame-ce, minimal text-forward UI, English only, one career per playthrough
(3–5 hours). Matches resolve as card play, not simulation.

## Stack

| Thing | Choice |
|---|---|
| Language | Python 3.12+ |
| Renderer | pygame-ce (NOT `pygame`) |
| Package manager | uv |
| Tests | pytest |
| Lint/format | ruff |
| Type checking | mypy, strict on `src/false_nine/core/` only |
| Save format | JSON |
| Target OS | Windows primary; Linux best-effort |

## Commands

```bash
uv sync                      # install
uv run false-nine            # run the game
uv run pytest                # all tests
uv run pytest tests/core     # core sim only, must stay fast (<5s)
uv run ruff check . --fix
uv run ruff format .
uv run mypy
uv run python -m tools.sim   # headless career simulation, see claude-context/10-testing.md
```

## Layout

```
src/false_nine/
  core/            # pure simulation. NO pygame import. NO I/O. Deterministic.
    state.py       # GameState dataclass, the single source of truth
    actions.py     # step(state, action, rng) -> StepResult. The core contract.
    rng.py         # seeded RNG, all randomness goes through this
    calendar.py    # weeks, seasons, phases
    resources.py   # time / energy / money
    stats.py       # ability, form, fitness, injury
    psyche.py      # stress, hope, cynicism, self_knowledge
    relationships.py
    match/         # card deck construction and match resolution
    events/        # event selection, requirements, effects
    opportunity.py # the career-ceiling system. Read claude-context/03 before touching.
    endings.py
    save.py
  content/         # loaders + validators for data/
  ui/              # pygame-ce only lives here
    screens/
    widgets/
    theme.py
data/              # authored JSON content — see claude-context/05-content-schema.md
  events/
  cards/
  clubs/
  npcs/
  dialogue/
tools/             # dev-only scripts, not shipped
tests/
claude-context/
```

## Hard rules

1. **`src/false_nine/core/` never imports pygame, never reads or writes files, never prints.**
   It is a pure function of `(GameState, PlayerAction) -> (GameState, list[Effect])`.
   If you are tempted to break this, stop and write an ADR instead.
2. **All randomness goes through `core/rng.py`.** No `random.random()`, no
   `random.choice()` anywhere else. A career must be exactly reproducible from
   `(seed, list_of_player_actions)`. This is the foundation of the whole test suite.
3. **Never falsify a number shown to the player.** The game's ceiling is enforced by
   the world, not by lying about stats. See `claude-context/03-mechanics-spec.md` §7. This is a
   design commitment, not a preference.
4. **No content in code.** Every event, card, club, NPC, and line of dialogue lives in
   `data/` as JSON. If you find yourself writing English prose inside a `.py` file,
   it belongs in `data/`.
5. **No new third-party dependency without an ADR** in `claude-context/`.
   Current allowed runtime deps: `pygame-ce` only.
6. **Do not add a football match simulation engine.** Matches are card resolution.
   Ball physics, formations, and tactical AI are out of scope forever.
7. **English only.** No localization layer, no i18n scaffolding. See ADR-004.

## Routing table

| If the task is about... | Read |
|---|---|
| Why the game exists, what it is not | `claude-context/01-vision.md` |
| Loop, phases, progression, endings | `claude-context/02-game-design.md` |
| Any number, formula, or rule | `claude-context/03-mechanics-spec.md` |
| Module boundaries, save format, performance | `claude-context/04-tech-architecture.md` |
| Adding or validating JSON content | `claude-context/05-content-schema.md` |
| Fonts, colour, sound, asset naming | `claude-context/06-art-audio-spec.md` |
| Screens, input, navigation, accessibility | `claude-context/07-ui-ux-spec.md` |
| Writing any player-facing text | `claude-context/08-narrative-bible.md` |
| What to build next, what "done" means | `claude-context/09-milestones.md` |
| Test strategy, what to assert | `claude-context/10-testing.md` |
| Packaging, versioning, shipping | `claude-context/11-build-release.md` |
| A settled technical decision | `claude-context/` |

## Conventions

- `snake_case` for files, functions, variables. `PascalCase` for classes.
- Content IDs are `snake_case` and globally unique: `ev_trial_rejection_01`,
  `card_hospital_ball`, `npc_mother`, `club_znamya_truda`.
- Type hints on every public function. `from __future__ import annotations` at top.
- Dataclasses over dicts for anything crossing a module boundary.
- Docstrings only where the *why* is non-obvious. Do not narrate the *what*.
- Commit messages: `area: imperative summary` (e.g. `match: seed fatigue cards from stress`).

## Working style

- Before implementing a system, restate the relevant spec section in your own words
  and flag any rule that is ambiguous. Do not silently pick an interpretation.
- Write the test first for anything in `src/false_nine/core/`.
- When a spec and the code disagree, the spec wins — fix the code, or amend the spec
  in the same commit and say so.
- Prefer deleting to adding. This is a small game with a small scope.
