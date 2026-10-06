"""One-piece PETG lift-off cover, with removable lower-foot receiver supports.

Use coordinates retain the accepted bin's occupied cells and common tool end.
The socket-down print pose reflects Y; ``seated`` applies the exact inverse.
Support release and real-tool fit remain printer/physical-trial questions.
"""

from math import ceil

from build123d import (
    Axis,
    BuildPart,
    BuildSketch,
    Locations,
    Mode,
    Part,
    Plane,
    Pos,
    Rectangle,
    RectangleRounded,
    Rotation,
    Sketch,
    add,
    loft,
)

from models.lib import fits
from models.lib.checks import Report
from models.lib.edges import as_part
from models.lib.gridfinity import FOOT_C1, FOOT_STRAIGHT, GRID, HEIGHT_UNIT, PAD
from models.lib.gridfinity_socket import socket_support, socket_tool

from . import base
from . import config as c
from . import layout as l
from . import profiles as p
from .corners import passage_corner_tools

IS_ASSEMBLY = False
PARAMS = [
    *c.PARAMS,
    {
        "name": "support",
        "label": "Built-in removable supports",
        "type": "boolean",
        "default": True,
    },
]

BODY_WALL = c.WALL
ROOF_THICKNESS = c.WALL
SKIRT_WALL = 1.2  # Three nominal 0.4 mm PETG extrusion widths.
SKIRT_ENGAGEMENT = 3.0
PLUG_FIT = fits.SLIDING  # Sliding fit, PETG baseline, TOTAL diametral clearance.
SKIRT_OUTER_INSET = c.WALL + PLUG_FIT / 2
SKIRT_INNER_INSET = SKIRT_OUTER_INSET + SKIRT_WALL
SHOULDER_RISE = SKIRT_INNER_INSET - BODY_WALL  # 45-degree inner transition.
EDGE_BREAK = l.EDGE_BREAK
SKIRT_LEAD_IN = EDGE_BREAK  # Both edges leave 0.8 mm at the entering tip.
SOCKET_DEPTH = FOOT_C1 + FOOT_STRAIGHT
RACK_CLEARANCE = PLUG_FIT / 2  # Sliding fit, PETG baseline, radial rack allowance.
END_CLEARANCE = PLUG_FIT / 2  # Sliding fit, PETG baseline, per-side tool passage.
RACK_CAP_RISE = l.RACK_CORNER_R + RACK_CLEARANCE + BODY_WALL  # Nominal 45° X retreat.


def socket_floor_z(layout: l.Layout) -> float:
    """Smallest whole-7-mm stack datum retaining roof and cover headroom."""
    return HEIGHT_UNIT * ceil(
        (layout.future_cover_ceiling + ROOF_THICKNESS) / HEIGHT_UNIT
    )


def socket_top_z(layout: l.Layout) -> float:
    return socket_floor_z(layout) + SOCKET_DEPTH


def ceiling_z(layout: l.Layout) -> float:
    return socket_floor_z(layout) - ROOF_THICKNESS


def print_location(layout: l.Layout):
    """Canonical use to socket-down print: (x, y, z) -> (x, -y, top-z)."""
    return Pos(0, 0, socket_top_z(layout)) * Rotation(180, 0, 0)


def use_location(layout: l.Layout):
    """Exact inverse; never relocate a stepped layout by its bounding box."""
    return Rotation(180, 0, 0) * Pos(0, 0, -socket_top_z(layout))


def _sections(levels: tuple[tuple[float, float], ...], outlines: dict[float, Sketch]):
    sections = []
    for z, inset in levels:
        with BuildSketch(Plane.XY.offset(z)) as section:
            add(outlines[inset])
        sections.append(section.sketch)
    return sections


def rack_cap_z(column: l.Column) -> float:
    """Retreat into the actual body cavity, never stop in the inner shoulder."""
    return max(
        column.rack_top + RACK_CLEARANCE + RACK_CAP_RISE,
        l.RIM_Z + SHOULDER_RISE + EDGE_BREAK,
    )


