# AI Cheat Helper for Nintendo Switch

A beginner-friendly workspace for using AI-assisted RAM research to create
personal cheats for legally owned, offline single-player Nintendo Switch games.

The project turns the CheatSlips learning curriculum into a guided, logged, and
increasingly automated workflow. The long-term goal is to automate repetitive
memory reads, scans, candidate narrowing, guarded test writes, restoration, and
stability validation without hiding the evidence needed to trust a result.

## Current status

The repository is in its initial planning and game-intake stage:

- safety and research rules are defined in `AGENTS.md`;
- the user's automation preference is recorded in `USER_PROFILE.md`;
- `Legend of Mana` is the tentative first game;
- no scanner or device adapter has been implemented;
- no software has been installed;
- no game memory has been read or modified.

The exact game title, first platform, running tool version, game version, Title
ID, Build ID, and first visible target value still need confirmation.

## Scope

This project supports:

- legally owned games;
- offline, single-player use;
- exact-value and changed-value RAM searches;
- read-only snapshots and candidate comparison;
- one-candidate-at-a-time reversible test writes;
- pointer, module-relative, or signature validation across relaunches;
- personal Atmosphere cheat files for the exact installed Build ID.

It does not support piracy, online or multiplayer cheating, DRM or anti-cheat
bypass, title/prod keys, copyrighted game distribution, or redistributable
trainers.

## Proposed first milestone

Use `Legend of Mana` Lucre as the first observable test value:

1. Confirm the exact game title.
2. Choose the emulator or physical Switch as the first research platform.
3. Record the active emulator version or Atmosphere/firmware versions.
4. Launch the legally owned game in an offline-safe state.
5. Record the visible Lucre amount.
6. Implement a read-only adapter for the selected platform.
7. Run an exact-value scan, change Lucre naturally in the game, and rescan.
8. Log candidates without writing to memory.

The first write-capable milestone will be separate and will require an explicit
apply action, original-value capture, guarded pause/resume, a second read, and a
restore path.

## Planned automation

The PC helper should eventually provide a consistent workflow for either
supported platform:

```text
identify target -> snapshot -> scan -> change game state -> rescan
                -> inspect one candidate -> guarded test -> restore
                -> relaunch validation -> generate reviewed cheat file
```

Automation defaults:

- read-only or dry-run;
- exact process/game identity checks;
- no bulk candidate writes;
- one experimental effect at a time;
- original bytes or values recorded before every write;
- automatic resume in failure paths;
- research-log output for every meaningful experiment;
- no promotion of one-session HEAP addresses as completed cheats.

Some in-game actions cannot be inferred safely. The helper may ask the user to
spend Lucre, take damage, heal, or change maps, then enter the new visible value
before it performs the next automated comparison.

## Repository layout

```text
AGENTS.md                         AI operating and safety instructions
README.md                         Project overview and starting point
USER_PROFILE.md                   Non-secret user/platform preferences
docs/sources.md                   Version-sensitive sources and check dates
games/legend-of-mana/game.md      Tentative first-game research card
tools/                            Future read-only and guarded-write helpers
```

Raw memory dumps, saves, keys, credentials, and private console data are ignored
or prohibited from Git.

## Working with the AI

Start by supplying the missing facts in `USER_PROFILE.md`. A minimal reply is:

```text
Game: Legend of Mana
Platform: emulator
Emulator and version: <name and version>
Visible Lucre: <current amount>
```

For physical hardware, replace the emulator line with the Atmosphere version,
system firmware version, and whether homebrew already launches.

The AI should then work through one observable checkpoint at a time, state the
expected result, log the evidence, and stop safely if the actual result differs.

## Sources

The conceptual curriculum begins at:

- https://cheatslips.com/wiki

Current release and compatibility decisions must be verified against primary
project documentation. The sources checked for this repository are recorded in
`docs/sources.md`.

## Git workflow

Local commits are intentionally frequent. Each commit should represent a small,
verified milestone and use a descriptive subject. Tests and `git diff --check`
must pass first. Pushing, publishing, or opening a pull request requires a
separate explicit request.
