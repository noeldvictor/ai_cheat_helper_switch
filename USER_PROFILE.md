# User Profile

Last updated: 2026-09-13

## Confirmed boundaries

- The user legally owns the target game.
- All research and cheat use will remain offline and single-player.
- No online, multiplayer, anti-cheat bypass, DRM bypass, piracy, or
  redistribution is in scope.

## Available platforms

- Physical Nintendo Switch (first-generation): available, already running
  Atmosphère with homebrew working (confirmed 2026-09-13).
- Nintendo Switch emulator on Windows: available, not the first platform.
- First research platform: physical Switch.
- Physical Switch Atmosphère version: unknown.
- Physical Switch system firmware version: unknown.

## Tools and connection

Already on the Switch (confirmed 2026-09-13):

- EdiZon-SE (homebrew app), version unknown.
- Breeze (homebrew app), version unknown.
- Ultrahand and/or the EdiZon overlay, used to toggle cheats in-game.

Not yet on the Switch:

- sys-botbase: not installed. Proposed research bridge; decision pending.
- FTP server (sys-ftpd or ftpd): unknown. Needed for Wi-Fi deployment.

PC side:

- The helper app runs on the Linux machine where Claude Code runs.
- PC and Switch talk over local Wi-Fi. The Switch IP address is used
  ephemerally and never committed.
- Do not install a tool until its current compatibility has been checked
  against the user's Atmosphère and firmware versions.

## First game

- Name: Dragon Quest Heroes: Torneko's Mystery Dungeon -Classic HD-
- Edition: Nintendo Switch (first-generation) version, confirmed by the user.
- Released 2026-09-09 (Square Enix). Also exists on Switch 2, PS5, Xbox, and
  Steam; those editions are out of scope.
- Game version: unknown.
- Title ID: unknown.
- Build ID: unknown.
- Previous candidate `Legend of Mana` is deferred, not abandoned.

Do not copy a Title ID or Build ID from a website and assume it matches the
installed game. Read both from the user's running copy or installed tool.

## Desired results

The user wants a flexible system: they describe a cheat in plain language
("I need a cheat that does X, Y, Z") and the AI drives the discovery loop.

Cheat kinds the system should support (all chosen by the user):

1. Set a value (gold, level, stats) through a relaunch-stable pointer chain.
2. Lock a value (infinite HP, no hunger) with the Atmosphère cheat VM.
3. Code patches (one-hit kill, no random encounters, speed) via ARM64
   instruction patches for the exact Build ID.
4. Item and inventory edits.

The first target value is undecided. Gold is the recommended first target
because it is a visible integer that changes naturally. Work on one
falsifiable target at a time.

## Assistance preference

- Experience level: beginner in memory research. Prefers short multiple-choice
  questions, concrete examples, and plain-language explanations. Abstract
  workflow descriptions did not land; explain by walking through one cheat.
- Preferred style: maximum practical automation. The AI runs scans and
  comparisons; the user performs natural in-game actions when asked.
- The AI should read the visible value from a Switch screenshot when the
  bridge supports it, and ask the user to confirm or correct it.
- Default every helper to read-only or dry-run mode.
- A memory write must require an explicit apply action, record the original
  value/bytes, touch only one confirmed candidate, resume in a `finally` path,
  verify with a second read, and offer immediate restoration.
- Do not bulk-write all candidates or automatically test several cheats.
- Deployment: FTP over Wi-Fi after the user confirms; back up any existing
  cheat file first. The user then toggles cheats with Ultrahand or EdiZon as
  they do today.

## Information needed next

1. Atmosphère version and system firmware version (shown in the Atmosphère
   boot splash or in Hekate / the homebrew menu).
2. Whether an FTP server (sys-ftpd, ftpd) is installed on the Switch.
3. Decision on the research bridge (see `docs/design.md`).
4. The Switch's local IP address, shared in chat only, when a session starts.
5. Later: game version, Title ID, and Build ID read from the running game.
