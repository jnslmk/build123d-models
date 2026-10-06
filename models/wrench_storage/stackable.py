"""Reference-profile hollow base and continuous tall walls for six wrenches.

The low tray remains a separate model. Its photo-qualified rack primitives and
tool poses are reused, clipped to this bin's own unhollowed reference base.
The continuous rim has an explicit foot-bearing shoulder and global tool-access
caps; it is a mating adaptation, not an exact copy of the reference lip.
"""

from math import ceil, floor

from build123d import (
    BuildPart,
    BuildSketch,
    Locations,
    Mode,
    Part,
    Pos,
    Plane,
    Rectangle,
    RectangleRounded,
    Sketch,
    add,
    extrude,
    fillet,
    loft,
    offset,
)

from models.lib import fits
from models.lib.checks import Report
from models.lib.edges import as_part
from models.lib.gridfinity import (
    GRID,
    HEIGHT_UNIT,
    PAD,
    TOLERANCE,
)

from . import base
from . import config as c
from . import layout as l
from . import profiles as p

IS_ASSEMBLY = False
PARAMS = c.PARAMS
WALL = c.WALL
WALL_CORNER_R = 3.75  # Standard convex body corner, after the 0.25 mm setback.
FOOT_C1 = 0.8
FOOT_STRAIGHT = 1.8
FOOT_C3 = 2.15
BASE_H = FOOT_C1 + FOOT_STRAIGHT + FOOT_C3
FOOT_BOTTOM_R = 0.8
FOOT_BAND_R = FOOT_BOTTOM_R + FOOT_C1
FOOT_CORNER_SPACING = GRID - 2 * (WALL_CORNER_R + TOLERANCE / 2)
BASE_BLOCK_TOP = BASE_H + WALL
HOLLOW_SHIFT = 0.4142 * WALL  # Reference's published ultra-light offset.
EDGE_BREAK = l.EDGE_BREAK
MIN_THROAT_CORNER_R = 2 * EDGE_BREAK  # Keep loft corners finite past the body radius.
STANDARD_RIM_WIDTH = WALL_CORNER_R - FOOT_BOTTOM_R  # 2.95 mm foot-bottom inset.
BEARING_WIDTH = WALL  # Nominal landing; its inner edge receives a 0.2 mm bevel.
SHOULDER_INSET = STANDARD_RIM_WIDTH + BEARING_WIDTH
SHOULDER_RISE = SHOULDER_INSET - WALL  # 45-degree support-free inward growth.
LANDING_HEIGHT = 0.6
TOP_TRIM = 0.75  # Reference full-profile trim, not added lip height.
RECEIVER_CLEARANCE = fits.SLIDING  # Sliding fit, PETG baseline, diametral gap.
PASSAGE_CLEARANCE = fits.FREE  # Free fit, PETG baseline, diametral tool gap.
FRONT_THROAT_INSET = PAD / 2 + l.TOOL_START_Y - PASSAGE_CLEARANCE / 2


def stack_pitch(layout: l.Layout) -> float:
    """Actual upper foot-bottom datum, whole 7 mm units with >=3 mm headroom."""
    return ceil(layout.future_cover_ceiling / HEIGHT_UNIT) * HEIGHT_UNIT


def rim_top(layout: l.Layout) -> float:
    """Actual reference-foot receiver height after the full-width top trim."""
    return stack_pitch(layout) + FOOT_C1 + FOOT_STRAIGHT + FOOT_C3 - TOP_TRIM


def back_throat_inset(layout: l.Layout) -> float:
    """Conservative common rear opening; preserve every free-fit tool prism."""
    return min(
        column.cells * GRID
        - GRID / 2
        - TOLERANCE / 2
        - l.TOOL_START_Y
        - max(l.envelope(lane.wrench)[0] for lane in column.lanes)
        - PASSAGE_CLEARANCE / 2
        for column in layout.columns
    )


