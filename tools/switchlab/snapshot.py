"""Hole-tolerant memory snapshots for value scans (read-only).

Mapped memory has gaps, and sys-botbase stops a read at the first unreadable
page but still sends the bytes it read before that. `read_range` keeps that
prefix, splits the remainder down to page size, and skips unmapped pages, so
the result is a list of contiguous pieces covering every readable byte.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable, List, Optional

from switchlab.regions import PAGE, Region

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SNAPSHOT_DIR = REPO_ROOT / "local" / "snapshots"  # git-ignored on purpose


@dataclass
class Piece:
    start: int
    data: bytes

    @property
    def end(self) -> int:
        return self.start + len(self.data)


def _merge_pieces(pieces: Iterable[Piece]) -> List[Piece]:
    out: List[Piece] = []
    for p in sorted(pieces, key=lambda p: p.start):
        if not p.data:
            continue
        if out and out[-1].end == p.start:
            out[-1] = Piece(out[-1].start, out[-1].data + p.data)
        else:
            out.append(Piece(p.start, p.data))
    return out


def read_range(read_partial: Callable[[int, int], bytes], start: int, end: int, chunk: int = 1 << 20, log=None) -> List[Piece]:
    """Read [start, end) with `read_partial(addr, size)` semantics of sys-botbase.

    Returns contiguous readable pieces. Unreadable pages are skipped.
    """
    pieces: List[Piece] = []
    holes = 0

    def rec(addr: int, size: int) -> None:
        nonlocal holes
        data = read_partial(addr, size)
        if len(data) == size:
            pieces.append(Piece(addr, data))
            return
        if data:
            pieces.append(Piece(addr, data))
            addr += len(data)
            size -= len(data)
        if size <= PAGE:
            holes += 1
            return  # this page is unreadable
        half = ((size // 2) + PAGE - 1) & ~(PAGE - 1)
        rec(addr, half)
        rec(addr + half, size - half)

    addr = start
    while addr < end:
        n = min(chunk, end - addr)
        rec(addr, n)
        addr += n
        if log:
            done = addr - start
            log(f"  read 0x{start:X}: {done / 1024**2:6.1f} / {(end - start) / 1024**2:.1f} MiB, {holes} hole pages")
    return _merge_pieces(pieces)


@dataclass
class Snapshot:
    label: str
    taken_at: str
    build_id: str
    pieces: List[Piece]

    @property
    def total_bytes(self) -> int:
        return sum(len(p.data) for p in self.pieces)

    def read(self, address: int, size: int) -> Optional[bytes]:
        for p in self.pieces:
            if p.start <= address and address + size <= p.end:
                off = address - p.start
                return p.data[off : off + size]
        return None

    def find(self, needle: bytes, align: int = 1) -> List[int]:
        """Addresses where `needle` occurs (aligned to `align`)."""
        hits: List[int] = []
        for p in self.pieces:
            i = p.data.find(needle)
            while i != -1:
                addr = p.start + i
                if addr % align == 0:
                    hits.append(addr)
                i = p.data.find(needle, i + 1)
        return hits

    def save(self, out_dir: Path = DEFAULT_SNAPSHOT_DIR) -> Path:
        out_dir.mkdir(parents=True, exist_ok=True)
        stem = f"{self.taken_at}-{self.build_id}-{self.label}"
        bin_path = out_dir / f"{stem}.bin"
        index = []
        with bin_path.open("wb") as f:
            for p in self.pieces:
                index.append({"start": p.start, "length": len(p.data), "offset": f.tell()})
                f.write(p.data)
        (out_dir / f"{stem}.json").write_text(
            json.dumps({"label": self.label, "taken_at": self.taken_at, "build_id": self.build_id, "pieces": index}, indent=1)
        )
        return bin_path

    @classmethod
    def load(cls, json_path: Path) -> "Snapshot":
        meta = json.loads(json_path.read_text())
        raw = json_path.with_suffix(".bin").read_bytes()
        pieces = [Piece(e["start"], raw[e["offset"] : e["offset"] + e["length"]]) for e in meta["pieces"]]
        return cls(meta["label"], meta["taken_at"], meta["build_id"], pieces)


def take_snapshot(client, regions: Iterable[Region], build_id: str, label: str, chunk: int = 1 << 20, log=None) -> Snapshot:
    pieces: List[Piece] = []
    for r in regions:
        if log:
            log(f"snapshot {r.describe().strip()}")
        pieces.extend(read_range(client.peek_absolute_partial, r.start, r.end, chunk=chunk, log=log))
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return Snapshot(label=label, taken_at=stamp, build_id=build_id, pieces=_merge_pieces(pieces))
