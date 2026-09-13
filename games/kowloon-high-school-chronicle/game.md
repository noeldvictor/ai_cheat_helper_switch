# Kowloon High-School Chronicle — Game Card

Status: active first game (user decision 2026-09-13)

## Baseline

- Legal ownership confirmed: yes
- Offline single-player use confirmed: yes
- Platform: physical first-generation Switch running Atmosphère 1.11,
  firmware 22.1
- Game version (display): 1.0.0, read from the running game 2026-09-13
- Title ID: 0100FF70134BA000 (read from the running game 2026-09-13)
- Build ID: 6547E06ECC5E8F4B (read from the running game 2026-09-13)
- Title version (numeric): 0
- Cheat file destination: `atmosphere/contents/0100FF70134BA000/cheats/6547E06ECC5E8F4B.txt`
- Save backup status: unknown
- Date last verified: 2026-09-13

## Tool state

- sys-botbase v2.5: installed, answers on port 6000
- EdiZon-SE, Breeze: installed, versions not reported
- Ultrahand / EdiZon overlay: installed for cheat toggling
- Connection method: local Wi-Fi from the Linux helper machine

## Desired effects

Broad goal: a flexible personal cheat set for offline play. Cheat kinds
wanted: set value, lock value, code patches, inventory edits.

Discovery queue (one experimental target at a time):

1. A visible integer that changes naturally (money or an item count)
2. HP
3. Other stats and progression values
4. Code-driven effects after the pipeline is proven

## First experiment

- Proposed target: to be chosen from what is visible on screen
- Visible starting value: unknown
- Proposed representation: exact little-endian integer search, one width at a
  time
- Region: HEAP first
- Search status: not started
- Writes performed: none
- Current game state: running (identity read 2026-09-13); nothing is paused

## Research log

See `research-log.md` once the first experiment starts.
