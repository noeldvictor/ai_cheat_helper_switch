import pytest

from switchlab.bridge.sysbotbase import BridgeError
from switchlab.guard import guarded_write, held_value, read_int, write_int


class FakeMem:
    """Client stub backed by a dict of address -> int."""

    def __init__(self, mem, fail_write_at=None):
        self.mem = dict(mem)
        self.fail_write_at = fail_write_at
        self.writes = []

    def peek_absolute(self, addr, width):
        if addr not in self.mem:
            raise BridgeError("unmapped")
        return self.mem[addr].to_bytes(width, "little")

    def poke_absolute(self, addr, data):
        value = int.from_bytes(data, "little")
        self.writes.append((addr, value))
        # simulate a write that does not stick
        self.mem[addr] = self.fail_write_at if self.fail_write_at is not None else value


def test_dry_run_never_writes():
    c = FakeMem({0x1000: 30})
    r = guarded_write(c, 0x1000, 4, 25, log=lambda *_: None)
    assert c.writes == [] and r.applied is False and r.original == 30
    assert "dry run" in r.describe()


def test_apply_writes_verifies_and_restores():
    c = FakeMem({0x1000: 30})
    r = guarded_write(c, 0x1000, 4, 25, expect_original=30, apply=True, log=lambda *_: None)
    assert r.ok and r.restored
    assert [v for _, v in c.writes] == [25, 30]
    assert c.mem[0x1000] == 30


def test_wrong_original_refuses_before_writing():
    c = FakeMem({0x1000: 42})
    with pytest.raises(BridgeError):
        guarded_write(c, 0x1000, 4, 25, expect_original=30, apply=True, log=lambda *_: None)
    assert c.writes == []


def test_value_too_wide_is_rejected():
    c = FakeMem({0x1000: 1})
    with pytest.raises(BridgeError):
        guarded_write(c, 0x1000, 2, 70000, apply=True, log=lambda *_: None)
    assert c.writes == []


def test_readback_mismatch_still_restores():
    c = FakeMem({0x1000: 30}, fail_write_at=7)
    r = guarded_write(c, 0x1000, 4, 25, apply=True, log=lambda *_: None)
    assert r.ok is False and r.readback == 7
    assert c.writes[-1] == (0x1000, 30)  # restore was attempted


def test_held_value_restores_even_on_exception():
    c = FakeMem({0x1000: 30})
    with pytest.raises(RuntimeError):
        with held_value(c, 0x1000, 4, 99, apply=True, log=lambda *_: None):
            raise RuntimeError("boom")
    assert c.mem[0x1000] == 30
    assert [v for _, v in c.writes] == [99, 30]


def test_read_and_write_int_roundtrip():
    c = FakeMem({0x2000: 0})
    write_int(c, 0x2000, 2, 513)
    assert read_int(c, 0x2000, 2) == 513
