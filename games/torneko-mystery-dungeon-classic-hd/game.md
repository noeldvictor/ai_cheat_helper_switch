# Dragon Quest Heroes: Torneko's Mystery Dungeon -Classic HD- — Game Card

Status: confirmed first game (2026-09-13)

## Baseline

- Legal ownership confirmed: yes
- Offline single-player use confirmed: yes
- Platform: physical first-generation Switch running Atmosphère
- Edition: Nintendo Switch (1) version; Switch 2 / PS5 / Xbox / Steam
  editions are out of scope
- Release date: 2026-09-09 (Square Enix; HD remaster of the 1993 Super
  Famicom game by Chunsoft)
- Game version: unknown
- Title ID: unknown
- Build ID: unknown
- Save backup status: unknown
- Date last verified: 2026-09-13

## Tool state

- Atmosphère version: unknown
- Switch system firmware version: unknown
- EdiZon-SE version: installed, version not reported
- Breeze version: installed, version not reported
- Ultrahand / EdiZon overlay: installed for cheat toggling
- sys-botbase: not installed (proposed research bridge)
- FTP server: unknown
- Connection method: local Wi-Fi

## Desired effects

Broad goal: a flexible personal cheat set for offline play.

Candidate effects named by the user: health, gold, experience, and more.
Cheat kinds wanted: set value, lock value, code patches, inventory edits.

Proposed discovery queue (one experimental target at a time):

1. Gold (visible integer; changes when buying, selling, or picking up)
2. Current HP (max HP likely adjacent)
3. Fullness / hunger
4. Level and experience
5. Item counts and inventory layout
6. Code-driven effects (one-hit kill, speed) after the pipeline is proven

## First experiment

- Proposed target: Gold (pending user confirmation)
- Visible starting value: unknown
- Proposed representation: exact little-endian integer search, one width at a
  time (u32 first, then u16)
- Region: HEAP first
- Search status: not started
- Writes performed: none
- Current game state: unknown; do not assume a process is running or paused

## Required next evidence

- Atmosphère and firmware versions.
- Bridge installed and reachable from the PC.
- Game launched offline; Title ID, Build ID, and game version read from the
  running copy.
- Visible gold value at the start of the first scan.
