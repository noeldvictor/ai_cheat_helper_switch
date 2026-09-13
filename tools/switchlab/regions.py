"""Discover mapped memory regions without a `query memory` command.

sys-botbase only reports the main NSO base and the kernel heap region base.
Some games never map the kernel heap region at all (their data lives in
blocks mapped elsewhere in the 39-bit address space). This module finds those
blocks by harvesting pointer-looking values from the main module's data and
bss, probing where they lead, and measuring each mapped block's extent with
binary search. All reads are read-only.
"""

from __future__ import annotations

import struct
from collections import Counter
from dataclasses import dataclass
from typing import Callable, Iterable, List, Optional

PAGE = 0x1000
ADDRESS_SPACE_END = 1 << 39  # 39-bit user address space on the Switch


@dataclass(frozen=True)
class Region:
    start: int
    end: int
    kind: str = "data"
    mem_type: int = -1
    perm: int = 0

    @property
    def size(self) -> int:
        return self.end - self.start

    def contains(self, addr: int) -> bool:
        return self.start <= addr < self.end

    def describe(self) -> str:
        extra = ""
        if self.mem_type >= 0:
            from switchlab.bridge.sysbotbase import MEM_TYPE_NAMES

            p = ("r" if self.perm & 1 else "-") + ("w" if self.perm & 2 else "-") + ("x" if self.perm & 4 else "-")
            extra = f"  {MEM_TYPE_NAMES.get(self.mem_type, hex(self.mem_type)):>18} {p}"
        return f"{self.kind:5} 0x{self.start:X}-0x{self.end:X}  {self.size / 1024**2:8.1f} MiB{extra}"


def parse_mod0(head: bytes) -> dict:
    """Parse the NSO MOD0 header from the first bytes of the main module.

    Returns offsets relative to the main base: `mod0`, `dynamic`, `bss_start`,
    `bss_end` (the in-memory end of the module).
    """
    if len(head) < 0x28:
        raise ValueError("need at least 0x28 bytes of the main module")
    mod0 = int.from_bytes(head[4:8], "little")
    if head[mod0 : mod0 + 4] != b"MOD0":
        raise ValueError("MOD0 magic not found; is this the main NSO base?")
    dynamic, bss_start, bss_end = struct.unpack_from("<iii", head, mod0 + 4)
    return {
        "mod0": mod0,
        "dynamic": mod0 + dynamic,
        "bss_start": mod0 + bss_start,
        "bss_end": mod0 + bss_end,
    }


def pointer_pages(data: bytes, lo: int, hi: int, exclude: Iterable[Region] = ()) -> Counter:
    """Count 8-byte aligned little-endian values in [lo, hi) by page address."""
    excl = list(exclude)
    pages: Counter = Counter()
    for (v,) in struct.iter_unpack("<Q", data[: len(data) - len(data) % 8]):
        if lo <= v < hi and not any(r.contains(v) for r in excl):
            pages[v & ~(PAGE - 1)] += 1
    return pages


def find_extent(readable: Callable[[int], bool], addr: int, cap: int = 8 << 30) -> Region:
    """Given a readable page, return the contiguous readable block around it.

    `readable(page_address)` must answer whether a 16-byte read succeeds.
    Uses exponential then binary search in both directions.
    """
    page = addr & ~(PAGE - 1)
    if not readable(page):
        raise ValueError(f"0x{page:X} is not readable")

    # upward: find first unreadable page above
    step = PAGE
    hi_ok, hi_bad = page, None
    while step <= cap:
        cand = page + step
        if cand >= ADDRESS_SPACE_END or not readable(cand):
            hi_bad = min(cand, ADDRESS_SPACE_END)
            break
        hi_ok = cand
        step *= 2
    if hi_bad is None:
        hi_bad = page + cap
    while hi_bad - hi_ok > PAGE:
        mid = (hi_ok + hi_bad) // 2 & ~(PAGE - 1)
        if readable(mid):
            hi_ok = mid
        else:
            hi_bad = mid

    # downward: find first unreadable page below
    step = PAGE
    lo_ok, lo_bad = page, None
    while step <= cap:
        cand = page - step
        if cand < 0 or not readable(cand):
            lo_bad = max(cand, -PAGE)
            break
        lo_ok = cand
        step *= 2
    if lo_bad is None:
        lo_bad = page - cap
    while lo_ok - lo_bad > PAGE:
        mid = (lo_ok + lo_bad) // 2 & ~(PAGE - 1)
        if readable(mid):
            lo_ok = mid
        else:
            lo_bad = mid
    return Region(lo_ok, hi_bad)


def merge(regions: Iterable[Region]) -> List[Region]:
    out: List[Region] = []
    for r in sorted(regions, key=lambda r: r.start):
        if out and r.start <= out[-1].end and r.kind == out[-1].kind:
            last = out.pop()
            r = Region(last.start, max(last.end, r.end), r.kind)
        out.append(r)
    return out


