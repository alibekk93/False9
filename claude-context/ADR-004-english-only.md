# ADR-004 — English only, no localization layer

Status: Accepted
Date: 2026-08-22

## Context
The game is set in Russia and much of its source material is Russian. A Russian
localization is an obvious future ask. Building i18n scaffolding costs little now and a
great deal later if retrofitted.

## Options
- English only, no scaffolding.
- English only, with a translation layer built in from the start.
- Bilingual from the start.

## Decision
English only, no localization layer, no `gettext`, no locale files. All player-facing
text lives in `data/` regardless — but for editability, not translation.

## Consequences
- One less system, one less dependency, no key-management overhead during the phase when
  content is churning fastest.
- Retrofitting Russian later means a real migration. Accepted; revisit only if the game
  finds an audience.
- A specific constraint follows for the writing: no untranslated Russian words used as
  atmosphere. Cultural specificity must come from behaviour and detail, not vocabulary
  the player cannot read (`08` §4.8).
