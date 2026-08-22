# 04 — Technical Architecture

## Principle

The game is a **pure simulation core** with a thin pygame shell bolted on. The core knows
nothing about pixels, files, time, or the player. This is not architectural taste — it is
what makes a 160-week career testable in milliseconds and what makes the ceiling
guarantee in `03` §7.1 auditable.

## Layers

```
┌──────────────────────────────────────────┐
│ ui/          pygame-ce, screens, input   │  may import core, content
├──────────────────────────────────────────┤
│ content/     JSON load + validate        │  may import core
├──────────────────────────────────────────┤
│ core/        pure sim, deterministic     │  imports nothing but stdlib
└──────────────────────────────────────────┘
```

Enforced by a test: `tests/test_boundaries.py` walks the AST of every module in
`src/false_nine/core/` and fails on any import outside the stdlib allowlist.

## The core contract

```python
def step(state: GameState, action: PlayerAction, rng: Rng) -> StepResult: ...

@dataclass(frozen=True)
class StepResult:
    state: GameState          # new state, old one untouched
    effects: list[Effect]     # what the UI should show and in what order
    prompts: list[Prompt]     # what the game now needs from the player
```

`GameState` is a frozen dataclass tree. Mutation is by `dataclasses.replace`. This costs
some allocation and buys trivial undo, trivial diffing for the ledger screen, and
trivial test assertions. At 160 weeks the cost is irrelevant.

`Effect` is a small tagged union — `StatChanged`, `MoneyChanged`, `RelationshipChanged`,
`CardResolved`, `EventFired`, `OpportunityConditionFailed`. The UI renders effects; it
never inspects state deltas itself. This keeps the week ledger honest and automatic.

## Determinism

`core/rng.py` wraps a single `random.Random` seeded from the career seed, and exposes
**named substreams**:

```python
rng.stream("match", week_index).randint(...)
rng.stream("injury", week_index).random()
rng.stream("opportunity", opportunity_id).random()
```

Substreams are derived by hashing `(seed, name, key)`. This means adding a new call site
in one system does not shift results in another — essential when tuning, and essential
for regression-testing balance changes.

Nothing else in the codebase may import `random`, `secrets`, or `time` for randomness.

## Content loading

`data/**/*.json` is loaded once at startup into frozen dataclasses. Validation is strict
and fails loudly at startup with the offending file and JSON path — never at week 94.

`tools/validate_content.py` runs the same validation standalone and is a CI gate. It also
checks referential integrity: every `npc_id`, `card_id`, `club_id`, `event_id`, and
`condition_id` referenced anywhere must exist.

Hot-reload of `data/` in dev builds (F5) is worth the small cost; content iteration is
the bulk of the remaining work after the systems land.

## UI architecture

- Single `pygame.Surface`, fixed logical resolution **1280×800**, integer-scaled to the
  window, letterboxed. No dynamic layout.
- A screen stack: `push(screen)` / `pop()`. Screens are `WeekScreen`, `MatchScreen`,
  `EventScreen`, `LedgerScreen`, `ProfileScreen`, `MenuScreen`, `EndingScreen`.
- Immediate-mode widgets in `ui/widgets/`. No retained widget tree, no framework.
  The UI is almost entirely text; a retained tree would be more code than it saves.
- Text rendering is the performance-critical path. Render text to cached surfaces keyed
  by `(string, font, colour, wrap_width)`; do not re-render per frame.

## Save format

```json
{
  "version": 3,
  "seed": "8f2c...",
  "created_at": "2026-08-22T14:03:00Z",
  "state": { ... },
  "action_log": [ {"week": 1, "action": "train", "arg": "technique"}, ... ]
}
```

- `version` is an integer. Migrations live in `core/save_migrations.py`, one function per
  version bump, tested against a corpus of old saves in `tests/fixtures/saves/`.
- Saves are written atomically (temp file + `os.replace`).
- Three manual slots plus one rolling autosave at each week boundary.
- **Save integrity check:** replaying `action_log` from `seed` must reproduce `state`
  byte-for-byte. Run in CI; optionally in-game behind a dev flag.

## Performance budget

Modest, but state it so nobody optimises the wrong thing:

| Metric | Budget |
|---|---|
| Frame time | ≤ 8 ms at 1280×800 (target 60 fps, mostly idle) |
| Week step (core only) | ≤ 2 ms |
| Full 160-week headless career | ≤ 400 ms |
| Startup to main menu | ≤ 1.5 s including content load |
| Memory | ≤ 300 MB |
| Save file | ≤ 400 KB |

`tools/sim.py` runs N headless careers and reports timing plus balance distributions.
That tool is how balance gets tuned; build it early (Milestone M2).

## Dependencies

Runtime: `pygame-ce`. That is the entire list.

Dev: `pytest`, `ruff`, `mypy`, `pyinstaller`. Adding anything requires an ADR. Resist
`pydantic` (dataclasses + a hand-written validator is ~150 lines and no runtime dep),
resist `attrs`, resist any ECS library — there are no entities here.

## Things deliberately not done

- No async. The game is turn-based and single-threaded.
- No database. JSON on disk is correct at this scale.
- No scripting language for events. Event conditions are a small declarative JSON
  expression language (`05` §5), evaluated by ~120 lines in `core/events/expr.py`.
  If it starts wanting loops or variables, that is the signal to stop and write an ADR.
- No telemetry.
