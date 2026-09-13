"""Durable records of what we found, stored in the repository.

A raw heap address dies with the game process. Losing one to a crash or a
relaunch used to mean repeating the whole search, which is what happened on
2026-09-13. What survives is everything around the address: how it was found,
where it sits inside its memory region, and what the bytes next to it look
like. Store that and the address can be recovered in seconds.

Findings live in `games/<slug>/findings/<label>.json` and are committed. They
contain no memory dumps, only a small window of bytes around one field, which
is research evidence about our own save state rather than game content.

Two operations matter:

- `capture` records a finding while the game is still running.
- `relocate` finds the field again in a new process, by searching for the
  current value and then ranking candidates by how well the surrounding bytes
  match the stored signature.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
GAMES_DIR = REPO_ROOT / "games"

SIG_BEFORE = 64
SIG_AFTER = 64


def findings_dir(game_slug: str) -> Path:
    return GAMES_DIR / game_slug / "findings"


@dataclass
class Finding:
    label: str
    game_slug: str
    build_id: str
    title_id: str
    width: int
    address: int
    value: int
    region_kind: str
    region_start: int
    region_offset: int
    main_nso_base: int
    sig_before: int
    sig_after: int
    signature: bytes
    recipe: List[str] = field(default_factory=list)
    status: str = "candidate"
    notes: str = ""
    captured_at: str = ""

    @property
    def path(self) -> Path:
        return findings_dir(self.game_slug) / f"{self.label}.json"

    @property
    def field_offset_in_signature(self) -> int:
        return self.sig_before

    def save(self) -> Path:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({
            "label": self.label,
            "game_slug": self.game_slug,
            "build_id": self.build_id,
            "title_id": self.title_id,
            "width": self.width,
            "address": f"0x{self.address:X}",
            "value": self.value,
            "region_kind": self.region_kind,
            "region_start": f"0x{self.region_start:X}",
            "region_offset": f"0x{self.region_offset:X}",
            "main_nso_base": f"0x{self.main_nso_base:X}",
            "sig_before": self.sig_before,
            "sig_after": self.sig_after,
            "signature": self.signature.hex().upper(),
            "recipe": self.recipe,
            "status": self.status,
            "notes": self.notes,
            "captured_at": self.captured_at,
        }, indent=1) + "\n")
        return self.path

    @classmethod
    def load(cls, game_slug: str, label: str) -> "Finding":
        path = findings_dir(game_slug) / f"{label}.json"
        d = json.loads(path.read_text())
        return cls(
            label=d["label"], game_slug=d["game_slug"], build_id=d["build_id"],
            title_id=d["title_id"], width=d["width"], address=int(d["address"], 16),
            value=d["value"], region_kind=d["region_kind"],
            region_start=int(d["region_start"], 16), region_offset=int(d["region_offset"], 16),
            main_nso_base=int(d["main_nso_base"], 16), sig_before=d["sig_before"],
            sig_after=d["sig_after"], signature=bytes.fromhex(d["signature"]),
            recipe=d.get("recipe", []), status=d.get("status", "candidate"),
            notes=d.get("notes", ""), captured_at=d.get("captured_at", ""),
        )

    @classmethod
    def list_all(cls, game_slug: str) -> List["Finding"]:
        d = findings_dir(game_slug)
        if not d.exists():
            return []
        return [cls.load(game_slug, p.stem) for p in sorted(d.glob("*.json"))]

    def describe(self) -> str:
        return (f"{self.label:22} {self.status:10} u{self.width * 8:<2} "
                f"0x{self.address:X}  {self.region_kind}+0x{self.region_offset:X}  "
                f"value {self.value}")


def capture(client, game_slug: str, label: str, address: int, width: int,
            recipe: Optional[List[str]] = None, status: str = "candidate",
            notes: str = "", sig_before: int = SIG_BEFORE, sig_after: int = SIG_AFTER) -> Finding:
    """Record a finding from the running game. Read-only."""
    from switchlab.bridge.sysbotbase import MEM_TYPE_NAMES
    from switchlab.identity import read_identity
    from switchlab.regions import regions_from_kernel

    ident = read_identity(client)
    if ident is None:
        raise RuntimeError("no game is running")
    value = int.from_bytes(client.peek_absolute(address, width), "little")
    lo = address - sig_before
    signature = client.peek_absolute(lo, sig_before + width + sig_after)

    region_kind, region_start, region_offset = "unknown", 0, 0
    for r in regions_from_kernel(client.query_memory_all()):
        if r.contains(address):
            region_kind = MEM_TYPE_NAMES.get(r.mem_type, hex(r.mem_type))
            region_start, region_offset = r.start, address - r.start
            break

    finding = Finding(
        label=label, game_slug=game_slug, build_id=ident.build_id,
        title_id=ident.title_id_hex, width=width, address=address, value=value,
        region_kind=region_kind, region_start=region_start, region_offset=region_offset,
        main_nso_base=ident.main_nso_base, sig_before=sig_before, sig_after=sig_after,
        signature=signature, recipe=recipe or [], status=status, notes=notes,
        captured_at=datetime.now().isoformat(timespec="seconds"),
    )
    finding.save()
    return finding


def score_signature(stored: bytes, seen: bytes, field_offset: int, width: int) -> float:
    """Fraction of surrounding bytes that match, ignoring the field itself."""
    if len(stored) != len(seen):
        return 0.0
    same = total = 0
    for i in range(len(stored)):
        if field_offset <= i < field_offset + width:
            continue  # the field changes; that is the point
        total += 1
        if stored[i] == seen[i]:
            same += 1
    return same / total if total else 0.0


def relocate(client, finding: Finding, current_value: int, regions,
             max_candidates: int = 4000, min_score: float = 0.6,
             log=None) -> List[Tuple[int, float]]:
    """Find the field again in a new process.

    Searches for `current_value` at the stored width, then ranks candidates by
    how closely the bytes around them match the stored signature. Returns
    (address, score) pairs sorted best first.
    """
    addrs, incomplete, capped = client.search(finding.width, current_value, regions)
    if log:
        log(f"{len(addrs)} addresses hold {current_value} as u{finding.width * 8}"
            + (" (capped)" if capped else ""))
    if capped or len(addrs) > max_candidates:
        raise RuntimeError(
            f"{len(addrs)} candidates is too many to score. Change the value in game and "
            "relocate on a rarer one, or narrow with a scan session first."
        )
    window = finding.sig_before + finding.width + finding.sig_after
    scored: List[Tuple[int, float]] = []
    for i, a in enumerate(addrs):
        try:
            seen = client.peek_absolute(a - finding.sig_before, window)
        except Exception:
            continue
        s = score_signature(finding.signature, seen, finding.field_offset_in_signature, finding.width)
        if s >= min_score:
            scored.append((a, s))
        if log and i and i % 500 == 0:
            log(f"  scored {i}/{len(addrs)}")
    scored.sort(key=lambda t: -t[1])
    return scored