def rack_passage_tool(layout: l.Layout) -> Part:
    """Clear frozen full-width rack ends without enlarging the bin footprint.

    Each relief interrupts the locating skirt only at its rack band. The
    remaining skirt carries the same 3 mm engagement; the cover remains one
    solid above the racks. A ruled cap relieves the horizontal roof edge.
    """
    with BuildPart() as reliefs:
        for column in layout.columns:
            for distance in p.HANDLE_STATIONS:
                sections = []
                # Taper the entire X reach back inside the 1 mm body wall.
                # A mere 0.2 mm all-axis shrink would still cap outside the
                # shell, leaving a square external roof edge. This X taper
                # is exactly 45 degrees; its Y taper is gentler.
                for z, x_shrink, y_shrink in (
                    (l.RIM_Z - SKIRT_ENGAGEMENT - 0.05, -EDGE_BREAK, -EDGE_BREAK),
                    (l.RIM_Z - SKIRT_ENGAGEMENT, -EDGE_BREAK, -EDGE_BREAK),
                    (l.RIM_Z - SKIRT_ENGAGEMENT + EDGE_BREAK, 0.0, 0.0),
                    (column.rack_top + RACK_CLEARANCE, 0.0, 0.0),
                    (
                        rack_cap_z(column),
                        RACK_CAP_RISE,
                        EDGE_BREAK,
                    ),
                ):
                    with BuildSketch(Plane.XY.offset(z)) as section:
                        with Locations((column.x, l.TOOL_START_Y + distance)):
                            RectangleRounded(
                                PAD
                                + 2 * (l.RACK_CORNER_R + RACK_CLEARANCE)
                                - 2 * x_shrink,
                                c.RACK_THICKNESS + 2 * RACK_CLEARANCE - 2 * y_shrink,
                                l.RACK_CORNER_R + RACK_CLEARANCE - y_shrink,
                            )
                    sections.append(section.sketch)
                loft(sections=sections, ruled=True)
    return reliefs.part


def end_relief_span(column: l.Column) -> tuple[float, float]:
    """Merge the whole column's end passage; never leave sub-bead lane necks."""
    return (
        min(lane.x - lane.wrench.head_thickness / 2 for lane in column.lanes)
        - END_CLEARANCE,
        max(lane.x + lane.wrench.head_thickness / 2 for lane in column.lanes)
        + END_CLEARANCE,
    )


def _end_reliefs(layout: l.Layout) -> Part:
    """Remove only the common-end skirt/shoulder intrusion during loaded lift.

    The outer 1 mm wall/flat rim stays intact. Separate per-lane cuts would
    leave 0.18 mm tongues, so each column uses one merged open-bottom passage.
    Its upper end merges into the existing 45-degree shoulder cavity.
    """
    y_outer = -GRID / 2 + (GRID - PAD) / 2 + BODY_WALL
    y_inner = -GRID / 2 + (GRID - PAD) / 2 + SKIRT_INNER_INSET + END_CLEARANCE
    with BuildPart() as reliefs:
        for column in layout.columns:
            left, right = end_relief_span(column)
            sections = []
            for z, flare in (
                (l.RIM_Z - SKIRT_ENGAGEMENT - 0.05, EDGE_BREAK),
                (l.RIM_Z - SKIRT_ENGAGEMENT, EDGE_BREAK),
                (l.RIM_Z - SKIRT_ENGAGEMENT + EDGE_BREAK, 0.0),
                (l.RIM_Z + SHOULDER_RISE + 0.05, 0.0),
            ):
                with BuildSketch(Plane.XY.offset(z)) as section:
                    with Locations(((left + right) / 2, (y_outer + y_inner) / 2)):
                        Rectangle(right - left + 2 * flare, y_inner - y_outer)
                sections.append(section.sketch)
            loft(sections=sections, ruled=True)
    return reliefs.part


