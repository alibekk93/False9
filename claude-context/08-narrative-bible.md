# 08 — Narrative Bible

Read this before writing **any** player-facing text: events, cards, match reports,
endings, and even UI labels.

## 1. The protagonist

Unnamed by default; the player names him. Born 2003 in a provincial city of ~350,000.
Father worked at a plant that no longer exists in the form he knew; mother is a nurse.
He is a false nine by position and by the game's title pun: the player who occupies the
place where the striker should be without ever being one.

He is **not remarkable and not pathetic**. He is diligent, quiet, moderately clever, bad
at asking for things, and better at football than almost everyone he will ever meet. The
writing must never make him a joke or a saint.

## 2. Setting

Contemporary Russia, lower divisions. The fictional geography:

- **Nizhnegorsk** — hometown. 350,000. A plant, a river, a bus station, one club.
- The third and fourth tiers, provincial towns of 40,000–200,000, reached by overnight bus.
- Occasional Moscow, always as somewhere he is passing through and not staying.
- One tempting dead end abroad: a fourth-tier Turkish club, a hotel room, a language app.

**All clubs, players, competitions, and officials are fictional.** No real names, ever
(ADR-003). Real-world texture comes from structure, not from licensing.

## 3. Tone

Neo-noir without the crime. Quiet realism. The register is **flat, concrete, and
unsentimental**, and it earns emotion by withholding it.

Motifs to return to: thresholds and corridors, waiting rooms, bus and train stations,
things half-finished, snow that has been walked on, fluorescent light, the specific
tiredness of 06:40, laminated signs, the phrase "temporarily."

## 4. Hard constraints

These are rules, not preferences. Violating any of them is a bug.

1. **Never state the theme.** No character says success is internal, or that he has
   learned to accept things, or that the journey mattered. If a line could be printed on
   a poster, delete it.
2. **No narrator.** Second person, present tense, tight to his perception. The prose
   knows only what he knows.
3. **No character is a mouthpiece.** Nobody exists to explain the game.
4. **No irony at his expense.** The game is not smarter than the protagonist.
5. **No cruelty from the world.** Nobody is a villain. The agent is not a crook; he is
   busy and has eleven other clients and this is the honest, worse reality.
6. **No poverty tourism.** Deprivation is written as texture and logistics, never as
   spectacle. If a passage would work as a photograph of somebody's kitchen taken without
   permission, rewrite it.
7. **No dialect spelling, no phonetic accents.** Register and syntax carry voice.
8. **No Russian words as flavour.** English only, which means no italicised untranslated
   nouns doing atmospheric work. Cultural specificity comes from what people do, not from
   vocabulary the player can't read.
9. **Sentences stay short.** Target average under 14 words. When a passage swells, cut it.
10. **No em-dash-heavy interiority.** He does not narrate his feelings. He notices the
    room.

## 5. Voice by content type

| Type | Length | Register |
|---|---|---|
| Event scene body | 2–5 sentences | observational, concrete, present tense |
| Choice text | ≤ 12 words | plain intention, no editorialising |
| Choice outcome | 1–2 sentences | consequence stated flatly |
| Card flavour | 1 sentence | physical, immediate |
| Card outcome | 1–2 sentences | what happened, who saw |
| Match report | 60–110 words | the register of a local newspaper that isn't trying |
| Ending epilogue | 400–700 words | the only place the prose is allowed to breathe |

Bad choice text: *"Bravely confront the director about the wages you're owed."*
Good choice text: *"Ask the director when you'll be paid."*

## 6. Warmth beats — a quota, not a mood

Bleakness without relief becomes noise and stops registering. **Minimum one warmth beat
per five weeks**, tracked by `tools/check_warmth.py` against the event corpus.

A warmth beat is small, specific, and unpurchased: a teammate saves him a seat, his
mother sends money he didn't ask for and doesn't mention it, someone remembers his
birthday on a bus, a kid at the training ground copies his warm-up. It is never a
reward for optimisation and it is never a mechanical bonus of any size. It is the only
place `accent_warm` appears (`06`).

The endgame density of warmth beats rises even as the career declines. That inversion is
the whole argument of the game, made without a single line of dialogue about it.

## 7. Cast

| NPC | Function | Note |
|---|---|---|
| Mother | the unpaid infrastructure of his life | Nurse. Never asks for anything. Her arc is whether he notices. |
| Father | expectation, then disappointment, then something quieter | Was not a footballer. Wanted a trade for him. Not a bully. |
| Kostya | the friend who stayed | Opens a business, fails, opens another. His life is going worse and he is happier. |
| Vitya | the teammate | Older, funnier, ends up coaching kids. Says the true thing first. |
| Ilya Nikolaevich | the coach who mattered | Believes in him at 17. Is wrong, and is not lying. |
| Ruslan | the agent | Not a crook. Overextended. Answers the phone 40% of the time. |
| Dasha | the partner | Has her own trajectory. Whether she stays depends on whether he is present, not on money. |

Each gets an arc of 4–6 events across the career with a real ending, including the
possibility of drifting out of the story unresolved.

## 8. Research grounding

Grounded in reporting from Russian lower-division football. Draw on the *structures*
described below; never lift a real person's story or name.

- **Players living on nothing**: the *Znamya Truda* account of a player supported by his
  girlfriend's salary and losing savings to a pyramid scheme — the model for the money
  system's texture and for `ev_pyramid_scheme`.
- **Unpaid wages as normal**: reporting on squads playing months without pay ("ready for
  anything, like a wounded animal") — the model for `03` §6.2 solvency and arrears.
- **Salary caps and provincial economics**: an FNL side sitting sixth with a wage ceiling
  around ₽100,000, competing on argument rather than money — the model for club traits
  and for what a "good" contract looks like in this game.
- **Geography as structural barrier**: the PFL Vostok zone reforms described as the death
  of football beyond the Urals — the model for remoteness and for opportunities that fail
  because of travel and timing.
- **Careers sideways, not upward**: a PFL player moving to the Turkish fourth tier, living
  in a hotel and learning the language — the model for the abroad dead end.
- **Debt and betting**: reporting on a player's gambling debts — the model for the
  betting trap, which must be written without moralising.
- **Clubs that vanish**: the journalist who found a town whose team had been gone five
  years and whose stadium had grown over — the model for `ev_club_folds` and the tone of
  Phase 3.
- **Money management as an unlearned skill**: coverage arguing clubs, leagues, and parents
  should teach it — the model for why no NPC ever gives him useful financial advice.

Full source list in `claude-context/sources.md`. When writing an event, cite which
structure it draws on in the JSON `notes` field.

## 9. Endings — writing constraints

Ten epilogues (`03` §9). Each is a single scene, 400–700 words, set 1–3 years after the
last playable week, in an ordinary location, doing an ordinary thing.

- **No summary.** The epilogue does not recount the career.
- **No stated moral.** Not one sentence of reflection that names what any of it meant.
- **No score, no stats, no "you achieved."** The ending screen shows the scene and
  nothing else.
- Football appears in every ending, but never centrally — on a television, in a schedule
  on a fridge, in a bag by a door, in a child's shin pads.
- The differentiator between endings is **who is in the room, and whether he is easy in
  it.** That is the only variable the writing is allowed to play.

The best ending and the worst ending must be indistinguishable on a CV.
