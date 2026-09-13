# sys-botbase-lab

A fork of [sys-botbase](https://github.com/olliz0r/sys-botbase) by olliz0r
(GPL-3.0, see `LICENSE`), vendored from upstream commit `ae13548`
(2026-06-02, "Missed a metadata check", the commit after tag v2.5).

It keeps the upstream program ID `430000000000000B` and every upstream
command, so it is a drop-in replacement for the installed `exefs.nsp`. It
adds research commands that move the expensive work onto the Switch:

| Command | Purpose |
|---|---|
| `queryMemoryAll` | list every mapped region (address, size, type, permissions) in one reply |
| `peekRaw <addr> <size>` | binary read: 8-byte little-endian length, then the bytes |
| `search <width> <value> <start> <size> [<start> <size> ...]` | on-device exact-value search; replies with matching addresses |
| `pause` / `resume` | hold the game frozen for an atomic snapshot; auto-resume on disconnect |
| `fsList <dir>` | lines `f|d<TAB>size<TAB>name`, then `END` (lab2) |
| `fsGet <path>` | binary: 8-byte length, then the file (lab2) |
| `fsPut <path> <size>` | replies `OK`, reads `size` raw bytes from the socket, replies `DONE <n>` (lab2) |
| `fsRename <a> <b>`, `fsDelete <p>`, `fsMkdir <d>` | reply `OK` or `ERR <errno>` (lab2) |
| `getVersion` | reports `2.5-lab<N>` |

The file commands make the PC able to push and pull SD-card files without an
FTP app. The user chose this knowing sys-botbase is an unauthenticated service
on the local network; keep the console on a trusted LAN.

Build (needs Docker; produces `sys-botbase/sys-botbase.nsp`):

```bash
docker run --rm -v "$PWD/switch/sys-botbase-lab/sys-botbase:/src" -w /src devkitpro/devkita64:latest make
```

Install: copy the resulting `sys-botbase.nsp` to the card as
`atmosphere/contents/430000000000000B/exefs.nsp` (back up the original
first) and reboot. Revert by restoring the original file.
