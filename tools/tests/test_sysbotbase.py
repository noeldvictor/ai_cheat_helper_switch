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


def test_module_has_no_write_commands():
    src = Path(SysBotBase.__module__.replace(".", "/"))
    text = (Path("tools") / src.with_suffix(".py")).read_text()
    for banned in ("poke", "freeze", "click", "press", "setStick", "touch"):
        assert f'"{banned}' not in text, f"write/input command {banned!r} found in read-only client"


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
