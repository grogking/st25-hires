# SPDX-FileCopyrightText: 2026 grogking
#
# SPDX-License-Identifier: MIT

"""BAN frame decoder. Offsets/skips are packed 320x200 CLUT8 linear addresses."""

from __future__ import annotations

from dataclasses import dataclass

from .bitmap import SCREEN_HEIGHT, SCREEN_WIDTH

LINEAR_SIZE = SCREEN_WIDTH * SCREEN_HEIGHT


@dataclass
class BanOp:
    kind: str
    linear: int
    color: int = 0
    skip: int = 0
    count: int = 0


def linear_to_xy(linear: int) -> tuple[int, int]:
    return linear % SCREEN_WIDTH, linear // SCREEN_WIDTH


def apply_ban_frame(data: bytes, start: int = 0) -> tuple[list[tuple[int, int, int]], int]:
    """
    Decode one BAN frame at ``start``.

    Returns (writes, next_offset) where writes is a list of (x, y, color)
    in 320x200 space. ``next_offset`` is the file position after this frame
    (what ScummVM stores in _banFileOffsets).
    """
    if start + 4 > len(data):
        raise ValueError("truncated BAN header")

    def u16(pos: int) -> int:
        return int.from_bytes(data[pos : pos + 2], "little")

    def i8(pos: int) -> int:
        v = data[pos]
        return v - 256 if v >= 128 else v

    offset = u16(start)
    if offset == 0xFFFF:
        start = 0
        offset = int.from_bytes(data[0:2], "little", signed=True) & 0xFFFF

    size = u16(start + 2)
    pos = start + 4
    # 8-byte dirty rectangle
    if size != 0:
        pos += 8

    writes: list[tuple[int, int, int]] = []
    linear = offset

    remaining = size
    while remaining > 0:
        remaining -= 1
        if pos >= len(data):
            raise ValueError("truncated BAN RLE")
        b = i8(pos)
        pos += 1
        if b == -128:
            skip = u16(pos)
            pos += 2
            linear += skip
        elif b < 0:
            c = data[pos]
            pos += 1
            count = (-b) + 1
            if c == 0:
                linear += count
            else:
                for _ in range(count):
                    x, y = linear_to_xy(linear)
                    writes.append((x, y, c))
                    linear += 1
        else:
            n = b + 1
            for _ in range(n):
                c = data[pos]
                pos += 1
                if c == 0:
                    linear += 1
                else:
                    x, y = linear_to_xy(linear)
                    writes.append((x, y, c))
                    linear += 1

    return writes, pos


def encode_solid_rect(x: int, y: int, w: int, h: int, color: int) -> bytes:
    """One BAN frame: fill a rectangle with a solid palette index (for tests)."""
    if color == 0:
        raise ValueError("color 0 is skip, not a write")
    offset = y * SCREEN_WIDTH + x
    ops = bytearray()
    for row in range(h):
        # one repeated-byte op for the row
        run = w
        # RLE repeat uses int8 b in [-127, -1] meaning count = -b+1, max 128
        while run:
            chunk = min(run, 128)
            b = -(chunk - 1)
            ops.append(b & 0xFF)
            ops.append(color)
            run -= chunk
        if row != h - 1:
            # jump to next row start: remaining pixels in this row + leftover
            skip = SCREEN_WIDTH - w
            ops.append(0x80)  # -128
            ops += skip.to_bytes(2, "little")

    size = 0
    pos = 0
    while pos < len(ops):
        b = ops[pos]
        sb = b - 256 if b >= 128 else b
        pos += 1
        size += 1
        if sb == -128:
            pos += 2
        elif sb < 0:
            pos += 1
        else:
            pos += sb + 1

    rect = (
        x.to_bytes(2, "little", signed=True)
        + y.to_bytes(2, "little", signed=True)
        + (x + w - 1).to_bytes(2, "little", signed=True)
        + (y + h - 1).to_bytes(2, "little", signed=True)
    )
    return (
        offset.to_bytes(2, "little")
        + size.to_bytes(2, "little")
        + rect
        + bytes(ops)
        + b"\xff\xff"
    )