def _finished(layout: l.Layout) -> Part:
    """Build a joined shoulder/skirt in use pose, then cut printed receivers."""
    top = socket_top_z(layout)
    tip = l.RIM_Z - SKIRT_ENGAGEMENT
    outer_levels = (
        (l.RIM_Z, EDGE_BREAK),
        (l.RIM_Z + EDGE_BREAK, 0.0),
        (top - EDGE_BREAK, 0.0),
        (top, EDGE_BREAK),
    )
    skirt_levels = (
        (tip, SKIRT_OUTER_INSET + SKIRT_LEAD_IN),
        (tip + SKIRT_LEAD_IN, SKIRT_OUTER_INSET),
        (l.RIM_Z, SKIRT_OUTER_INSET),
    )
    cavity_levels = (
        (tip - 0.05, SKIRT_INNER_INSET - SKIRT_LEAD_IN),
        (tip, SKIRT_INNER_INSET - SKIRT_LEAD_IN),
        (tip + SKIRT_LEAD_IN, SKIRT_INNER_INSET),
        (l.RIM_Z, SKIRT_INNER_INSET),
        (l.RIM_Z + SHOULDER_RISE, BODY_WALL),
        (ceiling_z(layout), BODY_WALL),
    )
    # Generate profiles and shared tools before a live builder: no auto-add
    # duplicates, and one socket prototype regardless of occupied-cell count.
    outlines = {
        inset: base.footprint(layout, inset)
        for inset in sorted(
            {i for _, i in (*outer_levels, *skirt_levels, *cavity_levels)}
        )
    }
    cutter = socket_tool(PAD, PAD, SOCKET_DEPTH)
    reliefs = rack_passage_tool(layout)
    end_reliefs = _end_reliefs(layout)
    with BuildPart() as body:
        loft(sections=_sections(outer_levels, outlines), ruled=True)
        loft(sections=_sections(skirt_levels, outlines), ruled=True)
        loft(
            sections=_sections(cavity_levels, outlines), ruled=True, mode=Mode.SUBTRACT
        )
        add(reliefs, mode=Mode.SUBTRACT)
        add(end_reliefs, mode=Mode.SUBTRACT)
    # Capture original upright edges before any rounding changes topology.
    # Rack caps, shoulder, and mouth retain their existing lead geometry;
    # each corner tool has its own local conical endpoint lead-outs.
    half_band = (c.RACK_THICKNESS + PLUG_FIT) / 2
    passage_corners = [
        edge
        for edge in body.part.edges().filter_by(Axis.Z)
        if any(
            abs(abs(edge.center().Y - (l.TOOL_START_Y + distance)) - half_band) < 1e-6
            for distance in p.HANDLE_STATIONS
        )
        or (
            edge.center().Y < -GRID / 2 + SKIRT_INNER_INSET + 1
            and any(
                abs(edge.center().X - side) < 1e-6
                for column in layout.columns
                for side in end_relief_span(column)
            )
        )
    ]
    corner_tools = passage_corner_tools(body.part, passage_corners, EDGE_BREAK)
    with BuildPart() as rounded:
        add(body.part)
        add(corner_tools, mode=Mode.SUBTRACT)
    printed_body = as_part(print_location(layout) * rounded.part)
    cutters = [
        as_part(Pos(x * GRID, -y * GRID, 0) * cutter)
        for x, y in sorted(layout.occupied)
    ]
    with BuildPart() as finished:
        add(printed_body)
        add(cutters, mode=Mode.SUBTRACT)
    return finished.part


def create(
    wrenches_per_column: int | float = c.DEFAULT_WRENCHES_PER_COLUMN,
    support: bool = True,
) -> Part:
    """Printable lid on z=0, socket mouths down, skirt up; no glue assembly."""
    layout = l.arrange(wrenches_per_column)
    clean = _finished(layout)
    if support:
        prototype = socket_support(PAD, PAD, SOCKET_DEPTH)
        supports = [
            as_part(Pos(x * GRID, -y * GRID, 0) * prototype)
            for x, y in sorted(layout.occupied)
        ]
        with BuildPart() as supported:
            add(clean)
            add(supports)
        part = supported.part
    else:
        part = clean
    part.label = "WORKZONE removable stackable wrench lid"
    return part


def seated(
    wrenches_per_column: int | float = c.DEFAULT_WRENCHES_PER_COLUMN,
) -> Part:
    """Finished lid at the original bin XY occupancy, shoulder at its 14 mm rim."""
    layout = l.arrange(wrenches_per_column)
    part = as_part(use_location(layout) * _finished(layout))
    part.label = "WORKZONE wrench lid (closed use pose, supports removed)"
    return part


def check() -> Report:
    from .lid_checks import run

    return run()