def wall_outline(
    layout: l.Layout,
    inset: float = 0.0,
    front_extension: float = 0.0,
    back_extension: float = 0.0,
) -> Sketch:
    """Occupied stepped outline with reference convex corners.

    Use the same occupied-column/convex-vertex convention as the low tray,
    independently of its 4 mm corner helper.
    Extending every column's front/rear before rounding yields one smooth
    asymmetric mouth, not six lane notches or a union of cell sockets.
    """
    with BuildSketch() as section:
        for column in layout.columns:
            with Locations(
                (
                    column.x,
                    (column.cells - 1) * GRID / 2
                    + (back_extension - front_extension) / 2,
                )
            ):
                Rectangle(GRID, column.cells * GRID + front_extension + back_extension)
        convex = []
        for vertex in section.vertices():
            y = -GRID / 2 if vertex.Y < -GRID / 2 + 0.01 else vertex.Y - back_extension
            neighbors = sum(
                (
                    floor((vertex.X + dx + GRID / 2) / GRID),
                    floor((y + dy + GRID / 2) / GRID),
                )
                in layout.occupied
                for dx in (-0.01, 0.01)
                for dy in (-0.01, 0.01)
            )
            if neighbors == 1:
                convex.append(vertex)
        fillet(
            convex,
            max(WALL_CORNER_R, inset + MIN_THROAT_CORNER_R) + TOLERANCE / 2,
        )
        offset(amount=-TOLERANCE / 2 - inset, mode=Mode.REPLACE)
    return section.sketch


def _loft(levels: tuple[tuple[float, Sketch], ...]) -> None:
    sections = []
    for z, outline in levels:
        with BuildSketch(Plane.XY.offset(z)) as section:
            add(outline)
        sections.append(section.sketch)
    loft(sections=sections, ruled=True)


def _foot_section(radius: float) -> Sketch:
    """Rounded cell profile; all levels share the 34 mm corner-centre spacing."""
    with BuildSketch() as section:
        RectangleRounded(
            FOOT_CORNER_SPACING + 2 * radius,
            FOOT_CORNER_SPACING + 2 * radius,
            radius,
        )
    return section.sketch


def _foot() -> Part:
    """Clean reference outside: .8 bevel, 1.8 band and 2.15 upper slope."""
    with BuildPart() as foot:
        _loft(
            (
                (0.0, _foot_section(FOOT_BOTTOM_R)),
                (FOOT_C1, _foot_section(FOOT_BAND_R)),
                (FOOT_C1 + FOOT_STRAIGHT, _foot_section(FOOT_BAND_R)),
                (BASE_H, _foot_section(WALL_CORNER_R)),
            )
        )
    return foot.part


def _foot_hollow() -> Part:
    """Reference ultra-light void, including the overlapping upper relief."""
    with BuildPart() as hollow:
        _loft(
            (
                (WALL, _foot_section(FOOT_BOTTOM_R - HOLLOW_SHIFT)),
                (FOOT_C1 + HOLLOW_SHIFT, _foot_section(FOOT_BAND_R - WALL)),
                (
                    FOOT_C1 + FOOT_STRAIGHT + HOLLOW_SHIFT,
                    _foot_section(FOOT_BAND_R - WALL),
                ),
                (BASE_H + HOLLOW_SHIFT, _foot_section(WALL_CORNER_R - WALL)),
            )
        )
        # This larger overlapping relief includes the reference's redundant
        # fourth stage and continues to 6.1642; the raw base ends at 5.75.
        _loft(
            (
                (BASE_H, _foot_section(WALL_CORNER_R - WALL - HOLLOW_SHIFT)),
                (
                    BASE_H + WALL + HOLLOW_SHIFT,
                    _foot_section(WALL_CORNER_R),
                ),
            )
        )
    return hollow.part


