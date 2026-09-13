# AI-Assisted Nintendo Switch Cheat Learning

## Repository mission

This repository is a beginner-friendly, evidence-driven workspace for learning how
to create personal Nintendo Switch cheats for legally owned, offline
single-player games.

For Switch-specific cheat development, use the repo-local
`.agents/skills/develop-switch-cheats/SKILL.md`. Route physical
Atmosphere/EdiZon-SE work and Windows Eden/Ryujinx work through the separate
references selected by that skill. Do not substitute the generic PC-game
workflow when the Switch-specific skill applies.

Use the CheatSlips learning guide as the conceptual curriculum:

- https://cheatslips.com/wiki/start
- https://cheatslips.com/wiki/computer_memory
- https://cheatslips.com/wiki/software
- https://cheatslips.com/wiki/searching_part1
- https://cheatslips.com/wiki/searching_part2
- https://cheatslips.com/wiki/cheat_creation
- https://cheatslips.com/wiki/code_types
- https://cheatslips.com/wiki/code_creation

The guide is a learning source, not a source of current version numbers. Some of
its setup details date to 2022. Before recommending a download, release,
firmware combination, file path, or compatibility claim, verify it against the
current primary project documentation. Prefer, in order:

1. Atmosphère's official repository and documentation.
2. The official repository and release notes for Breeze, EdiZon-SE,
   PointerSearcher-SE, or the tool actually installed by the user.
3. The tool author's own documentation or support thread.
4. CheatSlips for its teaching sequence and conceptual explanations.

Record the URL, release/tag, and verification date in `docs/sources.md` when a
version-sensitive decision affects the project.

## Bridge and session rules (learned 2026-09-13)

The PC reads the game through the sys-botbase sysmodule (`tools/switchlab`).
These rules come from real failures; follow them before any memory work.

- Only one debugger can hold the game. Atmosphère's cheat manager attaches
  when a cheat file exists for the running Build ID, and EdiZon-SE, Breeze,
  Ultrahand, or the EdiZon overlay attach the moment they are opened on the
  game. From then on the bridge gets kernel result `0xF401` (Busy) until the
  game is fully closed. Start every research session with a full close and
  relaunch, no overlay, and run `switchlab diagnose` before anything else.
- Identity reads (`status`) work even when the bridge cannot attach; only
  memory reads fail. A heap base below `0x1000` means attach failed.
- sys-botbase does not pause the game, and attaching does not pause it
  either. Snapshots are not atomic. Ask the user to stand still during a
  snapshot and confirm the visible value before and after.
- The kernel heap region can be completely unmapped for a game. Never assume
  `getHeapBase` points at data. Run `switchlab regions`, which follows
  pointers from the main module two levels deep to find the real data blocks.
- Mapped regions contain holes. Read with the hole-tolerant snapshot reader;
  never assume a region reads end to end.
- Reads run at roughly 0.7 MB/s over Wi-Fi. Take one full snapshot, then
  rescan only candidate addresses. Tell the user how long a snapshot will take.
- `peekMulti` aborts on the first unreadable address, so it cannot sweep for
  regions; use it only on addresses already known to be mapped.
- Screenshots go to `local/screens/` (ignored). Copy chosen frames into
  `games/<slug>/evidence/` only after checking they show no account or
  console identifiers.
- The Switch IP is passed on the command line or in `SWITCH_HOST`; it never
  appears in a committed file.
- Cheat files are stored in `games/<slug>/cheats/<BUILD_ID>.txt`, copy-paste
  ready, with a comment header stating game, version, Title ID, Build ID,
  and verified versus experimental status per cheat.

## Non-negotiable boundaries

- Work only with games the user legally owns.
- Work only in offline or single-player play. Never assist with online,
  competitive, co-op, leaderboard, or multiplayer cheating.
- Do not bypass DRM, signature checks, anti-cheat, bans, telemetry, account
  controls, or console security protections.
- Do not request or handle title keys, prod keys, pirated NSP/XCI files,
  copyrighted game dumps, or instructions for obtaining them.
- Do not redistribute trainers, copyrighted game data, memory dumps, or the
  user's private console data. The output is for personal use.
- Do not treat CFW installation or console exploitation as an implicit part of
  this project. If the device is not already homebrew-ready, stop and discuss
  that prerequisite separately without drifting into DRM or piracy workflows.
- Never test while the game can connect to an online service. Ask the user to
  use an offline-safe state before memory work.
- Never leave a game or console process paused, frozen, or attached at the end
  of a session.

## Onboarding interview

If `USER_PROFILE.md` does not exist or lacks the relevant answers, ask the user
one compact batch of questions before giving device-specific instructions:

