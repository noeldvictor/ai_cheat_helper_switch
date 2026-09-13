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

## Status

| Cheat | Stage | Address form | Next step |
|---|---|---|---|
| Max Money | not started | none | read the visible amount, then exact search |
| Max Attack | not started | none | wait for money to prove the pipeline |
| God Mode (HP lock) | not started | none | find current and max HP together |
| God Mode (damage patch) | not started | none | needs the HP address first |
| Walk/Run Speed x2 | not started | none | look for a float near the player struct |
| EXP x2 | not started | none | needs the EXP-add instruction |
| EXP x4 | not started | none | same patch site as x2 |
| EXP x8 | not started | none | same patch site as x2 |
| EXP x16 | not started | none | same patch site as x2 |
| EXP x100 | not started | none | same patch site, multiply instead of shift |
| Fast Forward | not started | none | confirm a speed or delta-time value exists |

## Max Money

- Stage: not started
- Visible value: unknown
- Data type: unknown, try u32 then u16
- Address this launch: none
- Stable form: none
- Original value: none
- Cheat code: none
- Survived relaunch: not tested
- Notes: first target, chosen because it proves the search pipeline end to end.
- Next step: user reaches a screen showing money, I read it from a screenshot
  and run an exact search.

## Max Attack

- Stage: not started
- Notes: may be derived from equipment rather than stored, in which case the
  stored value is overwritten on recalculation and needs a lock.
- Next step: after money is verified.

## God Mode (HP lock)

- Stage: not started
- Notes: current HP and maximum HP usually sit next to each other. Find both.
  Locking current HP to maximum is not true invulnerability, because the game
  still applies damage and the lock overwrites it a moment later.
- Next step: after money is verified. HP was visible as 100/100 in an earlier
  screenshot, so it is easy to observe.

## God Mode (damage patch)

- Stage: not started
- Notes: replace the instruction that subtracts damage from HP. Requires the HP
  address first, then finding the code that writes to it. Record the original
  instruction and provide an OFF code.
- Next step: after the HP lock works.

## Walk/Run Speed x2

- Stage: not started
- Notes: movement speed is usually a float, either stored near the player
  struct or as a constant in code. Try the stored value first. Doubling may
  break collision or animation, so test small increases first.
- Next step: after HP.

## EXP x2, x4, x8, x16

- Stage: not started
- Shared patch site: unknown
- Notes: these four are the same instruction patch with a different left shift,
  so finding the site once yields all four. The target is the amount added per
  kill, not a stored total, so a value write cannot do this.
- Next step: find the EXP total first, then find the code that writes to it.

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

## Open questions for this game

- Which engine is it? If it is Unity with IL2CPP, method names may be
  recoverable, which would make the EXP function findable by name instead of by
  search. Check by looking for `il2cpp` or `UnityEngine` strings in the main
  module once the game is running.
- Main module size is 66.7 MiB, which is large for static analysis without
  symbols.
