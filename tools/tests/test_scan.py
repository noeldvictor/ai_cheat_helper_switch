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
