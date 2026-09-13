import struct

import pytest

from switchlab.regions import PAGE, Region, find_extent, merge, parse_mod0, pointer_pages


def make_head(bss_start=0x1000, bss_end=0x3000):
    mod0_off = 8
    head = bytearray(0x40)
    head[4:8] = mod0_off.to_bytes(4, "little")
    head[8:12] = b"MOD0"
    struct.pack_into("<iiiiii", head, 12, 0x100, bss_start - mod0_off, bss_end - mod0_off, 0, 0, 0)
    return bytes(head)


def test_parse_mod0():
    mod = parse_mod0(make_head(0x1000, 0x3000))
    assert mod["mod0"] == 8
    assert mod["bss_start"] == 0x1000
    assert mod["bss_end"] == 0x3000
    with pytest.raises(ValueError):
        parse_mod0(b"\x00" * 0x40)


def test_pointer_pages_filters_range_and_exclusions():
    values = [0x2300001234, 0x2300001FFF, 0x10, 0x229E804010, 0x7FFFFFFFFF]
    data = b"".join(v.to_bytes(8, "little") for v in values)
    pages = pointer_pages(data, 0x8000000, 1 << 39, exclude=[Region(0x229E804000, 0x229E900000, "main")])
    assert pages == {0x2300001000: 2, 0x7FFFFFF000: 1}


def test_find_extent_binary_search():
    mapped = Region(0x2000000000, 0x2000000000 + 37 * PAGE)
    probes = []

    def readable(page):
        probes.append(page)
        return mapped.contains(page)

    region = find_extent(readable, 0x2000000000 + 5 * PAGE)
    assert (region.start, region.end) == (mapped.start, mapped.end)
    assert len(probes) < 60


def test_merge_overlapping_same_kind():
    out = merge([Region(0, 10), Region(5, 20), Region(30, 40), Region(35, 50, "main")])
    assert [(r.start, r.end, r.kind) for r in out] == [(0, 20, "data"), (30, 40, "data"), (35, 50, "main")]


def test_scan_regions_excludes_code_and_main():
    from switchlab.regions import scan_regions

    regs = [Region(0, 10, "main"), Region(10, 20, "code"), Region(20, 30, "data"), Region(30, 40, "heap")]
    assert [(r.start, r.kind) for r in scan_regions(regs)] == [(20, "data"), (30, "heap")]


def test_regions_from_kernel_and_scan_set():
    from switchlab.bridge.sysbotbase import MemRegion
    from switchlab.regions import regions_from_kernel, scan_regions_kernel

    mem = [
        MemRegion((0x1000, 0x1000, 0x3, 5)),   # code r-x
        MemRegion((0x2000, 0x1000, 0x4, 3)),   # code mutable rw-
        MemRegion((0x3000, 0x4000, 0xB, 3)),   # mapped rw-
        MemRegion((0x7000, 0x1000, 0xB, 1)),   # mapped r-- (skip)
        MemRegion((0x8000, 0x1000, 0x10, 0)),  # reserved (drop)
        MemRegion((0x9000, 0x1000, 0x2, 3)),   # stack rw-
    ]
    regs = regions_from_kernel(mem)
    assert [r.kind for r in regs] == ["code", "mdata", "data", "data", "stack"]
    scan = scan_regions_kernel(regs)
    assert [(r.start, r.kind) for r in scan] == [(0x2000, "mdata"), (0x3000, "data"), (0x9000, "stack")]
