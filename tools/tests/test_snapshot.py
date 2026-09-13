from pathlib import Path

from switchlab.regions import PAGE
from switchlab.snapshot import Piece, Snapshot, read_range

SBB_CHUNK = 4 * PAGE  # pretend sys-botbase reads in 16 KiB internal chunks


def fake_memory(mapped_pages):
    """Return a read_partial(addr, size) with sys-botbase semantics:
    internal chunks of SBB_CHUNK bytes; a chunk that touches an unmapped page
    fails, and the bytes of earlier chunks are still returned."""

    def content(page):
        return bytes([(page >> 12) & 0xFF]) * PAGE

    def read_partial(addr, size):
        out = b""
        pos = addr
        end = addr + size
        while pos < end:
            chunk_end = min(pos + SBB_CHUNK, end)
            pages = range(pos & ~(PAGE - 1), chunk_end, PAGE)
            if any(p not in mapped_pages for p in pages):
                return out
            for p in pages:
                lo = max(pos, p) - p
                hi = min(chunk_end, p + PAGE) - p
                out += content(p)[lo:hi]
            pos = chunk_end
        return out

    return read_partial


def test_read_range_skips_holes_and_keeps_prefix():
    base = 0x4000000000
    mapped = set(base + i * PAGE for i in range(0, 40) if i not in (7, 8, 21))
    pieces = read_range(fake_memory(mapped), base, base + 40 * PAGE, chunk=8 * PAGE)
    spans = [((p.start - base) // PAGE, (p.end - base) // PAGE) for p in pieces]
    assert spans == [(0, 7), (9, 21), (22, 40)]
    assert all(len(p.data) == (p.end - p.start) for p in pieces)
    assert pieces[0].data[:PAGE] == bytes([0]) * PAGE


def test_snapshot_find_and_roundtrip(tmp_path: Path):
    snap = Snapshot("t", "20260913-000000", "ABCD", [Piece(0x1000, b"\x00" * 8 + (84).to_bytes(4, "little") + b"\x00" * 4)])
    assert snap.find((84).to_bytes(4, "little"), align=4) == [0x1008]
    assert snap.find((84).to_bytes(2, "little"), align=2) == [0x1008]
    assert snap.read(0x1008, 4) == (84).to_bytes(4, "little")
    assert snap.read(0x0FF0, 4) is None
    path = snap.save(tmp_path)
    back = Snapshot.load(path.with_suffix(".json"))
    assert back.pieces[0].start == 0x1000 and back.pieces[0].data == snap.pieces[0].data
