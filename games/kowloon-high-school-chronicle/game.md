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
| 1 | Max money | write the value | easy |
| 2 | Max HP | write the maximum-HP field | easy |
| 3 | Infinite HP | lock current HP to its maximum each frame | easy |
| 4 | Max stats (attack, defence, others) | write each stat field | easy to medium |
| 5 | God mode | patch the instruction that subtracts damage | medium to hard |
| 6 | Infinite ammo (magazine) | lock the loaded round count | easy |
| 7 | Max reserve ammo | write the reserve count | easy |
| 8 | Double walk and run speed | edit the speed value, likely a float | medium |
| 9 | EXP x2, x4, x8, x16 | patch the EXP-add instruction with a left shift | hard |
| 10 | EXP x100 | same patch site, using a multiply instruction | hard |
| 11 | Fast forward | unknown; see the note below | unknown |

Candidate, not yet agreed: infinite AP. The status bar shows `AP 084` next to
HP, so AP is a spendable resource, but what it does is not yet confirmed. If it
limits actions, locking it is the same technique as infinite HP.

Notes on the harder items:

- **The HP family is four separate cheats**, and they promise different things.
  *Max HP* raises the ceiling only, so the player sits at 100/9999 until healed.
  *Full heal* sets current HP to maximum once, and is the quickest test that the
  current-HP address is right. *Infinite HP* rewrites current HP every frame;
  the game still applies damage first, so the bar may dip, and nothing protects
  against deaths that bypass HP. *God mode* patches the code so damage is never
  subtracted and the bar never moves. Build them in that order, because the HP
  lock is what lets us find the code that writes HP, which is what god mode
  needs. The starting values are known from a screenshot: HP 100/100 at level 1.
- **Max stats.** Check three things on every stat. Overflow: a signed 16-bit
  field set to 65535 reads as -1 and makes the player weaker, so write 9999 and
  not the type maximum. Recalculation: if the stat is derived from level or
  equipment, the write is replaced and the source has to be targeted instead.
  Formula breakage: a very large attack value can overflow the damage
  calculation and heal the enemy instead of hurting it.
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
