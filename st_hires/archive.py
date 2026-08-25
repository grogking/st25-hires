# SPDX-FileCopyrightText: 2026 grogking
#
# SPDX-License-Identifier: MIT

"""DATA.DIR / DATA.001 reader."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .lzss import decode_lzss


@dataclass
class DirEntry:
    name: str
    offset: int
    file_count: int


def _read_c_string(buf: bytes) -> str:
    return buf.split(b"\x00", 1)[0].decode("latin-1")


def parse_dir(data: bytes) -> list[DirEntry]:
    entries: list[DirEntry] = []
    for i in range(0, len(data) - 13, 14):
        name = _read_c_string(data[i : i + 8])
        if not name:
            continue
        ext = _read_c_string(data[i + 8 : i + 11])
        filename = f"{name}.{ext}" if ext else name
        off = data[i + 11] + (data[i + 12] << 8) + (data[i + 13] << 16)
        if off & (1 << 23):
            file_count = (off >> 16) & 0x7F
            offset = off & 0xFFFF
        else:
            file_count = 1
            offset = off & 0xFFFFFF
        entries.append(DirEntry(filename, offset, file_count))
    return entries


def extract_file(data_001: bytes, offset: int) -> bytes:
    uncmp = int.from_bytes(data_001[offset : offset + 2], "little")
    cmp_size = int.from_bytes(data_001[offset + 2 : offset + 4], "little")
    payload = data_001[offset + 4 : offset + 4 + cmp_size]
    if len(payload) != cmp_size:
        raise ValueError(f"truncated DATA.001 payload at {offset}")
    return decode_lzss(payload, uncmp)


def find_gog_roots(game_dir: Path) -> list[Path]:
    """Directories that contain DATA.DIR + DATA.001 (case-insensitive)."""
    roots: list[Path] = []
    if not game_dir.exists():
        return roots
    for path in [game_dir, *game_dir.rglob("*")]:
        if not path.is_dir():
            continue
        names = {p.name.lower(): p for p in path.iterdir() if p.is_file()}
        if "data.dir" in names and "data.001" in names:
            roots.append(path)
    return sorted(set(roots))


def load_archive(root: Path) -> dict[str, bytes]:
    names = {p.name.lower(): p for p in root.iterdir() if p.is_file()}
    dir_bytes = names["data.dir"].read_bytes()
    data_bytes = names["data.001"].read_bytes()
    out: dict[str, bytes] = {}
    for entry in parse_dir(dir_bytes):
        if entry.file_count != 1:
            continue
        try:
            out[entry.name.upper()] = extract_file(data_bytes, entry.offset)
        except (ValueError, KeyError):
            continue
    return out
