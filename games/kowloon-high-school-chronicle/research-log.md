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

## 2026-09-13 12:40 — clean relaunch fixes attach; regions discovered

```text
Date/time: 2026-09-13 12:40 to 12:55 local
Game version / TID / BID: 1.0.0 / 0100FF70134BA000 / 6547E06ECC5E8F4B
Tool and version: sys-botbase v2.5; switchlab 0.1.0 (status, diagnose, regions)
Target effect: none yet; environment and region discovery
Visible state before: title screen, then first dungeon: Kuro, HP 100/100,
  AP 084, Lv 1 (local/screens/20260913-124257-ok-check.jpg)
Search type / relation / region: none; reads only
Candidate address or expression: n/a
Data type: n/a
Original value or bytes: n/a
Experimental value or bytes: n/a
Was the game paused?: no (sys-botbase cannot pause; attach does not pause)
Visible result: after the user closed and relaunched the game without opening
  Ultrahand, diagnose reported "can attach". Main NSO base 0x229E804000
  (ASLR; changes per launch), main+0 reads a valid NSO header with MOD0 at +8.
  Kernel heap region 0x23A2800000 is unmapped at every probed offset.
  Throughput: 4 MiB in 6.1 s (about 0.7 MB/s).
  Region discovery (pointer harvesting, depth 2):
    code  0x229E800000-0x22A4465000   92.4 MiB (modules)
    main  0x229E804000-0x22A2AC2000   66.7 MiB (bss 0x3F48480-0x42BDD50)
    data  0x4980000000-0x4985740000   87.2 MiB
    data  0x4A11840000-0x4A36E54000  598.1 MiB (main heap)
    data  0x4A38CFD000-0x4A3997C000   12.5 MiB
  Scan set 697.8 MiB in 3 data blocks. Regions contain holes (an 18 MiB
  block failed at 11.4 MiB), handled by the snapshot reader.
Second-read result: n/a
Restored?: nothing written
Survived state change?: n/a (addresses are per-launch)
Survived relaunch?: n/a
Verdict: environment ready; proceed to first exact-value scan
Evidence paths: local/screens/20260913-124019-after-relaunch.jpg,
  local/screens/20260913-124257-ok-check.jpg (ignored)
Next experiment: full snapshot of the 3 data blocks with the user standing
  still, then exact scan for AP = 84 as u32 (then u16), then have the user
  spend AP and rescan candidates only.
```

## 2026-09-13 14:46 — lab build verified; first searches run

```text
Date/time: 2026-09-13 14:20 to 14:50 local
Game version / TID / BID: 1.0.0 / 0100FF70134BA000 / 6547E06ECC5E8F4B
Tool and version: sys-botbase-lab 2.5-lab2; switchlab 0.1.0
Target effect: measure the new bridge, then start real searches
Visible state before: first dungeon floor, Kuro, HP 100/100, AP 084, Lv 1,
  weapon magazine 30/30 with 0150 in reserve
  (local/screens/20260913-144626-ammo-check.jpg)
Search type / relation / region: exact u32 and u16 over the kernel-reported
  scan set, 787 MiB in 124 readable and writable blocks
Candidate address or expression: none confirmed yet
Data type: u32 for all three sessions
Original value or bytes: none written
Experimental value or bytes: none written
Was the game paused?: no
Visible result: bridge measurements, all large improvements over the upstream
  build. Region listing 166 regions in 0.06 s, against about 110 s by pointer
  harvesting. Binary read 5.06 MB/s, against 0.7 MB/s over hex, so a full
  583 MiB snapshot drops from about 14 minutes to about 2.
  Value frequency over the scan set, candidate cap 200000:
    100 (HP)            u32 3299     u16 46540
    150 (reserve ammo)  u32 8062     u16 15194
    30  (magazine)      u32 18776    u16 128888
    84  (AP)            capped       capped
    1   (level)         capped       capped
  Sessions created: hp 3282 candidates, ammo-reserve 8070, ammo-mag 18767.
Second-read result: not applicable
Restored?: nothing was written
Survived state change?: not yet tested
Survived relaunch?: not yet tested
Verdict: rescan. AP and level cannot be searched directly and must be reached
  through a structure whose address is already known.
Evidence paths: local/screens/20260913-144626-ammo-check.jpg (ignored),
  local/sessions/6547E06ECC5E8F4B-*.json (ignored)
Next experiment: user takes damage and fires rounds, then narrow each session
  by the new exact value.
```
