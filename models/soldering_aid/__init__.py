"""One-piece thin-wall soldering aid for two circular connectors.

The aid is a single L-profile extrusion. Its 2 mm rear wall prints flat with the
connector holes facing the heatbed, while the 2 mm lower leg rises as a side
support. The connector seats are direct threaded holes near the wall's top edge.

Calipers measured a 17 mm major diameter on the left connector and 20 mm on the
right. The pitches remain the existing unverified 1.5 mm and 1.0 mm settings;
confirm each pitch against the connector before printing.
"""

from __future__ import annotations

from bd_warehouse.thread import IsoThread
from build123d import (
    Align,
    Axis,
    BuildPart,
    BuildSketch,
    Cylinder,
    Locations,
    Mode,
    Part,
    Plane,
    Polygon,
    Pos,
    Rotation,
    add,
    extrude,
)

from models.lib.edges import as_part, chamfer_edge, fillet_edge, reseat_on_bed

WIDTH = 70.0
BASE_DEPTH = 44.0
WALL_THICKNESS = 2.0
SUPPORT_HEIGHT = 60.0  # 50% taller than the former 40 mm rear wall
HOLE_SPACING = 36.0

LEFT_THREAD_MAJOR_D = 17.0  # caliper measurement, left connector
LEFT_THREAD_PITCH = 1.5  # unverified; measure before printing
RIGHT_THREAD_MAJOR_D = 20.0  # caliper measurement, right connector
RIGHT_THREAD_PITCH = 1.0  # unverified; measure before printing
THREAD_CLEARANCE = 0.30  # printed female thread, PETG baseline; tune to connector
THREAD_LENGTH = WALL_THICKNESS
EDGE_FILLET = 0.8
EDGE_CHAMFER = 0.35
HOLE_TOP_MARGIN = 8.5  # functional edge margin, matching the side-margin scale

LEFT_THREAD_RADIUS = (LEFT_THREAD_MAJOR_D + THREAD_CLEARANCE) / 2
RIGHT_THREAD_RADIUS = (RIGHT_THREAD_MAJOR_D + THREAD_CLEARANCE) / 2
WALL_FRONT_Y = BASE_DEPTH / 2 - WALL_THICKNESS
MAX_THREAD_DIAMETER = max(LEFT_THREAD_MAJOR_D, RIGHT_THREAD_MAJOR_D) + THREAD_CLEARANCE
HOLE_OFFSETS = (
    (LEFT_THREAD_RADIUS - RIGHT_THREAD_RADIUS - HOLE_SPACING) / 2,
    (LEFT_THREAD_RADIUS - RIGHT_THREAD_RADIUS + HOLE_SPACING) / 2,
)  # center the unequal bores between equal side margins
SIDE_MARGIN_TOLERANCE = 1.0  # functional edge-margin difference, not a fit
HOLE_Z = SUPPORT_HEIGHT - MAX_THREAD_DIAMETER / 2 - HOLE_TOP_MARGIN
HOLE_Y = WALL_FRONT_Y


def _thread_data() -> list[tuple[float, IsoThread]]:
    """Return centered hole offsets and internal thread inserts."""
    result = []
    for offset, diameter, pitch in zip(
        HOLE_OFFSETS,
        (LEFT_THREAD_MAJOR_D, RIGHT_THREAD_MAJOR_D),
        (LEFT_THREAD_PITCH, RIGHT_THREAD_PITCH),
        strict=True,
    ):
        thread = IsoThread(
            major_diameter=diameter + THREAD_CLEARANCE,
            pitch=pitch,
            length=THREAD_LENGTH,
            external=False,
            end_finishes=("fade", "fade"),
            rotation=(-90, 0, 0),
        )
        result.append((offset, thread))
    return result


def create() -> Part:
    """Return the one-piece L-profile connector aid in print pose."""
    threads = _thread_data()
    with BuildPart() as aid:
        with BuildSketch(Plane.YZ) as profile:
            Polygon(
                (-BASE_DEPTH / 2, 0),
                (BASE_DEPTH / 2, 0),
                (BASE_DEPTH / 2, SUPPORT_HEIGHT),
                (BASE_DEPTH / 2 - WALL_THICKNESS, SUPPORT_HEIGHT),
                (BASE_DEPTH / 2 - WALL_THICKNESS, WALL_THICKNESS),
                (-BASE_DEPTH / 2, WALL_THICKNESS),
                align=None,
            )
        extrude(profile.sketch, amount=WIDTH)

        chamfer_edge(aid, aid.faces().sort_by(Axis.Z).first.edges(), EDGE_CHAMFER)
        chamfer_edge(aid, aid.faces().sort_by(Axis.Z).last.edges(), EDGE_CHAMFER)
        chamfer_edge(
            aid,
            [
                edge
                for edge in aid.edges()
                if abs(edge.center().Z - WALL_THICKNESS) < 0.01 and edge.length > 10.0
            ],
            EDGE_CHAMFER,
        )
        fillet_edge(aid, aid.edges().filter_by(Axis.Z), EDGE_FILLET)

        for offset, thread in threads:
            x = WIDTH / 2 + offset
            with Locations((x, HOLE_Y, HOLE_Z)):
                Cylinder(
                    thread.major_diameter / 2,
                    THREAD_LENGTH,
                    rotation=(-90, 0, 0),
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.SUBTRACT,
                )
            with Locations((x, HOLE_Y, HOLE_Z)):
                add(thread)

    centered = as_part(Pos(-WIDTH / 2, 0, 0) * aid.part)
    return reseat_on_bed(as_part(Rotation(-90, 0, 0) * centered))


__all__ = ["create"]
