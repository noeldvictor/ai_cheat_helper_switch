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

- sys-botbase-lab 2.5-lab2: uploaded to the card 2026-09-13 and verified by
  read-back; adds on-device search, kernel region listing, binary reads,
  pause/resume, and SD file transfer. Reboot verification pending.
- sys-botbase v2.5 (upstream): kept on the card as `exefs.nsp.orig` for
  recovery, and in the repository under `switch/sys-botbase-lab/backup/`
- ftpd v3.2.1: installed to `/switch/ftpd/ftpd.nro` 2026-09-13
- EdiZon-SE, Breeze: installed, versions not reported
- Ultrahand / EdiZon overlay: installed for cheat toggling
- Connection method: local Wi-Fi from the Linux helper machine

## Desired effects

Requested by the user on 2026-09-13. Work on one target at a time, in this
order. Value edits come first because they prove the search pipeline. Code
patches come last because they need the game's instructions disassembled for
this exact Build ID.

| # | Effect | Technique | Difficulty |
|---|---|---|---|
| 1 | Max money | write a value, then lock it | easy |
| 2 | Max attack | write a value | easy to medium |
| 3 | God mode | lock HP first, then patch the damage instruction | medium |
| 4 | Double walk and run speed | edit the speed value, likely a float | medium |
| 5 | EXP x2, x4, x8, x16 | patch the EXP-add instruction with a left shift | hard |
| 6 | EXP x100 | same patch site, using a multiply instruction | hard |
| 7 | Fast forward | unknown; see the note below | unknown |

Notes on the harder items:

- **God mode.** Locking current HP to its maximum is quick and usually enough.
  It is not true invulnerability, because the game still applies damage and the
  lock overwrites it a moment later. Effects that kill outright or bypass HP can
  still work. The stronger version replaces the instruction that subtracts
  damage, which requires finding that instruction first.
- **EXP multipliers.** These cannot be done by writing a value, because the
  target is the amount added per kill, not a stored total. The clean method is
  an instruction patch at the point where EXP is added. Powers of two are a
  single left shift, so x2 through x16 are one patch each with a different
  shift amount. x100 needs a multiply instruction and a spare register.
  A fallback exists using the Atmosphère cheat VM, which does support
  multiplication: store the previous total in a register, compute the change
  each frame, multiply it, and add the difference back. This is more fragile
  and is only worth trying if the patch site cannot be found.
- **Fast forward.** The Switch has no general speed control. This only works if
  the game keeps a delta-time value, a frame limit, or a speed multiplier that
  can be changed. Whether one exists here is unknown. Investigate it last,
  after the disassembly work for the EXP patch has already mapped the code.

Each finished cheat is written as a separate named entry in the cheat file, so
the EXP multipliers become five entries and only one is enabled at a time.

## First experiment

- Proposed target: money, the first item in the list above
- Visible starting value: unknown
- Proposed representation: exact little-endian integer search, one width at a
  time
- Region: HEAP first
- Search status: not started
- Writes performed: none
- Current game state: running (identity read 2026-09-13); nothing is paused

## Research log

See `research-log.md` once the first experiment starts.
