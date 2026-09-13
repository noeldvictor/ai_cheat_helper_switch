# AI Cheat Helper for Nintendo Switch

A workspace for AI-assisted RAM research that produces personal Atmosphère
cheat files for legally owned, offline single-player Nintendo Switch games.

You tell the AI which effect you want ("infinite HP", "999 gold"). The AI
drives a Python helper on the PC that reads the game's memory over Wi-Fi,
narrows candidates while you play, tests one candidate reversibly, and writes
a copy-paste-ready cheat file into this repository. You toggle the finished
cheat with Ultrahand or EdiZon exactly as before.

## Current status (2026-09-13)

- Physical first-generation Switch, Atmosphère 1.11, firmware 22.1.
- Research bridge: `sys-botbase-lab`, a fork of sys-botbase kept in
  `switch/sys-botbase-lab/`. It adds on-device value search, kernel region
  listing, binary reads, pause and resume, and SD card file transfer. The PC
  side is `tools/switchlab`.
- Working today: game identity (Title ID, Build ID, version), screenshots the
  AI can read, attach diagnosis, mapped region listing, hole-tolerant memory
  snapshots, candidate scan sessions, and file transfer to and from the card.
- Not yet built: guarded test writes, cheat-file generation and lint, pointer
  search, instruction patching.
- Active game: Kowloon High-School Chronicle (`games/kowloon-high-school-chronicle/`).
  Legend of Mana and Torneko's Mystery Dungeon are deferred.

## Cheats being built

In this order, for the active game. The game card holds the technique and
difficulty for each, and the research log holds the evidence.

1. Max money
2. Max attack
3. God mode
4. Double walk and run speed
5. EXP multipliers at x2, x4, x8 and x16
6. EXP multiplier at x100
7. Fast forward, if the game has a speed value that can be changed

The first four are value edits and locks. The EXP multipliers need the
instruction that adds EXP to be found and patched, because the target is the
amount added per kill rather than a stored total. Fast forward depends on the
game keeping a delta-time or frame-limit value, which is not yet known.

## Scope

Supported: legally owned games; offline, single-player use; exact-value and
changed-value RAM searches; read-only snapshots and candidate comparison;
one-candidate-at-a-time reversible test writes; pointer, module-relative, or
signature validation across relaunches; personal Atmosphère cheat files for
the exact installed Build ID.

Not supported: piracy, online or multiplayer cheating, DRM or anti-cheat
bypass, title/prod keys, copyrighted game distribution, redistributable
trainers.

## How a session works

1. **Switch**: close the game completely (Home, then X), relaunch it, and do
   not open Ultrahand or any cheat overlay on it. Opening a cheat overlay
   attaches Atmosphère's cheat manager to the game and blocks the bridge until
   the game is closed.
2. **PC**: the AI runs `status` (identity), `diagnose` (can the bridge attach),
   and `regions` (where the game's data lives).
3. **Switch**: reach a screen that shows the value you care about and stand
   still. The AI reads the number from a screenshot and asks you to confirm.
4. **PC**: the AI takes a memory snapshot (several minutes; the game keeps
   running, so do not press anything) and scans for the value.
5. **Switch**: change the value naturally (take damage, spend money). The AI
   rescans only the remaining candidates, which is fast. Repeat until few
   candidates remain.
6. **PC**: one candidate gets a small reversible test write after you say go,
   then the original is restored.
7. **Switch**: relaunch; the AI validates a pointer chain or static address.
8. **Repository**: the cheat file lands in `games/<slug>/cheats/<BUILD_ID>.txt`
   and gets copied to the card over Wi-Fi. Toggle it in Ultrahand or EdiZon.

Progress is tracked in two files per game. `cheat-notes.md` holds the current
state of each cheat and is updated in place as work happens, so you can see at
a glance which cheats are searching, confirmed, encoded, or verified.
`research-log.md` is the append-only record of what was tried and observed.

The full design, trade-offs, and lessons learned are in `docs/design.md`.

## Cheat files

Every finished or in-progress cheat lives in this repository so it is easy to
copy and paste:

```text
games/<game-slug>/cheats/<BUILD_ID>.txt   Atmosphère cheat file, copy as-is
games/<game-slug>/game.md                 identity, versions, requested effects
games/<game-slug>/cheat-notes.md          state of each cheat, updated as we go
games/<game-slug>/research-log.md         evidence for every experiment
```

Each cheat file starts with a comment block naming the game, version, Title
ID, Build ID, and which cheats are verified versus experimental. Only cheats
that pass the definition of done in `AGENTS.md` are marked verified.

## Helper commands

Run from the repository root. The Switch IP is passed at run time and never
committed.

```bash
export SWITCH_HOST=<switch-ip>
PYTHONPATH=tools python3 -m switchlab status       # bridge version + game identity
PYTHONPATH=tools python3 -m switchlab diagnose     # why memory reads fail, if they do
PYTHONPATH=tools python3 -m switchlab regions      # mapped data regions (about 2 minutes)
PYTHONPATH=tools python3 -m switchlab screenshot   # JPEG into local/screens/
PYTHONPATH=tools python3 -m switchlab peek main 0x0 64
PYTHONPATH=tools python3 -m pytest tools/tests -q
```

## Repository layout

```text
CLAUDE.md                           Claude Code entry point; imports AGENTS.md
AGENTS.md                           AI operating and safety rules
USER_PROFILE.md                     Non-secret user and platform facts
docs/design.md                      Architecture, bridge trade-off, lessons learned
docs/sources.md                     Version-sensitive sources and check dates
.agents/skills/develop-switch-cheats/  Switch cheat workflow skill and references
games/<slug>/                       Card, cheat notes, research log, evidence, cheats
switch/sys-botbase-lab/             Sysmodule fork source and recovery binaries
tools/switchlab/                    Python helper (bridge, identity, regions, snapshot, CLI)
tools/tests/                        Unit tests with a fake bridge
local/                              Ignored: downloads, screenshots, snapshots, dumps
```

Raw memory dumps, saves, keys, credentials, console identifiers, and IP
addresses never enter Git.

## Sources

The conceptual curriculum is the CheatSlips wiki (https://cheatslips.com/wiki).
Version and compatibility decisions are verified against primary project
documentation and recorded in `docs/sources.md`.

## Git workflow

Local commits are frequent and small. Tests and `git diff --check` pass
before each commit. Pushing happens when the user asks for it.
