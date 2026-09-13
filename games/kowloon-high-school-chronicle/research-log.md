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

## 2026-09-13 15:05 — magazine counter confirmed by a reversible write

```text
Date/time: 2026-09-13 15:00 to 15:06 local
Game version / TID / BID: 1.0.0 / 0100FF70134BA000 / 6547E06ECC5E8F4B
Tool and version: sys-botbase-lab 2.5-lab2; switchlab 0.1.0
Target effect: infinite ammo, magazine counter
Visible state before: magazine 16/30 after firing, reserve 0150, HP 100/100
Search type / relation / region: session `ammo-mag`, exact u32, kernel scan set
Candidate address or expression: 0x5567E6C2E0
Data type: u32
Original value or bytes: 16
Experimental value or bytes: 25
Was the game paused?: no
Visible result: 18767 candidates for 30 narrowed to exactly 1 after firing
  brought the count to 16. The guarded write of 25 changed the on-screen
  display from 16/30 to 25/30.
Second-read result: read back 25 after the write, then 16 after the restore
Restored?: yes, verified by a second read
Survived state change?: not yet tested
Survived relaunch?: not tested; this is a heap address from one launch
Verdict: confirmed for this launch. Not promotable until a stable form exists.
Evidence paths: local/screens/20260913-150029-after-firing.jpg,
  local/screens/20260913-150559-after-poke-timeout.jpg (both ignored)
Next experiment: relaunch, find the magazine again, and pointer search across
  the two launches.

Tool defect found and fixed: sys-botbase prints nothing in reply to a poke.
The client waited for a line and timed out, which aborted the context manager
before its restore path was armed, leaving the experimental value in memory.
The write itself had already landed. Pokes are now sent without waiting for a
reply, and a regression test asserts that no read is attempted.
```

## 2026-09-13 15:58 — game crashed during reserve ammo write tests

```text
Date/time: 2026-09-13 15:58 local
Game version / TID / BID: 1.0.0 / 0100FF70134BA000 / 6547E06ECC5E8F4B
Tool and version: sys-botbase-lab 2.5-lab2; switchlab 0.1.0
Target effect: separate two reserve ammo candidates
Visible state before: magazine 30/30, reserve 0060, HP 100/100, Lv 1
Search type / relation / region: session `reserve-u16` narrowed 5 -> 2 after a
  third reload took the reserve from 90 to 60
Candidate address or expression: 0x555A6627CC and 0x555A6627D2, 6 bytes apart
Data type: u16
Original value or bytes: 60 at both
Experimental value or bytes: 77 at the first, 88 at the second, then 77 as
  u16, 77 as u32, 1 as u16 and 5 as u8 at the first
Was the game paused?: no
Visible result: none of the writes changed the reading, which came straight
  back as 60 every time. The control write of 21 to the confirmed magazine
  address held for over a second in the same session, so the write path was
  working. Memory near the candidate reads as a repeating table,
  30, 30, 60, 30, 30, 60, which looks like configuration data rather than live
  state. A read 0x100 further on then failed, and the user reported the
  console showing "Software was closed. An error occurred."
Second-read result: pmdmntGetApplicationProcessId 527 (no application
  process), svcDebugActiveProcess 0x40A01 InvalidProcessId,
  svcReadDebugProcessMemory 0xE401 InvalidHandle. The game process is gone.
  The sysmodule still answers and reports 2.5-lab2, so the console is healthy.
Restored?: every write was paired with a restore, and each restore read back
  the original. Nothing was written to the SD card and no cheat file exists.
Survived state change?: not applicable
Survived relaunch?: not applicable
Verdict: reject the approach, not the addresses. I used writes as a discovery
  method on two unconfirmed candidates, which AGENTS.md forbids: writes are
  only for a single confirmed candidate. I cannot rule out that those writes
  caused the crash, even though the values appeared not to take. The game is a
  port of a 2004 title and may also be unstable on its own, but that is not a
  defence for breaking the rule.
Evidence paths: local/screens/20260913-155807-after-reload-3.jpg,
  local/screens/20260913-155845-reserve-*.jpg (ignored)
Next experiment: relaunch the game. Every heap address found so far is dead,
  including the confirmed magazine address, so the searches start again. Narrow
  to exactly one candidate before writing anything.
```
