"""Matching 1×2 BITS cover: translucent PETG, pillow down and mouth up.

The original short BITS cover's bore, cap, eased detent and 24 mm height are
extended by one Gridfinity cell. BITS reads across the long +X wall in use
pose. The blind engraving retains the inherited 0.45 mm backing allowance;
its glyph edges and the detent's tip-flat transitions are functional edges.
"""

from __future__ import annotations

from build123d import (
    Axis,
    BuildPart,
    BuildSketch,
    FontStyle,
    Locations,
    Mode,
    Part,
    Plane,
    RectangleRounded,
    Text,
    add,
    extrude,
    loft,
)

from models.lib.gridfinity import CORNER_R
from models.drill_storage.box import (
    CAP_FILLET,
    CAP_H,
    COVER_SEAT_CH,
    INNER_R,
    MOUTH_CH,
    SNAP_BACK,
    SNAP_LEAD_IN,
    SNAP_TIP_FLAT,
    SNAP_Z,
    TOP_FILLET,
)
from models.drill_storage.hex import config as h
from models.drill_storage.hex.cover import label_fit
from models.lib.checks import Report
from models.lib.edges import bottom_chamfer_tool, fillet_edge, reseat_on_bed

from . import config as c

IS_ASSEMBLY = False
PARAMS = []


def _snap_bead() -> Part:
    """Extend the original eased BITS detent without shifting its ramp roots."""
    # Buried overlap is a boolean-fuse allowance, not additional snap reach.
    # Only the outer boundary enters the wall: the inward ramp ends stay at
    # exactly zero reach, preserving the original insertion and removal profile.
    overlap = 0.01
    reach = h.cover_snap_protrusion("bits")
    with BuildPart() as bead:
        sections = []
        for z, protrusion in (
            (SNAP_Z - SNAP_LEAD_IN, 0.0),
            (SNAP_Z - SNAP_TIP_FLAT / 2, reach),
            (SNAP_Z + SNAP_TIP_FLAT / 2, reach),
            (SNAP_Z + SNAP_BACK, 0.0),
        ):
            with BuildSketch(Plane.XY.offset(z)) as section:
                RectangleRounded(
                    c.COVER_INNER_X + 2 * overlap,
                    c.COVER_INNER_Y + 2 * overlap,
                    INNER_R + overlap,
                )
                RectangleRounded(
                    c.COVER_INNER_X - 2 * protrusion,
                    c.COVER_INNER_Y - 2 * protrusion,
                    INNER_R - protrusion,
                    mode=Mode.SUBTRACT,
                )
            sections.append(section.sketch)
        loft(sections=sections, ruled=True)
    return bead.part


def _mouth_tool() -> Part:
    """Rounded-rectangle lead-in that starts on the actual uniform bore wall."""
    with BuildPart() as tool:
        with BuildSketch() as opening:
            RectangleRounded(
                c.COVER_INNER_X + 2 * MOUTH_CH,
                c.COVER_INNER_Y + 2 * MOUTH_CH,
                INNER_R + MOUTH_CH,
            )
        with BuildSketch(Plane.XY.offset(MOUTH_CH)) as bore:
            RectangleRounded(c.COVER_INNER_X, c.COVER_INNER_Y, INNER_R)
        loft(sections=[opening.sketch, bore.sketch], ruled=True)
    return tool.part


def label_tool() -> Part:
    """Return the exact blind BITS engraving tool, readable in cover use pose."""
    size, label_z, _horizontal = label_fit(c.COVER_H, "BITS")
    # Reuse the family's size cap and vertical band, but measure the actual
    # bold face rather than trusting its regular-font metrics or advance width.
    with BuildSketch() as probe:
        Text("BITS", font_size=size, font_style=FontStyle.BOLD)
    bounds = probe.sketch.bounding_box()
    flat_width = c.COVER_Y - 2 * CORNER_R
    flat_height = c.COVER_H - TOP_FILLET - 1.0
    size *= min(
        1.0,
        h.MARGIN * flat_width / bounds.size.X,
        h.MARGIN * flat_height / bounds.size.Y,
    )
    with BuildSketch() as glyph:
        Text("BITS", font_size=size, font_style=FontStyle.BOLD)
    center = glyph.sketch.bounding_box().center()
    wall = Plane(
        origin=(c.COVER_X / 2, 0, label_z),
        x_dir=(0, 1, 0),
        z_dir=(1, 0, 0),
    )
    with BuildPart() as tool:
        with BuildSketch(wall):
            with Locations((-center.X, -center.Y)):
                add(glyph.sketch)
        extrude(amount=-h.LABEL_DEPTH)
    return tool.part


def create_use_pose() -> Part:
    """Return the complete cover with its mouth at z=0 and cap facing +Z."""
    # Standalone builders must finish before the cover builder becomes active;
    # otherwise a helper can auto-add an unplaced copy into the cover.
    bead = _snap_bead()
    mouth = _mouth_tool()
    outer_mouth = bottom_chamfer_tool(
        c.COVER_X, c.COVER_Y, CORNER_R, 0.0, COVER_SEAT_CH
    )
    engraving = label_tool()

    with BuildPart() as cover:
        with BuildSketch():
            RectangleRounded(c.COVER_X, c.COVER_Y, CORNER_R)
        extrude(amount=c.COVER_H)
        pillow = cover.edges().filter_by_position(Axis.Z, c.COVER_H, c.COVER_H)
        if not pillow or not fillet_edge(cover, pillow, TOP_FILLET):
            raise RuntimeError("cannot round the BITS cover's pillow top")
        add(outer_mouth, mode=Mode.SUBTRACT)

        with BuildSketch():
            RectangleRounded(c.COVER_INNER_X, c.COVER_INNER_Y, INNER_R)
        extrude(amount=c.COVER_H - CAP_H, mode=Mode.SUBTRACT)
        ceiling_z = c.COVER_H - CAP_H
        ceiling = cover.edges().filter_by_position(Axis.Z, ceiling_z, ceiling_z)
        if not ceiling or not fillet_edge(cover, ceiling, CAP_FILLET):
            raise RuntimeError("cannot soften the BITS cover's inner ceiling")

        add(mouth, mode=Mode.SUBTRACT)
        add(bead)
        # Keep this cut identical to label_tool(): blind glyph floors preserve
        # the accepted backing, and the letter boundaries remain intentional.
        add(engraving, mode=Mode.SUBTRACT)

    result = cover.part
    result.label = "cover_bits_double"
    result.color = h.COVER_COLOR
    return result


def create() -> Part:
    """Return the support-free PETG cover pillow-down on the z=0 print bed."""
    return reseat_on_bed(create_use_pose(), flip=True)


def check() -> Report:
    """Run the cover's physical geometry gate without building on import."""
    from . import cover_checks

    return cover_checks.run()
