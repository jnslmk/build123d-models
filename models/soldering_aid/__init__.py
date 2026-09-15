"""One-piece L-shaped soldering aid for SP16 and SP17 threaded connectors.

The two panel-mount threads are intentionally different: SP16 is M16 x 1 and
SP17 is M17 x 1. The aid is a single L-profile extrusion: its broad lower leg
prints flat and the rear leg stops the held connectors from sliding away.

Thread dimensions are based on the connector-family naming and the SP17
manufacturer drawing: the SP17 panel cutout is Ø17 with a 15.6 mm anti-rotation
flat and its mounting thread is M17 x 1. SP16 follows the corresponding M16 x 1
panel thread used by the SP16 family. Verify the exact vendor variant before
printing, because third-party SP connectors are not dimensionally identical.
"""

from __future__ import annotations

from bd_warehouse.thread import IsoThread
from build123d import (
    BuildPart,
    BuildSketch,
    Circle,
    Locations,
    Mode,
    Part,
    Plane,
    Polygon,
    Pos,
    extrude,
)

from models.lib.edges import as_part

WIDTH = 70.0
PLATE_DEPTH = 40.0
PLATE_THICKNESS = 8.0
SUPPORT_HEIGHT = PLATE_DEPTH
THREAD_PITCH = 1.0
THREAD_CLEARANCE = 0.30  # printed female thread, PETG baseline; tune to connector
THREAD_LENGTH = 6.5
THREAD_COLLAR = THREAD_PITCH  # plain lead-in before the printed thread
HOLE_SPACING = 36.0


def create() -> Part:
    """Return the one-piece L-profile connector aid in print pose."""
    threads = [
        (
            x,
            diameter,
            IsoThread(
                major_diameter=diameter + THREAD_CLEARANCE,
                pitch=THREAD_PITCH,
                length=THREAD_LENGTH,
                external=False,
                end_finishes=("fade", "fade"),
            ),
        )
        for x, diameter in ((-HOLE_SPACING / 2, 16.0), (HOLE_SPACING / 2, 17.0))
    ]
    rear = PLATE_DEPTH / 2
    with BuildPart() as aid:
        with BuildSketch(Plane.YZ):
            Polygon(
                (-rear, 0),
                (rear, 0),
                (rear, SUPPORT_HEIGHT),
                (rear - PLATE_THICKNESS, SUPPORT_HEIGHT),
                (rear - PLATE_THICKNESS, PLATE_THICKNESS),
                (-rear, PLATE_THICKNESS),
                align=None,
            )
        extrude(amount=WIDTH)
        for x, _, thread in threads:
            with BuildSketch() as sketch:
                with Locations((WIDTH / 2 + x, 0)):
                    Circle(thread.min_radius)
            extrude(sketch.sketch, amount=PLATE_THICKNESS, mode=Mode.SUBTRACT)

    part = aid.part
    for x, _, thread in threads:
        # Internal thread roots overlap the wall. Rewrapping avoids the
        # Solid-plus-thread overload returning a ShapeList on the second bore.
        part = Part(part.wrapped) + (Pos(WIDTH / 2 + x, 0, THREAD_COLLAR) * thread)
    return as_part(Pos(-WIDTH / 2, 0, 0) * part)


__all__ = ["create"]
