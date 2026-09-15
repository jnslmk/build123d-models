"""One-piece thin-wall soldering aid for SP16-compatible and SP17 connectors.

The aid is a single L-profile extrusion. Its 2 mm lower leg prints flat and its
2 mm rear wall is 50% taller than the former 40 mm support. The threaded
connector seats are bosses at the top of that wall, close to its side ends.

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
    Cone,
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
BOSS_WALL = 2.0
TOP_MARGIN = 2.0  # functional edge margin, not a mating fit
HOLE_END_MARGIN = 3.0  # functional edge margin, not a mating fit

SP16_MAJOR_DIAMETER = 16.0  # generic SP16-compatible connector
SP16_PITCH = 1.5
SP17_MAJOR_DIAMETER = 17.0  # WEIPU SP17, per the SP1712 drawing
SP17_PITCH = 1.0
THREAD_CLEARANCE = 0.30  # printed female thread, PETG baseline; tune to connector
THREAD_LENGTH = 8.0
EDGE_FILLET = 0.8
EDGE_CHAMFER = 0.35

MAX_THREAD_MAJOR = max(SP16_MAJOR_DIAMETER, SP17_MAJOR_DIAMETER) + THREAD_CLEARANCE
MAX_BOSS_RADIUS = MAX_THREAD_MAJOR / 2 + BOSS_WALL
HOLE_OFFSET = WIDTH / 2 - MAX_BOSS_RADIUS - HOLE_END_MARGIN
HOLE_SPACING = 2 * HOLE_OFFSET
HOLE_Z = SUPPORT_HEIGHT - MAX_BOSS_RADIUS - TOP_MARGIN
WALL_FRONT_Y = BASE_DEPTH / 2 - WALL_THICKNESS


def _thread_data() -> list[tuple[float, IsoThread, float, float]]:
    """Return centered hole offsets, threads, boss radii and collar lengths."""
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
            rotation=(90, 0, 0),
        )
        result.append((offset, thread, thread.major_diameter / 2 + BOSS_WALL, pitch))
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

        for offset, thread, boss_radius, collar in threads:
            x = WIDTH / 2 + offset
            boss_depth = collar + THREAD_LENGTH
            straight_depth = boss_depth - EDGE_CHAMFER
            with Locations((x, WALL_FRONT_Y, HOLE_Z)):
                Cylinder(
                    boss_radius,
                    straight_depth,
                    rotation=(90, 0, 0),
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                )
            with Locations((x, WALL_FRONT_Y - straight_depth, HOLE_Z)):
                Cone(
                    boss_radius,
                    boss_radius - EDGE_CHAMFER,
                    EDGE_CHAMFER,
                    rotation=(90, 0, 0),
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                )
            with Locations((x, WALL_FRONT_Y, HOLE_Z)):
                Cylinder(
                    thread.min_radius,
                    boss_depth,
                    rotation=(90, 0, 0),
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.SUBTRACT,
                )

    part = aid.part
    for offset, thread, _, collar in threads:
        x = WIDTH / 2 + offset
        part = Part(part.wrapped) + (Pos(x, WALL_FRONT_Y - collar, HOLE_Z) * thread)
    return as_part(Pos(-WIDTH / 2, 0, 0) * part)


__all__ = ["create"]
