# SPDX-FileCopyrightText: 2026 grogking
#
# SPDX-License-Identifier: MIT

import unittest

from st_hires.bitmap import TrekBitmap, parse_bitmap, parse_palette, quantize_to_palette
from st_hires.archive import parse_dir


class BitmapTests(unittest.TestCase):
    def test_round_trip_header(self):
        bmp = TrekBitmap(12, 34, 4, 2, bytes([0, 1, 2, 3, 4, 5, 6, 7]))
        parsed = parse_bitmap(bmp.to_bytes())
        self.assertEqual(parsed, bmp)

    def test_quantize_keeps_index_zero_transparent(self):
        pal = [(i, i, i) for i in range(256)]
        pal[0] = (255, 0, 255)
        pal[5] = (10, 20, 30)
        rgba = bytes(
            [
                10,
                20,
                30,
                255,
                0,
                0,
                0,
                0,
            ]
        )
        pixels = quantize_to_palette(rgba, 2, 1, pal)
        self.assertEqual(pixels[0], 5)
        self.assertEqual(pixels[1], 0)

    def test_palette_expands_6bit(self):
        raw = bytes([0x10, 0x20, 0x30]) + bytes(256 * 3 - 3)
        pal = parse_palette(raw)
        self.assertEqual(pal[0], (0x10 << 2, 0x20 << 2, 0x30 << 2))


class DirTests(unittest.TestCase):
    def test_parse_simple_entry(self):
        name = b"IKIRK\x00\x00\x00"
        ext = b"BMP"
        offset = (0x1234).to_bytes(3, "little")
        data = name + ext + offset + bytes(14)
        entries = parse_dir(data)
        self.assertEqual(entries[0].name, "IKIRK.BMP")
        self.assertEqual(entries[0].offset, 0x1234)
        self.assertEqual(entries[0].file_count, 1)


if __name__ == "__main__":
    unittest.main()
