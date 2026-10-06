"""Lower-foot Gridfinity socket cutters and removable print supports.

Both helpers are centred in XY in socket-down print coordinates. The cutter
starts just below the bed; supports sit on z=0 with their two tabs overlapping
the roof. Geometry and process candidates are extracted unchanged from the
accepted drill-storage bin lid, not newly calibrated PETG support settings.
"""

from math import floor

from build123d import (
    Align,
    Box,
    BuildPart,
    BuildSketch,
    Locations,
    Mode,
    Part,
    Plane,
    RectangleRounded,
    extrude,
    loft,
)

from models.lib import fits
from models.lib.gridfinity import CORNER_R, FOOT_C1, FOOT_C3, FOOT_STRAIGHT

SOCKET_LEAD_IN = 0.3  # functional entry funnel for a Gridfinity foot
LATTICE_PITCH = 5.0
LATTICE_RIB = 0.8
# Support process candidates, not mating fits or calibrated PETG defaults.
# Retain the existing nominal gap to isolate attachment/coverage changes;
# effective separation must still be checked in the sliced PETG layer paths.
LATTICE_GAP = 0.2
SUPPORT_XY_GAP = 0.6  # per side: extrusion/first-layer separation from socket walls
SUPPORT_TAB_WIDTH = 0.4  # one nominal bead along a straight rail; verify in slicer
SUPPORT_TAB_DEPTH = 0.8  # across rail, retaining only 0.64 mm² total neck per cell
SUPPORT_ROOF_OVERLAP = 0.02  # minimal positive weld, not the fracture section
STACK_FIT = fits.SLIDING  # PETG sliding fit, diametral, between foot and socket


def socket_tool(cell_w: float, cell_d: float, depth: float) -> Part:
    """Origin-centred cutter for a foot's lower bevel and straight receiver."""
    bottom_inset = FOOT_C1 + FOOT_C3
    mid_inset = FOOT_C3
    with BuildPart(mode=Mode.PRIVATE) as tool:
        profiles = []
        for z, inset, lead in (
            (-0.05, mid_inset, SOCKET_LEAD_IN),
            (SOCKET_LEAD_IN, mid_inset, 0),
            (FOOT_STRAIGHT, mid_inset, 0),
            (depth, bottom_inset, 0),
        ):
            with BuildSketch(Plane.XY.offset(z)) as section:
                RectangleRounded(
                    cell_w - 2 * inset + STACK_FIT + 2 * lead,
                    cell_d - 2 * inset + STACK_FIT + 2 * lead,
                    CORNER_R - inset + STACK_FIT / 2 + lead,
                )
            profiles.append(section.sketch)
        loft(sections=profiles, ruled=True)
    return tool.part


def socket_support(cell_w: float, cell_d: float, depth: float) -> Part:
    """Bed-seated rail/lattice with two accessible gap-spanning roof tabs."""
    inset = FOOT_C1 + FOOT_C3
    # The ceiling is the narrowest socket section. Offset its whole contour,
    # including the corner radius, so no lower wall/bevel can touch the support.
    rail_w = cell_w - 2 * inset + STACK_FIT - 2 * SUPPORT_XY_GAP
    rail_d = cell_d - 2 * inset + STACK_FIT - 2 * SUPPORT_XY_GAP
    rail_r = CORNER_R - inset + STACK_FIT / 2 - SUPPORT_XY_GAP
    support_h = depth - LATTICE_GAP
    nx = max(1, floor(((cell_w - 2 * inset) / 2 - 1) / LATTICE_PITCH))
    ny = max(1, floor(((cell_d - 2 * inset) / 2 - 1) / LATTICE_PITCH))
    with BuildPart(mode=Mode.PRIVATE) as support:
        with BuildSketch():
            RectangleRounded(rail_w, rail_d, rail_r)
            RectangleRounded(
                rail_w - 2 * LATTICE_RIB,
                rail_d - 2 * LATTICE_RIB,
                rail_r - LATTICE_RIB,
                mode=Mode.SUBTRACT,
            )
        extrude(amount=support_h)
        # Extend every rib into the rail. Clipping the combined field prevents
        # rectangular rib ends protruding into half-cell rounded corners.
        for ix in range(-nx, nx + 1):
            with Locations((ix * LATTICE_PITCH, 0, 0)):
                Box(
                    LATTICE_RIB,
                    rail_d,
                    support_h,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                )
        for iy in range(-ny, ny + 1):
            with Locations((0, iy * LATTICE_PITCH, 0)):
                Box(
                    rail_w,
                    LATTICE_RIB,
                    support_h,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                )
        with BuildSketch():
            RectangleRounded(rail_w, rail_d, rail_r)
        extrude(amount=support_h, mode=Mode.INTERSECT)
        # Opposite short-side straight rail midpoints: substantial roof above,
        # direct access through the socket below. Cut tabs and peel inward rather
        # than levering on the finished lip. Rotate for a wide/short half cell.
        along_y = rail_d >= rail_w
        tab_offset = (rail_d if along_y else rail_w) / 2 - LATTICE_RIB / 2
        for sign in (-1, 1):
            with Locations(
                (
                    0 if along_y else sign * tab_offset,
                    sign * tab_offset if along_y else 0,
                    support_h,
                )
            ):
                Box(
                    SUPPORT_TAB_WIDTH if along_y else SUPPORT_TAB_DEPTH,
                    SUPPORT_TAB_DEPTH if along_y else SUPPORT_TAB_WIDTH,
                    LATTICE_GAP + SUPPORT_ROOF_OVERLAP,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                )
    return support.part