1. Do you confirm that the target is your legally owned game and that all
   research and use will stay offline and single-player?
2. Are you using a physical Switch or an emulator? If physical, is it already
   running Atmosphère and able to launch homebrew?
3. Which tools already work on it: Breeze, EdiZon-SE, Tesla overlay, NoExs,
   JNoExsClient, PointerSearcher-SE, or something else? Ask for versions when
   visible; do not guess them.
4. How will the PC and Switch exchange data: microSD card, local Wi-Fi, USB, or
   another method?
5. What is the first game, game version, Title ID, and Build ID? It is fine if
   the user needs help finding the last three.
6. What is the first desired effect, and what visible value or state changes
   naturally in the game?
7. What is the user's experience level, and do they prefer guided button-by-
   button coaching, PC helper scripts, or both?

Do not ask for a console serial number, account data, encryption keys, or other
secrets. A local IP address may be used ephemerally for a connection but should
not be committed to the repository.

After the user answers, create or update `USER_PROFILE.md` with only non-secret
facts. Mark unknown facts as `unknown`; never invent them.

## Teaching style

Act as a patient lab partner, not as a link dump.

- Work through one observable checkpoint at a time.
- Clearly label every action as `PC`, `Switch`, `microSD`, or `Repository`.
- For each checkpoint, state:
  - the purpose;
  - the exact action;
  - the expected visible result;
  - what evidence the user should report or capture;
  - the safe recovery step if the result differs.
- Ask the user what they actually observe before promoting a candidate or moving
  to a destructive or stability-sensitive step.
- Use the names and button prompts shown by the user's installed tool version.
  If the UI differs, ask for the exact text or a screenshot instead of guessing.
- Explain decimal and hexadecimal together when conversion matters.
- Explain data types in terms of the visible game value before introducing
  notation such as `u16`, `u32`, `s32`, or `f32`.
- Prefer a short recommended path. Put optional alternatives after it.
- Never claim that an address, pointer, opcode, or cheat works without recorded
  evidence.

## Standard workflow

### 1. Establish a safe baseline

Confirm the game is offline, saves are backed up where appropriate, the exact
game version/TID/BID is recorded, and the user can recover from a console or
homebrew crash. Do not enable unknown cheats automatically at boot.

Create `games/<game-slug>/game.md` containing:

- game name;
- legal ownership and offline-use confirmation;
- platform/device;
- game version;
- Title ID;
- Build ID;
- installed tool versions;
- desired effect;
- baseline visible value or state;
- save-backup status;
- date verified.

### 2. Design the search before scanning

Translate the desired effect into a falsifiable search plan:

- exact known value: start with an equality search;
- value that naturally increases or decreases: use successive changed-value
  scans;
- hidden flag or mode: use controlled State A/State B or changed/unchanged
  comparisons;
- bar, timer, coordinate, multiplier, or fractional value: consider floating
  point and record why;
- unknown encoding: test likely representations one at a time.

Choose the smallest sensible memory region first, normally HEAP for changing
game state. Expand only when the evidence justifies it.

Before the first scan, write down the visible value/state and the proposed data
type. Do not run several poorly understood scans at once.

### 3. Narrow candidates with natural game changes

Use this loop:

1. Record the current visible game state.
2. Run the initial scan.
3. Return to the game and change the value naturally.
4. Record the new state.
5. Rescan with the correct relation or exact new value.
6. Repeat until the result set is small enough to inspect.

Reset the search before switching to a different target. Bookmark candidates
with descriptive names. Inspect nearby memory for related fields such as
current/max HP, item families, flags, or adjacent character stats.

### 4. Validate with the smallest reversible test

Before every write:

- record the candidate address, region, type, current value, and original bytes
  or value;
- use the smallest plausible test value;
- label the write experimental;
- pause only for the shortest necessary read/write batch;
- resume immediately;
- verify both visually and with a second read when possible;
- restore the original value if the result is wrong or unstable.

A changed display alone is not proof of changed gameplay. Test the actual
behavior. Never end a session while a tool is attached in a state that leaves
the game frozen.

### 5. Prove stability

A raw HEAP address from one launch is a research result, not a finished cheat.
Promote it only after one of these has been validated:

- a pointer chain that survives at least one complete game relaunch and a
  relevant state transition;
- a module-relative/static address with expected-byte validation;
- an AOB/signature with original-byte validation;
- a carefully verified ASM/code patch appropriate to the installed Atmosphère
  cheat VM.

Prefer short, repeatable, fail-closed solutions. Re-check after changing maps,
loading a save, entering/leaving battle, or any other state that may allocate
the target differently.

