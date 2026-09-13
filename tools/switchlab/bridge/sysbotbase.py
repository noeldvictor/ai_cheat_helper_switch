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

    def _send(self, cmd: str) -> None:
        """Send a command that produces no reply (only `configure`)."""
        if self._sock is None:
            raise BridgeError("not connected")
        if not cmd.startswith("configure "):
            raise BridgeError("_send is only for configure commands")
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
