# SPDX-FileCopyrightText: 2026 grogking
#
# SPDX-License-Identifier: MIT

"""Interplay custom BMP / XOR / SHP (not Windows BMP)."""

from __future__ import annotations

from dataclasses import dataclass

SCREEN_WIDTH = 320
SCREEN_HEIGHT = 200


@dataclass
class TrekBitmap:
    xoffset: int
    yoffset: int
    width: int
    height: int
    pixels: bytes

    def to_bytes(self) -> bytes:
        header = (
            self.xoffset.to_bytes(2, "little")
            + self.yoffset.to_bytes(2, "little")
            + self.width.to_bytes(2, "little")
            + self.height.to_bytes(2, "little")
        )
        expected = self.width * self.height
        if len(self.pixels) != expected:
            raise ValueError(f"pixel count {len(self.pixels)} != {expected}")
        return header + self.pixels


R3S_HEADER_SIZE = 36


def parse_bitmap(data: bytes) -> TrekBitmap:
    if len(data) < 8:
        raise ValueError("bitmap too small")
    xoffset = int.from_bytes(data[0:2], "little")
    yoffset = int.from_bytes(data[2:4], "little")
    width = int.from_bytes(data[4:6], "little")
    height = int.from_bytes(data[6:8], "little")
    pixels = data[8 : 8 + width * height]
    if len(pixels) != width * height:
        raise ValueError("truncated bitmap pixels")
    return TrekBitmap(xoffset, yoffset, width, height, pixels)


def parse_shp_frames(data: bytes) -> list[TrekBitmap]:
    """SHP = one or more concatenated custom bitmaps (STARS.SHP is multi-frame)."""
    frames: list[TrekBitmap] = []
    pos = 0
    length = len(data)
    while pos + 8 <= length:
        width = int.from_bytes(data[pos + 4 : pos + 6], "little")
        height = int.from_bytes(data[pos + 6 : pos + 8], "little")
        need = 8 + width * height
        if width == 0 or height == 0 or pos + need > length:
            break
        frames.append(parse_bitmap(data[pos : pos + need]))
        pos += need
    if not frames:
        raise ValueError("no SHP frames")
    return frames


def parse_r3s(data: bytes) -> TrekBitmap:
    """R3S = 36-byte view header then one SHP-style bitmap. Palette is BRIDGE.PAL."""
    if len(data) < R3S_HEADER_SIZE + 8:
        raise ValueError("r3s too small")
    return parse_bitmap(data[R3S_HEADER_SIZE:])


def parse_palette(data: bytes) -> list[tuple[int, int, int]]:
    """VGA 6-bit PAL (256*3). Expand to 8-bit RGB."""
    if len(data) < 256 * 3:
        raise ValueError("palette too small")
    pal = []
    for i in range(256):
        r, g, b = data[i * 3 : i * 3 + 3]
        pal.append((r << 2, g << 2, b << 2))
    return pal


def bitmap_to_rgba(bmp: TrekBitmap, palette: list[tuple[int, int, int]]) -> bytes:
    out = bytearray(bmp.width * bmp.height * 4)
    for i, idx in enumerate(bmp.pixels):
        if idx == 0:
            out[i * 4 : i * 4 + 4] = b"\x00\x00\x00\x00"
        else:
            r, g, b = palette[idx]
            out[i * 4 : i * 4 + 4] = bytes((r, g, b, 255))
    return bytes(out)


def quantize_to_palette(
    rgba: bytes, width: int, height: int, palette: list[tuple[int, int, int]]
) -> bytes:
    """Map 8-bit RGBA onto the game palette. Index 0 stays transparent."""
    pixels = bytearray(width * height)
    pal = palette

    def dist2(r, g, b, pr, pg, pb):
        dr, dg, db = r - pr, g - pg, b - pb
        return dr * dr + dg * dg + db * db

    for i in range(width * height):
        r, g, b, a = rgba[i * 4 : i * 4 + 4]
        if a < 128:
            pixels[i] = 0
            continue
        best = 1
        best_d = dist2(r, g, b, *pal[1])
        for idx in range(1, 256):
            d = dist2(r, g, b, *pal[idx])
            if d < best_d:
                best_d = d
                best = idx
                if d == 0:
                    break
        pixels[i] = best
    return bytes(pixels)


def scale_offsets(bmp: TrekBitmap, scale: int) -> TrekBitmap:
    return TrekBitmap(
        bmp.xoffset * scale,
        bmp.yoffset * scale,
        bmp.width,
        bmp.height,
        bmp.pixels,
    )


def downscale_nearest(pixels: bytes, src_w: int, src_h: int, dst_w: int, dst_h: int) -> bytes:
    if src_w % dst_w or src_h % dst_h:
        raise ValueError("hi-res size must be an integer multiple of the original")
    sx = src_w // dst_w
    sy = src_h // dst_h
    out = bytearray(dst_w * dst_h)
    for y in range(dst_h):
        for x in range(dst_w):
            out[y * dst_w + x] = pixels[(y * sy) * src_w + (x * sx)]
    return bytes(out)
