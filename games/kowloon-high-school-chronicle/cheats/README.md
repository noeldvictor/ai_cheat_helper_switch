# Cheat files for Kowloon High-School Chronicle

Destination on the card: `sdmc:/atmosphere/contents/0100FF70134BA000/cheats/`

The file for the installed build will be `6547E06ECC5E8F4B.txt` (game version
1.0.0). It does not exist yet. When it does, copy it as-is and toggle the
entries in Ultrahand or EdiZon.

Planned entries, in the order they will be built:

| Entry | Kind | Status |
|---|---|---|
| Max Money | value write | not started |
| Max Attack | value write | not started |
| God Mode (HP lock) | value lock | not started |
| God Mode (damage patch) | instruction patch | not started |
| Walk/Run Speed x2 | value or patch | not started |
| EXP x2 | instruction patch | not started |
| EXP x4 | instruction patch | not started |
| EXP x8 | instruction patch | not started |
| EXP x16 | instruction patch | not started |
| EXP x100 | instruction patch | not started |
| Fast Forward | unknown | not started |

Rules for this file:

- The comment header states the game, version, Title ID, Build ID, and whether
  each entry is verified or experimental.
- Only one EXP multiplier may be enabled at a time.
- Enable experimental entries one at a time.
- An entry is marked verified only after it passes the definition of done in
  `AGENTS.md`, which includes surviving a full game relaunch.
