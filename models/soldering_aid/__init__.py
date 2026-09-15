"""One-piece thin-wall soldering aid for SP16-compatible and SP17 connectors.

The aid is a single L-profile extrusion. Its 2 mm lower leg prints flat and its
2 mm rear wall is 50% taller than the former 40 mm support. The connector seats
remain on the lower leg, now with printed female threads directly through it.

WEIPU documents SP17 as M17 x 1. The similarly named SP16 parts found in
supplier listings are not an official WEIPU SP16 family; this model therefore
uses the common generic SP16-compatible M16 x 1.5 specification on the left.
Confirm that pitch against the connector in hand before printing.
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
    extrude,
)

from models.lib.edges import as_part, chamfer_edge, fillet_edge

WIDTH = 70.0
BASE_DEPTH = 44.0
WALL_THICKNESS = 2.0
SUPPORT_HEIGHT = 60.0  # 50% taller than the former 40 mm rear wall
HOLE_SPACING = 36.0

SP16_MAJOR_DIAMETER = 16.0  # generic SP16-compatible connector
SP16_PITCH = 1.5
SP17_MAJOR_DIAMETER = 17.0  # WEIPU SP17, per the SP1712 drawing
SP17_PITCH = 1.0
THREAD_CLEARANCE = 0.30  # printed female thread, PETG baseline; tune to connector
THREAD_LENGTH = WALL_THICKNESS
EDGE_FILLET = 0.8
EDGE_CHAMFER = 0.35

HOLE_OFFSET = HOLE_SPACING / 2
HOLE_Z = 0.0
HOLE_Y = 0.0


def _thread_data() -> list[tuple[float, IsoThread]]:
    """Return centered hole offsets and their printed female threads."""
    result = []
    for offset, diameter, pitch in (
        (-HOLE_OFFSET, SP16_MAJOR_DIAMETER, SP16_PITCH),
        (HOLE_OFFSET, SP17_MAJOR_DIAMETER, SP17_PITCH),
    ):
        thread = IsoThread(
            major_diameter=diameter + THREAD_CLEARANCE,
            pitch=pitch,
            length=THREAD_LENGTH,
            external=False,
            end_finishes=("fade", "chamfer"),
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
                    thread.min_radius,
                    THREAD_LENGTH,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.SUBTRACT,
                )

    part = aid.part
    for offset, thread in threads:
        x = WIDTH / 2 + offset
        part = Part(part.wrapped) + (Pos(x, HOLE_Y, HOLE_Z) * thread)
    return as_part(Pos(-WIDTH / 2, 0, 0) * part)


__all__ = ["create"]
