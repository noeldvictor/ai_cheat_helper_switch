import io
from pathlib import Path

import pytest

from switchlab.bridge.sysbotbase import (
    BridgeError,
    SysBotBase,
    normalize_build_id,
    parse_hex_bytes,
    parse_u64,
)
from switchlab.identity import read_identity
from switchlab.screen import capture_screenshot


class FakeSocket:
    def __init__(self, replies):
        self.replies = replies
        self.sent = []

    def settimeout(self, _t):
        pass

    def sendall(self, data):
        self.sent.append(data)

    def close(self):
        pass


class FakeReader:
    def __init__(self, sock):
        self.sock = sock

    def readline(self, _hint=None):
        cmd = self.sock.sent[-1].decode().strip().split()[0]
        return self.sock.replies[cmd].encode() + b"\n"

    def close(self):
        pass


def make_client(replies):
    client = SysBotBase("203.0.113.1")
    client._sock = FakeSocket(replies)
    client._reader = FakeReader(client._sock)
    return client


def test_parse_helpers():
    assert parse_hex_bytes("") == b""
    assert parse_hex_bytes("DEADBEEF") == b"\xde\xad\xbe\xef"
    assert parse_u64("") is None
    assert parse_u64("0000000080004000") == 0x80004000
    assert normalize_build_id("") is None
    assert normalize_build_id("0123456789abcdef") == "0123456789ABCDEF"
    with pytest.raises(BridgeError):
        parse_hex_bytes("ABC")
    with pytest.raises(BridgeError):
        normalize_build_id("nothex")


def test_commands_are_crlf_terminated_and_single_line():
    client = make_client({"getVersion": "2.5"})
    assert client.get_version() == "2.5"
    assert client._sock.sent == [b"getVersion\r\n"]
    with pytest.raises(BridgeError):
        client.command("getVersion\nsomething")


def test_identity_none_when_no_game():
    client = make_client({"getTitleID": "", "getBuildID": "", "getMainNsoBase": "", "getHeapBase": ""})
    assert read_identity(client) is None


def test_identity_reads_all_fields():
    client = make_client(
        {
            "getTitleID": "0100ABCD00001000",
            "getTitleVersion": "0000000000010000",
            "getBuildID": "0123456789abcdef",
            "getMainNsoBase": "0000000080004000",
            "getHeapBase": "0000004000000000",
            "game": "nsGetApplicationControlData() failed: 0x6410",
        }
    )
    ident = read_identity(client)
    assert ident.title_id_hex == "0100ABCD00001000"
    assert ident.build_id == "0123456789ABCDEF"
    assert ident.cheat_sd_path == "atmosphere/contents/0100ABCD00001000/cheats/0123456789ABCDEF.txt"
    assert ident.display_name is None


def test_peek_size_mismatch_is_an_error():
    client = make_client({"peekMain": ""})
    with pytest.raises(BridgeError):
        client.peek_main(0x10, 4)
    client = make_client({"peekMain": "01020304"})
    assert client.peek_main(0x10, 4) == b"\x01\x02\x03\x04"
    assert client._sock.sent[-1] == b"peekMain 0x10 4\r\n"


def test_screenshot_saved_as_jpeg(tmp_path: Path):
    jpeg = b"\xff\xd8\xff\xe0" + b"\x00" * 8
    client = make_client({"pixelPeek": jpeg.hex().upper()})
    path = capture_screenshot(client, out_dir=tmp_path, label="home menu")
    assert path.read_bytes() == jpeg
    assert path.name.endswith("-home_menu.jpg")


def test_screenshot_rejects_non_jpeg():
    client = make_client({"pixelPeek": "00112233"})
    with pytest.raises(BridgeError):
        client.screenshot()


def test_module_has_no_input_or_freeze_commands():
    """Writes are allowed through guard.py, but the client must never send
    controller input or set up freezes behind the user's back."""
    src = Path(SysBotBase.__module__.replace(".", "/"))
    text = (Path("tools") / src.with_suffix(".py")).read_text()
    for banned in ("freeze", "click", "press", "setStick", "touch", "clickSeq"):
        assert f'"{banned}' not in text, f"input/freeze command {banned!r} found in the client"


def test_poke_absolute_sends_little_endian_hex_and_never_reads():
    # No scripted reply: if poke tried to read one, FakeReader would raise.
    # sys-botbase prints nothing for a poke, so waiting would hang until the
    # socket timed out, and the write would already have landed.
    client = make_client({})
    client.poke_absolute(0x5567E6C2E0, (25).to_bytes(4, "little"))
    # The 0x prefix matters: without it the sysmodule parses each pair as decimal.
    assert client._sock.sent[-1] == b"pokeAbsolute 0x5567E6C2E0 0x19000000\r\n"


def test_send_rejects_commands_that_do_reply():
    client = make_client({})
    with pytest.raises(BridgeError):
        client._send("getVersion")


class QueueReader:
    """Reader that serves scripted multi-line replies per command."""

    def __init__(self, sock, script):
        self.sock = sock
        self.script = script  # {cmd: [lines]}
        self.pending = []

    def readline(self, _hint=None):
        if not self.pending:
            cmd = self.sock.sent[-1].decode().strip().split()[0]
            self.pending = list(self.script[cmd])
        return self.pending.pop(0).encode() + b"\n"

    def close(self):
        pass


def test_decode_result():
    from switchlab.bridge.sysbotbase import decode_result

    assert decode_result(62465) == "0xF401 kernel Busy"
    assert decode_result(58369) == "0xE401 kernel InvalidHandle"
    assert decode_result(0) == "0 (success)"


