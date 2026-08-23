# 03 — Mechanics Spec

Every rule here should map to a test. Values marked **[TUNE]** are first guesses meant to
be changed after playtesting; the *structure* around them is not.

All arithmetic is on floats internally, rounded only for display. Clamp after every
operation.

---

## 1. Calendar

- Career runs seasons 1–16, ages 16–32 (`age = 15 + season`).
  The formula is the rule: he is 16 in season 1 and **31 during season 16**, and turns 32
  in the off-season resolution step after it, which is when §9 evaluates the endings.
  The "16–32" and "26–32" ranges elsewhere in the docs are inclusive of that birthday.
- Each season has **10 playable weeks** (`week` 1–10) plus an off-season resolution step.
- `week_index = (season - 1) * 10 + week`, range 1–160.
- Phase boundaries: Phase 1 = seasons 1–3, Phase 2 = seasons 4–10, Phase 3 = seasons 11–16.
- Matches occur in weeks 2, 3, 5, 6, 8, 9, 10 of a season (7 matches/season) unless the
  protagonist is injured, suspended, or not in the squad.
- **Phase 3 compression:** in seasons 13–16, weeks 4 and 7 are auto-resolved with a
  summary card rather than played. Player sees the ledger, spends no AP.

## 2. Resources

### 2.1 Action Points (AP)

- Base **4 AP/week**.
- Modifiers: `-1` if `fatigue > 70`; `-1` if `stress > 80`; `+1` in Phase 3 from season 13.
- Floor 2, ceiling 5.
- Unspent AP is lost. Never banked.

Actions cost 1 AP each unless noted:

| Action | Effect summary |
|---|---|
| Train (choose: technique / physical / mental) | `+ability`, `+fatigue 12`, injury risk. Unavailable while injured. |
| Recover | `-fatigue 25`, `-stress 6` [TUNE], `-0.5` weeks off an injury [TUNE] |
| Work (side job) | `+money`, `+fatigue 8`, `-time for everything else` |
| Socialise (choose NPC) | `+closeness 6`, `+trust 2`, `-stress 8`. Unavailable for a drifted NPC (§8). |
| Deal With It | resolves a pending obligation: debt payment, bureaucracy, medical |
| Drift | 0 AP, ends the week immediately. `+stress 5` [TUNE] if obligations pending. |

### 2.2 Fatigue (0–100)

```
fatigue += 12 per Train, +8 per Work, +6 per match played
fatigue -= 25 per Recover
fatigue -= 8 passive per week
```
Effects: `fatigue > 60` → deck quality penalty (§5.3). `fatigue > 80` → injury risk ×1.8.

### 2.3 Money (₽)

Integer rubles. Starting balance 0 at age 16 (family supports him; see `ev_allowance`).

Weekly:
```
money += wage_paid_this_week          # see §6.2, often 0
money -= living_cost                  # 4_000 Phase 1 (partial), 12_000 Phase 2, 18_000 Phase 3 [TUNE]
money -= debt_interest                # §2.4
money += side_job_income * work_ap    # 6_000 per Work AP [TUNE]
```
Money may go negative. Negative balance auto-converts to debt at week end.

### 2.4 Debt

- `debt` in ₽, interest **3%/week** compounding [TUNE].
- `debt > 100_000` unlocks the desperation event pool (`tag: desperate`).
- `debt > 300_000` unlocks `pool: dangerous_creditor`, which has permanent consequences.
- Debt can be reduced by Deal With It (pays `min(money, debt)`), by asking an NPC
  (requires `trust ≥ 60`, costs `dependence +15`), or by a bad option.

## 3. Ability

Three visible stats, 1–100, displayed honestly at all times.

| Stat | Trained by | Ages |
|---|---|---|
| `technique` | Train:technique | peaks ~26, decays 0.4/season after 29 |
| `physical` | Train:physical | peaks ~24, decays 1.2/season after 27 |
| `mental` | Train:mental, and by surviving events | never decays |

`ability = 0.4*technique + 0.35*physical + 0.25*mental`

Starting values at 16: `technique 30`, `physical 30`, `mental 20` [TUNE]. `stress` starts
at 20 [TUNE]. Stats have a **floor of 1** and no ceiling; the floor exists so permanent
injury damage cannot drive a stat negative, and is not a cap.

### 3.1 Training gain

