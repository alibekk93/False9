# 02 — Game Design

The "why" layer. For exact values and formulas, see `03-mechanics-spec.md`.

## Shape of a playthrough

One career. Age 16 → 32. **16 seasons**, each **10 playable weeks**, so **160 weeks**
total. At a target of ~70 seconds per week, that lands at ~3.1 hours, plus onboarding
and endgame. Weeks are not uniform in weight: heavy decision weeks alternate with fast
ones, and later seasons compress (see §5).

## The week (core loop)

Every week the player:

1. **Reads the week header** — club situation, money, body, mood, what's coming.
2. **Spends 4 Action Points** across: Train, Recover, Work, Socialise, Deal With It
   (errands, bureaucracy, debts), Drift (do nothing — costs 0 AP but consumes the week).
3. **Plays the match** if there is one, as a card hand (§3).
4. **Resolves 0–2 events** — scripted or conditional, presented as short scenes with
   choices.
5. **Sees the week's ledger** — what changed, what didn't get paid, who called and
   wasn't called back.

The loop is deliberately mundane. The tension comes from the fact that 4 AP is never
enough to keep the body, the wallet, and the people all in acceptable condition, and
that neglect compounds silently for weeks before it presents a bill.

## The match as cards

Matches do not simulate football. Each match:

- The game **builds a deck** from the protagonist's current ability, form, fitness,
  and psychological state.
- The player is dealt a **hand of 5 Moment cards** and plays 3 across three match beats
  (early, middle, late).
- Cards resolve into a match rating, fitness cost, injury risk, relationship deltas,
  and narrative flags.

The critical mechanic: **psychological state pollutes the deck**. High stress seeds
`card_hide` and `card_rushed_pass`. High cynicism seeds `card_late_tackle` and
`card_argue_with_ref`. Low hope seeds `card_go_through_motions`. The player cannot see
these coming, only that their hand is worse. This makes mental state legible through
play rather than through a status bar — and it is the mechanism by which a life falling
apart off the pitch degrades performance on it, without any hidden penalty to stats.

Deck construction is fully deterministic and inspectable. No hidden dice roll decides
whether he is good today; his week decided it.

## Money

Income is unreliable by design. A club has a **solvency** value; when it is low, wages
arrive late or not at all, and the player finds out only on payday. Side jobs (Work AP)
are reliable but cost the AP that would have gone into training or into people. Debt
accrues interest weekly and unlocks a small, seductive set of bad options — a loan from
the wrong person, a bet on a match, an agent who wants a cut of everything.

Betting is available and mathematically negative. It is never signposted as a trap.
Sources on the real thing: the Bozhenov debt story, the *Znamya Truda* player living on
his girlfriend's salary. See `08-narrative-bible.md` §8.

## Career phases

### Phase 1 — Youth and academy (16–18, seasons 1–3, 30 weeks)

Trials, school, parental expectations, the first coach who matters, the first injury.
AP is contested by school and by home. This phase plays as an ordinary, hopeful career
game and **must be genuinely enjoyable on its own terms** — everything later depends on
the player having wanted it.

Ends with a placement: a professional contract at a third-tier club, a semi-pro deal, or
nothing and a year lost. All three are survivable. None are a good start.

### Phase 2 — The climb (19–25, seasons 4–10, 70 weeks)

The longest phase and the heart of the game. Unstable contracts, clubs in provincial
towns, unpaid wages, bus travel, a move abroad to a fourth-tier foreign league as a
tempting dead end. The player will spend this phase optimising hard toward a promotion
or a transfer upward. **Opportunities appear regularly and fail mundanely** (§7 of `03`).

Roughly one genuine chance per two seasons. Each is real, each is winnable in the sense
that the player's inputs matter, and each is stacked by things outside his control.
Some players will convert one. Converting one moves him one division, not one tier of
existence.

### Phase 3 — Plateau and drift (26–32, seasons 11–16, 60 weeks)

The chances stop coming and the game stops pretending. Wages stabilise at a low level or
stop entirely. The body accumulates permanent damage. Side work becomes central. New
options open that were invisible before: coaching kids, a stake in a Sunday-league club,
leaving football, going back to school, becoming the person who fixes the pitch.

This phase compresses — weeks batch into months where nothing decisive happens — and the
AP economy loosens slightly. The player has more room and less to spend it on. That
feeling is the point.

## Progression and the ceiling

Ability rises with training and falls with age and injury, honestly, on a visible curve.
A well-played protagonist becomes genuinely good — good enough for the second tier,
respected in his league, the best player in most rooms he enters.

He does not become a star, because **stardom is not a function of ability in this game**.
It is a function of ability *times* opportunity, and opportunity is a separate system
that the player only partially controls. See `03` §7 for the exact enforcement, which is
the single most important thing in the design to get right.

## Relationships

Seven tracked NPCs (mother, father, childhood friend Kostya, a teammate, a coach, an
agent, a partner). Each tracked on four axes: **trust, respect, dependence, closeness**.

These do not modify football outcomes. They modify which events are available, what the
protagonist can ask for when he is desperate, what the psyche system does under load, and
the ending. A player who optimises football and neglects people will have an
indistinguishable career and a materially worse life. That asymmetry is the argument the
game is making, and it is made entirely through mechanics.

## Endings

Triggered at age ~32 or earlier on a career-ending injury. Every ending is a mediocre
football career. What varies is a 3-axis inner state:

| Axis | Poles |
|---|---|
| Reconciliation | reconciled with family / estranged |
| Acceptance | at peace with the modest life / still haunted |
| Grounding | stable (work, people, health) / lost (debt, drink, isolation) |

Eight primary endings from the axis combinations, plus two special cases (career-ending
injury at 22; leaving football entirely before 25). Endings are epilogue scenes, not
score screens. No ending is labelled good or bad, and no ending text states the theme.

## What the player is doing, honestly

For three hours: allocating a week, playing a hand, reading a scene, watching a number.
The game earns its ending by making that loop good enough that the player invests in a
future the game already knows isn't coming.
