# 05 — Content Schema

All authored content is JSON in `data/`. No prose in `.py` files, ever.

Every file is an object with a `schema` key naming its type and an `items` array.
IDs are globally unique across all types. Validation is strict: unknown keys are an
error, not a warning.

```
data/
  events/       ev_*.json      scenes with choices
    opportunity_fail/          the 12+ named failure scenes (03 §7.3)
  cards/        card_*.json    match Moment cards
  clubs/        clubs.json
  npcs/         npcs.json
  opportunities/opportunities.json
  endings/      ending_*.json
  strings/      ui.json        all UI chrome text
```

---

## 1. Event

```json
{
  "schema": "event",
  "items": [
    {
      "id": "ev_wages_late_01",
      "pools": ["club_trouble"],
      "tags": ["money", "club", "phase2"],
      "weight": 10,
      "repeatable": false,
      "cooldown_weeks": 12,
      "requires": {
        "all": [
          {"path": "club.solvency", "op": "<", "value": 45},
          {"path": "phase", "op": "in", "value": [2, 3]},
          {"path": "flags", "op": "not_contains", "value": "left_football"}
        ]
      },
      "scene": {
        "location": "changing_room",
        "time_of_day": "evening",
        "body": [
          "The envelope system has stopped. Nobody announces it.",
          "Vitya is the one who says it out loud, because Vitya always is."
        ]
      },
      "choices": [
        {
          "id": "c_ask_directly",
          "text": "Ask the director when you'll be paid.",
          "requires": {"all": [{"path": "psyche.cynicism", "op": "<", "value": 60}]},
          "effects": [
            {"type": "psyche", "key": "stress", "delta": 6},
            {"type": "relationship", "npc": "npc_coach", "key": "respect", "delta": 4},
            {"type": "flag", "set": "asked_about_wages"}
          ],
          "outcome_text": "He says the word 'temporarily' four times."
        },
        {
          "id": "c_say_nothing",
          "text": "Say nothing.",
          "effects": [
            {"type": "psyche", "key": "stress", "delta": 10},
            {"type": "psyche", "key": "cynicism", "delta": 5}
          ],
          "outcome_text": "You get changed. The bus is at seven."
        }
      ]
    }
  ]
}
```

**Rules**
- `weight` is relative within a pool. Omit for scripted events (those are scheduled by
  `week_index` in `requires`).
- `cooldown_weeks` prevents re-firing. Non-repeatable events also set an implicit flag.
- Exactly 2–4 choices. Never one. Never more than four — the UI does not scroll.
- `outcome_text` is required on every choice. Choices without consequence text feel
  broken even when the mechanical effect is real.
- Choices may be gated by `requires`; gated-out choices are **shown, greyed, with the
  reason**. Seeing what you can't do is part of the design.

## 2. Effect types

| `type` | Keys | Notes |
|---|---|---|
| `stat` | `key` (technique/physical/mental), `delta` | rare outside training |
| `psyche` | `key`, `delta` | |
| `money` | `delta` | integer ₽ |
| `debt` | `delta` | |
| `relationship` | `npc`, `key`, `delta` | |
| `fatigue` | `delta` | |
| `injury` | `severity`, `weeks` | forced injury |
| `flag` | `set` \| `clear` | string flag on state |
| `opportunity` | `id`, `condition`, `resolve` | fail/pass a named world condition |
| `club` | `key`, `delta` \| `set` | e.g. solvency |
| `unlock_pool` | `pool` | |
| `queue_event` | `id`, `in_weeks` | scheduled follow-up |

## 3. Card

```json
{
  "schema": "card",
  "items": [
    {
      "id": "card_hospital_ball",
      "title": "Hospital ball",
      "pool": "pool_tired",
      "beat_tags": ["middle", "late"],
      "weight_source": null,
      "flavour": "The pass is a second late and half a yard short.",
      "outcomes": [
        {
          "weight": 60,
          "rating_delta": -0.8,
          "momentum": -1,
          "fatigue": 4,
          "injury_roll": 0.06,
          "text": "Kotov takes the hit that was meant for you and doesn't look up."
        },
        {
          "weight": 40,
          "rating_delta": -0.3,
          "momentum": 0,
          "fatigue": 4,
          "text": "It skips off the surface and out. Nobody says anything."
        }
      ],
      "effects": [
        {"type": "relationship", "npc": "npc_teammate", "key": "respect", "delta": -2}
      ]
    }
  ]
}
```