def discover_regions(client, window: int = 32 << 20, bss_cap: int = 64 << 20, max_probes: int = 60, depth: int = 2, log=print) -> List[Region]:
    """Find the main module extent and the data blocks reachable by pointers.

    Level 1 harvests pointers from the main module's data and bss. Each further
    level harvests pointers from the data blocks found so far, which reaches
    heaps that the main module only references indirectly.
    """
    main = client.get_main_nso_base()
    if not main:
        raise ValueError("no game is running")
    mod = parse_mod0(client.peek_main(0, 0x40))
    bss_end = mod["bss_end"]
    main_region = Region(main, main + ((bss_end + PAGE - 1) & ~(PAGE - 1)), "main")
    log(f"main module: {main_region.describe()}  (bss 0x{mod['bss_start']:X}-0x{bss_end:X})")

    start = max(0, mod["bss_start"] - window)
    end = min(bss_end, mod["bss_start"] + bss_cap)
    log(f"reading main+0x{start:X}..0x{end:X} ({(end - start) / 1024**2:.1f} MiB) to harvest pointers")
    data = client.peek_main(start, end - start)
    heap = client.get_heap_base() or 0

    def readable(page: int) -> bool:
        try:
            client.peek_absolute(page, 16)
            return True
        except Exception:
            return False

    found: List[Region] = [main_region]
    sources = [data]
    for level in range(1, depth + 1):
        pages: Counter = Counter()
        for blob in sources:
            pages.update(pointer_pages(blob, 0x8000000, ADDRESS_SPACE_END, exclude=found))
        log(f"level {level}: {sum(pages.values())} pointer-like values into {len(pages)} pages outside known regions")
        new_regions: List[Region] = []
        probes = 0
        for page, count in pages.most_common():
            if probes >= max_probes:
                break
            if any(r.contains(page) for r in found):
                continue
            probes += 1
            if not readable(page):
                continue
            region = find_extent(readable, page)
            if region.start < main_region.end and region.end > main_region.start:
                kind = "code"
            elif heap and heap <= region.start < heap + (6 << 30):
                kind = "heap"
            else:
                kind = "data"
            region = Region(region.start, region.end, kind)
            found.append(region)
            new_regions.append(region)
            log(f"  found {region.describe()}  (via {count} pointers to 0x{page:X})")
        if not new_regions or level == depth:
            break
        sources = []
        for r in new_regions:
            if r.kind == "data" and r.size <= (64 << 20):
                log(f"  reading {r.describe().strip()} for level {level + 1}")
                from switchlab.snapshot import read_range  # local import avoids a cycle

                sources.extend(p.data for p in read_range(client.peek_absolute_partial, r.start, r.end))
    return merge(found)


def scan_regions(regions: Iterable[Region]) -> List[Region]:
    """Regions worth scanning for game values: data and heap blocks only."""
    return [r for r in regions if r.kind in ("data", "heap")]


# Memory types whose readable+writable pages can hold game state.
SCANNABLE_TYPES = {0x2, 0x4, 0x5, 0x9, 0xB, 0x15}


def regions_from_kernel(mem_regions, main_base: int = 0) -> List[Region]:
    """Turn svcQueryDebugProcessMemory output into Regions with a kind."""
    out: List[Region] = []
    for m in mem_regions:
        t = m.mem_type
        if t in (0x0, 0x10):
            continue
        if t in (0x3, 0x8, 0x14):
            kind = "code"
        elif t == 0x5:
            kind = "heap"
        elif t in (0x4, 0x9, 0x15):
            kind = "mdata"  # writable module data (.data/.bss)
        elif t == 0xB:
            kind = "data"
        elif t == 0x2:
            kind = "stack"
        else:
            kind = "other"
        out.append(Region(m.addr, m.addr + m.size, kind, t, m.perm))
    return out


def scan_regions_kernel(regions: Iterable[Region]) -> List[Region]:
    """Readable+writable regions of scannable types, largest data first."""
    picked = [r for r in regions if r.mem_type in SCANNABLE_TYPES and (r.perm & 3) == 3]
    order = {"mdata": 0, "heap": 1, "data": 2, "stack": 3}
    return sorted(picked, key=lambda r: (order.get(r.kind, 9), -r.size))


def discover_regions_auto(client, log=print) -> List[Region]:
    """Kernel listing on the lab build; pointer harvesting otherwise."""
    if client.is_lab():
        regs = regions_from_kernel(client.query_memory_all())
        log(f"kernel reports {len(regs)} mapped regions")
        return regs
    log("upstream sys-botbase: falling back to pointer harvesting (about 2 minutes)")
    return discover_regions(client, log=log)
