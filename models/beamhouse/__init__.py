"""Beamhouse project (.bhs) for the stella octangula.

Emits the scene document the Beamhouse visualiser loads: twelve strip
fixtures — one per lamp — with the same wire patch the ``gled2`` project
patches into Art-Net, plus placement overrides that put every lamp exactly
where ``led_profiles.assemblies.stella_octangula`` builds it. The CAD is the
only source of truth; this package projects it.

Coordinates follow the house convention: the CAD's z-up millimetres map to
Beamhouse's y-up metres as (x, y, z)_cad -> (x, z, -y)_cad / 1000, so the
suspension axis stays vertical. Lamp orientations use Beamhouse's three.js
``XYZ`` Euler order to align both the tube axis and the diffuser-facing normal.

    uv run python -c "import models.beamhouse; models.beamhouse.write()"
    uv run check beamhouse
"""

from __future__ import annotations

import json
from math import asin, atan2, degrees
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


def _scene_components(vector) -> tuple[float, float, float]:
    """CAD z-up coordinates mapped to Beamhouse y-up coordinates."""
    return vector.X, vector.Z, -vector.Y


def _cad_to_scene(point) -> list[float]:
    """CAD millimetres, z up, to Beamhouse metres, y up."""
    return [component / 1000 for component in _scene_components(point)]


def _euler_xyz(matrix) -> tuple[float, float, float]:
    """Three.js XYZ Euler angles for a rotation matrix."""
    clamped = min(1.0, max(-1.0, matrix[0][2]))
    if abs(clamped) < 0.9999999:
        return (
            degrees(atan2(-matrix[1][2], matrix[2][2])),
            degrees(asin(clamped)),
            degrees(atan2(-matrix[0][1], matrix[0][0])),
        )
    return degrees(atan2(matrix[2][1], matrix[1][1])), degrees(asin(clamped)), 0.0


def _aim(segment: LampSegment) -> tuple[float, float, float]:
    """Place the original GLB with +X along the lamp and its diffuser outward."""
    direction = (segment.end - segment.start).normalized()
    x_axis = _scene_components(direction)
    y_axis = tuple(-value for value in _scene_components(segment.outward))
    z_axis = _scene_components(segment.outward.cross(direction))
    matrix = tuple(zip(x_axis, y_axis, z_axis))
    return _euler_xyz(matrix)


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
