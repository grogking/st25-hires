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

## Godot 4 host (`godot/`)

Personal runtime wrapper for the owner's GOG copy. **Do not put `TREKCD`, `DATA.*`, VOC, BMP, SHP, or R3S files in git.** The project opens without them and plays the opening flyby with obvious placeholder cards.

### Open / Play

1. Install [Godot 4.3+](https://godotengine.org/download) (developed against 4.5).
2. Import `godot/project.godot`.
3. Point at GOG data (directory that contains `DATA.DIR`, `DATA.001`, and `DATA.RUN`):

```sh
# Windows cmd
set ST25_GAME_DIR=G:\star trek\Star Trek 25th Anniversary\TREKCD

# PowerShell
$env:ST25_GAME_DIR="G:\star trek\Star Trek 25th Anniversary\TREKCD"
```

Or copy `godot/st25.cfg.example` to `godot/st25.cfg` and set `game_dir=...`, or set **Project Settings → st25/game_dir**. Command line: `godot --path godot -- --game-dir "G:/star trek/Star Trek 25th Anniversary/TREKCD"`.

4. Press Play. Native composite is **320×200** nearest-neighbor, stretched to a 4:3 window (`canvas_items`, not `viewport`, so a later scaler shader can hook the blit). Tick/sim is ~18.2 Hz.

R to restart the flyby.

### What this slice draws (GOG, not ScummVM)

Starfield → side-on Enterprise crossing a large red planet (full frame, no grey subtitle bar) → ship leaves. Title/credits are skipped. If `STARS.SHP`, `PLANET.SHP`, `BRIDGE.PAL`, and `ENT##.R3S` are in the archive they are used; otherwise colored placeholders.

Ships and the planet are **Sprite3D billboards** in an orthographic 3D view (1 unit = 1 native pixel). There is no Enterprise mesh. That is the original engine's pseudo-3D model and the setup later space combat can share. A pure 2D blit would match this intro equally well; 3D is here for depth and camera, not for polygonal ships.

R3S view pick: `ENT{00,11,...,66}.R3S` is the yaw band; sequential `fileIndex` is elevation. The flyby prefers an equatorial side-on (`ENT33` / elevation ~3) by picking a wide sprite on that ring. Palette is `BRIDGE.PAL` (index 0 transparent). Format notes: [R3S](https://st25sprites.neocities.org/R3Sfiles), [SHP](https://st25sprites.neocities.org/SHPfiles).

### Python extras for the same formats

```sh
python -m st_hires list-files --game-dir "G:/star trek/Star Trek 25th Anniversary/TREKCD"
python -m st_hires dump-file ENT33.R3S --index 3 --game-dir "G:/star trek/Star Trek 25th Anniversary/TREKCD" --out /tmp/ent33.r3s
```

`dump-file` writes decompressed bytes locally; do not commit them.

## Tests

```sh
python -m unittest discover -s tests -v
```

## Next engine work

After BAN is correct at 1×: Enterprise / R3 mode 2 ([st25sprites.neocities.org](https://st25sprites.neocities.org) R3S notes). Then `hires/` overlay.
