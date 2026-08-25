# SPDX-FileCopyrightText: 2026 grogking
#
# SPDX-License-Identifier: MIT

import unittest

from st_hires.ban import apply_ban_frame, encode_solid_rect, linear_to_xy
from st_hires.bitmap import SCREEN_WIDTH


class BanLinearTests(unittest.TestCase):
    def test_linear_to_xy(self):
        self.assertEqual(linear_to_xy(0), (0, 0))
        self.assertEqual(linear_to_xy(319), (319, 0))
        self.assertEqual(linear_to_xy(320), (0, 1))
        self.assertEqual(linear_to_xy(20 * 320 + 10), (10, 20))

    def test_solid_rect_lands_on_xy_not_pitched_scatter(self):
        frame = encode_solid_rect(10, 20, 3, 2, color=7)
        writes, nxt = apply_ban_frame(frame, 0)
        expected = {
            (10, 20),
            (11, 20),
            (12, 20),
            (10, 21),
            (11, 21),
            (12, 21),
        }
        got = {(x, y) for x, y, c in writes}
        self.assertEqual(got, expected)
        self.assertTrue(all(c == 7 for _, _, c in writes))
        self.assertGreater(nxt, 0)

    def test_pitch_384_wrong_vs_xy_right(self):
        """Simulates OpenGL pitch=384: dest+=skip scatters; xy mapping does not."""
        frame = encode_solid_rect(10, 20, 3, 2, color=7)
        writes, _ = apply_ban_frame(frame, 0)

        pitched = bytearray(384 * 200)
        for x, y, c in writes:
            pitched[y * 384 + x] = c

        self.assertEqual(pitched[20 * 384 + 10], 7)
        self.assertEqual(pitched[21 * 384 + 10], 7)
        self.assertEqual(pitched[20 * 320 + 10], 0)

        wrong = bytearray(384 * 200)
        linear = 20 * SCREEN_WIDTH + 10
        for x, y, c in writes:
            # naive: treat file linear as byte offset into pitched surface
            wrong[linear] = c
            linear += 1
        self.assertNotEqual(wrong[21 * 384 + 10], 7)


if __name__ == "__main__":
    unittest.main()