def test_diagnose_reports_already_debugged_and_restores_setting():
    client = SysBotBase("203.0.113.1")
    client._sock = FakeSocket({})
    client._reader = QueueReader(
        client._sock, {"getHeapBase": ["svcDebugActiveProcess: 62465", "svcGetInfo: 58369", "0000000000000004"]}
    )
    report = client.diagnose()
    assert report["attached"] is False
    assert report["codes"]["svcDebugActiveProcess"] == 62465
    assert "already being debugged" in report["verdict"]
    assert client._sock.sent[0] == b"configure printDebugResultCodes 1\r\n"
    assert client._sock.sent[-1] == b"configure printDebugResultCodes 0\r\n"


def test_diagnose_reports_healthy_attach():
    client = SysBotBase("203.0.113.1")
    client._sock = FakeSocket({})
    client._reader = QueueReader(client._sock, {"getHeapBase": ["0000004000000000"]})
    report = client.diagnose()
    assert report["attached"] is True
    assert "should work" in report["verdict"]


def test_parse_memory_regions_and_search_reply():
    from switchlab.bridge.sysbotbase import parse_memory_regions, parse_search_reply

    regs = parse_memory_regions("229E800000 4000 3 5 4A11840000 25614000 B 3 ")
    assert (regs[0].addr, regs[0].size, regs[0].mem_type, regs[0].perm) == (0x229E800000, 0x4000, 3, 5)
    assert regs[1].type_name == "mapped" and regs[1].readable and regs[1].writable
    assert parse_search_reply("4A11841000 4A11842004 ! + ") == ([0x4A11841000, 0x4A11842004], True, True)
    assert parse_search_reply("") == ([], False, False)


def test_search_batches_commands_and_validates():
    client = make_client({"search": "1000 2000 ", "getVersion": "2.5-lab1"})
    regions = [(0x1000 * i, 0x100) for i in range(1, 900)]
    addrs, inc, cap = client.search(4, 84, regions, max_cmd_len=2000)
    sent = [m for m in client._sock.sent if m.startswith(b"search ")]
    assert len(sent) > 1 and all(len(m) <= 2100 for m in sent)
    assert addrs[:2] == [0x1000, 0x2000] and not inc and not cap
    assert client.is_lab()
    with pytest.raises(BridgeError):
        client.search(2, 70000, [(0, 16)])


def test_peek_raw_reads_binary_header_then_bytes():
    client = SysBotBase("203.0.113.1")
    client._sock = FakeSocket({})
    payload = bytes(range(16))

    class RawReader:
        def __init__(self):
            self.buf = (16).to_bytes(8, "little") + payload

        def read(self, n):
            out, self.buf = self.buf[:n], self.buf[n:]
            return out

        def close(self):
            pass

    client._reader = RawReader()
    assert client.peek_raw(0x1000, 16) == payload
    assert client._sock.sent[-1] == b"peekRaw 0x1000 16\r\n"


def test_paused_context_always_resumes():
    client = make_client({"pause": "0", "resume": "0"})
    try:
        with client.paused():
            raise RuntimeError("boom")
    except RuntimeError:
        pass
    assert client._sock.sent[-2:] == [b"pause\r\n", b"resume\r\n"]


class ScriptedIO:
    """Reader/socket pair replaying exact bytes for fs protocol tests."""

    def __init__(self, stream: bytes):
        self.stream = stream
        self.sent = []

    # socket side
    def settimeout(self, _t):
        pass

    def sendall(self, data):
        self.sent.append(data)

    def close(self):
        pass

    # reader side
    def read(self, n):
        out, self.stream = self.stream[:n], self.stream[n:]
        return out

    def readline(self, _hint=None):
        i = self.stream.find(b"\n")
        if i == -1:
            out, self.stream = self.stream, b""
            return out
        out, self.stream = self.stream[: i + 1], self.stream[i + 1 :]
        return out


def _fs_client(stream: bytes) -> SysBotBase:
    c = SysBotBase("203.0.113.1")
    io_ = ScriptedIO(stream)
    c._sock = io_
    c._reader = io_
    return c


def test_fs_list_parses_until_end():
    c = _fs_client(b"d\t0\tatmosphere\nf\t97925\texefs.nsp\nEND\n")
    assert c.fs_list("/") == [("d", 0, "atmosphere"), ("f", 97925, "exefs.nsp")]
    assert c._sock.sent == [b"fsList /\r\n"]


def test_fs_get_and_put_protocol():
    payload = b"hello switch"
    c = _fs_client(len(payload).to_bytes(8, "little") + payload)
    assert c.fs_get("/switch/x.bin") == payload

    c = _fs_client(b"OK\n" + b"DONE 12\n")
    c.fs_put("/switch/x.bin", payload)
    assert c._sock.sent == [b"fsPut /switch/x.bin 12\r\n", payload]

    c = _fs_client(b"ERR open 2\n")
    with pytest.raises(BridgeError):
        c.fs_put("/nope/x.bin", payload)


def test_fs_put_verified_reads_back_and_renames():
    payload = b"abc"
    stream = b"OK\nDONE 3\n" + (3).to_bytes(8, "little") + payload + b"OK\n"
    c = _fs_client(stream)
    c.fs_put_verified("/switch/y.bin", payload)
    assert c._sock.sent[-1] == b"fsRename /switch/y.bin.upload /switch/y.bin\r\n"
