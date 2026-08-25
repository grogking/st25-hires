# SPDX-FileCopyrightText: 2026 grogking
#
# SPDX-License-Identifier: MIT

"""LZSS used by DATA.001 (N=0x1000, F=0x10, threshold 3)."""

from __future__ import annotations

N = 0x1000
THRESHOLD = 3


def decode_lzss(data: bytes, uncompressed_size: int) -> bytes:
    hist = bytearray(N)
    bufpos = 0
    out = bytearray()
    i = 0
    length = len(data)

    while i < length and len(out) < uncompressed_size:
        flagbyte = data[i]
        i += 1
        for bit in range(8):
            if len(out) >= uncompressed_size or i >= length:
                break
            if (flagbyte & (1 << bit)) == 0:
                if i + 1 >= length:
                    break
                offsetlen = data[i] | (data[i + 1] << 8)
                i += 2
                run = (offsetlen & 0xF) + THRESHOLD
                offset = (bufpos - (offsetlen >> 4)) & (N - 1)
                for j in range(run):
                    tempa = hist[(offset + j) & (N - 1)]
                    out.append(tempa)
                    hist[bufpos] = tempa
                    bufpos = (bufpos + 1) & (N - 1)
                    if len(out) >= uncompressed_size:
                        break
            else:
                tempa = data[i]
                i += 1
                out.append(tempa)
                hist[bufpos] = tempa
                bufpos = (bufpos + 1) & (N - 1)

    if len(out) != uncompressed_size:
        raise ValueError(
            f"LZSS size mismatch: expected {uncompressed_size}, got {len(out)}"
        )
    return bytes(out)


def encode_lzss_literals(data: bytes) -> bytes:
    """Valid LZSS: every byte is a literal. Good enough for patches/ drop-in files."""
    out = bytearray()
    i = 0
    while i < len(data):
        chunk = data[i : i + 8]
        flag = 0
        for j in range(len(chunk)):
            flag |= 1 << j
        out.append(flag)
        out.extend(chunk)
        i += 8
    return bytes(out)


def wrap_patch_file(uncompressed: bytes) -> bytes:
    """Original EXE patches/%s.%s format: uint16 LE size + LZSS payload."""
    if len(uncompressed) > 0xFFFF:
        raise ValueError(
            f"File is {len(uncompressed)} bytes; original patches cap at 65535"
        )
    payload = encode_lzss_literals(uncompressed)
    return len(uncompressed).to_bytes(2, "little") + payload
