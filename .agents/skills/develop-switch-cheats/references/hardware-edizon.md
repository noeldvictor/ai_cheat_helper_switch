# Physical Switch: Atmosphere and EdiZon-SE

Use this for a physical Switch already running Atmosphere and homebrew. Do not
turn it into a CFW exploitation, piracy, key-extraction, or dumping guide.

## Readiness

Record the exact system/Atmosphere version, EdiZon-SE or Breeze version, game
version, Title ID, Build ID, connection method, offline state, and backup status.
Verify current compatibility from primary sources; never assume a web TID/BID
matches the running copy.

- https://github.com/tomvita/EdiZon-SE/releases
- https://github.com/tomvita/SE-tools
- https://github.com/tomvita/PointerSearcher-SE
- https://github.com/Atmosphere-NX/Atmosphere

## Known-value search

1. Record the visible value and state.
2. Try one plausible type: often `u16` or `u32` for small positive counters;
   use `f32` only when behavior supports it.
3. Search HEAP first, or HEAP+MAIN when the location is genuinely unknown.
4. Change the value naturally and rescan for the exact new value.
5. Repeat until few candidates remain.
6. Bookmark candidates with type/state, inspect nearby memory, record the
   original, and test one modest reversible value.
7. Resume immediately and verify gameplay, not only the display.

Reset before changing targets. Button prompts vary by release; use the installed
build's prompts or request a screenshot rather than copying old controls.

## Unknown or hidden state

Capture State A, change only the target when practical, capture State B, then
apply changed/unchanged, increase/decrease, or State A/B filters. Alternate
controlled states until manageable. If a poke changes only UI, trace its
writer/reader instead of promoting it.

## Pointer search

A current-launch bookmark is not a finished cheat.

1. Find/bookmark the target in session 1.
2. Attach PointerSearcher-SE to `dmnt` using its documented connection.
3. Dump pointer-capable memory and record the target.
4. Fully relaunch the game and find the target again.
5. Take a second dump and narrow the first set.
6. Prefer shorter chains with small consistent offsets.
7. Import/reproduce a candidate in EdiZon-SE.
8. Validate in a third allocation and relevant state transition.
9. Document state-limited chains or reject them.

Only one remote client may attach at a time. Detach cleanly and never leave the
game frozen.

## Static and ASM paths

For MAIN-relative data, record the base relationship, offset, width, and expected
original. Recheck after relaunch. For ASM, disassemble the exact BID, record the
original ARM64 instruction and affected registers, explain the gameplay effect,
provide a verified OFF code, and test one instruction at a time.

## PC bridge with sys-botbase

Verified 2026-09-13 on Atmosphère 1.11 / firmware 22.1 with sys-botbase v2.5.

- The sysmodule opens a kernel debug session around every command. Only one
  debugger may hold the game, so any cheat file for the running Build ID, or
  any cheat overlay opened on the game, blocks the bridge with kernel `Busy`
  (0xF401) until the game is fully closed. Fix: close and relaunch, no
  overlay, then `switchlab diagnose`.
- Attaching does not pause the game. There is no pause command. The user
  stands still during snapshots; confirm the visible value before and after.
- `getHeapBase` may point at an unmapped kernel heap region. Use
  `switchlab regions` (pointer harvesting from the main module, two levels)
  to find the real data blocks, then snapshot with the hole-tolerant reader.
- Expect about 0.7 MB/s over hex on the upstream build, and about 5 MB/s on a
  build that sends binary. Prefer an on-device search over pulling memory to the
  PC at all.
- `peekMulti` aborts on the first unreadable address; use it only on known
  candidates.
- A poke prints nothing. Do not wait for a reply: the socket blocks until it
  times out, and the write has already landed with no cleanup armed.
- Search width and alignment decide what a scan can see. A 4-byte search steps
  4 bytes and misses a 2-byte field on a 2-byte boundary. Probe a value at every
  plausible width before committing, and treat a candidate set that collapses to
  zero as a wrong width rather than a moved address.
- Values that are small or common exceed any candidate cap, which silently
  truncates the set. Measure the match count first and pick a rarer value, or
  reach the field from a structure whose address is already known.
- To test a finished cheat file, the file must be on the card at launch, which
  attaches the cheat manager. Research and cheat testing therefore happen in
  separate launches of the game.
