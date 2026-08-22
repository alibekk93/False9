# 01 — Vision

## Pitch

A career management game about a Russian footballer who is good, works hard, and never
makes it — and about what he builds instead.

## The player

Adults who play management and life-sim games (Football Manager, *Disco Elysium*,
*Papers, Please*, *Citizen Sleeper*) and are willing to be disappointed on purpose.
They should be able to enjoy the game as a straight, demanding career optimiser for
several hours before they understand what it is doing to them.

## Pillars

1. **Scarcity is the whole game.** Time, energy, and money are always insufficient.
   Every week the player gives something up. There is no build that solves this.
2. **The world is indifferent, not hostile.** Nothing is out to get the protagonist.
   Clubs fold, scouts don't show, wages arrive late, a manager who liked him gets
   sacked. Failure is structural and boring, which is what makes it real.
3. **Small warmth against large cold.** The game is bleak, not nihilistic. A phone call
   answered, a promise kept, a teammate who remembers your name — these are the actual
   rewards, and the systems must make the player feel their weight.
4. **The numbers never lie.** The ceiling is enforced by the world's opportunity
   structure, never by falsifying displayed stats. The player who reads the code should
   find no cheat.
5. **Retrospective revelation.** The meaning arrives in the last hour, assembled from
   choices made in the first three. No character explains the theme aloud. Ever.

## Non-goals

Explicitly out of scope. Do not build these, do not propose them.

- **Football simulation.** No pitch, no ball, no formations, no tactical AI, no
  positioning. Matches are card resolution and always will be. (ADR-002)
- **A winning path.** There is no hidden route to the Champions League. Players will
  look for one. Let them; there is nothing there.
- **Multiplayer, live service, procedural infinity.** One authored career, 3–5 hours.
- **Licensed clubs, players, or competitions.** Everything is fictional-but-plausible.
  Real club and player names never appear in `data/`. (ADR-003)
- **Localization.** English only. (ADR-004)
- **Explicit moralising.** No ending screen tells the player what the game meant. No
  therapist NPC. No epilogue text that says "and he learned that success is internal."
- **Punishing the player for playing badly at football.** Bad football decisions cost
  him a career he was never going to have. Bad *human* decisions cost him things that
  matter. Only the second kind should sting.

## The one-sentence test

If a proposed feature can't be justified as "this makes a specific week harder to
allocate, or makes a specific relationship harder to keep," it probably doesn't belong.

## Risk register

| Risk | Mitigation |
|---|---|
| Player perceives the ceiling as rigged, quits angry | Every blocked opportunity gets a specific, mundane, in-fiction cause. See `03` §7. |
| Bleakness with no relief becomes tedious rather than affecting | Mandatory warmth beats — `08` §6 sets a minimum density |
| Three hours of spreadsheet before the payoff | Phase 1 must be genuinely fun as a straight career game |
| Scope creep into Football Manager | Non-goals above are load-bearing; ADR required to change |
