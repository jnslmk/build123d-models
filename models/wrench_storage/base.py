"""Low open tray, hollow Gridfinity feet and bed-rooted handle racks."""

from math import floor, sqrt

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
    Rectangle,
    RectangleRounded,
    Sketch,
    add,
    extrude,
    fillet,
    loft,
    offset,
)

from models.lib.edges import as_part, top_chamfer_tool
from models.lib.gridfinity import (
    BASE_H,
    CORNER_R,
    GRID,
    PAD,
    TOLERANCE,
    gridfinity_foot,
    gridfinity_foot_cavity,
)

from . import config as c
from . import layout as l
from . import profiles as p

IS_ASSEMBLY = False
FOOT_CAVITY_WALL = c.WALL * sqrt(
    2
)  # A 45-degree wall needs this XY offset for 1 mm normal thickness.
PARAMS = c.PARAMS


def footprint(layout: l.Layout, inset: float = 0.0) -> Sketch:
    """Round convex corners without adding material in absent stepped cells."""
    occupied = layout.occupied
    with BuildSketch() as section:
        for column in layout.columns:
            with Locations((column.x, (column.cells - 1) * GRID / 2)):
                Rectangle(GRID, column.cells * GRID)
        convex = []
        for vertex in section.vertices():
            neighbors = sum(
                (
                    floor((vertex.X + dx + GRID / 2) / GRID),
                    floor((vertex.Y + dy + GRID / 2) / GRID),
                )
                in occupied
                for dx in (-0.01, 0.01)
                for dy in (-0.01, 0.01)
            )
            if neighbors == 1:
                convex.append(vertex)
        fillet(convex, CORNER_R + TOLERANCE / 2)
        offset(amount=-TOLERANCE / 2 - inset, mode=Mode.REPLACE)
    return section.sketch


def notch_tool(lane: l.Lane, y: float, station: int, top: float) -> Part:
    """Open notch with a 45-degree lead-in; full-band raw underside sets floor."""
    floor = lane.floor_z(station)
    half = lane.slot_width / 2
    ch = l.SLOT_LEAD
    # Local x is transverse, local y is vertical; extrusion points along -Y.
    plane = Plane(
        origin=(lane.x, y + c.RACK_THICKNESS / 2 + ch, 0),
        x_dir=(1, 0, 0),
        z_dir=(0, -1, 0),
    )
    with BuildPart() as tool:
        with BuildSketch(plane):
            Polygon(
                (-half, floor),
                (half, floor),
                (half, top - ch),
                (half + ch, top),
                (half + ch, top + 1),
                (-half - ch, top + 1),
                (-half - ch, top),
                (-half, top - ch),
                align=None,
            )
        extrude(amount=c.RACK_THICKNESS + 2 * ch)
        # Round the four upright tooth corners with subtractive relief. The
        # straight central slot keeps its measured width; only its front/rear
        # entries widen. This is a notch-specific boolean, not an OCC edge op.
        radius = ch
        for x_sign in (-1, 1):
            for y_sign in (-1, 1):
                x_corner = lane.x + x_sign * half
                y_corner = y + y_sign * c.RACK_THICKNESS / 2
                with BuildSketch(Plane.XY.offset(floor)):
                    with Locations(
                        (x_corner + x_sign * radius / 2, y_corner - y_sign * radius / 2)
                    ):
                        Rectangle(radius, radius)
                    with Locations(
                        (x_corner + x_sign * radius, y_corner - y_sign * radius)
                    ):
                        Circle(radius, mode=Mode.SUBTRACT)
                extrude(amount=top - floor + 1)
    return tool.part


