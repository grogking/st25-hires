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


def sequential_data001_offset(data_run: bytes, run_offset: int, file_index: int) -> int:
    """Map a sequential DIR entry onto a DATA.001 record via DATA.RUN.

    CD layout (GOG TREKCD): the DIR offset is an index into DATA.RUN. At that
    index: 24-bit LE start in DATA.001, then uint16 LE strides for files 1..n.
    """
    if file_index < 0:
        raise ValueError("file_index must be >= 0")
    pos = run_offset
    if pos + 3 > len(data_run):
        raise ValueError(f"truncated DATA.RUN header at {run_offset}")
    offset = data_run[pos] + (data_run[pos + 1] << 8) + (data_run[pos + 2] << 16)
    pos += 3
    for _ in range(file_index):
        if pos + 2 > len(data_run):
            raise ValueError("truncated DATA.RUN stride table")
        offset += int.from_bytes(data_run[pos : pos + 2], "little")
        pos += 2
    return offset


def _file_map(root: Path) -> dict[str, Path]:
    return {p.name.lower(): p for p in root.iterdir() if p.is_file()}


def load_named_file(root: Path, name: str, file_index: int = 0) -> bytes:
    """Decompress one archive member. ``file_index`` selects a sequential run."""
    names = _file_map(root)
    if "data.dir" not in names or "data.001" not in names:
        raise FileNotFoundError(f"DATA.DIR / DATA.001 missing under {root}")
    entries = {e.name.upper(): e for e in parse_dir(names["data.dir"].read_bytes())}
    key = name.upper()
    if key not in entries:
        raise KeyError(name)
    entry = entries[key]
    data_001 = names["data.001"].read_bytes()
    if entry.file_count == 1:
        if file_index != 0:
            raise IndexError(f"{name} is not a sequential file")
        return extract_file(data_001, entry.offset)
    if file_index >= entry.file_count:
        raise IndexError(f"{name} file_index {file_index} >= {entry.file_count}")
    if "data.run" not in names:
        raise FileNotFoundError(f"DATA.RUN missing under {root} (needed for {name})")
    data001_off = sequential_data001_offset(
        names["data.run"].read_bytes(), entry.offset, file_index
    )
    return extract_file(data_001, data001_off)


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
