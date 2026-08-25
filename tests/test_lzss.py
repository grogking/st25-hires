# SPDX-FileCopyrightText: 2026 grogking
#
# SPDX-License-Identifier: MIT

import unittest

from st_hires.lzss import decode_lzss, encode_lzss_literals, wrap_patch_file


class LzssTests(unittest.TestCase):
    def test_literal_round_trip(self):
        src = bytes(range(256)) * 3 + b"KIRK"
        packed = encode_lzss_literals(src)
        self.assertEqual(decode_lzss(packed, len(src)), src)

    def test_patch_wrapper_size_header(self):
        src = b"hello trek"
        wrapped = wrap_patch_file(src)
        uncmp = int.from_bytes(wrapped[:2], "little")
        self.assertEqual(uncmp, len(src))
        self.assertEqual(decode_lzss(wrapped[2:], uncmp), src)

    def test_rejects_over_64k(self):
        with self.assertRaises(ValueError):
            wrap_patch_file(b"\x00" * 70000)


if __name__ == "__main__":
    unittest.main()