```
gain = base_gain * age_factor * fatigue_factor * facility_factor
base_gain      = 0.85                                   [TUNE]
age_factor     = 1.4 if age<=19, 1.0 if <=24, 0.6 if <=28, 0.25 otherwise
fatigue_factor = 1.0 if fatigue<50, 0.6 if <75, 0.25 otherwise
facility_factor= club.facilities (0.5 – 1.2)
```
Diminishing returns: multiply `gain` by `(1 - stat/100) ** 0.7`.

**There is no cap on these stats.** A maximally optimised protagonist reaches an ability
around 75 by age 26 — good, not elite. This emerges from the curve, not from a clamp.
Do not add a clamp. (See §7.)

**"Maximally optimised" means** the player who trains as hard as the fatigue system
permits and ignores money entirely — `tools.sim.train_max`, roughly 2.9 Train AP/week.
He is the anchor because he is the fastest possible climber: if he lands in the 70s,
nobody reaches the 90s. `base_gain` was calibrated against him (M1) and the spec's
original guess of 1.6 put him at ~97; `base_gain` is the `[TUNE]` knob and the exponent
is not, so `base_gain` moved.

Measured at M2, with matches in the loop, across 1000 seeds: **median ability 70.5 at
26, 99th percentile 76.1**. Matches cost `+6` fatigue about seven times a season, so
the anchor spends more AP on Recover than he did at M1, when the same policy reached a
median of 75. `base_gain` did **not** move for this — the M2 band is 68–78 and 70.5 sits
inside it. A player who also works to live lands nearer 53.
**Re-calibrate at M4**, when club wages free AP that currently has to go to Work.

### 3.2 Form (0–100)

Rolling quality of recent matches. `form = 0.7*form + 0.3*(last_match_rating*10)`.
Starts at 50. Affects deck quality (§5.3) and event availability.

### 3.3 Injury

Each match and each Train roll injury:
```
p_injury = base * fatigue_mult * age_mult * (1 + 0.02 * injury_history_count)
base            = 0.04 match, 0.02 train                  [TUNE]
fatigue_mult    = 1.0 / 1.8 (fatigue>80)
age_mult        = 1.0 if age<=25, 1.3 if <=29, 1.7 otherwise
```
On injury, roll severity: minor (60%, 1–2 weeks), moderate (30%, 3–8 weeks), severe
(10%, 12–30 weeks). Moderate and severe apply **permanent `physical` damage**:
`-2` moderate, `-6` severe. This is the only irreversible stat loss and it is honest,
visible, and explained in-fiction.

`injury_history_count ≥ 4` with age ≥ 28 makes `ev_career_ending_injury` eligible.

## 4. Psyche

Four values, 0–100. Visible to the player as words, not numbers (see `07` §4).

| Value | Rises from | Falls from |
|---|---|---|
| `stress` | unpaid wages, debt, conflict, injury, Drift with obligations | Recover, Socialise, resolution events |
| `hope` | wins, opportunities appearing, promises kept to him | opportunities failing, being dropped, aging |
| `cynicism` | opportunities failing, corruption events, broken promises | warmth beats, sustained closeness with any NPC |
| `self_knowledge` | reflection events, endings of arcs, honest choices | never falls |

`hope` starts at 75 and drifts down `-0.8/season` passively from season 5 — applied
once at the end of each season from 5 onward, alongside the ability decay in §3.1.
`cynicism` starts at 10. `self_knowledge` starts at 5 and is the only monotonic value in
the game.

`07` §4 shows three of these as a single word. The value behind it:

```
strain = stress + cynicism + (100 - hope)          # 0-300
mood   = mood_words[min(6, strain // 30)]          # [TUNE: band 30]
```

A band of 30 puts a fresh 16-year-old on *steady* and reaches *done* at a strain of 180,
which takes real damage on two axes at once rather than one bad season.

Psyche does **not** modify ability. It modifies the deck (§5.3), event availability, and
the ending. This separation must hold: a depressed protagonist is not worse at football,
he just plays worse, which is a different and more accurate claim.

## 5. Match resolution

### 5.1 Structure

Three beats: `early`, `middle`, `late`. Player is dealt **5 cards**, plays **1 per beat**
(2 discarded at the end). Each card resolves immediately and its outcome can modify the
next beat's context (`momentum`, `-1..+1`).

### 5.2 Card anatomy