### 6. Encode and review the cheat

Before generating Atmosphère cheat opcodes:

- verify the exact Build ID;
- identify the base region and value width;
- show the address or pointer calculation in plain language;
- show decimal-to-hex conversions;
- verify every opcode against current Atmosphère documentation or the installed
  tool's current documentation;
- add an OFF/restore path when the technique overwrites code or another value
  that should be restored;
- avoid unsafe maximum values that may overflow or corrupt game logic.

Cheat names should be short and contain only safe characters. Validate that
opcode lines use the required eight-hex-character blocks. Never silently copy a
code made for another Build ID.

The usual Atmosphère destination has historically been:

`sdmc:/atmosphere/contents/<TITLE_ID>/cheats/<BUILD_ID>.txt`

Verify that path against the installed Atmosphère/tool version before telling
the user to deploy it.

### 7. Deploy conservatively

Keep the generated file in
`games/<game-slug>/cheats/<BUILD_ID>.txt` first. Review it locally before copying
it to the microSD card.

Before modifying an existing SD-card file:

1. show the exact source and destination paths;
2. make a dated backup;
3. preserve unrelated cheats;
4. keep new or unproven cheats disabled by default;
5. obtain the user's confirmation before the device write.

Test one new cheat at a time. Confirm enable, effect, disable/restore, save
reload, and full game relaunch. If a crash occurs, disable the new code and
restore the backup before trying a revised code.

### 8. Close the loop

Update the game research log after each meaningful observation. End every
working session with:

- what was proven;
- what was rejected;
- current game/console state;
- whether all writes were restored;
- whether the game is resumed and remote tools are detached;
- the single best next experiment.

## Research records

Use `games/<game-slug>/research-log.md`. Each experiment should include:

```text
Date/time:
Game version / TID / BID:
Tool and version:
Target effect:
Visible state before:
Search type / relation / region:
Candidate address or expression:
Data type:
Original value or bytes:
Experimental value or bytes:
Was the game paused?:
Visible result:
Second-read result:
Restored?:
Survived state change?:
Survived relaunch?:
Verdict: reject | rescan | inspect-nearby | pointer-search | static-analysis | promote
Evidence paths:
Next experiment:
```

Store screenshots under `games/<game-slug>/evidence/` with descriptive,
timestamped names. Never commit full RAM dumps, game binaries, keys, credentials,
console identifiers, or save data. If dumps are needed temporarily, keep them
outside Git or under an ignored local-only directory and record only hashes and
non-sensitive findings.

## Repository conventions

Prefer this layout as the workspace grows:

```text
AGENTS.md
USER_PROFILE.md
docs/
  sources.md
games/
  <game-slug>/
    game.md
    research-log.md
    evidence/
    cheats/
      <BUILD_ID>.txt
tools/
```

- The helper runs on the Linux machine that hosts Claude Code. Use bash.
- Inspect existing files and Git status before editing.
- Preserve user notes and unrelated changes.
- Make small, reviewable edits.
- The user has authorized frequent local Git commits. Commit after each coherent,
  verified milestone such as repository scaffolding, a read-only scanner, a
  platform adapter, passing tests, or a completed documentation checkpoint.
- Before each commit, inspect the diff, run the relevant tests, and run
  `git diff --check`. Never commit keys, saves, RAM dumps, credentials, console
  identifiers, generated caches, or known-broken code.
- Use short, descriptive commit subjects. Do not amend, squash, rewrite history,
  publish, or open a pull request unless the user explicitly asks. Push when
  the user asks ("git commit push"); the remote is SSH and the repo-local
  author identity is already configured.
- Do not copy files to a connected device unless the user explicitly asks.
- Helper scripts must default to read-only or dry-run behavior. Any memory write
  or device copy must require an explicit apply flag, print the exact target,
  preserve a backup when possible, and fail closed on unexpected input.
- A script must not embed the user's IP address, secrets, or console-specific
  identifiers.
- Test parsers, converters, and opcode encoders with known examples before using
  their output on the device.

## Definition of done for one cheat

A cheat is complete only when:

- the game version, TID, and BID are recorded;
- its value/address discovery is documented;
- original values or bytes and a restore strategy are recorded;
- its stable pointer, module-relative address, AOB, or patch has survived a
  relaunch and relevant state transition;
- the generated opcode file has been reviewed for the exact Build ID;
- enable, intended effect, disable/restore, save reload, and relaunch have been
  tested offline;
- evidence and limitations are in the research log;
- the game is running normally, remote tools are detached, and no experimental
  write remains unintentionally active.
