"""Identity of the game currently running on the Switch."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from switchlab.bridge.sysbotbase import SysBotBase


@dataclass(frozen=True)
class GameIdentity:
    title_id: int
    title_version: Optional[int]
    build_id: str
    main_nso_base: int
    heap_base: int
    display_name: Optional[str] = None
    display_version: Optional[str] = None

    @property
    def title_id_hex(self) -> str:
        return f"{self.title_id:016X}"

    @property
    def cheat_file_name(self) -> str:
        return f"{self.build_id}.txt"

    @property
    def cheat_sd_path(self) -> str:
        return f"atmosphere/contents/{self.title_id_hex}/cheats/{self.cheat_file_name}"

    def describe(self) -> str:
        lines = [
            f"Game:            {self.display_name or 'unknown'}",
            f"Display version: {self.display_version or 'unknown'}",
            f"Title ID:        {self.title_id_hex}",
            f"Build ID:        {self.build_id}",
            f"Title version:   {self.title_version if self.title_version is not None else 'unknown'}",
            f"Main NSO base:   0x{self.main_nso_base:X}",
            f"Heap base:       0x{self.heap_base:X}",
            f"Cheat file:      {self.cheat_sd_path}",
        ]
        return "\n".join(lines)


def read_identity(client: SysBotBase) -> Optional[GameIdentity]:
    """Read the running game's identity, or None when no game is running."""
    title_id = client.get_title_id()
    if title_id is None or title_id == 0:
        return None
    build_id = client.get_build_id()
    main_base = client.get_main_nso_base()
    heap_base = client.get_heap_base()
    if build_id is None or not main_base or not heap_base:
        return None
    return GameIdentity(
        title_id=title_id,
        title_version=client.get_title_version(),
        build_id=build_id,
        main_nso_base=main_base,
        heap_base=heap_base,
        display_name=client.get_game_field("name"),
        display_version=client.get_game_field("version"),
    )
