# Cheat files for Kowloon High-School Chronicle

Destination on the card: `sdmc:/atmosphere/contents/0100FF70134BA000/cheats/`

The file for the installed build will be `6547E06ECC5E8F4B.txt` (game version
1.0.0). It does not exist yet. When it does, copy it as-is and toggle the
entries in Ultrahand or EdiZon.

Planned entries, in the order they will be built. The state of each one is
tracked in `../cheat-notes.md`.

| Entry | Kind | What it promises | Status |
|---|---|---|---|
| Max Money | value write | money set high | not started |
| Max HP | value write | the HP ceiling is raised; current HP is unchanged until healed | not started |
| Full Heal | value write | current HP set to maximum once | not started |
| Infinite HP | value lock | current HP is restored every frame; damage still lands first | not started |
| Max Attack | value write | attack stat set high without overflowing the damage formula | not started |
| Max Defence | value write | defence stat set high | not started |
| God Mode | instruction patch | damage is never subtracted; the bar does not move | not started |
| Walk/Run Speed x2 | value or patch | movement doubled | not started |
| EXP x2 | instruction patch | EXP gained per kill doubled | not started |
| EXP x4 | instruction patch | EXP gained per kill quadrupled | not started |
| EXP x8 | instruction patch | EXP gained per kill multiplied by 8 | not started |
| EXP x16 | instruction patch | EXP gained per kill multiplied by 16 | not started |
| EXP x100 | instruction patch | EXP gained per kill multiplied by 100 | not started |
| Fast Forward | unknown | game runs faster, if a speed value exists | not started |

Rules for this file:

- The comment header states the game, version, Title ID, Build ID, and whether
  each entry is verified or experimental.
- Only one EXP multiplier may be enabled at a time.
- Infinite HP and God Mode overlap. Enable one or the other, not both.
- Enable experimental entries one at a time.
- An entry is marked verified only after it passes the definition of done in
  `AGENTS.md`, which includes surviving a full game relaunch.
