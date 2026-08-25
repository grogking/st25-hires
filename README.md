# Star Trek 25th Anniversary / Judgment Rites hi-res tools

Home for GOG hi-res modding of *Star Trek: 25th Anniversary* and *Judgment Rites*. Host-side toolkit — not CircuitPython, not Adafruit hardware.

GOG data on Windows:

- `G:\Star Trek\Star Trek 25th Anniversary\TREKCD`
- `G:\Star Trek\Star Trek - Judgment Rites\TREK2`

Engine path is **ScummVM `startrek`**, not patching `STARTREK.EXE`. Local fork (if present): `tools/scummvm`.

## Why this exists

The original EXEs are 320×200, 8-bit. `DATA.001` stores uncompressed size as uint16 (~64KB). You cannot drop a 2× PNG into the archive.

Two install targets:

1. **Bake-down** — hi-res PNG → original-size paletted custom BMP → `patches/`
2. **True hi-res** — ScummVM overlay `hires/scale.txt` + `NAME.BMP.png` (`initGraphics(320*scale, 200*scale)`, coords `* scale`). Engine work; **BAN / Enterprise must be correct at 1× first**. Do not mix scale bugs with BAN bugs.

## Confirmed: original `patches/`

`STARTREK.EXE` at `0x36932` contains `patches/%s.%s` then `Not found`, after `open data.001`. Drop files next to `DATA.DIR` as `patches/IKIRK.BMP` (basename + extension). `TREKJR.EXE` had no `patches` string.

Original EXE wants **LZSS-wrapped** files (`uint16 size` + payload). ScummVM's `patches/` path loads **raw uncompressed** files.

## BAN dest-offset (the in-flight engine bug)

`renderBan` treated `lockScreenPixels() + offset` as a 320-byte CLUT8 stride. OpenGL surfaces may have pitch padding or 32-bit pixels, which scatters console lights even when the frame chain advances. File skip values are 320-linear; do not `dest += skip` on the backend surface. Map `x = linear % 320`, `y = linear / 320`, write via `getBasePtr` / `setPixel`. Background bitmap stays 320-wide pointer math.

Patch: [scummvm-patch/APPLY.md](scummvm-patch/APPLY.md)

On the bridge, watch the first BAN tick for:

```
StarTrek lockScreen: 320x200 pitch=P bpp=B
```

Smoking gun is `pitch != 320` and/or `bpp != 1`.

## CLI

```sh
pip install -r requirements.txt
python -m st_hires find-games --game-dir "G:/Star Trek"
python -m st_hires extract --game-dir "G:/Star Trek" --out extracted
python -m st_hires to-png extracted/TREKCD --out png
python -m st_hires from-png hires/BRIDGE.BMP.png --like extracted/TREKCD/BRIDGE.BMP --palette extracted/TREKCD/PALETTE.PAL --out raw/BRIDGE.BMP
python -m st_hires compress raw --out "G:/Star Trek/Star Trek 25th Anniversary/TREKCD/patches"
```

`from-png` accepts an integer-multiple PNG (2×/4×) and nearest-neighbor downscales to the original BMP size, then quantizes to the game palette (index 0 = transparent).

The Python `st_hires` CLI is the portable copy of the node-format lib and DOSBox bake-down (7938/7938 round-trip, HD bridge in-game).

## Tests

```sh
python -m unittest discover -s tests -v
```

## Next engine work

After BAN is correct at 1×: Enterprise / R3 mode 2 ([st25sprites.neocities.org](https://st25sprites.neocities.org) R3S notes). Then `hires/` overlay.
