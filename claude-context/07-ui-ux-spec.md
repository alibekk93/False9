# 07 — UI / UX Spec

## Screen inventory

| Screen | Purpose |
|---|---|
| `TitleScreen` | new career / continue / settings / quit |
| `NewCareerScreen` | name, hometown, position, seed (optional) |
| `WeekScreen` | **the main screen.** Status, AP allocation, week context |
| `EventScreen` | a scene with 2–4 choices |
| `MatchScreen` | three beats of card play |
| `LedgerScreen` | end-of-week summary of every change |
| `ProfileScreen` | stats, injury history, contract, relationships (read-only) |
| `SeasonScreen` | end-of-season resolution, contract offers, transfer window |
| `EndingScreen` | epilogue |
| `SettingsScreen` | audio, motion, text size, key bindings |

## Flow

```
Title ─┬─ Continue ──┐
       └─ NewCareer ─┴─> WeekScreen ─┬─> EventScreen ──┐
                            ▲        ├─> MatchScreen ──┤
                            │        └─> ProfileScreen ┘
                            │                          │
                            └────── LedgerScreen <─────┘
                                         │
                            (week 10) SeasonScreen
                                         │
                            (season 16) EndingScreen
```

`ProfileScreen` is reachable from anywhere and pauses nothing (the game is turn-based).
`SettingsScreen` overlays. There is no in-match escape to Profile — once a hand is dealt,
it plays out.

## WeekScreen layout

Three columns on the 1280 grid:

```
┌─ 380 ──────────┬─ 480 ───────────────┬─ 356 ─────────┐
│ STATUS         │ THIS WEEK           │ PEOPLE        │
│ Season 6 / W3  │                     │               │
│ Age 21         │ Zarya away at       │ Mother   ····│
│                │ Kolomna. Bus leaves │ Kostya   ····│
│ Technique  54  │ Thursday 06:40.     │ Vitya    ····│
│ Physical   61  │                     │ Agent    ····│
│ Mental     48  │ Wages: 3 weeks late │               │
│                │                     │ (dots = drift)│
│ Body   worn    │ ┌─ ACTION POINTS ─┐ │               │
│ Mood   tight   │ │ ○ ○ ○ ○         │ │ PENDING       │
│                │ │ [Train ▸]       │ │ · Kostya asked│
│ ₽ 2,400        │ │ [Recover]       │ │   about money │
│ Debt 41,000    │ │ [Work]          │ │ · Medical due │
│                │ │ [Socialise ▸]   │ │               │
│                │ │ [Deal With It▸] │ │               │
│                │ │ [Drift]         │ │               │
│                │ └─────────────────┘ │               │
└────────────────┴─────────────────────┴───────────────┘
              [ End week ▸ ]   (enabled at 0 AP or via Drift)
```

Selecting an action with a submenu (`▸`) opens an inline list, not a modal.

## Reading psyche as words, not numbers

`03` §4 keeps psyche numeric internally. The UI never shows those numbers. Two fields,
`Body` and `Mood`, each map a computed value to one of seven words. Word tables live in
`data/strings/ui.json`.

- **Body** (from fatigue + injury): `fresh, ready, worked, heavy, worn, hurting, broken`
- **Mood** (from stress, hope, cynicism): `light, steady, flat, tight, sour, hollow, done`

The player must not be able to reverse-engineer an exact value. This is the one place the
game withholds precision — and it withholds precision, which is not the same as lying.
Stats, money, form, and contract terms are always exact.

## MatchScreen

Three beats, played in sequence. Per beat: five cards fanned across the lower third, the
beat context in the upper area (score, minute, one line of situation). Player selects one
card; it animates to centre, resolves, and the outcome text holds for **1.6 s minimum**
before the next beat. No skip on first playthrough of a beat; hold `Space` to fast-forward
after that.

After the third beat: match rating, one-paragraph report, effects list. The report is
authored from templates in `data/events/match_reports/`, selected by rating band and
result. **The report describes his performance, not the team's glory.**

## LedgerScreen

The week's `Effect` list, rendered one line at a time at 90 ms intervals:

```
  Technique      54 → 55        +1
  Fatigue        38 → 62       +24
  ₽           8,900 → 2,400  −6,500
  Debt       39,800 → 41,000 +1,200
  Kostya      closeness         −5     (not contacted, 9 weeks)
```

Losses in `neg`, gains in `pos`, unchanged omitted. The relationship line with its
parenthetical reason is the most important row on this screen — it is how neglect becomes
visible before it becomes irreversible.

## Input

Full keyboard and mouse. Controller is out of scope for v1.0.

| Key | Action |
|---|---|
| `↑ ↓` / mouse | move selection |
| `Enter` / click | confirm |
| `Esc` | back / settings |
| `Tab` | Profile |
| `Space` | advance text, fast-forward resolved beat |
| `1`–`5` | select card by position in hand |
| `F5` | reload `data/` (dev builds only) |

Every action reachable by keyboard alone. Focus ring in `accent_cold`, 2 px, always
visible — no "focus only on keyboard input" heuristics.

## Accessibility floor (v1.0, non-negotiable)

- **Text scale**: 100% / 125% / 150%. Layout reflows; nothing clips. Tested at 150%.
- **Full key remapping**, persisted in settings.
- **Motion reduction** toggle (`06`).
- **Colour is never the only channel**: gains/losses carry `+`/`−` signs, pool identity on
  cards carries a text label as well as an edge colour.
- **No timed inputs anywhere.** The 1.6 s card hold is a minimum, not a deadline.
- **Dyslexia-friendly option**: switches body font to Atkinson Hyperlegible and raises
  line height to 1.7.
- **Screen shake, flashing, strobing**: none exist, so nothing to disable.

## Content warnings

The game covers debt, gambling, alcohol, injury, family conflict, and depression. A
plain, unskippable content notice appears once before a new career, listing themes and
noting which of the heaviest are avoidable versus structural. It does not editorialise.

## Onboarding

No tutorial screen. The first three weeks of Phase 1 are authored to introduce one system
each (AP, match cards, relationships) through scenes that would exist anyway. A tooltip
appears the first time each stat is shown and never again. `?` opens a reference panel.

Design constraint: a player must be able to understand the AP economy without reading
anything they didn't want to read.
