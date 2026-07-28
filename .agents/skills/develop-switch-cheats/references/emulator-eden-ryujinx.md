# Windows Emulators: Eden and Ryujinx

Use only with a legally owned game already running in the user's installed
emulator. Do not help obtain games, firmware, keys, updates, or unofficial
emulator downloads.

EdiZon-SE does not run inside Eden or Ryujinx. Use a guarded Windows host-process
scanner for discovery and the emulator's Atmosphere-compatible loader for final
cheat testing.

## Runtime identity

Record emulator/version/channel, executable path and PID, game/version, TID,
BID, relevant CPU/JIT backend, game state, and visible value. Confirm the image
path before reads; reject ambiguous processes.

## Host-process discovery

The Windows process contains mapped Switch guest memory. A Windows
`0x000001...` address is not an Atmosphere address.

1. Pause through the emulator, or suspend the exact PID only for short batches.
2. Enumerate committed readable regions; prefer writable non-executable regions
   for changing state.
3. Search little-endian representations of the visible value.
4. Resume, change naturally, pause, rescan, and resume in cleanup.
5. Record host address, allocation base, type, and original.
6. Test one candidate with guarded write and immediate restore.
7. Relaunch and determine whether the host address moved.
8. Map the result to guest HEAP/MAIN or an instruction offset before generating
   an Atmosphere code.

A host pointer may support a private diagnostic helper, but is not portable and
must be labeled host-only.

## Eden

Use Eden's per-game UI to obtain identity and import/open mods or cheats. Current
releases support importing mods/cheats, but UI and storage paths vary. Prefer UI
actions over guessing AppData paths.

- https://eden-emu.dev/
- https://git.eden-emu.dev/eden-emu/eden
- https://git.eden-emu.dev/eden-emu/eden/wiki

## Ryujinx-family builds

Current documentation describes Atmosphere-style cheats except pause/resume
opcodes. Use the per-game mod directory/manager, put each pack under a named
folder containing `cheats/<BUILD_ID>.txt`, then Manage Cheats and enable one
entry at a time.

- https://docs.ryujinx.app/guides/setup-guide/#managing-cheats

Verify the installed fork's UI. Never generate PauseProcess/ResumeProcess
opcodes for a Ryujinx target.

## Porting

Require the same TID and BID. Prefer verified MAIN/module-relative patches,
revalidate HEAP pointers per runtime, never port a Windows host address, account
for opcode limitations, label runtime variants, and test the final target after
relaunch/state change.
