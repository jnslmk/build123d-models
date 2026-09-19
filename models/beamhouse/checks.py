"""Assertions for the beamhouse .bhs project.

The document must satisfy every rule Beamhouse's strict loader (app/src/bhs.ts)
enforces — top-level keys, required scene properties, definition and fixture
shapes — because that is what will parse it. On top of that the patch must tile
the wire slots without gaps or overlaps (the visualiser and gled have to light
the same pixel), and the overrides' rotations must align both a fixture's +X
axis along its lamp and the original GLB's diffuser toward the CAD face normal.

    uv run check beamhouse
"""

from __future__ import annotations

import json
import sys
from math import cos, radians, sin

from models.beamhouse import (
    CHANNELS_PER_PIXEL,
    LAMP_DEFINITION,
    PIXELS_PER_LAMP,
    SLOTS_PER_UNIVERSE,
    breaks_for,
    document,
    pitch_mm,
)
from models.led_profiles.assemblies.stella_octangula import lamp_segments
from models.lib.checks import Report

KNOWN_TOP_LEVEL = {
    "patch",
    "definitions",
    "fixtures",
    "overrides",
    "density",
    "beamLength",
    "views",
}


def run() -> Report:
    r = Report()
    doc = document()
    segments = lamp_segments()

    r.section("document shape")
    r.check(set(doc) <= KNOWN_TOP_LEVEL, "top-level keys known", f"{sorted(doc)}")
    r.check(0 <= doc["density"] <= 1, "density in range", str(doc["density"]))
    r.check(1 <= doc["beamLength"] <= 40, "beamLength in range", str(doc["beamLength"]))
    r.check(doc["patch"]["kind"] == "snapshot", "patch is an inline snapshot", "")
    r.check(json.loads(json.dumps(doc)) == doc, "document is JSON-round-trippable", "")

    r.section("definition")
    definition = doc["definitions"][LAMP_DEFINITION]
    r.check(definition["kind"] == "strip", "definition is a strip", "")
    r.check(
        definition["pixels"] == PIXELS_PER_LAMP,
        "pixel count",
        str(definition["pixels"]),
    )
    r.check(
        abs(definition["pitchMm"] - pitch_mm()) < 1e-9 and definition["pitchMm"] > 0,
        "pitch spreads the pixels over one lamp",
        f"{definition['pitchMm']:.2f} mm",
    )
    r.check(
        definition["channelsPerPixel"] == CHANNELS_PER_PIXEL,
        "three slots per pixel",
        "",
    )

    r.section("patch tiling")
    covered: list[tuple[int, int]] = []
    for fixture_index, fixture in enumerate(doc["fixtures"]):
        runs = [
            break_["footprint"] // CHANNELS_PER_PIXEL for break_ in fixture["addresses"]
        ]
        r.check(
            sum(runs) == PIXELS_PER_LAMP,
            f"fixture {fixture['id']} covers its pixels",
            "",
        )
        for break_ in fixture["addresses"]:
            start = (break_["universe"] - 1) * SLOTS_PER_UNIVERSE + break_["address"]
            covered.append((start, start + break_["footprint"]))
    covered.sort()
    r.check(covered[0][0] == 1, "patch starts at slot 1", "")
    gaps = [
        (prev_end, next_start)
        for (_, prev_end), (next_start, _) in zip(covered, covered[1:])
        if next_start != prev_end
    ]
    r.check(not gaps, "slots contiguous, no gaps or overlaps", f"{len(covered)} runs")

    r.section("overrides")
    r.check(
        set(doc["overrides"]) == {str(fixture["id"]) for fixture in doc["fixtures"]},
        "one placement per fixture",
        f"{len(doc['overrides'])} placements",
    )
    for fixture_index, (fixture, segment) in enumerate(zip(doc["fixtures"], segments)):
        placement = doc["overrides"][str(fixture["id"])]
        pos, (rx, ry, rz) = placement["pos"], placement["rot"]
        in_range = (
            all(abs(value) < 1e6 for value in pos)
            and max(abs(rx), abs(ry), abs(rz)) <= 360.0
        )
        r.check(
            len(pos) == 3 and in_range,
            f"fixture {fixture['id']} placement finite",
            f"pos {pos}",
        )
        direction = segment.end - segment.start
        norm = direction.length
        rx_rad, ry_rad, rz_rad = radians(rx), radians(ry), radians(rz)
        cx, sx = cos(rx_rad), sin(rx_rad)
        cy, sy = cos(ry_rad), sin(ry_rad)
        cz, sz = cos(rz_rad), sin(rz_rad)
        rotation = (
            (cy * cz, -cy * sz, sy),
            (cx * sz + sx * sy * cz, cx * cz - sx * sy * sz, -sx * cy),
            (sx * sz - cx * sy * cz, sx * cz + cx * sy * sz, cx * cy),
        )
        aimed = tuple(rotation[axis][0] * norm for axis in range(3))
        actual = (direction.X, direction.Z, -direction.Y)
        direction_error = max(abs(a - b) for a, b in zip(aimed, actual))
        r.check(
            direction_error < 1e-6 * max(norm, 1.0),
            f"fixture {fixture['id']} rot points +X along the lamp",
            f"max component error {direction_error:.2e} mm",
        )
        diffuser = tuple(-rotation[axis][1] for axis in range(3))
        outward = (
            segment.outward.X,
            segment.outward.Z,
            -segment.outward.Y,
        )
        outward_error = max(abs(a - b) for a, b in zip(diffuser, outward))
        r.check(
            outward_error < 1e-6,
            f"fixture {fixture['id']} diffuser faces outward",
            f"max component error {outward_error:.2e}",
        )
        r.check(
            fixture["addresses"] == breaks_for(fixture_index),
            f"fixture {fixture['id']} ({segment.name}) breaks match gled's wire space",
            "",
        )
    return r


def main() -> None:
    r = run()
    print(r.render())
    sys.exit(1 if r.failures else 0)


if __name__ == "__main__":
    main()
