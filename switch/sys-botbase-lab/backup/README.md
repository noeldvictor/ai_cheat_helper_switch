# Backups of the sysmodule binary

Both files belong at `sdmc:/atmosphere/contents/430000000000000B/exefs.nsp`.
Rename on copy; only one can be installed at a time.

| File | What it is |
|---|---|
| `exefs.nsp.v2.5-original` | upstream sys-botbase v2.5 release binary (sys-botbase25.zip, GitHub release 2026-05-24), the known-good fallback |
| `exefs.nsp.lab1` | sys-botbase-lab 2.5-lab1 built 2026-09-13 from `../sys-botbase` |

Verify with `sha256sum -c SHA256SUMS.txt`. If the console fails to boot
after an install, restore `exefs.nsp.v2.5-original` as `exefs.nsp`.
