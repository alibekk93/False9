# 09 — Milestones

Living document. Claude Code reads this to know what to build next and when to stop.
**Do not start a milestone until the previous one's acceptance test passes.**

Slice strategy: a **thin skeleton of all three phases** first. Every system exists in
crude form and a full 160-week career is playable end to end before anything is deep.
This front-loads the discovery of whether the ceiling reads as tragedy or as cheating,
which is the only question that can kill the project.

---

## M0 — Skeleton (no game yet)

**Scope**: repo, `uv` project, ruff/mypy/pytest wired, `GameState` dataclass, seeded RNG
with substreams, calendar advancing 160 weeks, save/load round-trip, boundary test,
empty pygame window with the screen stack and theme tokens.

**Excludes**: all gameplay.

**Acceptance**: `uv run pytest` green; `tools/sim.py` advances a career from week 1 to 160
with no actions and no crash in under 400 ms; boundary test fails if `pygame` is imported
into `core/`.

---

## M1 — The week works

**Scope**: AP allocation, all six actions, fatigue/money/debt, three ability stats with
training curve and diminishing returns, injury rolls, WeekScreen and LedgerScreen.

**Excludes**: matches, events, relationships, psyche, clubs.

**Acceptance**: a human can play 20 weeks and feel the AP squeeze. Ledger shows every
change with a reason. `test_training_curve_shape` confirms an optimally-trained 26-year-old
lands in the 70s, not the 90s, with no clamp in the code.

---

## M2 — Matches and the balance tool

**Scope**: card schema and loader, deck construction, three-beat play, MatchScreen,
match rating and reports. **`tools/sim.py` extended into the balance harness**: run N
headless careers, output distributions of ability, money, match rating, injury count.

Build the harness here, not later. Everything after this is tuned against it.

**Excludes**: pollution pools (cards exist but psyche doesn't drive them yet).

**Acceptance**: 1000 headless careers complete; ability distribution at age 26 has median
in 68–78 and 99th percentile below 88. Match plays in under 90 seconds by hand.

---

## M3 — Psyche, pollution, relationships

**Scope**: four psyche values, pollution pools driving deck composition, seven NPCs with
four axes, drift, Socialise, the People column, Body/Mood word mapping.

**Acceptance**: `test_psyche_does_not_touch_stats` and
`test_relationships_do_not_affect_match` pass. A career played with zero Socialise and one
played with heavy Socialise produce statistically indistinguishable ability curves and
visibly different hands. This is the design's central claim; verify it here.

---

## M4 — Clubs, contracts, the opportunity system

**Scope**: club model, solvency, wages/arrears, contracts, transfer windows, SeasonScreen.
`core/opportunity.py` with six opportunities, world conditions with reveal weeks, and the
12 named failure scenes.

The most important milestone in the project. Read `03` §7 in full before starting.

**Acceptance**: 1000 careers → mean opportunities converted between 0.5 and 1.5; no career
converts more than 2; no career sees the same failure scene twice; every world condition
in `data/` has a distinct authored failure event. `test_no_hidden_ceiling` greps `core/`
for stat clamps and hardcoded ability limits and fails on any hit.

---

## M5 — Content pass 1: the full spine

**Scope**: enough authored content for one coherent playthrough — ~60 events covering
all three phases, seven NPC arcs at 4 events each, 30 positive cards, 8 per pollution
pool, 10 clubs, all 10 endings drafted.

**Acceptance**: a full 3-hour career is playable start to finish with no placeholder text
visible. Warmth-beat density check passes (≥1 per 5 weeks). Content validator green.

---

## M6 — First playtest and the verdict

**Scope**: no new features. Five external playtesters, full careers, structured debrief.

**The question**: at the end, did the ceiling feel like *the world* or like *the game*?

**Acceptance**: at least 4 of 5 describe the failures in terms of in-fiction causes
(the scout, the manager, the money) rather than mechanical suspicion ("it was rigged",
"stats don't matter"). **If this fails, stop and redesign §7 before building anything
else.** Everything downstream is worthless if this reads wrong.

---

## M7 — Depth pass

**Scope**: Phase 3 compression, the abroad dead end, betting and debt spirals, desperation
pools, dangerous creditor arc, event count to ~140, card count to ~90, match report
templates, onboarding tooltips.

**Acceptance**: second playtest round reports no phase feeling thin. Median session
completion 3–5 hours.

---

## M8 — Accessibility, settings, polish

**Scope**: text scale at 125%/150% with reflow, full key remapping, motion reduction,
dyslexia font option, contrast CI gate, content warning screen, audio implementation and
mixer, all ambience beds and UI sounds.

**Acceptance**: full career completable at 150% text with keyboard only, motion reduced,
audio off. Contrast checker green.

---

## M9 — Ship

**Scope**: PyInstaller builds, save migration corpus, crash reporting to a local log,
itch.io page, store assets, launch checklist in `11-build-release.md`.

**Acceptance**: clean Windows machine installs and completes a career from a downloaded
build. Save from M5 loads and plays under M9 code.

---

## Standing definition of done

A feature is done when: the spec section is implemented as written, tests exist for its
rules, `tools/validate_content.py` and `tools/sim.py` still pass, no new dependency was
added without an ADR, and any spec ambiguity found along the way has been resolved in
`claude-context/` in the same commit.

## Deferred (not now, maybe never)

Controller support · Steam release · achievements · a second protagonist · a manager
mode · any form of multiplayer · localization · mod support.
