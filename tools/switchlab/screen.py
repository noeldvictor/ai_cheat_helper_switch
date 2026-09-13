"""Fetch a screenshot from the Switch so the AI can read visible values."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from switchlab.bridge.sysbotbase import SysBotBase

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCREEN_DIR = REPO_ROOT / "local" / "screens"  # git-ignored on purpose


def capture_screenshot(client: SysBotBase, out_dir: Path = DEFAULT_SCREEN_DIR, label: str = "screen") -> Path:
    """Save the current screen as JPEG under an ignored local folder."""
    data = client.screenshot()
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    safe_label = "".join(c if c.isalnum() or c in "-_" else "_" for c in label) or "screen"
    path = out_dir / f"{stamp}-{safe_label}.jpg"
    path.write_bytes(data)
    return path
