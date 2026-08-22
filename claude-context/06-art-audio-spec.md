# 06 — Art and Audio Spec

The game is text-forward: **typography, colour, and space are the art direction.** There
are no character portraits, no sprites, no illustrated scenes. This is a production
decision (one developer, no artist) that the design should wear as a style rather than
apologise for. The reference points are administrative documents, team sheets, printed
match reports, and bus timetables — not games.

## Resolution and layout

- Logical resolution **1280×800**, integer-scaled, letterboxed. Never stretched.
- Baseline grid of **8 px**. All vertical rhythm snaps to it.
- Margins: 64 px outer, 32 px between columns. Generous whitespace is the mood.
- Maximum text measure **68 characters**. Wrap, never scale text to fit.

## Typography

| Role | Font | Size | Use |
|---|---|---|---|
| Body | IBM Plex Sans | 18 | scene prose, choices |
| Numeric / data | IBM Plex Mono | 16 | stats, money, ledger, tables |
| Header | IBM Plex Sans SemiBold | 28 | screen titles, week header |
| Small caps label | IBM Plex Sans | 12, tracked +0.08em | field labels, section markers |

IBM Plex is OFL-licensed and ships in `assets/fonts/` with `LICENSE.txt` alongside.
Do not add a display or decorative typeface. Do not use italics for emphasis in prose;
use a line break.

## Palette

Desaturated, cold, low contrast between elements but high contrast for text. Named
constants live in `ui/theme.py` and nowhere else.

| Token | Hex | Use |
|---|---|---|
| `bg_deep` | `#0E1113` | screen background |
| `bg_panel` | `#161A1D` | panels, cards |
| `bg_raised` | `#1F2529` | hover, selected |
| `line` | `#2B3237` | rules, borders |
| `text_primary` | `#D8DCDE` | body |
| `text_muted` | `#7C878D` | labels, secondary |
| `text_dim` | `#4E585E` | disabled, greyed choices |
| `accent_cold` | `#5B7C8D` | interactive, focus ring |
| `accent_warm` | `#B08558` | the warmth beats, and only those |
| `neg` | `#8C4A4A` | losses, injuries, debt |
| `pos` | `#5F7A5A` | gains — deliberately muted, never bright |

**`accent_warm` is a scarce resource.** It appears on screen only during a warmth beat
(`08` §6), on a kept promise, and in exactly two ending epilogues. If it shows up on a
button, the palette is broken. Grep for it in review.

Contrast: every text/background pair must clear **WCAG AA (4.5:1)**. Verified by
`tools/check_contrast.py` in CI. `text_dim` on `bg_deep` is the one exception and is only
used for genuinely non-essential greyed text; the reason string beside it uses
`text_muted`.

## Match cards

A card is a rectangle: 280×180, 1 px `line` border, `bg_panel` fill, title in header
style, flavour in body, pool indicated by a 3 px left edge in a pool colour. No
illustration. Pool colours are all within the cold range except `pool_hurt`, which uses
`neg` — the player should feel the hand darken without being told.

## Motion

Minimal and slow. Everything eases over **180 ms**. Card deal staggers 60 ms per card.
Screen transitions are a 200 ms crossfade. No bounce, no elastic, no particles, no screen
shake. The one exception: the week ledger reveals its lines sequentially at 90 ms
intervals, because watching the damage arrive one line at a time is the feeling.

Full motion-reduction toggle in settings collapses all of the above to instant.

## Audio

Ambient and diegetic only. No music score, no stingers, no win fanfare — a fanfare would
undo the entire design.

**Ambience beds** (looping, per location, 60–120 s, seamless): `changing_room`,
`training_ground_winter`, `bus_night`, `apartment`, `stadium_empty`, `stadium_small_crowd`,
`corridor`, `station`, `pitch_rain`.

**UI sounds** (dry, quiet, ≤ 200 ms): `select`, `confirm`, `back`, `card_deal`,
`card_resolve`, `ledger_line`, `week_end`. Peak −18 dBFS. If a sound is noticeable, it is
too loud.

**No sound plays on**: gaining a stat, winning a match, receiving money. Positive feedback
sounds are the standard mechanism for making a career game feel good, and this game
should not feel good in that way.

Format: OGG Vorbis q5, 44.1 kHz. Ambience mono, UI mono. Two mixer buses (`ambience`,
`ui`), each with a settings slider, plus a master. All default to 70%.

## Asset conventions

```
assets/
  fonts/       IBMPlexSans-Regular.ttf, IBMPlexSans-SemiBold.ttf, IBMPlexMono-Regular.ttf
  audio/
    ambience/  amb_bus_night.ogg
    ui/        ui_card_deal.ogg
  icons/       ico_fatigue.svg → rasterised to ico_fatigue@1x.png at build
```

Naming: `type_subject_variant.ext`, lowercase, snake_case. Every asset directory has a
`SOURCES.md` recording origin and licence for each file. No asset enters the repo without
that line — this is what makes shipping possible later.

Icons: at most **12** in the entire game, single-weight line style, 24×24. If a concept
needs a thirteenth icon, use a word instead.
