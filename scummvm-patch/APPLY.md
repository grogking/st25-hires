# Apply ScummVM startrek patches

Patches are against **upstream ScummVM** `engines/startrek/`.

```sh
cd /path/to/scummvm
patch -p1 < /path/to/scummvm-patch/0001-startrek-ban-clut8-linear.patch
patch -p1 < /path/to/scummvm-patch/0002-startrek-bridge-fidelity.patch
```

Or from this repo root when `tools/scummvm` is an upstream clone:

```sh
git -C tools/scummvm apply --verbose ../../scummvm-patch/0001-startrek-ban-clut8-linear.patch
git -C tools/scummvm apply --verbose ../../scummvm-patch/0002-startrek-bridge-fidelity.patch
```

## What each patch does

| Patch | Purpose |
|-------|---------|
| `0001` | BAN dest-offset: map packed 320-linear addresses through `Surface::getBasePtr` / `writeScreenIndexed` so OpenGL pitch/bpp does not scatter console lights |
| `0002` | Bridge fidelity: wire starfield on tick, Tab/`entcur` flight cursor, `.R3S` billboard battle stub, music loop / same-file load fix, cursor replace for Tab |

## After apply (Windows)

1. Rebuild `scummvm.exe`
2. Idle bridge A/B vs GOG (no Tab) — see [`BRIDGE-FIDELITY.md`](../BRIDGE-FIDELITY.md)
3. Do **not** retune UNPROVEN Z-step / turn scale without an EXE break

On first BAN tick the engine logs:

```
StarTrek lockScreen: WxH pitch=P bpp=B
```

Smoking gun is `pitch != 320` and/or `bpp != 1`.
