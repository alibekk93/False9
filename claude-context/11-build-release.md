# 11 — Build and Release

Deliberately thin. Most of this matters only at M9; do not build it early.

## Targets

| Platform | Status |
|---|---|
| Windows 10/11 x64 | primary |
| Linux x64 | best-effort, unsigned tarball |
| macOS | not supported in v1.0 (signing and notarisation cost more than the audience) |

## Packaging

PyInstaller, one-folder mode (not one-file — startup is faster and `data/` stays
inspectable, which is a feature for a game whose design claim is "no hidden cheat").

```powershell
uv run pyinstaller build/false-nine.spec --noconfirm --clean
```

The spec bundles `assets/` and `data/` as datas. `data/` ships **unpacked** and readable.
A `MODDING.md` note says so plainly; edits are unsupported but not prevented.

## Versioning

`MAJOR.MINOR.PATCH`. Single source of truth in `src/false_nine/__about__.py`, read by the spec file,
the title screen, and the save writer.

- MINOR: new content or systems.
- PATCH: fixes and balance.
- Every release bumps `SAVE_VERSION` only if `GameState` changed shape, and every bump
  gets a migration plus a fixture save in `tests/fixtures/saves/`.

## Save compatibility promise

Saves from any released version load in every later version. This is cheap to honour now
and impossible to retrofit. `tools/verify_save_corpus.py` loads every historical fixture
under current code, in CI.

## Crash handling

Uncaught exception → write `crash_<timestamp>.log` next to the save directory containing
traceback, version, seed, week index, and the last 20 actions. Show a plain dialogue with
the log path. **No automatic upload, no telemetry, no network calls of any kind.** The
game never opens a socket.

Because saves are `(seed, action_log)`, a crash log plus a save is a complete, exactly
reproducible bug report. Say so in the dialogue text.

## Distribution

itch.io first, direct download, pay-what-you-want with a minimum. Steam is deferred and
requires an ADR — it adds a Steamworks dependency, a review cycle, and a refund window
that interacts badly with a 3-hour game.

## Store page requirements (M9 only)

- Capsule art, 6 screenshots, one 45 s trailer of actual play with no music.
- Description that does not spoil the design. Sell it as a hard, realistic lower-division
  career game. That is not a lie; it is what the first three hours are.
- Content warnings listed on the page as well as in-game (`07`).
- Accessibility features listed explicitly.

## Licensing and attribution

- Code: choose before M9. Source-available is compatible with the "no hidden cheat" claim
  and worth considering.
- Fonts: IBM Plex under OFL, Atkinson Hyperlegible under OFL. Ship both licences in
  `assets/fonts/`.
- Audio: every file's origin and licence recorded in `assets/audio/SOURCES.md`. No file
  without a line.
- A `CREDITS.md` generated from the SOURCES files at build time.

## Launch checklist

- [ ] Clean Windows VM: download, extract, run, complete a full career
- [ ] Save from M5 loads and plays
- [ ] All historical fixture saves load
- [ ] No placeholder text anywhere (`tools/find_placeholders.py`)
- [ ] Content validator, contrast check, full test suite green
- [ ] 1000-career sim: ending distribution has no ending at 0% and none above 25%
- [ ] Every asset has a licence line
- [ ] Content warning screen present and accurate
- [ ] Version, credits, and licences visible from the title screen
- [ ] Crash handler produces a usable log on a forced exception
