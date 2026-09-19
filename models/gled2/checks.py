"""Assertions for the gled2 installation SVG.

The SVG is a projection of the CAD and a patch for gled at once, so the checks
hold both halves: the lamp set is the assembly's, and the address patch stays
contiguous and inside gled's two-universe split rule. The file itself must
re-parse with one Hjson/JSON ``<desc>`` per lamp, because that is exactly what
gled's strict parser will do on load.

    uv run check gled2
"""

from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET

from models.gled2 import (
    LEDS_PER_UNIVERSE,
    PIXELS_PER_LAMP,
    VERTEX_GROUPS,
    lamp_parameters,
    svg_text,
)
from models.led_profiles.assemblies.stella_octangula import lamp_segments
from models.lib.checks import Report

SVG_NS = "{http://www.w3.org/2000/svg}"


def run() -> Report:
    r = Report()
    segments = lamp_segments()

    r.section("lamp set")
    r.check(len(segments) == 12, "twelve lamps", f"{len(segments)} lamps")
    r.check(
        len({segment.name for segment in segments}) == 12,
        "wiring labels unique",
        ", ".join(sorted(s.name for s in segments)),
    )

    r.section("patch")
    starts = [
        lamp_parameters(segment, index)["start"]
        for index, segment in enumerate(segments)
    ]
    r.check(
        starts == [index * PIXELS_PER_LAMP for index in range(12)],
        "starts contiguous at PIXELS_PER_LAMP stride",
        f"starts {starts[0]}..{starts[-1]}",
    )
    total = len(segments) * PIXELS_PER_LAMP
    r.check(
        total <= 2 * LEDS_PER_UNIVERSE,
        "patch fits gled's two universes",
        f"{total} LEDs, {LEDS_PER_UNIVERSE} per universe",
    )

    r.section("groups")
    known = {"base", "offset", *VERTEX_GROUPS}
    named = {
        group
        for index, segment in enumerate(segments)
        for group in lamp_parameters(segment, index)["groups"]
    }
    r.check(
        named <= known,
        "every named group is defined",
        f"unknown: {sorted(named - known)}"
        if named - known
        else f"{len(named)} groups used",
    )

    r.section("svg")
    root = ET.fromstring(svg_text())
    paths = root.findall(f".//{SVG_NS}path")
    r.check(len(paths) == 12, "twelve lamp paths", f"{len(paths)} paths")
    seen: set[str] = set()
    declared = 0
    for path in paths:
        lamp_id = path.get("id", "")
        descriptions = [child for child in path if child.tag == f"{SVG_NS}desc"]
        if not lamp_id or lamp_id in seen or len(descriptions) != 1:
            r.check(
                False, f"lamp {lamp_id or '?'}: unique id + one desc", "malformed path"
            )
            continue
        seen.add(lamp_id)
        try:
            parameters = json.loads(descriptions[0].text or "")
            declared += parameters["count"]
        except (json.JSONDecodeError, KeyError, TypeError) as error:
            r.check(False, f"lamp {lamp_id}: desc parses", str(error))
            continue
    r.check(
        declared == 12 * PIXELS_PER_LAMP,
        "declared LEDs match the patch",
        f"{declared} LEDs in the file",
    )
    return r


def main() -> None:
    r = run()
    print(r.render())
    sys.exit(1 if r.failures else 0)


if __name__ == "__main__":
    main()
