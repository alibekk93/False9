# 10 — Testing

## Why testing carries unusual weight here

The design makes a strong claim: the protagonist's ceiling emerges from an honest world
model rather than from a cheat. That claim is only meaningful if it is *verified*. Most
of the interesting tests in this project are not correctness tests — they are tests that
the game is not lying.

Secondary reason: balancing a 160-week career by hand is impossible. The headless
simulator is the primary balancing instrument, and it only works if the core is pure.

## Layers

### 1. Unit tests — `tests/core/`

Fast (<5 s for the whole directory), no I/O, no pygame. Cover every formula in `03`.

Write these first. Each spec section maps to a test module:
`test_resources.py`, `test_stats.py`, `test_injury.py`, `test_psyche.py`,
`test_deck.py`, `test_match.py`, `test_wages.py`, `test_opportunity.py`,
`test_relationships.py`, `test_endings.py`.

### 2. Property tests

Hand-rolled, no `hypothesis` dependency — a loop over seeds is sufficient.

- Ability, psyche, fatigue never leave `[0, 100]` across 1000 random careers.
- `self_knowledge` is monotonic non-decreasing across every career.
- Money and debt are always integers; debt never negative.
- Card outcome weights sum to 100 for every card in `data/`.
- No event fires while its cooldown is active.

### 3. Determinism and save integrity

The load-bearing test. `tests/test_determinism.py`:

```python
def test_replay_reproduces_state(seed, actions):
    a = run_career(seed, actions)
    b = run_career(seed, actions)
    assert a == b                      # bit-identical

def test_save_roundtrip(seed, actions):
    s = run_career(seed, actions)
    loaded = load(dump(s))
    assert loaded == s

def test_action_log_reconstructs_state(save):
    assert replay(save.seed, save.action_log) == save.state
```

Run against a corpus of 50 stored `(seed, action_log)` pairs in `tests/fixtures/careers/`.
Adding a system must not change existing careers unless intended — when it does, the diff
is reviewed deliberately and the corpus regenerated in its own commit.

### 4. Boundary and hygiene tests

- `test_boundaries.py` — AST-walk `src/false_nine/core/`, fail on any non-stdlib import.
- `test_no_stray_random.py` — fail on `import random` anywhere but `core/rng.py`.
- `test_no_prose_in_code.py` — fail on any string literal over 60 chars in `src/false_nine/`
  that isn't a docstring, comment, or in `ui/theme.py`. Content belongs in `data/`.
- `test_no_hidden_ceiling.py` — grep `src/false_nine/core/` for suspicious patterns: `min(.*ability`,
  `MAX_ABILITY`, `is_star`, `cap`. Any hit fails and requires an explicit allowlist entry
  with a comment explaining why it is not a cheat.

### 5. Design-invariant tests

These encode the arguments the game is making. If one fails, either there is a bug or the
design changed — and if the design changed, `03` gets amended in the same commit.

```
test_psyche_does_not_touch_stats
test_relationships_do_not_affect_match
test_ceiling_emerges_without_clamp        # p99 ability at 26 < 88, no clamp in code
test_opportunity_conversion_rate          # mean 0.5–1.5 of 6 across 1000 careers
test_failure_scenes_unique_per_career
test_warmth_beat_density                  # >= 1 per 5 weeks in the event corpus
test_every_world_condition_has_named_failure
```

### 6. Content validation — `tools/validate_content.py`

CI gate. Schema conformance, ID uniqueness, referential integrity, outcome weights,
`outcome_text` present on every choice, no orphan events (`tools/reachability.py` proves
every event is reachable from at least one plausible state).

### 7. Balance simulation — `tools/sim.py`

```bash
uv run python -m tools.sim --careers 1000 --strategy optimal --report balance.md
uv run python -m tools.sim --careers 1000 --strategy neglectful
uv run python -m tools.sim --careers 1000 --strategy random --seed 42
```

Strategies are scripted AP policies: `train_max` (the ceiling anchor of `03` §3.1),
`careerist` (the same training plus keeping his agent warm — the "well-prepared player"
`03` §7.2 quotes its conversion rate for), `balanced`, `broke` (always Work), and the
matched pair `quiet` / `social`.

Two of them are anchors and the difference matters. `train_max` is who the **ability**
ceiling is measured against, because he climbs fastest. He is the wrong anchor for the
**opportunity** rate: he never speaks to Ruslan, so three of the six chances gate him
out before the world gets a say, and a chance he was never eligible for is not one the
world took off him. `careerist` is the anchor for `03` §7.

Reports: ability curve percentiles, money and debt distributions, injury counts, matches
played, opportunities converted, ending distribution, weeks with 0 AP available.

`optimal` and `neglectful` producing near-identical *careers* and very different *lives*
is the number to watch. That gap is the game.

### 8. Manual test passes

Automated tests cannot check whether it feels rigged. Structured playtest protocol in
`claude-context/playtest-protocol.md`, run at M6 and M7. The single question that matters is in
`09` M6.

## CI

On every push: ruff, mypy on `core/`, pytest, content validation, contrast check, and a
100-career sim smoke run. Total budget under 3 minutes; if it grows past that, the sim
count comes down, not the tests.

## What is not tested

- pygame rendering. No screenshot tests, no UI automation. Not worth the cost at this
  scale; caught by manual passes.
- Audio playback.
- Prose quality. Handled by the constraints in `08` and by reading it.
