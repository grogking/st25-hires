# SPDX-FileCopyrightText: 2026 grogking
#
# SPDX-License-Identifier: MIT

import unittest

from st_hires.bitmap import TrekBitmap, parse_r3s, parse_shp_frames


class ShpR3sTests(unittest.TestCase):
    def test_shp_multi_frame(self):
        a = TrekBitmap(1, 2, 2, 1, bytes([9, 8]))
        b = TrekBitmap(3, 4, 1, 2, bytes([7, 6]))
        frames = parse_shp_frames(a.to_bytes() + b.to_bytes())
        self.assertEqual(frames, [a, b])

    def test_r3s_skips_36_byte_header(self):
        bmp = TrekBitmap(5, 6, 2, 2, bytes([1, 2, 3, 4]))
        blob = bytes(range(36)) + bmp.to_bytes()
        parsed = parse_r3s(blob)
        self.assertEqual(parsed, bmp)


if __name__ == "__main__":
    unittest.main()