Defined in `data/cards/*.json` (schema in `05` §3). A card has:
`id`, `title`, `beat_tags`, `requires`, `weight_source`, `outcomes[]` with weights,
each outcome carrying `rating_delta`, `fatigue`, `injury_roll`, `effects[]`, `text`.

### 5.3 Deck construction (deterministic)

The deck is 20 cards, assembled each match:

```
positive_slots = round(10 * quality)
noise_slots    = 20 - positive_slots
quality = clamp(
    0.30
  + 0.45 * (ability / 100)
  + 0.20 * (form / 100)
  - 0.20 * (fatigue / 100)
  - 0.25 * (stress / 100)
  - 0.15 * (cynicism / 100)
  + 0.10 * (hope / 100),
  0.05, 0.95)
```

`positive_slots` are filled from cards whose `weight_source` matches the protagonist's
strongest stats. `noise_slots` are filled from the **pollution pools**, weighted:

| Pool | Driven by | Example cards |
|---|---|---|
| `pool_anxious` | `stress` | `card_hide`, `card_rushed_pass`, `card_safe_backpass` |
| `pool_bitter` | `cynicism` | `card_late_tackle`, `card_argue_with_ref`, `card_blame_teammate` |
| `pool_flat` | `100 - hope` | `card_go_through_motions`, `card_jog_back` |
| `pool_tired` | `fatigue` | `card_heavy_legs`, `card_hospital_ball` |
| `pool_hurt` | active injury | `card_favour_the_knee` |

If no pool is driven above threshold **[TUNE: 35]**, fill remaining noise slots with
`pool_neutral`.

The player never sees the deck composition. They see the hand, and after a few bad weeks
they will notice the hand has gone bad. That is the intended discovery.

### 5.4 Match outcome

```
performance = sum(rating_delta of 3 played cards) + momentum_bonus
rating      = clamp(5.0 + performance, 1.0, 10.0)
```
Team result is drawn from club strength vs opponent strength, nudged by `rating`, but is
**not** the player's score. The game never congratulates the player for a team win.

## 6. Clubs and employment

### 6.1 Club model

`tier` (1–5, where 4–5 are semi-pro/amateur), `strength`, `facilities` (0.5–1.2),
`solvency` (0–100), `town` (population, remoteness), `wage_offer`.

### 6.2 Wages

Each payday (weeks 5 and 10):
```
p_paid_in_full = solvency / 100
roll -> full | partial (50%) | nothing
```
Missed wages accumulate as `arrears`. Arrears may be paid in a lump later (30% chance at
season end) or written off when a club folds. Unpaid wages add `+8 stress` per incident
and `+4 cynicism`.

`solvency` drifts down for tier 4–5 clubs and can trigger `ev_club_folds`, which
terminates the contract mid-season and voids arrears. Directly modelled on the real
lower-division cases in `08` §8.

### 6.3 Contracts

Length 1–3 seasons. Expiry triggers the transfer window resolution, which is where the
opportunity system (§7) does its work.

## 7. The opportunity system — THE CEILING

**Read this whole section before implementing anything in `src/false_nine/core/opportunity.py`.**

### 7.1 The commitment

The protagonist's career ceiling is enforced **entirely by the availability and
resolution of opportunities**, never by:

- capping or secretly reducing a stat,
- lying about a displayed number,
- rerolling a result the player already saw,
- an invisible "is_star = False" flag consulted at the last moment.

If a future contributor can point at a line of code and say "this is where the game
cheats," the design has failed. The world is stacked; the dice are not loaded.

### 7.2 Structure

An **Opportunity** is a multi-week arc with an explicit, visible set of **conditions**,
of which the player controls some and not others.

```
Opportunity:
  id, tier_target, window (season, weeks)
  player_conditions:   [ability >= X, form >= Y, fitness ok, agent.trust >= Z]
  world_conditions:    [scout_attends, club_has_budget, manager_still_employed,
                        no_competing_signing, visa_ok, timing]
```

Player conditions are genuinely achievable and genuinely matter. World conditions are
each individually plausible, each around **55–75% likely**, and there are **four to six
of them**. The product does the work: a well-prepared player converting a chance sits at
roughly 8–15%, which is both honest and, over ~6 opportunities across a career, produces
about one small success and five specific, memorable failures.

