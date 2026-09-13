import json
from pathlib import Path

import pytest

from switchlab import findings as F
from switchlab.findings import Finding, relocate, score_signature


@pytest.fixture(autouse=True)
def games_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(F, "GAMES_DIR", tmp_path)
    yield tmp_path


def make_finding(**kw):
    base = dict(
        label="ammo-magazine", game_slug="game", build_id="BID", title_id="TID",
        width=4, address=0x5567E6C2E0, value=16, region_kind="heap",
        region_start=0x556784E000, region_offset=0x61E2E0, main_nso_base=0x7B3604000,
        sig_before=4, sig_after=4,
        signature=bytes([1, 2, 3, 4]) + (16).to_bytes(4, "little") + bytes([5, 6, 7, 8]),
        recipe=["exact u32 30", "fire rounds", "exact u32 16"], status="confirmed",
    )
    base.update(kw)
    return Finding(**base)


def test_save_and_load_roundtrip():
    f = make_finding()
    path = f.save()
    assert path.name == "ammo-magazine.json"
    raw = json.loads(path.read_text())
    assert raw["address"] == "0x5567E6C2E0"      # hex in the file, readable by a human
    assert raw["recipe"][0] == "exact u32 30"
    back = Finding.load("game", "ammo-magazine")
    assert back.address == f.address and back.signature == f.signature and back.width == 4


def test_list_all_finds_every_record():
    make_finding().save()
    make_finding(label="reserve", address=0x555A6627CC, width=2).save()
    labels = [x.label for x in Finding.list_all("game")]
    assert labels == ["ammo-magazine", "reserve"]


def test_score_ignores_the_field_itself():
    stored = bytes([1, 2, 3, 4]) + (16).to_bytes(4, "little") + bytes([5, 6, 7, 8])
    same_but_new_value = bytes([1, 2, 3, 4]) + (99).to_bytes(4, "little") + bytes([5, 6, 7, 8])
    assert score_signature(stored, same_but_new_value, 4, 4) == 1.0
    half = bytes([1, 2, 9, 9]) + (99).to_bytes(4, "little") + bytes([5, 6, 7, 8])
    assert score_signature(stored, half, 4, 4) == 0.75
    assert score_signature(stored, b"\x00" * 3, 4, 4) == 0.0


class RelocClient:
    def __init__(self, hits, memory):
        self.hits = hits
        self.memory = memory  # {address: bytes}

    def search(self, width, value, regions):
        return list(self.hits), False, False

    def peek_absolute(self, addr, size):
        if addr not in self.memory:
            raise RuntimeError("unmapped")
        return self.memory[addr][:size]


def test_relocate_ranks_the_real_match_first():
    f = make_finding()
    good = bytes([1, 2, 3, 4]) + (7).to_bytes(4, "little") + bytes([5, 6, 7, 8])
    poor = bytes([9, 9, 9, 9]) + (7).to_bytes(4, "little") + bytes([9, 9, 9, 9])
    client = RelocClient([0x2000, 0x3000], {0x2000 - 4: poor, 0x3000 - 4: good})
    ranked = relocate(client, f, 7, [(0, 1)])
    assert ranked[0] == (0x3000, 1.0)
    assert all(addr != 0x2000 for addr, _ in ranked)   # below min_score


def test_relocate_refuses_when_there_are_too_many_candidates():
    f = make_finding()
    client = RelocClient(list(range(0, 9000, 4)), {})
    with pytest.raises(RuntimeError, match="too many"):
        relocate(client, f, 7, [(0, 1)], max_candidates=100)
