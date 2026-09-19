"""Beamhouse project (.bhs) for the stella octangula.

Emits the scene document the Beamhouse visualiser loads: twelve strip
fixtures — one per lamp — with the same wire patch the ``gled2`` project
patches into Art-Net, plus placement overrides that put every lamp exactly
where ``led_profiles.assemblies.stella_octangula`` builds it. The CAD is the
only source of truth; this package projects it.

Coordinates follow the house convention: the CAD's z-up millimetres map to
Beamhouse's y-up metres as (x, y, z)_cad -> (x, z, -y)_cad / 1000, so the
suspension axis stays vertical. Lamp orientations are the two-angle
decomposition Beamhouse's three.js 'XYZ' Euler needs to point a strip's local
+X along its lamp.

    uv run python -c "import models.beamhouse; models.beamhouse.write()"
    uv run check beamhouse
"""

from __future__ import annotations

import json
from math import atan2, degrees, hypot
from pathlib import Path

from models.gled2 import CHANNELS_PER_PIXEL, LEDS_PER_UNIVERSE, PIXELS_PER_LAMP
from models.led_profiles import config as c
from models.led_profiles.assemblies.stella_octangula import (
    LampSegment,
    lamp_segments,
)

LAMP_DEFINITION = "bhs:stella-lamp"

# The reference rig's scene constants (app/src/scene.ts).
DENSITY = 0.32
BEAM_LENGTH_M = 10

# gled's wire space as Beamhouse sees it: Art-Net Port-Address 0 is Beamhouse
# universe 1, and a pixel's first slot is 1 + (led % 170) * 3.
UNIVERSE_OFFSET = 1
SLOTS_PER_UNIVERSE = LEDS_PER_UNIVERSE * CHANNELS_PER_PIXEL


def pitch_mm(length: float = c.LENGTH) -> float:
    """Pixel pitch that spreads PIXELS_PER_LAMP over one lamp."""
    return length / PIXELS_PER_LAMP


def breaks_for(segment_index: int, pixels: int = PIXELS_PER_LAMP) -> list[dict]:
    """A lamp's pixels as contiguous per-universe runs at gled's wire slots.

    Mirrors gled's own split rule (LED n lives at wire LED segment_index *
    PIXELS_PER_LAMP + n, wrapping universes every LEDS_PER_UNIVERSE), so the
    visualiser and gled light the same pixel on the same slot.
    """
    breaks = []
    led = segment_index * pixels
    remaining = pixels
    while remaining:
        in_universe = LEDS_PER_UNIVERSE - led % LEDS_PER_UNIVERSE
        run = min(remaining, in_universe)
        breaks.append(
            {
                "universe": UNIVERSE_OFFSET + led // LEDS_PER_UNIVERSE,
                "address": 1 + (led % LEDS_PER_UNIVERSE) * CHANNELS_PER_PIXEL,
                "footprint": run * CHANNELS_PER_PIXEL,
            }
        )
        led += run
        remaining -= run
    return breaks


def _cad_to_scene(point) -> list[float]:
    """CAD millimetres, z up, to Beamhouse metres, y up."""
    return [point.X / 1000, point.Z / 1000, -point.Y / 1000]


def _aim(segment: LampSegment) -> tuple[float, float, float]:
    """Euler XYZ degrees pointing a fixture's local +X along the lamp."""
    direction = segment.end - segment.start
    dx, dy, dz = direction.X, direction.Y, direction.Z
    return (0.0, degrees(atan2(-dz, dx)), degrees(atan2(dy, hypot(dx, dz))))


def document(length: float = c.LENGTH) -> dict:
    """The whole .bhs document as plain data, ready to serialise."""
    segments = lamp_segments(length)
    fixtures = [
        {
            "id": index + 1,
            "definition": LAMP_DEFINITION,
            "mode": "default",
            "addresses": breaks_for(index),
        }
        for index in range(len(segments))
    ]
    overrides = {
        str(index + 1): {
            "pos": _cad_to_scene((segment.start + segment.end) * 0.5),
            "rot": list(_aim(segment)),
        }
        for index, segment in enumerate(segments)
    }
    return {
        "patch": {"kind": "snapshot", "fixtures": fixtures},
        "definitions": {
            LAMP_DEFINITION: {
                "kind": "strip",
                "pixels": PIXELS_PER_LAMP,
                "pitchMm": pitch_mm(length),
                "channelsPerPixel": CHANNELS_PER_PIXEL,
                "primitive": "Cylinder",
            }
        },
        "fixtures": fixtures,
        "density": DENSITY,
        "beamLength": BEAM_LENGTH_M,
        "overrides": overrides,
        "views": {"iso": {"position": [4.5, 3.5, 4.5], "target": [0, 0, 0]}},
    }


def write(
    path: str | Path = "exports/beamhouse-stella-octangula.bhs",
    length: float = c.LENGTH,
) -> Path:
    """Write the .bhs project, returning the path written."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(document(length), separators=(",", ":")), encoding="utf-8"
    )
    return destination
