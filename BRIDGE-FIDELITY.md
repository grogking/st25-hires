# Bridge fidelity (match GOG, one gap at a time)

Working notes for ScummVM `startrek` patches under [`scummvm-patch/`](scummvm-patch/). Apply against upstream ScummVM `engines/startrek/`. Local clone (gitignored): `tools/scummvm`.

## Phase 1 — Idle A/B (code baseline)

| Side | Stars | Speed | Scatter | Gaps |
|------|-------|-------|---------|------|
| GOG (expected) | yes | medium crawl | even | clean recycle |
| Stock ScummVM | **no** | n/a | n/a | blank viewscreen |

**Cause:** [`bridge.cpp`](tools/scummvm/engines/startrek/bridge.cpp) `// TODO: starfield` — `handleBridgeEvents` never calls `drawStarfield` / `updateStarfieldAndShips`. Star math already exists in `space.cpp` (`NUM_STARS` 16, near-clip 50, divisor 150).

**Live check (Windows):** after applying starfield-wire patch, idle bridge, no Tab — four words each side vs GOG.

## UNPROVEN (do not retune blindly)

| Item | Current patch value | How to prove |
|------|---------------------|--------------|
| Bridge forward Z / tick | `Point3(0,0,2)` along view | DOSBox-X break on star tick ADD |
| Turn / pitch scale | deadzone 12px, ~0.004 rad/px/tick | EXE `entcur` path or live break |
| Inertia | none | EXE only |

## Patch order

See [`scummvm-patch/APPLY.md`](scummvm-patch/APPLY.md).

## Hi-res gate

Do **not** start `hires/` overlay work until idle + turn A/B vs GOG passes at 1×. See README “Next engine work”.
