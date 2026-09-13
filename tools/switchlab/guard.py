"""Guarded single-address writes.

Policy, from AGENTS.md: a memory write must require an explicit apply action,
record the original value first, touch exactly one confirmed address, verify
with a second read, restore in a cleanup path, and fail closed when the
original is not what we expected.

Nothing here writes unless `apply=True` is passed. Without it the call reports
what it would do and returns.
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Optional

from switchlab.bridge.sysbotbase import BridgeError, SysBotBase

WIDTHS = (1, 2, 4, 8)


@dataclass(frozen=True)
class WriteResult:
    address: int
    width: int
    original: int
    intended: int
    readback: Optional[int]
    applied: bool
    restored: bool

    @property
    def ok(self) -> bool:
        return self.applied and self.readback == self.intended

    def describe(self) -> str:
        if not self.applied:
            return (f"dry run: 0x{self.address:X} holds {self.original}, would become "
                    f"{self.intended} ({self.width}-byte). Pass apply=True to write.")
        state = "ok" if self.ok else f"MISMATCH, read back {self.readback}"
        return (f"0x{self.address:X}: {self.original} -> {self.intended} ({self.width}-byte), "
                f"{state}; restored={self.restored}")


def _check(address: int, width: int, value: int) -> None:
    if width not in WIDTHS:
        raise BridgeError(f"width must be one of {WIDTHS}")
    if address <= 0:
        raise BridgeError("address must be positive")
    if not 0 <= value < (1 << (8 * width)):
        raise BridgeError(f"{value} does not fit in {width} bytes")


def read_int(client: SysBotBase, address: int, width: int) -> int:
    if width not in WIDTHS:
        raise BridgeError(f"width must be one of {WIDTHS}")
    return int.from_bytes(client.peek_absolute(address, width), "little")


def write_int(client: SysBotBase, address: int, width: int, value: int) -> None:
    """Raw write with no checks. Use guarded_write instead."""
    _check(address, width, value)
    client.poke_absolute(address, value.to_bytes(width, "little"))


def guarded_write(
    client: SysBotBase,
    address: int,
    width: int,
    value: int,
    expect_original: Optional[int] = None,
    apply: bool = False,
    restore: bool = True,
    hold: float = 0.0,
    log=print,
) -> WriteResult:
    """Write one value, verify it, and put the original back.

    `expect_original` fails the call before writing if the address does not
    already hold that value, which catches a moved or wrong address.
    `hold` keeps the new value in place for that many seconds before restoring,
    long enough to look at the screen.
    """
    _check(address, width, value)
    original = read_int(client, address, width)
    if expect_original is not None and original != expect_original:
        raise BridgeError(
            f"0x{address:X} holds {original}, expected {expect_original}; refusing to write"
        )
    if not apply:
        result = WriteResult(address, width, original, value, None, False, False)
        log(result.describe())
        return result

    log(f"writing {value} to 0x{address:X} ({width}-byte), original {original}")
    restored = False
    readback = None
    try:
        write_int(client, address, width, value)
        readback = read_int(client, address, width)
        if readback != value:
            log(f"read back {readback}, expected {value}")
        if hold > 0:
            time.sleep(hold)
    finally:
        if restore:
            try:
                write_int(client, address, width, original)
                now = read_int(client, address, width)
                restored = now == original
                if not restored:
                    log(f"RESTORE FAILED: 0x{address:X} holds {now}, wanted {original}")
            except BridgeError as exc:
                log(f"RESTORE FAILED: {exc}")
    result = WriteResult(address, width, original, value, readback, True, restored)
    log(result.describe())
    return result


@contextmanager
def held_value(client: SysBotBase, address: int, width: int, value: int,
               expect_original: Optional[int] = None, apply: bool = False, log=print):
    """Hold a value at one address for the duration of the block, then restore.

    Restoration runs even if the block raises.
    """
    _check(address, width, value)
    original = read_int(client, address, width)
    if expect_original is not None and original != expect_original:
        raise BridgeError(
            f"0x{address:X} holds {original}, expected {expect_original}; refusing to write"
        )
    if not apply:
        log(f"dry run: would hold {value} at 0x{address:X}, original {original}")
        yield WriteResult(address, width, original, value, None, False, False)
        return
    write_int(client, address, width, value)
    readback = read_int(client, address, width)
    log(f"holding {value} at 0x{address:X} (read back {readback}), original {original}")
    try:
        yield WriteResult(address, width, original, value, readback, True, False)
    finally:
        write_int(client, address, width, original)
        now = read_int(client, address, width)
        if now == original:
            log(f"restored 0x{address:X} to {original}")
        else:
            log(f"RESTORE FAILED: 0x{address:X} holds {now}, wanted {original}")
