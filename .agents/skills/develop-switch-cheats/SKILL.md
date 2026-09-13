---
name: develop-switch-cheats
description: Develop, automate, port, debug, and validate cheats for legally owned offline single-player Nintendo Switch games. Use for physical Switch workflows with Atmosphere, EdiZon-SE, Breeze, Noexs, and PointerSearcher-SE; Windows emulator workflows with Eden or Ryujinx host-process memory scans; TID/BID-specific Atmosphere cheat files; HEAP/MAIN searches; pointer chains; ASM patches; emulator-to-hardware porting; and reversible RAM experiments.
---

# Develop Switch Cheats

## Core contract

Work only with the user's legally owned offline single-player game. Do not help
obtain games, firmware, keys, or copyrighted dumps. Do not bypass DRM or
anti-cheat, enable online cheating, edit network outcomes, or build
redistributable trainers.

Keep every experiment reversible:

1. Identify the exact target game process, version, Title ID, and Build ID.
2. Record the visible state and original value or bytes.
3. Pause only for the shortest fragile read/write batch.
4. Test one candidate with the smallest plausible change.
5. Resume in a guaranteed cleanup path.
6. Verify visually and by a second read.
7. Restore failed or temporary tests.
8. Never finish with a game paused or a debugger attached.

## PC bridge track (this repository's default)

The physical Switch runs sys-botbase; the PC runs `tools/switchlab`. Read
`references/hardware-edizon.md` section "PC bridge with sys-botbase" before
touching memory. Order of operations: full game relaunch with no overlay,
`status`, `diagnose` (must report "can attach"), `regions`, screenshot to
read the visible value, snapshot, scan, candidate-only rescans.

## Route the session

Choose one track before suggesting tools or addresses:

- **Physical Switch with Atmosphere/EdiZon-SE or Breeze:** read
  [references/hardware-edizon.md](references/hardware-edizon.md) completely
  before device-specific actions.
- **Windows Eden or Ryujinx:** read
  [references/emulator-eden-ryujinx.md](references/emulator-eden-ryujinx.md)
  completely before process-memory or emulator-specific actions.
- **Generate, review, install, or port an Atmosphere cheat file:** also read
  [references/atmosphere-cheat-files.md](references/atmosphere-cheat-files.md)
  completely.

For emulator-to-hardware porting, read all three references. Never mix a Windows
host address, Switch guest address, MAIN-relative offset, and HEAP offset without
labeling which address space each value belongs to.

## Minimum intake

Record unknown rather than guessing:

- game name, region, version, Title ID, and Build ID;
- physical hardware or exact emulator name/version;
- exact desired effect;
- visible value/state and a safe natural way to change it;
- save-backup and offline status;
- installed research tools and versions;
- current evidence paths.

If the target is broad, begin with one visible numeric value such as money or an
item count. Prove the pipeline before HP, hidden flags, damage, speed, or ASM.

## Shared discovery loop

1. Capture the visible state and search hypothesis.
2. Choose one likely little-endian type at a time.
3. Search the smallest plausible guest region.
4. Change the value naturally in normal gameplay.
5. Rescan with exact, increased/decreased, changed/unchanged, or State A/B.
6. Bookmark a small candidate set and inspect neighboring fields.
7. Poke one candidate reversibly; a display-only change is not gameplay proof.
8. Classify it as static MAIN, dynamic HEAP, module-relative, pointer-resolved,
   or only a host-process address.
9. Verify a pointer, module offset, or instruction patch across a full relaunch
   and a relevant state transition.
10. Generate and test a Build-ID-specific Atmosphere cheat with expected
    originals and an OFF/restore strategy where applicable.

Do not promote a one-session address.

## Automation contract

Automate reads, region enumeration, snapshots, comparisons, candidate
narrowing, conversions, opcode linting, and research logging when supported.

Any write-capable helper must default read-only, require an explicit apply flag,
print the exact process/address space/address/type/original/new value, reject
ambiguous targets, touch one candidate, restore or give a restoration command,
resume in cleanup, and fail closed on unexpected originals or mapping changes.

The user still performs meaningful natural game-state changes. Do not automate
controller input merely to make a scan appear hands-free.

## Evidence and outputs

Maintain `game.md`, `research-log.md`, `evidence/`, and
`cheats/<BUILD_ID>.txt` under the game's repository folder. Never commit RAM
dumps, saves, game binaries, keys, credentials, console identifiers, or
emulator-private data.

## Escalation ladder

When a direct search fails: retry justified types/scaling, use state scans,
inspect nearby structs, find the writer/reader, trace the UI formatter, then use
static analysis for the exact build. Create a guarded instruction patch only
after recording original instructions. Stop and restore after crashes.
