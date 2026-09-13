"""Read-only client for the sys-botbase sysmodule (TCP port 6000).

Protocol facts verified against sys-botbase v2.5 source on 2026-09-13:

- Commands are plain text terminated by a newline.
- Memory reads (`peek*`) answer with uppercase hex, two characters per byte,
  followed by a single newline. A failed read answers with an empty line.
- `getTitleID`, `getTitleVersion`, `getMainNsoBase`, `getHeapBase` answer
  with 16 uppercase hex digits, or an empty line when no game is running.
- `getBuildID` answers with the first 8 bytes of the build id as 16 lowercase
  hex digits, or an empty line when no game is running.
- `pixelPeek` answers with a JPEG image encoded as hex, one line.

This module deliberately contains no `poke`, `freeze`, or input commands.
"""

from __future__ import annotations

import socket
from typing import Optional

DEFAULT_PORT = 6000
_MAX_LINE_HINT = 4 * 1024 * 1024


class BridgeError(RuntimeError):
    """Raised when the bridge cannot be reached or answers unexpectedly."""


# Horizon kernel result descriptions (module 1) that matter for attaching.
_KERNEL_DESCRIPTIONS = {
    114: "InvalidHandle",
    121: "NotFound",
    122: "Busy",
    125: "InvalidState",
    517: "InvalidProcessId",
}


def decode_result(rc: int) -> str:
    """Explain a Horizon result code as printed by sys-botbase (decimal)."""
    module = rc & 0x1FF
    description = rc >> 9
    if rc == 0:
        return "0 (success)"
    if module == 1:
        name = _KERNEL_DESCRIPTIONS.get(description, f"description {description}")
        return f"0x{rc:X} kernel {name}"
    return f"0x{rc:X} module {module} description {description}"


ALREADY_DEBUGGED = 0xF401  # kernel Busy from svcDebugActiveProcess

# Horizon memory types (low byte of MemoryInfo.type), from libnx.
MEM_TYPE_NAMES = {
    0x0: "unmapped", 0x1: "io", 0x2: "normal", 0x3: "code_static", 0x4: "code_mutable",
    0x5: "heap", 0x6: "shared", 0x7: "weird_mapped", 0x8: "module_code_static",
    0x9: "module_code_mutable", 0xA: "ipc_buffer0", 0xB: "mapped", 0xC: "thread_local",
    0xD: "transfer_isolated", 0xE: "transfer", 0xF: "process", 0x10: "reserved",
    0x11: "ipc_buffer1", 0x12: "ipc_buffer3", 0x13: "kernel_stack", 0x14: "code_ro",
    0x15: "code_rw", 0x16: "coverage", 0x17: "insecure",
}


class MemRegion(tuple):
    """(addr, size, mem_type, perm) as reported by svcQueryDebugProcessMemory."""

    __slots__ = ()

    @property
    def addr(self) -> int:
        return self[0]

    @property
    def size(self) -> int:
        return self[1]

    @property
    def mem_type(self) -> int:
        return self[2]

    @property
    def perm(self) -> int:
        return self[3]

    @property
    def readable(self) -> bool:
        return bool(self.perm & 1)

    @property
    def writable(self) -> bool:
        return bool(self.perm & 2)

    @property
    def type_name(self) -> str:
        return MEM_TYPE_NAMES.get(self.mem_type, f"type_{self.mem_type:X}")


def parse_memory_regions(line: str) -> list:
    toks = line.split()
    if len(toks) % 4:
        raise BridgeError("queryMemoryAll reply is not a multiple of four tokens")
    out = []
    for i in range(0, len(toks), 4):
        out.append(MemRegion((int(toks[i], 16), int(toks[i + 1], 16), int(toks[i + 2], 16), int(toks[i + 3], 16))))
    return out


def parse_search_reply(line: str) -> tuple:
    """Return (addresses, incomplete, capped) from a `search` reply line."""
    toks = line.split()
    incomplete = "!" in toks
    capped = "+" in toks
    addrs = [int(t, 16) for t in toks if t not in ("!", "+")]
    return addrs, incomplete, capped


