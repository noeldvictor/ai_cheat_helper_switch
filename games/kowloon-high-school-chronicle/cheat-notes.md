# Cheat Notes — Kowloon High-School Chronicle

Current state of every cheat, updated in place. The chronological record of
what was tried and observed is in `research-log.md`, which is append-only.

Build ID: `6547E06ECC5E8F4B`. Game version 1.0.0. Every address here is valid
only for this build. A game update changes the Build ID and invalidates all of
it.

Stages: `not started`, `searching`, `candidates`, `confirmed`, `stable`,
`encoded`, `verified`, `blocked`, `rejected`. A cheat is only `verified` after
it passes the definition of done in `AGENTS.md`, which includes a full game
relaunch.

Known starting values, from screenshots taken 2026-09-13 on the first dungeon
floor: character Kuro, HP 100/100, AP 084, Lv 1, weapon magazine 30/30 with
0150 in reserve. Two other weapon slots show 1/1.

## How common each value is

Measured against the live game on 2026-09-13, over a 787 MiB scan set. This
decides which values can be searched directly. The candidate cap is 200000.

| Value | As u32 | As u16 |
|---|---|---|
| 100 (HP) | 3299 | 46540 |
| 150 (reserve ammo) | 8062 | 15194 |
| 30 (magazine) | 18776 | 128888 |
| 84 (AP) | capped | capped |
| 1 (level) | capped | capped |

HP, ammo and reserve are all searchable as u32. AP and level are too common to
search directly and need a different approach: find the player structure from a
known field, then read the neighbouring values.

## Status

| Cheat | Stage | Address form | Next step |
|---|---|---|---|
| Max Money | not started | none | read the visible amount, then exact search |
| Max HP | searching | none | session `hp`, 3282 candidates; narrow after damage |
| Full Heal | searching | none | same session as Max HP |
| Infinite HP | searching | none | same session as Max HP |
| Max Stats | not started | none | open the status screen and read each stat |
| God Mode (damage patch) | not started | none | needs the current-HP address first |
| Infinite Ammo (magazine) | searching | none | session `ammo-mag`, 18767 candidates; narrow after firing |
| Max Reserve Ammo | searching | none | session `ammo-reserve`, 8070 candidates |
| Walk/Run Speed x2 | not started | none | look for a float near the player structure |
| EXP x2, x4, x8, x16 | not started | none | needs the EXP-add instruction |
| EXP x100 | not started | none | same patch site, multiply instead of shift |
| Fast Forward | not started | none | confirm a speed or delta-time value exists |
| Infinite AP (candidate) | not started | none | find it from the player structure, not by search |

## Max Money

- Stage: not started
- Visible value: unknown
- Data type: unknown, try u32 then u16
- Address this launch: none
- Stable form: none
- Original value: none
- Cheat code: none
- Survived relaunch: not tested
- Notes: first target, because it proves the search pipeline end to end without
  risking anything. Write a large safe value, not the type maximum.
- Next step: user reaches a screen showing money, I read it from a screenshot
  and run an exact search.

## The HP family

These four are separate cheats that promise different things. Build them in the
order below, because each one produces the information the next one needs.

### Max HP

- Stage: not started
- Target: the maximum-HP field, currently 100
- Notes: raises the ceiling only. After the write the player is at 100/9999
  until healed. If the game derives maximum HP from level or equipment, the
  write gets replaced on the next recalculation and the source has to be
  targeted instead, or the value locked.
- Verification: open the status screen and confirm the new maximum, then heal
  and confirm current HP can actually reach it.
- Next step: search for 100 and expect two nearby addresses, current and
  maximum. Take damage to tell them apart: current changes, maximum does not.

### Full Heal

- Stage: not started
- Target: the current-HP field
- Notes: a single write setting current HP to maximum. Not a lock. This is the
  quickest test that the current-HP address is correct.
- Next step: after the current/maximum pair is identified.

### Infinite HP

- Stage: not started
- Target: the current-HP field, rewritten every frame
- Notes: the game still applies damage and the lock overwrites it a moment
  later, so the bar may visibly dip. This does not prevent death from anything
  that bypasses the HP value: instant-death effects, scripted deaths, falling,
  or a death check that runs between the game's write and ours.
