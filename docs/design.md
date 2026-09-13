# Helper Design

Status: proposal, 2026-09-13. Nothing here is implemented yet.

This answers "can we fork EdiZon or Breeze and run a Python web app that
Claude uses to make cheats?" Short answer: yes, and no fork is needed. The
Switch keeps running the tools it already has. The PC runs a small Python app.
Claude drives that app from this repository.

## The three pieces

```text
+-----------------------+   Wi-Fi    +------------------------------+
| Nintendo Switch       | <--------> | Linux PC (this machine)      |
|                       |            |                              |
| game (offline)        |  peek/poke | tools/ Python app            |
| research bridge       |  screenshot|   - bridge client            |
|   (sys-botbase or     |            |   - snapshot / scan / narrow |
|    Noexes, see below) |            |   - guarded test write       |
| EdiZon-SE, Breeze     |            |   - cheat-file generator     |
| Ultrahand / EdiZon    |  FTP       |   - FTP deploy with backup   |
|   overlay (toggle)    | <--------- |   - web dashboard + HTTP API |
| FTP server            |            |   - research log writer      |
+-----------------------+            +--------------+---------------+
                                                    | CLI / HTTP
                                             Claude Code (drives it)
                                                    | chat
                                                  the user
```

The finished product of every session is a normal Atmosphère cheat file:

`sdmc:/atmosphere/contents/<TITLE_ID>/cheats/<BUILD_ID>.txt`

Ultrahand and EdiZon toggle it exactly as they do today.

## What one session looks like

Example: the user says "I need infinite HP."

1. Claude asks the user to launch the game offline and reach a spot where HP
   is visible. Claude reads the Title ID, Build ID, and game version from the
   running game through the bridge and records them in the game card.
2. Claude takes a screenshot through the bridge, reads the HP number, and asks
   the user to confirm it. Without a screenshot bridge, the user types it.
3. Claude runs an exact-value scan over the game's heap. The web dashboard
   shows the candidate count.
4. Claude says: "Take some damage, then tell me when you are done." The user
   plays for a moment. Claude takes another screenshot, reads the new HP, and
   rescans. Repeat two or three times until a handful of candidates remain.
5. Claude inspects the bytes around the best candidate (max HP is usually next
   to current HP) and proposes one small reversible test, for example
   "write current HP = 5 at address X, original value 23".
6. After the user says go, the app records the original, writes the test
   value, reads it back, and reports. The user confirms the HP on screen
   changed and that taking damage behaves as expected. The app restores the
   original value.
