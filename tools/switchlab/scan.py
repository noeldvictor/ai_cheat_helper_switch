"""Candidate narrowing sessions (read-only).

A session starts with an on-device exact search (lab build) and is narrowed
by re-reading only the surviving candidates, which takes seconds. Sessions
are saved as JSON under the ignored local/sessions folder so a run can be
resumed and audited.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from switchlab.bridge.sysbotbase import BridgeError

REPO_ROOT = Path(__file__).resolve().parents[2]
SESSION_DIR = REPO_ROOT / "local" / "sessions"

OPS = ("exact", "changed", "unchanged", "increased", "decreased")


@dataclass
class ScanSession:
    label: str
    build_id: str
    width: int
    candidates: List[int]
    values: Dict[int, int] = field(default_factory=dict)  # last read value per candidate
    history: List[dict] = field(default_factory=list)

    @property
    def path(self) -> Path:
        return SESSION_DIR / f"{self.build_id}-{self.label}.json"

    def save(self) -> Path:
        SESSION_DIR.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(
                {
                    "label": self.label,
                    "build_id": self.build_id,
                    "width": self.width,
                    "candidates": self.candidates,
                    "values": {f"{a:X}": v for a, v in self.values.items()},
                    "history": self.history,
                },
                indent=1,
            )
        )
        return self.path

    @classmethod
    def load(cls, build_id: str, label: str) -> "ScanSession":
        path = SESSION_DIR / f"{build_id}-{label}.json"
        if not path.exists():
            raise FileNotFoundError(f"no session {label} for build {build_id} (looked at {path})")
        d = json.loads(path.read_text())
        return cls(
            d["label"], d["build_id"], d["width"], list(d["candidates"]),
            {int(a, 16): v for a, v in d["values"].items()}, d["history"],
        )

    def note(self, op: str, value: Optional[int], before: int) -> None:
        self.history.append(
            {"time": datetime.now().isoformat(timespec="seconds"), "op": op, "value": value, "before": before, "after": len(self.candidates)}
        )


def read_values(client, addrs: Iterable[int], width: int, batch: int = 256, log=None) -> Dict[int, int]:
    """Current values of candidate addresses. Unreadable ones are dropped."""
    addrs = sorted(set(addrs))
    out: Dict[int, int] = {}
    for i in range(0, len(addrs), batch):
        chunk = addrs[i : i + batch]
        pairs = [(a, width) for a in chunk]
        try:
            data = client.peek_multi(pairs)
        except BridgeError:
            data = b""
        if len(data) == width * len(chunk):
            for j, a in enumerate(chunk):
                out[a] = int.from_bytes(data[j * width : (j + 1) * width], "little")
            continue
        # a pair failed: fall back to single reads and drop the unreadable
        for a in chunk:
            try:
                out[a] = int.from_bytes(client.peek_absolute(a, width), "little")
            except BridgeError:
                pass
        if log:
            log(f"  batch at 0x{chunk[0]:X}: fell back to single reads, kept {sum(1 for a in chunk if a in out)}/{len(chunk)}")
    return out


def start_exact(client, regions, width: int, value: int, label: str, build_id: str, log=None) -> ScanSession:
    """New session from an on-device exact search over (start, size) pairs."""
    addrs, incomplete, capped = client.search(width, value, regions)
    session = ScanSession(label, build_id, width, sorted(addrs), {a: value for a in addrs})
    session.note("exact", value, 0)
    session.history[-1].update({"incomplete": incomplete, "capped": capped})
    if log:
        flags = (" (some memory unreadable)" if incomplete else "") + (" (hit cap reached; narrow with a rescan)" if capped else "")
        log(f"{len(addrs)} candidates for {value} as {width}-byte{flags}")
    session.save()
    return session


def refine(client, session: ScanSession, op: str, value: Optional[int] = None, log=None) -> ScanSession:
    """Keep candidates whose current value satisfies `op` (see OPS)."""
    if op not in OPS:
        raise ValueError(f"op must be one of {OPS}")
    if op == "exact" and value is None:
        raise ValueError("exact needs a value")
    before = len(session.candidates)
    current = read_values(client, session.candidates, session.width, log=log)
    keep: List[int] = []
    for a in session.candidates:
        if a not in current:
            continue
        now, prev = current[a], session.values.get(a)
        ok = {
            "exact": lambda: now == value,
            "changed": lambda: prev is not None and now != prev,
            "unchanged": lambda: prev is not None and now == prev,
            "increased": lambda: prev is not None and now > prev,
            "decreased": lambda: prev is not None and now < prev,
        }[op]()
        if ok:
            keep.append(a)
    session.candidates = keep
    session.values = {a: current[a] for a in keep}
    session.note(op, value, before)
    session.save()
    if log:
        log(f"{before} -> {len(keep)} candidates after {op}{'' if value is None else ' ' + str(value)}")
    return session
