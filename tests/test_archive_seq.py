# SPDX-FileCopyrightText: 2026 grogking
#
# SPDX-License-Identifier: MIT

import tempfile
import unittest
from pathlib import Path

from st_hires.archive import (
    load_named_file,
    parse_dir,
    sequential_data001_offset,
)
from st_hires.lzss import encode_lzss_literals


def _wrap_data001(uncompressed: bytes) -> bytes:
    payload = encode_lzss_literals(uncompressed)
    return (
        len(uncompressed).to_bytes(2, "little")
        + len(payload).to_bytes(2, "little")
        + payload
    )


def _dir_entry(name8: bytes, ext3: bytes, offset24: int) -> bytes:
    assert len(name8) == 8 and len(ext3) == 3
    return name8 + ext3 + offset24.to_bytes(3, "little")


class SequentialArchiveTests(unittest.TestCase):
    def test_run_table_adds_strides(self):
        # start at 0x100, then +0x10, +0x20
        run = bytes([0x00, 0x01, 0x00, 0x10, 0x00, 0x20, 0x00])
        self.assertEqual(sequential_data001_offset(run, 0, 0), 0x100)
        self.assertEqual(sequential_data001_offset(run, 0, 1), 0x110)
        self.assertEqual(sequential_data001_offset(run, 0, 2), 0x130)

    def test_load_named_sequential_and_single(self):
        file_a = b"ALPHA-SPRITE"
        file_b = b"BETA-SPRITE!!"
        rec_a = _wrap_data001(file_a)
        rec_b = _wrap_data001(file_b)
        if len(rec_a) % 2:
            rec_a += b"\x00"
        data_001 = rec_a + rec_b

        run = (
            (0).to_bytes(3, "little")
            + len(rec_a).to_bytes(2, "little")
        )

        # ENT33.R3S sequential, count=2, DATA.RUN at 0 (high bit + count in byte 2)
        seq_off = 0x800000 | (2 << 16) | 0
        # STARS.SHP single file stored after the sequential records
        stars = _wrap_data001(b"STARFRAME")
        stars_off = len(data_001)
        data_001 = data_001 + stars

        dir_bytes = (
            _dir_entry(b"ENT33\x00\x00\x00", b"R3S", seq_off)
            + _dir_entry(b"STARS\x00\x00\x00", b"SHP", stars_off)
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "DATA.DIR").write_bytes(dir_bytes)
            (root / "DATA.001").write_bytes(data_001)
            (root / "DATA.RUN").write_bytes(run)

            entries = parse_dir(dir_bytes)
            self.assertEqual(entries[0].file_count, 2)
            self.assertEqual(entries[0].offset, 0)
            self.assertEqual(entries[1].file_count, 1)

            self.assertEqual(load_named_file(root, "ent33.r3s", 0), file_a)
            self.assertEqual(load_named_file(root, "ENT33.R3S", 1), file_b)
            self.assertEqual(load_named_file(root, "STARS.SHP"), b"STARFRAME")
            with self.assertRaises(IndexError):
                load_named_file(root, "STARS.SHP", 1)


if __name__ == "__main__":
    unittest.main()
