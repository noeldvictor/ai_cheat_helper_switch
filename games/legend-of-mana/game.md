# Legend of Mana — Game Card

Status: deferred; crashed at launch on 2026-09-13 with sys-botbase installed.
Cause unknown. Before retrying, capture the crash type (Atmosphère fatal
screen with error code, or the system's "software was closed" dialog) and
check whether a cheats folder exists for its Build ID on the card.

## Baseline

- Legal ownership confirmed: yes
- Offline single-player use confirmed: yes
- Platform: physical first-generation Switch running Atmosphère
- First research platform: physical Switch (sys-botbase bridge)
- Game version: unknown
- Title ID: unknown
- Build ID: unknown
- Save backup status: unknown
- Date last verified: 2026-09-13

## Tool state

- Atmosphère version: 1.11 (user-reported 2026-09-13)
- Switch system firmware version: 22.1 (user-reported 2026-09-13)
- Breeze: installed, version not reported
- EdiZon-SE: installed, version not reported
- Ultrahand / EdiZon overlay: installed for cheat toggling
- sys-botbase v2.5: installed and verified 2026-09-13 (answers on port 6000)
- Noexes / PointerSearcher-SE: not installed
- Connection method: local Wi-Fi

## Desired effects

Broad goal: a useful set of personal offline cheats.

Proposed discovery queue:

1. Lucre/money
2. Consumable or material quantity
3. Player HP
4. Experience/progression
5. Battle gauge/cooldown
6. Damage or one-hit-kill
7. Movement or speed-related effects

Only one target may be experimental at a time.

## First experiment

- Proposed target: Lucre
- Visible starting value: unknown
- Proposed representation: start with exact integer searches, testing likely
  widths one at a time
- Region: HEAP first
- Search status: not started
- Writes performed: none
- Current game state: unknown; do not assume a process is running or paused

## Required next evidence

- Game launched offline; Title ID, Build ID, and game version read from the
  running copy through the bridge.
- Visible Lucre value read from a screenshot and confirmed by the user.