def _rack(column: l.Column, station: int, mask: Part) -> Part:
    y = l.TOOL_START_Y + p.HANDLE_STATIONS[station]
    top = column.rack_top
    with BuildPart() as rack:
        with BuildSketch():
            with Locations((column.x, y)):
                RectangleRounded(PAD, c.RACK_THICKNESS, l.RACK_CORNER_R)
        extrude(amount=top)
        add(mask, mode=Mode.INTERSECT)
        add(
            as_part(
                Pos(column.x, y, 0)
                * top_chamfer_tool(
                    PAD, c.RACK_THICKNESS, l.RACK_CORNER_R, top, l.EDGE_BREAK
                )
            ),
            mode=Mode.SUBTRACT,
        )
        for lane in column.lanes:
            add(notch_tool(lane, y, station, top), mode=Mode.SUBTRACT)
    return rack.part


def create(wrenches_per_column: int | float = c.DEFAULT_WRENCHES_PER_COLUMN) -> Part:
    """One connected bin, foot-down at z=0; no future lid interface."""
    layout = l.arrange(wrenches_per_column)
    occupied = layout.occupied
    cells = sorted(occupied)
    outside = footprint(layout)
    inside = footprint(layout, c.WALL)
    outer_bevel = footprint(layout, l.EDGE_BREAK)
    inner_bevel = footprint(layout, c.WALL - l.EDGE_BREAK)
    feet = gridfinity_foot()
    seams_by_cell = {
        (x, y): (
            (x - 1, y) in occupied,
            (x + 1, y) in occupied,
            (x, y - 1) in occupied,
            (x, y + 1) in occupied,
        )
        for x, y in cells
    }
    cavities = {
        seams: gridfinity_foot_cavity(
            PAD, PAD, FOOT_CAVITY_WALL, l.BED_THICKNESS, seams
        )
        for seams in sorted(set(seams_by_cell.values()))
    }
    # Unhollowed mask clips rack roots to the real tapered foot profile. Above
    # the feet it follows ONLY occupied cells, including the omitted step cell.
    with BuildPart() as mask:
        for x, y in cells:
            add(as_part(Pos(x * GRID, y * GRID, 0) * feet))
        with BuildSketch(Plane.XY.offset(BASE_H)):
            add(outside)
        extrude(amount=max(col.rack_top for col in layout.columns) - BASE_H)

    with BuildPart() as bin_part:
        for x, y in cells:
            add(as_part(Pos(x * GRID, y * GRID, 0) * feet))
        # Ruled outer bevel avoids an OCC chamfer over a stepped perimeter.
        sections = []
        for z, inset in (
            (BASE_H, 0),
            (l.RIM_Z - l.EDGE_BREAK, 0),
            (l.RIM_Z, l.EDGE_BREAK),
        ):
            with BuildSketch(Plane.XY.offset(z)) as section:
                add(outside if inset == 0 else outer_bevel)
            sections.append(section.sketch)
        loft(sections=sections, ruled=True)
        # The main cavity leaves only cell-seam webs at 4.4..5.4 mm, not a
        # long unsupported floor slab. Its mouth is beveled on the inside too.
        sections = []
        for z, inset in (
            (l.SEAT_Z, c.WALL),
            (l.RIM_Z - l.EDGE_BREAK, c.WALL),
            (l.RIM_Z, c.WALL - l.EDGE_BREAK),
            (l.RIM_Z + 1, c.WALL - l.EDGE_BREAK),
        ):
            with BuildSketch(Plane.XY.offset(z)) as section:
                add(inside if inset == c.WALL else inner_bevel)
            sections.append(section.sketch)
        loft(sections=sections, ruled=True, mode=Mode.SUBTRACT)
        for x, y in cells:
            add(
                as_part(Pos(x * GRID, y * GRID, 0) * cavities[seams_by_cell[x, y]]),
                mode=Mode.SUBTRACT,
            )
        for column in layout.columns:
            for station in range(len(p.HANDLE_STATIONS)):
                add(_rack(column, station, mask.part))
    bin_part.part.label = "WORKZONE open wrench bin"
    return bin_part.part


def check():
    """The leaf runs the same permanent physical gate as its package alias."""
    from .checks import run

    return run()
