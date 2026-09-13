import pytest

from switchlab import scan as scanmod
from switchlab.scan import ScanSession, read_values, refine, start_exact


class FakeLab:
    """Minimal client: memory dict, on-device search, peek_multi semantics."""

    def __init__(self, mem):
        self.mem = dict(mem)  # addr -> int (u32)

    def search(self, width, value, regions):
        return sorted(a for a, v in self.mem.items() if v == value), False, False

    def peek_multi(self, pairs):
        out = b""
        for a, n in pairs:
            if a not in self.mem:
                return out
            out += self.mem[a].to_bytes(n, "little")
        return out

    def peek_absolute(self, a, n):
        from switchlab.bridge.sysbotbase import BridgeError

        if a not in self.mem:
            raise BridgeError("unmapped")
        return self.mem[a].to_bytes(n, "little")


@pytest.fixture(autouse=True)
def session_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(scanmod, "SESSION_DIR", tmp_path)
    yield tmp_path


def test_exact_then_narrow_by_value_and_relation():
    mem = {0x1000: 84, 0x2000: 84, 0x3000: 84, 0x4000: 7}
    client = FakeLab(mem)
    s = start_exact(client, [(0x1000, 0x4000)], 4, 84, "ap", "BID")
    assert s.candidates == [0x1000, 0x2000, 0x3000]

    client.mem[0x2000] = 80          # the real AP dropped
    client.mem[0x3000] = 90          # noise went up
    refine(client, s, "exact", 80)
    assert s.candidates == [0x2000]

    # relation ops use the last stored values
    s2 = start_exact(client, [(0, 1)], 4, 80, "ap2", "BID")
    client.mem[0x2000] = 75
    refine(client, s2, "decreased")
    assert s2.candidates == [0x2000]
    refine(client, s2, "unchanged")
    assert s2.candidates == [0x2000]
    assert [h["op"] for h in s2.history] == ["exact", "decreased", "unchanged"]


def test_read_values_drops_unreadable_and_falls_back():
    client = FakeLab({0x1000: 1, 0x3000: 3})
    vals = read_values(client, [0x1000, 0x2000, 0x3000], 4, batch=2)
    assert vals == {0x1000: 1, 0x3000: 3}


def test_session_roundtrip():
    s = ScanSession("hp", "BID", 2, [0x10, 0x20], {0x10: 5, 0x20: 6})
    s.note("exact", 5, 0)
    s.save()
    back = ScanSession.load("BID", "hp")
    assert back.candidates == [0x10, 0x20] and back.values == {0x10: 5, 0x20: 6} and back.width == 2


class WidthAwareLab:
    """Search results differ per width, like the real device."""

    def __init__(self, by_width, capped_widths=()):
        self.by_width = by_width          # {width: [addresses]}
        self.capped = set(capped_widths)
        self.mem = {}

    def search(self, width, value, regions):
        return list(self.by_width.get(width, [])), False, width in self.capped

    def peek_multi(self, pairs):
        return b""

    def peek_absolute(self, a, n):
        from switchlab.bridge.sysbotbase import BridgeError

        if a not in self.mem:
            raise BridgeError("unmapped")
        return self.mem[a].to_bytes(n, "little")


def test_probe_widths_reports_capped_and_usable():
    from switchlab.scan import probe_widths

    c = WidthAwareLab({4: [1, 2, 3], 2: list(range(10)), 1: []}, capped_widths=(1,))
    probes = {p.width: p for p in probe_widths(c, [(0, 16)], 90)}
    assert probes[4].usable and probes[4].hits == 3
    assert probes[2].usable and probes[2].hits == 10
    assert probes[1].capped and not probes[1].usable
    assert "CAPPED" in probes[1].describe()


def test_probe_skips_widths_too_small_for_the_value():
    from switchlab.scan import probe_widths

    c = WidthAwareLab({2: [1], 4: [1]})
    widths = [p.width for p in probe_widths(c, [(0, 16)], 300)]
    assert 1 not in widths  # 300 does not fit in one byte


def test_start_exact_all_widths_opens_one_session_per_usable_width():
    from switchlab.scan import ScanSession, start_exact_all_widths

    c = WidthAwareLab({4: [0x10], 2: [0x20, 0x22]}, capped_widths=())
    sessions = start_exact_all_widths(c, [(0, 16)], 90, "reserve", "BID")
    assert set(sessions) == {4, 2}
    assert ScanSession.load("BID", "reserve-u32").candidates == [0x10]
    assert ScanSession.load("BID", "reserve-u16").candidates == [0x20, 0x22]


def test_all_widths_raises_when_nothing_is_usable():
    from switchlab.scan import CandidateCollapse, start_exact_all_widths

    c = WidthAwareLab({4: [], 2: []})
    with pytest.raises(CandidateCollapse):
        start_exact_all_widths(c, [(0, 16)], 90, "nope", "BID")


def test_refine_to_zero_raises_and_leaves_the_session_intact():
    from switchlab.scan import CandidateCollapse, refine, start_exact

    client = FakeLab({0x1000: 150, 0x2000: 150})
    s = start_exact(client, [(0x1000, 0x2000)], 4, 150, "reserve", "BID")
    assert len(s.candidates) == 2
    client.mem = {0x1000: 7, 0x2000: 7}      # the real field was never here
    with pytest.raises(CandidateCollapse) as err:
        refine(client, s, "exact", 120)
    assert "width" in str(err.value)
    assert len(s.candidates) == 2            # session preserved, not destroyed


def test_refine_to_zero_is_allowed_when_asked_explicitly():
    from switchlab.scan import refine, start_exact

    client = FakeLab({0x1000: 150})
    s = start_exact(client, [(0x1000, 0x2000)], 4, 150, "r2", "BID")
    client.mem = {0x1000: 7}
    refine(client, s, "exact", 120, allow_empty=True)
    assert s.candidates == []
