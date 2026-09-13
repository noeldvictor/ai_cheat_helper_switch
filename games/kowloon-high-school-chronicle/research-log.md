# Research Log — Kowloon High-School Chronicle

## 2026-09-13 12:25 — bridge cannot attach to the game

```text
Date/time: 2026-09-13 12:25 local
Game version / TID / BID: 1.0.0 / 0100FF70134BA000 / 6547E06ECC5E8F4B
Tool and version: sys-botbase v2.5 over Wi-Fi; switchlab 0.1.0
Target effect: none yet (identity and read sanity check)
Visible state before: new-game difficulty selection screen
Search type / relation / region: none; sanity reads of main+0x0 and heap+0x0
Candidate address or expression: n/a
Data type: n/a
Original value or bytes: n/a
Experimental value or bytes: n/a
Was the game paused?: no
Visible result: getTitleID, getBuildID, getMainNsoBase succeed (they do not
  need a debug handle). getHeapBase returns 4 and every peek returns empty.
Second-read result: with printDebugResultCodes on:
  svcDebugActiveProcess: 62465 (0xF401, kernel Busy = already being debugged)
  svcGetInfo / svcReadDebugProcessMemory: 58369 (0xE401, InvalidHandle)
Restored?: nothing was written; debug-code printing turned back off
Survived state change?: n/a
Survived relaunch?: n/a
Verdict: inspect-nearby (environment), not a memory result. Another debugger
  holds the game process. Most likely Atmosphere's cheat manager because a
  cheat file exists for this Build ID, or EdiZon-SE / Breeze / a cheat
  overlay opened the game this session.
Evidence paths: local/screens/20260913-122511-kowloon-start.jpg (ignored)
Next experiment: confirm whether atmosphere/contents/0100FF70134BA000/cheats/
  exists on the card; if so move it aside, relaunch, run `switchlab diagnose`
  and expect "can attach".
```