7. The user relaunches the game. Claude finds HP again (fast now, because the
   value's neighbourhood is known) and confirms whether the address moved. If
   it moved, Claude runs a pointer search across the two launches to find a
   stable chain.
8. Claude generates the cheat file, lints every opcode against the
   Atmosphère cheat specification for this exact Build ID, backs up any
   existing file on the Switch, and uploads it over FTP after the user
   confirms.
9. The user enables "Infinite HP" in Ultrahand or EdiZon and tests. Claude
   writes the research log entry: what was proven, what was rejected, and
   whether every experimental write was restored.

The user never runs a scan by hand and never types an address. The user does
the in-game actions and confirms what they see.

## The one real constraint: only one debugger at a time

Reading a game's memory on the Switch means holding a kernel debug session
on the game process. Only one holder is allowed. Atmosphère's own cheat
manager (`dmnt`) takes it when a cheat file exists for the running title, and
EdiZon-SE, Breeze, Ultrahand, and the EdiZon overlay make it attach on demand.

So a session has two modes, and switching between them means relaunching the
game:

- Research mode: no cheat file for this Build ID on the card at launch, and no
  EdiZon-SE / Breeze / overlay opened on the game. The bridge can read and
  write freely.
- Test mode: the generated cheat file is on the card. `dmnt` owns the game.
  The bridge cannot read memory (it reports an error, not a crash). Cheats are
  toggled with Ultrahand or EdiZon as usual.

The Noexes fork sidesteps part of this by going through `dmnt:cht` when the
cheat manager is already attached. sys-botbase does not.

## Bridge options

| | sys-botbase | Noexes (tomvita fork) | No bridge: Breeze dumps |
|---|---|---|---|
| Install | one folder on the SD card, v2.5 (2026-05-24) | one sysmodule folder | nothing new |
| Protocol | plain text over TCP port 6000; Python client is trivial | binary over TCP; Python client written from the open-source Java client | files copied via FTP or card reader |
| Reads / writes | yes | yes | on console only |
| Screenshot for Claude to read | yes (`pixelPeek`) | no | no |
| List memory regions | no; the app must probe the heap in chunks | yes (`query memory`) | Breeze knows them |
| Full-heap scan speed | slow over Wi-Fi (hex text doubles the bytes); must be measured | faster (binary) but still Wi-Fi bound | fastest (on device) |
| Works while `dmnt` cheats are attached | no | yes | yes |
| Freeze a value during research | yes | yes (fork) | Breeze can |
| Extra | controller input, but the project rule is not to automate gameplay | breakpoints, on-device search (fork) | pointer search via PointerSearcher-SE |
| Risk | attach failures when a cheat file is present; needs a relaunch to switch modes | fork README warns of a crash if an app force-loads `dmnt:cht` while attached | slowest loop; more button-pressing for the user |

Recommendation: start with sys-botbase. It gives Claude screenshots and a
client that fits in one Python file, so the whole loop above works on day one.
Measure the full-heap scan time on the first session. If it is too slow, use
Breeze on the console for the very first scan (a few button presses guided by
Claude), and let the PC take over from the candidate list. Add a Noexes client
later if region listing and coexistence with `dmnt` become necessary. The
bridge is an adapter behind one interface, so this swap does not change the
rest of the app.

## Python app layout (planned)

```text
tools/
  switchlab/
    bridge/        base interface; sysbotbase.py; noexes.py (later)
    identity.py    TID, BID, version, heap base, main base
    snapshot.py    chunked heap reads to an ignored local dir; hashes only in Git
    scan.py        exact, changed, unchanged, increased, decreased; u8..u64, s32, f32
    candidates.py  bookmarks and session state (SQLite)
    guard.py       one-candidate guarded write: original, write, read back, restore
    pointer.py     multi-launch pointer chain search (or import from Breeze)
    cheatfile.py   Atmosphère opcode encoder and linter, Build ID checked
    deploy.py      FTP upload with dated backup; explicit apply flag
    screen.py      screenshot fetch for Claude to read
    log.py         research-log.md entries
    web/           dashboard (candidates, log, state) and HTTP API
    cli.py         every action also available from the command line
  tests/           encoder, parser, and scan tests with known examples
```

Safety defaults carried over from `AGENTS.md`: read-only unless `--apply`,
one candidate per write, originals recorded first, resume and restore in a
cleanup path, no freeze during research unless the user asks, no writes to
the SD card without confirmation, no keys, dumps, saves, or IP addresses in
Git.

## Lessons learned 2026-09-13 (first live session)

1. Attach exclusivity is real and easy to trip. One Ultrahand click on the
   game produced kernel `Busy` (0xF401) on every read until the game was
   fully closed. `switchlab diagnose` now decodes this. Identity commands
   still work in that state, which is misleading; the heap base reads as a
   junk value such as 4.
2. Attaching does not pause the game. Noexes implements pause as a separate
   `svcBreakDebugProcess`; sys-botbase never calls it. Snapshots are not
   atomic; the user stands still and the visible value is confirmed by
   screenshot before and after.
3. The kernel heap region was entirely unmapped for Kowloon. The data lives
   in blocks elsewhere in the 39-bit space. `switchlab regions` finds them by
   harvesting pointer-like values from the main module's data and bss,
   probing where they lead, and measuring extents by binary search. One level
   found 18 MiB; two levels found the 598 MiB main heap.
4. Regions have holes. A straight read of an 18 MiB block stopped at 11.4
   MiB. The snapshot reader keeps the good prefix, splits the rest down to
   page size, and skips unmapped pages.
5. Throughput is about 0.7 MB/s (4 MiB in 6.1 s). Kowloon's scan set is
   about 700 MiB, so a full snapshot takes roughly 17 minutes. The plan is one
   full snapshot, then candidate-only rescans, which take seconds.
6. `peekMulti` aborts on the first unreadable address, so it is useless for
   sweeping and only safe on known-mapped candidates.
7. No FTP server is present, so card writes need a card reader until ftpd is
   installed.
8. Legend of Mana crashed at launch with sys-botbase installed. Untested
   whether the two are related; capture the crash type before retrying.

## Milestones

1. Done 2026-09-13: bridge client, identity, screenshot, diagnose, region
   discovery, hole-tolerant snapshots. Read-only, tested live.
2. In progress: value scan + candidate narrowing with the live game (first
   target chosen from what is visible on screen; AP 84 in Kowloon).
3. Guarded single-candidate test write and restore.
4. Cheat-file generation, opcode lint, FTP deploy with backup.
5. Relaunch validation and pointer search.
6. Code patches: disassemble the exact Build ID, patch one instruction at a
   time with an OFF code.

## Open decisions

- Bridge choice: decided 2026-09-13, sys-botbase v2.5 installed and verified.
- Atmosphère 1.11 and firmware 22.1 reported; sys-botbase v2.5 boots and answers on them.
- Whether an FTP server is already on the Switch.
- First target: a visible integer in Kowloon High-School Chronicle (2026-09-13).
