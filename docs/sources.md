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