**Rules**
- `pool` is one of `pool_neutral`, `pool_anxious`, `pool_bitter`, `pool_flat`,
  `pool_tired`, `pool_hurt`, or `pool_positive`.
- `weight_source` for positive cards names the stat that makes them likelier to be drawn
  (`technique`, `physical`, `mental`) — null for pollution cards.
- Outcome weights must sum to 100.
- Every card needs `flavour` (shown on the card face) and every outcome needs `text`
  (shown on resolution). Both are one or two sentences. See `08` §5 for voice.

**Minimum content:** 30 positive cards, 8 per pollution pool, 10 neutral. The player
sees ~112 matches; repetition is acceptable but a pollution pool with 3 cards will read
as a bug.

## 4. Club, NPC, Opportunity

```json
{"schema": "club", "items": [{
  "id": "club_zarya_borisoglebsk",
  "name": "Zarya Borisoglebsk",
  "tier": 4,
  "strength": 38,
  "facilities": 0.6,
  "solvency": 35,
  "town": {"name": "Borisoglebsk", "population": 60000, "remoteness": 0.7},
  "wage_offer": 45000,
  "traits": ["late_wages", "old_pitch", "loyal_crowd"]
}]}
```

```json
{"schema": "npc", "items": [{
  "id": "npc_kostya",
  "name": "Kostya",
  "role": "childhood_friend",
  "introduced_week": 1,
  "initial": {"trust": 70, "respect": 50, "dependence": 20, "closeness": 75},
  "arc_events": ["ev_kostya_business", "ev_kostya_asks", "ev_kostya_drifts"],
  "drift_threshold_weeks": 20
}]}
```

```json
{"schema": "opportunity", "items": [{
  "id": "opp_s5_tier3_trial",
  "season": 5,
  "window_weeks": [3, 7],
  "tier_target": 3,
  "player_conditions": [
    {"path": "ability", "op": ">=", "value": 52},
    {"path": "form", "op": ">=", "value": 60},
    {"path": "relationships.npc_agent.trust", "op": ">=", "value": 40}
  ],
  "world_conditions": [
    {"id": "scout_attends",        "p": 0.65, "reveal_week": 4, "fail_event": "ev_of_scout_flight"},
    {"id": "manager_still_there",  "p": 0.70, "reveal_week": 5, "fail_event": "ev_of_manager_sacked"},
    {"id": "club_has_budget",      "p": 0.60, "reveal_week": 6, "fail_event": "ev_of_budget_gone"},
    {"id": "no_academy_signing",   "p": 0.60, "reveal_week": 6, "fail_event": "ev_of_academy_kid"},
    {"id": "medical_clears",       "p": 0.75, "reveal_week": 7, "fail_event": "ev_of_old_ankle"}
  ],
  "success_event": "ev_of_signed_tier3"
}]}
```

`reveal_week` is what makes failure ordinary rather than cruel: the condition resolves
and the player learns about it *during* the arc, not at the end. See `03` §7.2.

## 5. Condition expression language

Deliberately tiny. Evaluated by `core/events/expr.py`.

```json
{"all": [ ... ]}          // AND
{"any": [ ... ]}          // OR
{"not": { ... }}          // NOT
{"path": "psyche.stress", "op": ">=", "value": 70}
```

Ops: `==`, `!=`, `<`, `<=`, `>`, `>=`, `in`, `not_in`, `contains`, `not_contains`.

`path` is a dotted accessor into `GameState`. Paths are validated at load time against
the actual dataclass tree — a typo in a path is a startup error, not a silent `False`.

**No arithmetic, no variables, no function calls.** If a condition needs those, add a
named computed property to `GameState` (e.g. `state.is_broke`) and reference that.

## 6. Strings

`data/strings/ui.json` holds every piece of UI chrome — button labels, headers, tooltips,
stat names, the words used to describe psyche states (`07` §4). Nothing player-visible is
hardcoded in `ui/`, even though there is no localization. This is for editability, not
translation.

## 7. Authoring checklist

Before committing new content, run `uv run python -m tools.validate_content`. It checks:
schema conformance, ID uniqueness, referential integrity, outcome weights summing to 100,
every event reachable by at least one state (via `tools/reachability.py`), and no event
with a choice lacking `outcome_text`.