**Crucially: world conditions are rolled at the moment they become fictionally true**,
early in the arc, and are *knowable* — the player can find out that the scout cancelled,
often before the trial. The failure is not a surprise dice roll at the end. It is a
gathering, visible, ordinary disappointment.

### 7.3 Mandatory: every failure has a name

`ev_opportunity_fail` must never fire with generic text. Each world condition that fails
resolves to a specific authored scene:

- The scout's flight from Yekaterinburg is cancelled; he watches a video instead.
- The manager who asked about him is sacked eleven days before the trial.
- The club signs a 19-year-old from the academy of a club with money, because the
  academy has a relationship and his agent does not.
- The medical flags an old ankle. Not badly. Just enough.
- The club is bought and the new owner brings four players with him.
- The paperwork sits on a desk in Moscow until the window closes.

Minimum **12 authored failure scenes** in `data/events/opportunity_fail/`, each tied to
a specific condition, each mundane, none malicious. A player who fails six opportunities
must fail them six different ways.

### 7.4 Success is real but small

Converting an opportunity moves the protagonist up **one tier at most**, to a club that
is itself precarious. There is no opportunity in the game with `tier_target < 2`. The
top of the achievable world is a mid-table second-tier club in a city of 400,000, on
₽180,000/month, in a squad where he is respected. That is the best ending the career
can produce and it is, deliberately, fine.

### 7.5 Opportunity schedule

Six opportunities, roughly seasons 3, 5, 7, 9, 11, 13. After season 13 no new
opportunities are generated; the player will notice the absence before the game
acknowledges it. Do not add a consolation opportunity in Phase 3.

## 8. Relationships

Four axes per NPC, 0–100: `trust`, `respect`, `dependence`, `closeness`.

- Socialise: `+closeness 6`, `+trust 2`, `-stress 8`. Requires the NPC be reachable.
- Not contacting an NPC for **8+ weeks**: `-closeness 5`. This is charged **once per
  eight weeks of silence** — at 8 weeks, again at 16, and so on — not every week past
  the eighth. Weekly it would empty a bond in under four months, which is not what not
  calling your mother does. Any contact resets the clock.
- After **20 weeks** of silence the NPC is `drifted` and out of reach: Socialise no
  longer offers them, and only a repair event brings them back. `drifted` is derived
  from the last contact week, not stored, so it cannot fall out of sync with it.
- Asking for money: `+dependence 15`, `-respect 5`, `-trust 3`. Gated on `trust ≥ 60`.
- Keeping a promise: `+trust 12`. Breaking one: `-trust 20`. Asymmetric on purpose.
- `dependence > 70` on any NPC unlocks resentment events on their side.

Relationships gate the ending's Reconciliation and Grounding axes and nothing else
mechanical. They must never modify ability, form, or match outcome.

## 9. Endings

Evaluated at season 16 end, or on `ev_career_ending_injury`, or on the player choosing to
leave football.

```
reconciliation = mean(trust, closeness) of [npc_mother, npc_father]      >= 55 ?
acceptance     = self_knowledge - (0.5 * cynicism) + (0.3 * hope)        >= 40 ?
grounding      = has_stable_income and debt < 50_000 and no active
                 self_destructive flag                                    ?
```
Three booleans → 8 endings, IDs `ending_000` … `ending_111`. Plus `ending_special_injury`
and `ending_special_left_early`.

Each ending is a 400–700 word authored epilogue scene. See `08` §9 for the constraints
on writing them — in particular, none of them may state the theme.

## 10. Save/load

Save is `(seed, GameState snapshot, action_log)`. A save must be verifiable: replaying
`action_log` from `seed` must reproduce the snapshot exactly. `tools/verify_save.py`
asserts this and runs in CI on a corpus of saves. This is the guarantee that §7.1 holds.

## 11. Failure modes to test for explicitly

| Symptom | Test |
|---|---|
| An optimal player exceeds ability 85 | `test_ceiling_emerges_without_clamp` |
| A player converts >2 of 6 opportunities in 1000 sims | `test_opportunity_conversion_rate` |
| Same failure scene twice in one career | `test_failure_scenes_unique_per_career` |
| Psyche silently changes ability | `test_psyche_does_not_touch_stats` |
| Relationships change match outcome | `test_relationships_do_not_affect_match` |
| Any RNG call outside `core/rng.py` | `test_no_stray_random_imports` |
