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
- Physical Switch Atmosphère version: 1.11 (user-reported 2026-09-13; patch level not yet confirmed).
- Physical Switch system firmware version: 22.1 (user-reported 2026-09-13).

## Tools and connection

Already on the Switch (confirmed 2026-09-13):

- EdiZon-SE (homebrew app), version unknown.
- Breeze (homebrew app), version unknown.
- Ultrahand and/or the EdiZon overlay, used to toggle cheats in-game.

Not yet on the Switch:

- sys-botbase v2.5: installed 2026-09-13 and verified. It answers
  `getVersion` with `2.5` on TCP port 6000 from the Linux helper machine.
- FTP server (sys-ftpd or ftpd): unknown. Needed for Wi-Fi deployment.

PC side:

- The helper app runs on the Linux machine where Claude Code runs.
- PC and Switch talk over local Wi-Fi. The Switch IP address is used
  ephemerally and never committed.
- Do not install a tool until its current compatibility has been checked
  against the user's Atmosphère and firmware versions.

## First game

- Name: Kowloon High-School Chronicle (Nintendo Switch), chosen 2026-09-13.
- Display version 1.0.0, Title ID 0100FF70134BA000, Build ID
  6547E06ECC5E8F4B, all read from the running game through the bridge.
- Legend of Mana: deferred; it crashed at launch on 2026-09-13 (cause not yet
  investigated; details in its game card).
- Dragon Quest Heroes: Torneko's Mystery Dungeon -Classic HD-: deferred.

Do not copy a Title ID or Build ID from a website and assume it matches the
installed game. Read both from the user's running copy or installed tool.

## Desired results

The user wants a flexible system: they describe a cheat in plain language
("I need a cheat that does X, Y, Z") and the AI drives the discovery loop.

Cheat kinds the system should support (all chosen by the user):

1. Set a value (money, level, stats) through a relaunch-stable pointer chain.
2. Lock a value (infinite HP) with the Atmosphère cheat VM.
3. Code patches (god mode, EXP multipliers, speed) via ARM64 instruction
   patches for the exact Build ID.
4. Item and inventory edits.

Specific cheats requested on 2026-09-13, in the agreed order of work:

1. Max money
2. Max HP (raise the ceiling)
3. Full heal (one write of current HP to maximum)
4. Infinite HP (lock current HP each frame)
5. Max stats, such as attack and defence
6. God mode (damage never subtracted; needs a code patch)
7. Infinite ammo, meaning the loaded magazine never drops
8. Max reserve ammo
9. Double walk and run speed
10. EXP multipliers at x2, x4, x8, x16
11. EXP multiplier at x100
12. Fast forward, if the game has a speed or delta-time value to change

The user asked on 2026-09-13 for the health and stat cheats to be described
precisely rather than lumped together as "god mode". Keep them as separate
entries with separate promises.

The per-game breakdown, with the technique and difficulty for each, is in the
game card. Work on one falsifiable target at a time. Money is first because it
proves the search pipeline before any code patching starts.

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

## Session facts learned 2026-09-13

- The user is present during sessions and wants questions only when the tool
  cannot find the answer itself.
- Opening Ultrahand on a game blocks the bridge until the game is closed.
- No FTP server is on the Switch (ports 5000, 21, 2121 closed). Cheat files
  go to the card by card reader until one is installed.
- Reads run at about 0.7 MB/s; Kowloon's scan set is about 700 MiB.

## Information needed next

1. Done 2026-09-13: Atmosphère 1.11, firmware 22.1 (patch levels to confirm from the
   System Settings version line).
2. Done 2026-09-13: no FTP server present; install ftpd later for Wi-Fi deploy.
3. Done 2026-09-13: research bridge is sys-botbase v2.5, installed and answering.
4. The Switch's local IP address, shared in chat only, when a session starts.
5. Done 2026-09-13 for Kowloon High-School Chronicle: version, Title ID, and
   Build ID read from the running game.
