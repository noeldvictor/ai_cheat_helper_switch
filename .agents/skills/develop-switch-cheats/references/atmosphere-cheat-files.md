# Atmosphere Cheat Files

Use the current official specification as authority:

- https://github.com/Atmosphere-NX/Atmosphere/blob/master/docs/features/cheats.md

Do not infer an opcode when the specification can be checked.

## Identity and layout

Record game/version, 16-hex TID, 16-hex BID, and target runtime. The cheat
filename is `<BUILD_ID>.txt`.

Typical hardware path:
`atmosphere/contents/<TITLE_ID>/cheats/<BUILD_ID>.txt`

Emulators wrap the file in a per-game named mod/cheat folder. Follow the current
UI/docs. Never rename another BID's file and call it compatible.

## Generation

- Put each visible name in brackets.
- Emit uppercase eight-hex-character opcode words.
- Verify width, memory region, registers, offsets, and values.
- Log decimal/hex conversions.
- Validate expected originals before instruction patches.
- Provide OFF/restore entries only from verified originals.
- Avoid unsafe maxima and overflow.
- Keep master dependencies explicit.
- Avoid unsupported pause/resume opcodes on Ryujinx targets.
- Do not add prose comments unsupported by the manager.

Static writes, register/pointer operations, conditionals, keypress blocks,
arithmetic, loops, and control opcodes exist; look up exact current encoding.

## Validation

Lint tokens, balance blocks, initialize registers, recalculate pointer steps,
confirm the running BID, keep new entries disabled, back up existing files, test
one entry, and verify enable/effect/disable/restore/save reload/full relaunch.
Document runtime limitations. A discovery-session-only result is incomplete.