def create(wrenches_per_column: int | float = c.DEFAULT_WRENCHES_PER_COLUMN) -> Part:
    """One bed-rooted reference-base bin; unchanged slots/poses, no roof/supports."""
    layout = l.arrange(wrenches_per_column)
    pitch, top = stack_pitch(layout), rim_top(layout)
    shoulder_start = pitch - LANDING_HEIGHT - SHOULDER_RISE
    lower_opening = STANDARD_RIM_WIDTH - RECEIVER_CLEARANCE / 2
    straight_opening = FOOT_C3 - RECEIVER_CLEARANCE / 2
    top_opening = TOP_TRIM - RECEIVER_CLEARANCE / 2
    insets = (
        WALL,
        SHOULDER_INSET,
        SHOULDER_INSET - EDGE_BREAK,
        lower_opening,
        straight_opening,
        top_opening,
        FRONT_THROAT_INSET,
    )
    mouths = {
        inset: wall_outline(
            layout,
            inset,
            max(0.0, inset - FRONT_THROAT_INSET),
            max(0.0, inset - back_throat_inset(layout)),
        )
        for inset in insets
    }
    # Apply the full 45-degree edge break after the rear access cap. Capping
    # an already-beveled nominal inset would leave only a half-width bevel
    # where the longest wrench needs the extra rear clearance.
    bearing_inset = SHOULDER_INSET - EDGE_BREAK
    rear_bearing_inset = min(SHOULDER_INSET, back_throat_inset(layout)) - EDGE_BREAK
    mouths[bearing_inset] = wall_outline(
        layout,
        bearing_inset,
        max(0.0, bearing_inset - FRONT_THROAT_INSET),
        max(0.0, bearing_inset - rear_bearing_inset),
    )
    outside = wall_outline(layout)
    top_outside = wall_outline(layout, EDGE_BREAK)
    # Complete the own-base solids before assembling walls and unchanged racks.
    foot, hollow = _foot(), _foot_hollow()
    with BuildPart() as mask:
        for x, y in sorted(layout.occupied):
            add(as_part(Pos(x * GRID, y * GRID, 0) * foot))
        with BuildSketch(Plane.XY.offset(BASE_H)):
            add(outside)
        extrude(amount=max(column.rack_top for column in layout.columns) - BASE_H)
    with BuildPart() as lower_base:
        for x, y in sorted(layout.occupied):
            add(as_part(Pos(x * GRID, y * GRID, 0) * foot))
        # The reference raw block is externally cleaned to the continuous
        # outline, rather than leaving 42 mm cell squares above the feet.
        with BuildSketch(Plane.XY.offset(BASE_H)):
            add(outside)
        extrude(amount=BASE_BLOCK_TOP - BASE_H)
        for x, y in sorted(layout.occupied):
            add(as_part(Pos(x * GRID, y * GRID, 0) * hollow), mode=Mode.SUBTRACT)
    with BuildPart() as body:
        _loft(
            (
                (BASE_H, outside),
                (top - EDGE_BREAK, outside),
                (top, top_outside),
            )
        )
        with BuildPart(mode=Mode.PRIVATE) as lower_cavity:
            _loft(
                (
                    (BASE_H - 0.05, mouths[WALL]),
                    (shoulder_start, mouths[WALL]),
                    (pitch - LANDING_HEIGHT, mouths[SHOULDER_INSET]),
                    (pitch - EDGE_BREAK, mouths[SHOULDER_INSET]),
                    (pitch, mouths[SHOULDER_INSET - EDGE_BREAK]),
                )
            )
        add(lower_cavity.part, mode=Mode.SUBTRACT)
        # A real horizontal landing at pitch joins the two cavities. It seats
        # foot-bottom material, rather than merely matching the receiver throat.
        with BuildPart(mode=Mode.PRIVATE) as upper_cavity:
            _loft(
                (
                    (pitch, mouths[lower_opening]),
                    (pitch + FOOT_C1, mouths[straight_opening]),
                    (pitch + FOOT_C1 + FOOT_STRAIGHT, mouths[straight_opening]),
                    (
                        pitch
                        + FOOT_C1
                        + FOOT_STRAIGHT
                        + straight_opening
                        - FRONT_THROAT_INSET,
                        mouths[FRONT_THROAT_INSET],
                    ),
                    (top, mouths[top_opening]),
                    (top + 0.1, mouths[top_opening]),
                )
            )
        add(upper_cavity.part, mode=Mode.SUBTRACT)
    with BuildPart() as bin_part:
        add(lower_base.part)
        add(body.part)
        for column in layout.columns:
            for station in range(len(p.HANDLE_STATIONS)):
                add(base._rack(column, station, mask.part))
    bin_part.part.label = "WORKZONE tall lidless stackable wrench bin"
    return bin_part.part


def check() -> Report:
    from .stackable_checks import run

    return run()
