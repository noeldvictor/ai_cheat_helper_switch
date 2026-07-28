# User Profile

Last updated: 2026-07-28

## Confirmed boundaries

- The user legally owns the target game.
- All research and cheat use will remain offline and single-player.
- No online, multiplayer, anti-cheat bypass, DRM bypass, piracy, or
  redistribution is in scope.

## Available platforms

- Physical Nintendo Switch: available.
- Nintendo Switch emulator on Windows: available.
- Preferred platform for the first RAM-search session: unknown.
- Physical Switch Atmosphère version: unknown.
- Physical Switch homebrew status: unknown.
- Emulator name and version: unknown.

## Tools and connection

- Installed memory-search tools and versions: unknown.
- The user is willing to install the appropriate tools.
- Physical Switch connection method: unknown.
- Do not select or install a tool until its current compatibility has been
  checked against the user's Atmosphère, firmware, or emulator version.

## First game

- User-entered name: `Legend of Manga`.
- Likely intended name: `Legend of Mana` for Nintendo Switch.
- Exact title confirmation: pending.
- Game version: unknown.
- Title ID: unknown.
- Build ID: unknown.

Do not copy a Title ID or Build ID from a website and assume it matches the
installed game. Read both from the user's running copy or installed tool.

## Desired results

The user wants a broad set of useful offline single-player effects ("all the
good stuff"). Work on one falsifiable target at a time. Proposed order:

1. Lucre/money, because it is a visible numeric value suitable for validating
   the automated scanner.
2. A visible consumable or material quantity.
3. Player current/max HP.
4. Experience or level progression.
5. Battle gauges or cooldowns.
6. Damage, one-hit-kill, movement, or other code-driven effects only after the
   read/search/write pipeline is proven safe.

This order is provisional. The first exact target and its visible starting value
still require user confirmation.

## Assistance preference

- Preferred style: maximum practical automation.
- Build PC helper scripts for repeated RAM reads, exact-value scans,
  changed/unchanged snapshot comparisons, candidate narrowing, experiment
  logging, and reversible validation.
- Default every helper to read-only or dry-run mode.
- A memory write must require an explicit apply action, record the original
  value/bytes, touch only one confirmed candidate, resume in a `finally` path,
  verify with a second read, and offer immediate restoration.
- Do not bulk-write all candidates or automatically test several cheats.
- The user may still need to perform natural in-game actions such as spending
  Lucre, taking damage, healing, or changing maps. Ask for the resulting visible
  value before continuing the automated rescan.

## Information needed next

1. Confirm whether the game is **Legend of Mana**.
2. Choose the first platform:
   - emulator for easier PC-side automation; or
   - physical Switch for direct hardware discovery.
3. If emulator: provide its name/version and confirm the game already launches.
4. If physical Switch: provide the Atmosphère version, system firmware version,
   and whether homebrew already launches.
5. Open the game offline and provide the current visible Lucre value, or name a
   different first target and its visible value.
