# beamhouse — stella octangula project

The [Beamhouse](../../../lighting/beamhouse) `.bhs` scene for the
`led_profiles` stella octangula: twelve strip fixtures — one per 1.5 m lamp —
placed where the assembly builds them, patched at gled's wire addresses so
what gled plays is what the visualiser shows.

## Load

```bash
cd ~/git-projects/lighting/beamhouse && bun run start
# load beamhouse-stella-octangula.bhs from the UI (or a .bhs URL)
```

The scene carries an inline snapshot patch (12 fixtures), one
`bhs:stella-lamp` strip definition (23 px, 65.22 mm pitch, 3 slots/px),
per-fixture placement overrides, and an `iso` camera view. Beamhouse renders
that definition with the original `led_profiles.previz_body` and
`led_profiles.previz_diffuser` GLBs; `Cylinder` is only the missing-asset
fallback.

## Patch

Same wire space as the `gled2` project: lamp `b0` starts at LED 0, lamps run
contiguously (23 px each), and Beamhouse universe = Art-Net Port-Address + 1,
first slot = 1 + (LED mod 170) × 3. Universe 1 holds LEDs 0–169 (into lamp
`o1`), universe 2 the rest; lamps crossing the seam carry two address breaks.

## Coordinates

CAD z-up millimetres map to Beamhouse's y-up metres as
`(x, y, z)_cad → (x, z, -y)_cad / 1000`; the suspension axis stays vertical.
Orientations use the full three.js `XYZ` Euler rotation: local +X follows the
lamp axis and the diffuser follows the CAD assembly's outward face normal.

## Regenerate

```bash
uv run python -c "import models.beamhouse; models.beamhouse.write('<output.bhs>')"
uv run check beamhouse
```

`PIXELS_PER_LAMP` lives in `models.gled2` — both projects share it, change it
there and regenerate both. Lamp axes come from
`led_profiles.assemblies.stella_octangula.lamp_segments`; nothing here
re-derives geometry.
