# Verified Sources

Verification date: 2026-07-28

These sources establish the current project/tool context. Recheck release pages
immediately before installing or updating software.

## Game

### Legend of Mana for Nintendo Switch

- Source: https://www.nintendo.com/us/store/products/legend-of-mana-switch/
- Publisher source: Nintendo product page.
- Verified facts: the title is `Legend of Mana`, it has a Nintendo Switch
  release, and the release date shown is 2021-06-24.
- Not established by this source: the user's installed game version, Title ID,
  or Build ID.

## Runtime and memory tools

### Atmosphère

- Source: https://github.com/Atmosphere-NX/Atmosphere
- Primary project repository.
- The official changelog begins with `1.11.2` when checked.
- Recheck the current release and compatibility notes before any installation.

### Atmosphere cheat specification

- Source: https://github.com/Atmosphere-NX/Atmosphere/blob/master/docs/features/cheats.md
- Primary definition of cheat-file behavior and opcode encoding.
- Recheck this specification before generating or reviewing opcodes.

### EdiZon-SE

- Source: https://github.com/tomvita/EdiZon-SE/releases
- Primary release page for the maintained EdiZon-SE fork used by the
  CheatSlips-style workflow.
- GitHub marked `3.8.37a` as latest when checked.
- Its release note says it recompiles 3.8.37 for Atmosphère 1.10.0+
  compatibility and bundles an updated Breeze beta.
- Do not use the alternate build unless its documented special case applies.

### SE tools overview

- Source: https://github.com/tomvita/SE-tools
- Primary author overview for EdiZon-SE, PointerSearcher-SE, and Noexes.
- It documents the progression from value search, to bookmark, to pointer
  search, to cheat-code generation.
- Its quick-start examples are conceptual references; verify button prompts and
  tool compatibility against the actual installed versions.

### Eden

- Sources: https://eden-emu.dev/ and
  https://git.eden-emu.dev/eden-emu/eden
- Primary project pages for current releases and documentation.
- Current releases expose mod/cheat importing, but verify the installed
  version's UI and per-game path before giving instructions.

### Ryujinx-family documentation

- Source: https://docs.ryujinx.app/guides/setup-guide/#managing-cheats
- Current documentation describes per-game Atmosphere-style cheat management.
- It explicitly excludes Atmosphere pause/resume cheat opcodes, so generated
  codes targeting this runtime must avoid them.

## Curriculum

### CheatSlips Switch cheat learning guide

- Source: https://cheatslips.com/wiki
- Use for the learning sequence: memory concepts, software, searching, pointer
  discovery, Atmosphère code types, and code-file construction.
- Several pages contain 2021-2022-era versions and instructions. Treat those as
  historical examples and verify current operational details with the primary
  repositories above.

## Added 2026-09-13

### Dragon Quest Heroes: Torneko's Mystery Dungeon -Classic HD-

- Sources: https://www.nintendo.com/en-gb/Games/Nintendo-Switch-download-software/Dragon-Quest-Heroes-Torneko-s-Mystery-Dungeon-Classic-HD-3184730.html
  and https://www.rpgsite.net/news/21336-dragon-quest-heroes-tornekos-mystery-dungeon-classic-hd-shadow-drops-on-switch-1-2-ps5-xbox-pc-stea
- Verified facts: released 2026-09-09 by Square Enix on Nintendo Switch,
  Nintendo Switch 2, PS5, Xbox Series, and Steam. HD remaster of the 1993
  Super Famicom game. The user owns the Switch (1) version.
- Not established: installed game version, Title ID, Build ID.

### sys-botbase

- Sources: https://github.com/olliz0r/sys-botbase and
  https://github.com/olliz0r/sys-botbase/blob/master/commands.md
- Verified 2026-09-13 from source: latest release `v2.5` published
  2026-05-24; TCP server on port 6000 (`util.c`); plain-text commands
  (`peek`, `poke`, `peekMain`, `pokeMain`, `peekAbsolute`, `pointerPeek`,
  `freeze`, `getTitleID`, `getBuildID`, `getTitleVersion`, `getHeapBase`,
  `getMainNsoBase`, `pixelPeek`, controller input).
- Memory access is a kernel debug session (`svcDebugActiveProcess`,
  `svcReadDebugProcessMemory`, `svcWriteDebugProcessMemory`) opened and closed
  around each command (`commands.c`). It does not use `dmnt:cht`.
- Consequence: it cannot read the game while Atmosphère's cheat manager holds
  the debug session (see the Atmosphère entry below). No memory-region
  enumeration command exists.
- Release notes do not state Atmosphère or firmware requirements.
- Compatibility check for the user's firmware 22.1 / Atmosphère 1.11
  (2026-09-13): confirmed working on the user's console the same day
  (boots, answers `getVersion` = `2.5`). Maintainer had not stated it. Open issues #105, #106, #107
  ask for firmware 22 support with no maintainer reply; #105 was traced to
  an outdated Hekate/Nyx, not to sys-botbase. `v2.5` was built 2026-05-24,
  after firmware 22.0.0 shipped, and its ten commits since `v2.41` are
  error-handling fixes only. One unreleased commit (2026-06-02, "Missed a
  metadata check") sits on master. Program ID `430000000000000B`; ships a
  `toolbox.json` and needs a reboot. Install is reversible by deleting
  `atmosphere/contents/430000000000000B` from the card.

### Atmosphère cheat manager attach rules

- Source: https://github.com/Atmosphere-NX/Atmosphere/blob/master/docs/features/cheats.md
- Verified 2026-09-13: when an application launches, `dmnt` looks for a
  cheat file for the title and Build ID; if none is found the cheat manager
  stops. If cheats are found it opens a kernel debug session on the process.
  Homebrew can call `ForceOpenCheatProcess` to attach anyway (this is what
  EdiZon-SE, Breeze, and the cheat overlays do) and `ForceCloseCheatProcess`
  to release the process for another debugger.
- `atmosphere!dmnt_cheats_enabled_by_default` controls whether listed cheats
  start toggled on.

### Noexes (tomvita fork)

- Sources: https://github.com/tomvita/Noexes (fork of
  https://github.com/mdbell/Noexes)
- Verified 2026-09-13 from source: binary TCP protocol (`Commands.java`):
  status, poke8/16/32/64, read, write, continue, pause, attach, detach,
  query memory (region enumeration), query memory multi, current pid, get
  pids, get title id, read multi, set breakpoint; the fork adds freeze,
  on-device local search, fetch result, and detach dmnt. The fork's server
  uses `dmnt:cht` when the cheat manager is already attached instead of
  failing. Installed as sysmodule `054e4f4558454000`. Port is set in the
  server's `main.cpp`; confirm before implementing a client.
- Caveat from the fork README: launching an app that force-loads `dmnt:cht`
  while Noexes is attached can crash the console.
- Original repository is archived (July 2023); the Java client is
  `JNoexsClient.jar`.

### Breeze

- Source: https://github.com/tomvita/Breeze-Beta
- Checked 2026-09-13: on-console cheat tool built around Atmosphère's cheat
  VM; latest documented release Beta 113.00; outputs cheat files, bookmarks,
  dumps, ASM disassembly. No PC-client or network mode documented.

### Ultrahand Overlay

- Source: https://github.com/ppkantorski/Ultrahand-Overlay
- Checked 2026-09-13: Tesla-Menu replacement overlay, requires HOS 16.0.0+.
  The user uses it (or the EdiZon overlay) to toggle Atmosphère cheats. The
  helper's output is a standard `cheats/<BUILD_ID>.txt`, so this toggling
  workflow is unchanged.
