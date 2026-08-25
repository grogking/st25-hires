# Apply the BAN dest-offset fix

This patch is against **upstream ScummVM** `engines/startrek/` (tested on current master).

If you already have a local startrek fork, apply the same idea even if hunks fail: do **not** `dest += skip` on `lockScreen()->getPixels()`.

```sh
cd /path/to/scummvm
patch -p1 < /path/to/scummvm-patch/0001-startrek-ban-clut8-linear.patch
```

This repo's ScummVM tree is `tools/scummvm` (upstream clone plus local startrek work). From the repo root:

```sh
git -C tools/scummvm apply --verbose ../../scummvm-patch/0001-startrek-ban-clut8-linear.patch
```

On first BAN tick the engine logs:

```
StarTrek lockScreen: WxH pitch=P bpp=B
```

Smoking gun is `pitch != 320` and/or `bpp != 1`. The fix maps BAN linear addresses with `x = linear % 320`, `y = linear / 320` and writes through `Surface::getBasePtr` / `setPixel`. File `skip` values stay in 8-bit-320 space.

Background (`bgPixels`) is still packed 320-wide CLUT8; that pointer math is unchanged.