- Verification: take a real hit from an enemy and confirm survival. A number
  that stays at 100 on screen is not proof on its own.
- Next step: after Full Heal confirms the address.

### God Mode (damage patch)

- Stage: not started
- Target: the instruction that subtracts damage from HP
- Notes: the bar never moves at all, because nothing ever writes a reduced
  value. Stronger than Infinite HP. Still does not cover damage on a different
  code path, or deaths that never touch HP. Record the original instruction and
  ship an OFF code with it.
- Next step: use the confirmed current-HP address as the watchpoint target to
  find the code that writes HP. This is the first cheat that needs disassembly.

## Max Stats

- Stage: not started
- Targets: attack, defence, and any other numeric stats on the status screen
- Notes: check three things for every stat.
  1. Overflow. A signed 16-bit field set to 65535 reads as -1 and makes the
     player weaker. Write 9999, not the type maximum.
  2. Recalculation. If the stat is derived from level or equipment, the write
     is replaced and the source must be targeted instead.
  3. Formula breakage. A very large attack value can overflow the damage
     calculation and heal the enemy instead of hurting it.
- Verification: hit an enemy and confirm the damage number rose.
- Next step: user opens the status screen so I can read every stat from a
  screenshot, then search them one at a time.

## Ammunition

The status display shows a loaded magazine and a reserve count per weapon.
At the time of the first search the active weapon read 30/30 with 0150 in
reserve, and two other slots read 1/1. Each weapon has its own pair of
counters, so a value lock covers one weapon only. Covering every weapon needs
a patch on the instruction that decrements the count, which is the same kind
of work as god mode.

### Infinite Ammo (magazine)

- Stage: searching
- Session: `ammo-mag`, u32, started from value 30, 18767 candidates
- Notes: locking the loaded count means the weapon never needs reloading. If
  the game reloads by moving rounds from reserve to magazine, locking the
  magazine alone may still drain the reserve, so check both after the lock.
- Verification: fire repeatedly and confirm the count does not fall and the
  weapon keeps firing. A frozen number with no shots coming out means the
  game tracks ammo somewhere else as well.
- Next step: user fires a few rounds, then narrow the session to the new count.

### Max Reserve Ammo

- Stage: searching
- Session: `ammo-reserve`, u32, started from value 150, 8070 candidates
- Notes: 150 is a more distinctive value than 30, so this session should narrow
  faster and may point at the weapon structure, which would give the magazine
  address as a nearby field.
- Next step: user fires and reloads so the reserve drops, then narrow.

## Walk/Run Speed x2

- Stage: not started
- Notes: movement speed is usually a float, either stored near the player
  structure or as a constant in code. Try the stored value first. Doubling can
  break collision or animation, so test smaller increases first.
- Next step: after the HP work.

## EXP x2, x4, x8, x16

- Stage: not started
- Shared patch site: unknown
- Notes: these four are the same instruction patch with a different left shift,
  so finding the site once yields all four. The target is the amount added per
  kill, not a stored total, so a value write cannot do this.
- Next step: find the EXP total first, then use a watchpoint to find the code
  that writes to it.

## EXP x100

- Stage: not started
- Notes: same patch site as above, but 100 is not a power of two, so it needs a
  multiply instruction and a spare register.
- Next step: after one of the shift versions works.

## Fast Forward

- Stage: not started
- Notes: the Switch has no general speed control. This only works if the game
  keeps a delta-time value, a frame limit, or a speed multiplier. Whether one
  exists here is unknown.
- Next step: last. By then the disassembly done for the EXP patch will have
  mapped enough of the code to judge whether a timing value exists.

## Infinite AP (candidate)

- Stage: not started
- Notes: not yet agreed with the user. The status bar shows `AP 084` beside HP,
  so AP is a spendable resource, but its purpose is unconfirmed. If it limits
  actions per turn or per floor, locking it uses the same technique as
  Infinite HP and costs almost nothing once HP is done.
- Next step: confirm what AP does, then ask whether to include it.

## Open questions for this game

- Which engine is it? If it is Unity with IL2CPP, method names may be
  recoverable, which would make the EXP function findable by name instead of by
  search. Check for `il2cpp` and `UnityEngine` strings in the main module once
  the game is running.
- Main module size is 66.7 MiB, which is large for static analysis without
  symbols.
