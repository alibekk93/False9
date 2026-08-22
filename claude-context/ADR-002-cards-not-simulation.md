# ADR-002 — Matches resolve as cards, not simulation

Status: Accepted
Date: 2026-08-22

## Context
A football career game invites a football match engine. Building one is months of work,
is the most heavily contested design space in the genre, and would put the project in
direct comparison with Football Manager — a comparison it cannot survive and does not
want.

More importantly: the game is not about football matches. It is about the weeks between
them.

## Options
- 2D top-down match simulation with positioning and tactics.
- Statistical match resolution with no player input.
- Card-based resolution: a deck built from the protagonist's condition, a hand per match.

## Decision
Card resolution. Three beats, five cards dealt, three played. The deck is assembled
deterministically from ability, form, fatigue, and psychological state.

## Consequences
- Psychological state can pollute the deck (`03` §5.3), making a life falling apart off
  the pitch legible in play without any hidden stat penalty. This is the mechanic the
  decision was really made for.
- Match content becomes authored JSON, so match variety scales with writing rather than
  with engine work.
- The player never controls tactics, teammates, or the ball. Some genre expectations go
  unmet; that is accepted.
- Forbids: ball physics, formations, opponent tactical AI, a pitch view. Permanently.
