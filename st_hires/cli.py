# SPDX-FileCopyrightText: 2026 grogking
#
# SPDX-License-Identifier: MIT

"""CLI: extract, to-png, from-png, compress, find-games."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .archive import find_gog_roots, load_archive
from .ban import apply_ban_frame, linear_to_xy
from .bitmap import (
    TrekBitmap,
    bitmap_to_rgba,
    parse_bitmap,
    parse_palette,
    quantize_to_palette,
)
from .lzss import wrap_patch_file

DEFAULT_GAME_DIR = Path("G:/Star Trek")


def _png_mod():
    try:
        from PIL import Image
    except ImportError as exc:
        raise SystemExit("Pillow is required: pip install -r requirements.txt") from exc
    return Image


def cmd_find_games(args: argparse.Namespace) -> int:
    roots = find_gog_roots(Path(args.game_dir))
    if not roots:
        print(f"No DATA.DIR/DATA.001 under {args.game_dir}", file=sys.stderr)
        return 1
    for root in roots:
        print(root)
    return 0


def cmd_extract(args: argparse.Namespace) -> int:
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    roots = find_gog_roots(Path(args.game_dir))
    if not roots:
        print(f"No GOG data under {args.game_dir}", file=sys.stderr)
        return 1
    for root in roots:
        dest = out / root.name
        dest.mkdir(parents=True, exist_ok=True)
        files = load_archive(root)
        (dest / "index.json").write_text(
            json.dumps(sorted(files), indent=2) + "\n", encoding="utf-8"
        )
        for name, blob in files.items():
            (dest / name).write_bytes(blob)
        print(f"{root}: {len(files)} files -> {dest}")
    return 0


def _pick_palette(files: dict[str, bytes], name: str) -> list[tuple[int, int, int]]:
    upper = name.upper()
    if "BRIDGE" in upper or upper.endswith(".SHP") or upper.endswith(".R3S"):
        key = "BRIDGE.PAL" if "BRIDGE.PAL" in files else "palette.pal"
    else:
        key = "PALETTE.PAL" if "PALETTE.PAL" in files else "BRIDGE.PAL"
    for candidate in (key, "PALETTE.PAL", "BRIDGE.PAL"):
        for existing in files:
            if existing.upper() == candidate:
                return parse_palette(files[existing])
    raise FileNotFoundError("no PALETTE.PAL / BRIDGE.PAL in archive")


def cmd_to_png(args: argparse.Namespace) -> int:
    Image = _png_mod()
    src = Path(args.src)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    files = {p.name.upper(): p.read_bytes() for p in src.iterdir() if p.is_file()}
    count = 0
    for name, blob in files.items():
        if not name.endswith((".BMP", ".XOR", ".SHP")):
            continue
        try:
            bmp = parse_bitmap(blob)
            pal = _pick_palette(files, name)
            rgba = bitmap_to_rgba(bmp, pal)
            img = Image.frombytes("RGBA", (bmp.width, bmp.height), rgba)
            img.save(out / f"{name}.png")
            count += 1
        except ValueError:
            continue
    print(f"wrote {count} PNGs to {out}")
    return 0


def cmd_from_png(args: argparse.Namespace) -> int:
    Image = _png_mod()
    png = Image.open(args.png).convert("RGBA")
    like = parse_bitmap(Path(args.like).read_bytes())
    pal = parse_palette(Path(args.palette).read_bytes())
    src_w, src_h = png.size
    if (src_w, src_h) != (like.width, like.height):
        if src_w % like.width or src_h % like.height:
            raise SystemExit(
                f"PNG {src_w}x{src_h} is not an integer multiple of "
                f"{like.width}x{like.height}"
            )
        rgba = png.tobytes()
        # downscale in RGB then quantize
        img = png.resize((like.width, like.height), Image.Resampling.NEAREST)
        rgba = img.tobytes()
        pixels = quantize_to_palette(rgba, like.width, like.height, pal)
    else:
        pixels = quantize_to_palette(png.tobytes(), like.width, like.height, pal)
    out_bmp = TrekBitmap(like.xoffset, like.yoffset, like.width, like.height, pixels)
    Path(args.out).write_bytes(out_bmp.to_bytes())
    print(f"wrote {args.out} ({like.width}x{like.height})")
    return 0


def cmd_compress(args: argparse.Namespace) -> int:
    src = Path(args.src)
    dest = Path(args.out)
    dest.mkdir(parents=True, exist_ok=True)
    n = 0
    for path in src.iterdir():
        if not path.is_file():
            continue
        wrapped = wrap_patch_file(path.read_bytes())
        (dest / path.name).write_bytes(wrapped)
        n += 1
    print(f"compressed {n} files -> {dest} (original EXE patches/ format)")
    return 0


def cmd_ban_preview(args: argparse.Namespace) -> int:
    data = Path(args.ban).read_bytes()
    writes, nxt = apply_ban_frame(data, 0)
    print(f"frame writes={len(writes)} next=0x{nxt:x}")
    if writes:
        x, y, c = writes[0]
        print(f"first pixel ({x},{y}) color {c} linear={y * 320 + x}")
        lx, ly = linear_to_xy(y * 320 + x)
        assert (lx, ly) == (x, y)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="st_hires")
    parser.add_argument("--game-dir", default=str(DEFAULT_GAME_DIR))
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("find-games")
    p.set_defaults(func=cmd_find_games)

    p = sub.add_parser("extract")
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_extract)

    p = sub.add_parser("to-png")
    p.add_argument("src")
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_to_png)

    p = sub.add_parser("from-png")
    p.add_argument("png")
    p.add_argument("--like", required=True, help="original custom BMP to copy offsets from")
    p.add_argument("--palette", required=True)
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_from_png)

    p = sub.add_parser("compress")
    p.add_argument("src")
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_compress)

    p = sub.add_parser("ban-preview")
    p.add_argument("ban")
    p.set_defaults(func=cmd_ban_preview)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