def parse_hex_bytes(line: str) -> bytes:
    """Turn a sys-botbase hex line into bytes. Empty line means failed read."""
    text = line.strip()
    if not text:
        return b""
    if len(text) % 2:
        raise BridgeError(f"odd-length hex reply: {text[:32]!r}...")
    try:
        return bytes.fromhex(text)
    except ValueError as exc:
        raise BridgeError(f"non-hex reply: {text[:32]!r}...") from exc


def parse_u64(line: str) -> Optional[int]:
    """Parse a 16-hex-digit reply; None when the reply is empty (no game)."""
    text = line.strip()
    if not text:
        return None
    try:
        return int(text, 16)
    except ValueError as exc:
        raise BridgeError(f"expected hex number, got {text!r}") from exc


def normalize_build_id(line: str) -> Optional[str]:
    """Return the 16-character uppercase Build ID used for cheat file names."""
    text = line.strip()
    if not text:
        return None
    if len(text) != 16 or any(c not in "0123456789abcdefABCDEF" for c in text):
        raise BridgeError(f"unexpected build id reply: {text!r}")
    return text.upper()


class SysBotBase:
    """One TCP session to sys-botbase. Read-only by construction."""

    def __init__(self, host: str, port: int = DEFAULT_PORT, timeout: float = 5.0):
        if not host:
            raise BridgeError("a Switch host address is required")
        self.host = host
        self.port = port
        self.timeout = timeout
        self._sock: Optional[socket.socket] = None
        self._reader = None

    # -- session -----------------------------------------------------------
    def connect(self) -> "SysBotBase":
        try:
            self._sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
        except OSError as exc:
            raise BridgeError(f"cannot reach sys-botbase at {self.host}:{self.port}: {exc}") from exc
        self._reader = self._sock.makefile("rb")
        return self

    def close(self) -> None:
        if self._reader is not None:
            self._reader.close()
            self._reader = None
        if self._sock is not None:
            self._sock.close()
            self._sock = None

    def __enter__(self) -> "SysBotBase":
        return self.connect()

    def __exit__(self, *_exc) -> None:
        self.close()

    # -- transport ---------------------------------------------------------
    def command(self, cmd: str, timeout: Optional[float] = None) -> str:
        """Send one command and return its single reply line without newline."""
        if self._sock is None or self._reader is None:
            raise BridgeError("not connected")
        if "\n" in cmd or "\r" in cmd:
            raise BridgeError("command must be a single line")
        self._sock.settimeout(timeout if timeout is not None else self.timeout)
        try:
            self._sock.sendall((cmd + "\r\n").encode("ascii"))
            raw = self._reader.readline(_MAX_LINE_HINT)
            while raw and not raw.endswith(b"\n"):
                raw += self._reader.readline(_MAX_LINE_HINT)
        except socket.timeout as exc:
            raise BridgeError(f"timeout waiting for reply to {cmd.split()[0]!r}") from exc
        except OSError as exc:
            raise BridgeError(f"connection error during {cmd.split()[0]!r}: {exc}") from exc
        if not raw:
            raise BridgeError("connection closed by the Switch")
        return raw.decode("ascii", errors="replace").rstrip("\r\n")

    # sys-botbase commands that write but print nothing. Waiting for a reply
    # to one of these blocks until the socket times out.
    _SILENT = ("configure ", "pokeAbsolute ", "pokeMain ", "poke ", "pointerPoke ")

    def _send(self, cmd: str) -> None:
        """Send a command that produces no reply."""
        if self._sock is None:
            raise BridgeError("not connected")
        if not cmd.startswith(self._SILENT):
            raise BridgeError(f"_send is only for commands with no reply: {self._SILENT}")
        self._sock.settimeout(self.timeout)
        self._sock.sendall((cmd + "\r\n").encode("ascii"))

    def _command_lines(self, cmd: str, stop) -> list:
        """Send a command and collect reply lines until `stop(line)` is true."""
        if self._sock is None or self._reader is None:
            raise BridgeError("not connected")
        self._sock.settimeout(self.timeout)
        self._sock.sendall((cmd + "\r\n").encode("ascii"))
        lines = []
        try:
            while True:
                raw = self._reader.readline(_MAX_LINE_HINT)
                if not raw:
                    raise BridgeError("connection closed by the Switch")
                line = raw.decode("ascii", errors="replace").rstrip("\r\n")
                lines.append(line)
                if stop(line) or len(lines) > 16:
                    return lines
        except socket.timeout as exc:
            raise BridgeError(f"timeout waiting for reply to {cmd!r}") from exc

    # -- diagnostics -------------------------------------------------------
    def diagnose(self) -> dict:
        """Ask sys-botbase for its kernel result codes on one attach attempt.

        Temporarily enables the sysmodule's debug-code printing and always
        turns it back off. Returns a dict with `codes` ({svc: rc}), `attached`
        (bool), and a human `verdict`.
        """
        self._send("configure printDebugResultCodes 1")
        try:
            lines = self._command_lines(
                "getHeapBase", lambda ln: ln == "" or (len(ln) == 16 and all(c in "0123456789ABCDEF" for c in ln))
            )
        finally:
            self._send("configure printDebugResultCodes 0")
        codes = {}
        for ln in lines:
            if ":" in ln:
                name, _, num = ln.partition(":")
                try:
                    codes[name.strip()] = int(num.strip())
                except ValueError:
                    pass
        attach_rc = codes.get("svcDebugActiveProcess", 0)
        attached = attach_rc == 0
        if attached and codes.get("svcGetInfo", 0) == 0:
            verdict = "the bridge can attach to the game; memory reads should work"
        elif attach_rc == ALREADY_DEBUGGED:
            verdict = (
                "the game is already being debugged by something else (kernel Busy). "
                "Usual cause: Atmosphere's cheat manager attached at launch because a cheat file "
                "exists for this Build ID, or EdiZon-SE / Breeze / a cheat overlay opened the game. "
                "Move the title's cheats folder aside and relaunch the game, or close the other tool."
            )
        elif attach_rc:
            verdict = f"attach failed: svcDebugActiveProcess -> {decode_result(attach_rc)}"
        else:
            verdict = "attach succeeded but the handle was rejected: " + ", ".join(
                f"{k} -> {decode_result(v)}" for k, v in codes.items() if v
            )
        return {"codes": codes, "attached": attached and not any(codes.values()), "verdict": verdict, "lines": lines}

    # -- identity (all read-only) -----------------------------------------
    def get_version(self) -> str:
        return self.command("getVersion")

    def get_title_id(self) -> Optional[int]:
        return parse_u64(self.command("getTitleID"))

    def get_title_version(self) -> Optional[int]:
        return parse_u64(self.command("getTitleVersion"))

    def get_build_id(self) -> Optional[str]:
        return normalize_build_id(self.command("getBuildID"))

    def get_main_nso_base(self) -> Optional[int]:
        return parse_u64(self.command("getMainNsoBase"))

    def get_heap_base(self) -> Optional[int]:
        return parse_u64(self.command("getHeapBase"))

    def get_game_field(self, field: str) -> Optional[str]:
        """`game name|version|author|rating`; None when the Switch reports an error."""
        if field not in {"name", "version", "author", "rating", "icon"}:
            raise BridgeError(f"unknown game field {field!r}")
        reply = self.command(f"game {field}")
        if not reply or reply.startswith("nsGetApplicationControlData"):
            return None
        return reply

    # -- memory reads ------------------------------------------------------
    def _peek_partial(self, verb: str, address: int, size: int) -> bytes:
        """Read up to `size` bytes; a short result means the read hit an
        unreadable page (sys-botbase sends the good prefix, then stops)."""
        if size <= 0:
            raise BridgeError("size must be positive")
        if address < 0:
            raise BridgeError("address must be non-negative")
        # Roughly 2 hex chars per byte over Wi-Fi; allow generous time.
        timeout = max(self.timeout, 5.0 + size / 200_000)
        return parse_hex_bytes(self.command(f"{verb} 0x{address:X} {size}", timeout=timeout))

    def peek_absolute_partial(self, address: int, size: int) -> bytes:
        return self._peek_partial("peekAbsolute", address, size)

    def _peek(self, verb: str, address: int, size: int) -> bytes:
        data = self._peek_partial(verb, address, size)
        if len(data) != size:
            raise BridgeError(
                f"{verb} 0x{address:X} {size}: expected {size} bytes, got {len(data)} "
                "(empty means the read failed: unmapped page, or another debugger holds the game; "
                "run `switchlab diagnose`)"
            )
        return data

    def peek_absolute(self, address: int, size: int) -> bytes:
        return self._peek("peekAbsolute", address, size)

    def peek_main(self, offset: int, size: int) -> bytes:
        """Read relative to the main NSO base."""
        return self._peek("peekMain", offset, size)

    def peek_heap(self, offset: int, size: int) -> bytes:
        """Read relative to the heap base."""
        return self._peek("peek", offset, size)

    def peek_multi(self, pairs) -> bytes:
        """`peekAbsoluteMulti` on known-mapped (address, size) pairs. The
        sysmodule aborts on the first unreadable address, so a short reply
        means at least one pair failed; callers fall back to single reads."""
        args = " ".join(f"0x{a:X} {n}" for a, n in pairs)
        total = sum(n for _, n in pairs)
        return parse_hex_bytes(self.command(f"peekAbsoluteMulti {args}", timeout=max(self.timeout, 5.0 + total / 200_000)))

    # -- sys-botbase-lab commands (fork in switch/sys-botbase-lab) ----------
    def is_lab(self) -> bool:
        return "-lab" in self.get_version()

    def query_memory_all(self) -> list:
        """Every mapped region from the kernel. Requires the lab build."""
        line = self.command("queryMemoryAll", timeout=max(self.timeout, 30.0))
        if not line.strip():
            raise BridgeError("queryMemoryAll returned nothing (attach failed, or not the lab build)")
        return parse_memory_regions(line)

    def peek_raw(self, address: int, size: int) -> bytes:
        """Binary read (lab build). Returns exactly `size` bytes or raises."""
        if size <= 0 or size > (2 << 20):
            raise BridgeError("peekRaw size must be 1..2 MiB")
        if self._sock is None or self._reader is None:
            raise BridgeError("not connected")
        self._sock.settimeout(max(self.timeout, 5.0 + size / 500_000))
        try:
            self._sock.sendall(f"peekRaw 0x{address:X} {size}\r\n".encode("ascii"))
            header = self._reader.read(8)
            if len(header) != 8:
                raise BridgeError("peekRaw: short header (not the lab build?)")
            count = int.from_bytes(header, "little")
            if count == 0:
                raise BridgeError(f"peekRaw 0x{address:X} {size}: range not readable")
            data = self._reader.read(count)
        except socket.timeout as exc:
            raise BridgeError("timeout during peekRaw") from exc
        if len(data) != count or count != size:
            raise BridgeError(f"peekRaw: expected {size} bytes, got {len(data)}")
        return data

    def search(self, width: int, value: int, regions, max_cmd_len: int = 16000) -> tuple:
        """On-device exact search over (start, size) pairs. Returns
        (addresses, incomplete, capped). Splits into several commands if the
        region list would exceed the sysmodule's input line limit."""
        if width not in (1, 2, 4, 8):
            raise BridgeError("width must be 1, 2, 4 or 8")
        if value < 0 or value >= (1 << (8 * width)):
            raise BridgeError(f"value {value} does not fit in {width} bytes")
        pairs = [f"0x{s:X} 0x{n:X}" for s, n in regions if n > 0]
        addrs: list = []
        incomplete = capped = False
        batch: list = []
        batches = []
        length = 0
        for p in pairs:
            if batch and length + len(p) + 1 > max_cmd_len:
                batches.append(batch)
                batch, length = [], 0
            batch.append(p)
            length += len(p) + 1
        if batch:
            batches.append(batch)
        for b in batches:
            line = self.command(f"search {width} {value} " + " ".join(b), timeout=max(self.timeout, 120.0))
            a, inc, cap = parse_search_reply(line)
            addrs.extend(a)
            incomplete |= inc
            capped |= cap
        return addrs, incomplete, capped

    def pause(self) -> int:
        """Freeze the game (lab build). Always pair with resume(); prefer paused()."""
        return int(self.command("pause"))

    def resume(self) -> int:
        return int(self.command("resume"))

    def paused(self):
        """Context manager: pause on enter, resume on exit no matter what."""
        client = self

        class _Paused:
            def __enter__(self_inner):
                rc = client.pause()
                if rc != 0:
                    raise BridgeError(f"pause failed: {decode_result(rc)}")
                return client

            def __exit__(self_inner, *_exc):
                client.resume()
                return False

        return _Paused()

    # -- memory writes ------------------------------------------------------
    # These are raw primitives. Policy (explicit apply, original capture,
    # read-back, restore) lives in switchlab.guard; call that, not these.
    def poke_absolute(self, address: int, data: bytes) -> None:
        if not data:
            raise BridgeError("nothing to write")
        # parseStringToByteBuffer only treats the argument as hex when it
        # starts with "0x"; without the prefix it parses each pair as decimal.
        self._send(f"pokeAbsolute 0x{address:X} 0x{data.hex().upper()}")

    def poke_main(self, offset: int, data: bytes) -> None:
        if not data:
            raise BridgeError("nothing to write")
        self._send(f"pokeMain 0x{offset:X} 0x{data.hex().upper()}")

    # -- SD card files (lab2 build) -----------------------------------------
    def fs_list(self, path: str) -> list:
        """[(kind, size, name)] for a directory on the card."""
        lines = self._command_lines(f"fsList {path}", lambda ln: ln == "END" or ln.startswith("ERR"))
        if lines and lines[0].startswith("ERR"):
            raise BridgeError(f"fsList {path}: {lines[0]}")
        out = []
        for ln in lines:
            if ln == "END":
                break
            kind, size, name = ln.split("\t", 2)
            out.append((kind, int(size), name))
        return out

    def fs_get(self, path: str) -> bytes:
        if self._sock is None or self._reader is None:
            raise BridgeError("not connected")
        self._sock.settimeout(max(self.timeout, 60.0))
        self._sock.sendall(f"fsGet {path}\r\n".encode("ascii"))
        header = self._reader.read(8)
        if len(header) != 8:
            raise BridgeError("fsGet: short header (not the lab2 build?)")
        size = int.from_bytes(header, "little")
        if size == 0:
            raise BridgeError(f"fsGet {path}: not found or unreadable")
        data = b""
        while len(data) < size:
            chunk = self._reader.read(size - len(data))
            if not chunk:
                break
            data += chunk
        if len(data) != size:
            raise BridgeError(f"fsGet {path}: expected {size} bytes, got {len(data)}")
        return data

    def fs_put(self, path: str, data: bytes) -> None:
        """Upload bytes to `path` on the card. Verify with fs_get afterwards."""
        if self._sock is None or self._reader is None:
            raise BridgeError("not connected")
        if " " in path:
            raise BridgeError("paths with spaces are not supported")
        reply = self.command(f"fsPut {path} {len(data)}", timeout=max(self.timeout, 60.0))
        if reply != "OK":
            raise BridgeError(f"fsPut {path}: {reply}")
        self._sock.settimeout(max(self.timeout, 120.0))
        self._sock.sendall(data)
        raw = self._reader.readline()
        done = raw.decode("ascii", errors="replace").strip()
        if done != f"DONE {len(data)}":
            raise BridgeError(f"fsPut {path}: {done}")

    def fs_put_verified(self, path: str, data: bytes) -> None:
        """Upload to a temp name, read it back, compare, then rename into place."""
        tmp = path + ".upload"
        self.fs_put(tmp, data)
        back = self.fs_get(tmp)
        if back != data:
            self.fs_delete(tmp)
            raise BridgeError(f"fsPut {path}: read-back mismatch, upload removed")
        self.fs_rename(tmp, path)

    def _fs_simple(self, cmd: str) -> None:
        reply = self.command(cmd, timeout=max(self.timeout, 30.0))
        if reply != "OK":
            raise BridgeError(f"{cmd.split()[0]}: {reply}")

    def fs_rename(self, src: str, dst: str) -> None:
        self._fs_simple(f"fsRename {src} {dst}")

    def fs_delete(self, path: str) -> None:
        self._fs_simple(f"fsDelete {path}")

    def fs_mkdir(self, path: str) -> None:
        self._fs_simple(f"fsMkdir {path}")

    # -- screen ------------------------------------------------------------
    def screenshot(self) -> bytes:
        """Return the current screen as JPEG bytes."""
        reply = self.command("pixelPeek", timeout=max(self.timeout, 20.0))
        if reply.startswith("capssc"):
            raise BridgeError(f"screenshot failed on the Switch: {reply}")
        data = parse_hex_bytes(reply)
        if not data.startswith(b"\xff\xd8"):
            raise BridgeError(f"screenshot reply is not a JPEG ({len(data)} bytes)")
        return data
