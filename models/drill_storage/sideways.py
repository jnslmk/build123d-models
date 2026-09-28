"""Foot-down horizontal drill guides and their tool layout.

The rear ASA guide supports the shanks along Y. The PETG side-opening cover
owns the forward bed and feet, and slides on the guide's short dovetail rail.
The frozen X/Z layouts reserve every tool's full outside envelope.
"""

from build123d import (
    Align,
    Box,
    BuildPart,
    BuildSketch,
    Compound,
    Cone,
    Cylinder,
    FontStyle,
    Locations,
    Mode,
    Plane,
    Polygon,
    Pos,
    RectangleRounded,
    Rotation,
    Text,
    add,
    extrude,
    loft,
)
from models.lib.edges import as_part, top_chamfer_tool
from . import config as c
from .box import (
    BASE_H,
    CORNER_R,
    GRID,
    HEIGHT_UNIT,
    PAD,
    add_stacking_lip,
    cut_stacking_socket,
    gridfinity_foot,
)
from .sets import DrillSet, StepDrill
from .tools import STEEL, create_drill, create_hex_tool, create_step_drill

# Frozen cross-sections solved against every tool's full outside envelope, with
# 1.5 mm side margins, 2 mm vertical margins, and >=1 mm between reserved
# circles. The rear ASA guide cuts only the shank clearance, leaving more wall.
WOOD_XZ = {
    "2": (3.10, 31.70),
    "2.5": (-8.78, 7.95),
    "3": (-17.45, 31.20),
    "3.5": (-17.20, 11.79),
    "4": (13.25, 30.70),
    "5": (16.45, 20.67),
    "6": (-1.38, 19.49),
    "7": (5.58, 14.91),
    "8": (-2.49, 10.70),
    "9": (14.45, 11.20),
    "10": (6.64, 24.96),
    "CSK": (-10.85, 17.25),
}
METAL_XZ = {
    "1": (18.05, 17.83),
    "1.5": (-11.06, 31.95),
    "2": (17.65, 31.70),
    "2.5": (-17.70, 7.95),
    "3": (11.58, 31.20),
    "4": (-3.92, 30.61),
    "5": (16.45, 9.20),
    "6": (-15.95, 29.70),
    "8": (14.95, 24.86),
    "10": (4.26, 27.70),
    "TAP": (8.66, 15.38),
    "STEP": (-8.63, 17.06),
}

# The guide end is deliberately closed: a drill seats against an ASA back wall.
BACK_WALL = 2.0
GUIDE_DEPTH = 21.0
BED_THICKNESS = 1.6
EDGE_CHAMFER = 0.4
GUIDE_TOP_CHAMFER = 0.2
FRONT_CORNER_R = 0.25

RAIL_X = 4.0
RAIL_START = 26.0  # relative to the full holder's rear
RAIL_END = 40.0
RAIL_TOP = BASE_H + BED_THICKNESS + 1.5

LABEL_SIZE = 6.0  # bold capitals have ~4.5 mm actual glyph height
LABEL_DEPTH = 0.5  # stays within the 1 mm PETG cover wall
TOOL_LABEL_SIZE = 4.2  # bold digits render just over 3 mm tall
TOOL_LABEL_DEPTH = 0.8  # leaves 1.2 mm of the ASA guide's 2 mm back wall
TOOL_LABEL_MARGIN = 0.4  # flat rear face ends at PAD/2 - CORNER_R


def stacking_receiver(y: float, top_z: float):
    """Full-foot socket ring; its host's intact roof forms the socket floor."""
    with BuildPart() as receiver:
        add_stacking_lip(top_z + BASE_H)
        cut_stacking_socket(top_z + BASE_H)
    return as_part(Pos(0, y, 0) * receiver.part)


def engrave_set_name(label: str, plane: Plane) -> None:
    """Cut readable, bold lettering into an outward-facing solid wall."""
    with BuildSketch(plane) as lettering:
        Text(label.upper(), font_size=LABEL_SIZE, font_style=FontStyle.BOLD)
    extrude(to_extrude=lettering.sketch, amount=-LABEL_DEPTH, mode=Mode.SUBTRACT)


def tool_map_glyphs(drills: DrillSet):
    """Position each size against its guide on the solid rear-face map."""
    _cells, positions = layout_for(drills)
    flat_half = PAD / 2 - CORNER_R - TOOL_LABEL_MARGIN
    for key, (hole_x, z) in positions.items():
        with BuildSketch() as lettering:
            Text(key, font_size=TOOL_LABEL_SIZE, font_style=FontStyle.BOLD)
        glyph = lettering.sketch
        bounds = glyph.bounding_box()
        # METAL 1.5 otherwise touches the adjacent 6 label after the 6 is
        # clamped away from the rounded corner.
        shift = 1.3 if drills.name == "metal" and key == "1.5" else 0.0
        x = min(
            flat_half - bounds.max.X, max(-flat_half - bounds.min.X, hole_x + shift)
        )
        yield key, x, z, glyph


def engrave_tool_map(rear: float, glyphs) -> None:
    """Cut sizes into the rear face, leaving the crowded guide mouths intact."""
    plane = Plane(origin=(0, rear, 0), x_dir=(1, 0, 0), z_dir=(0, -1, 0))
    for _key, x, z, glyph in glyphs:
        extrude(
            to_extrude=plane.location * Pos(x, z, 0) * glyph,
            amount=-TOOL_LABEL_DEPTH,
            mode=Mode.SUBTRACT,
        )


def layout_for(drills: DrillSet) -> tuple[int, dict[str, tuple[float, float]]]:
    """Use 1x3 for wood, 1x4 for the 132 mm metal bit; both pack at 5U."""
    if drills.name == "wood":
        return 3, WOOD_XZ
    if drills.name == "metal":
        return 4, METAL_XZ
    raise ValueError(f"no horizontal holder layout for {drills.name}")


def _cover_rail(rear: float):
    """A low, printable dovetail above the rear foot, clear of both tool sets."""
    with BuildPart() as rail:
        with BuildSketch(Plane.XZ.offset(-(rear + RAIL_END))):
            Polygon(
                (RAIL_X - 1.0, BASE_H + BED_THICKNESS),
                (RAIL_X + 1.0, BASE_H + BED_THICKNESS),
                (RAIL_X + 1.6, RAIL_TOP - 0.6),
                (RAIL_X + 1.6, RAIL_TOP),
                (RAIL_X - 1.6, RAIL_TOP),
                (RAIL_X - 1.6, RAIL_TOP - 0.6),
                align=None,
            )
        extrude(amount=RAIL_END - RAIL_START)
    return rail.part


def _cut_guide(x: float, z: float, radius: float, rear: float) -> None:
    """Cut a horizontal blind bore and its side-facing mouth lead-in."""
    with Locations((x, rear + BACK_WALL + GUIDE_DEPTH / 2, z)):
        Cylinder(radius, GUIDE_DEPTH + 0.1, rotation=(90, 0, 0), mode=Mode.SUBTRACT)
    with Locations((x, rear + BACK_WALL + GUIDE_DEPTH - EDGE_CHAMFER / 2, z)):
        Cone(
            radius + EDGE_CHAMFER,
            radius,
            EDGE_CHAMFER,
            rotation=(90, 0, 0),
            mode=Mode.SUBTRACT,
        )


def _guide_block(rear: float, height: float):
    """Foot-matched rear corners and tighter, intact bore-mouth corners."""
    length = BACK_WALL + GUIDE_DEPTH
    sections = []
    for z, inset in (
        (BASE_H, 0.0),
        (height - GUIDE_TOP_CHAMFER, 0.0),
        (height, GUIDE_TOP_CHAMFER),
    ):
        with BuildSketch(Plane.XY.offset(z)) as profile:
            with Locations((0, rear + length / 2)):
                RectangleRounded(PAD - 2 * inset, length - 2 * inset, CORNER_R - inset)
            with Locations((0, rear + length - 2)):
                RectangleRounded(PAD - 2 * inset, 4 - 2 * inset, FRONT_CORNER_R - inset)
        sections.append(profile.sketch)
    with BuildPart() as guide:
        loft(sections=sections, ruled=True)
    return guide.part


def create_base_for(drills: DrillSet):
    """Print just the rear ASA guide and its single Gridfinity foot."""
    cells, positions = layout_for(drills)
    length = cells * GRID - (GRID - PAD)
    height = 5 * HEIGHT_UNIT
    rear = -length / 2
    glyphs = tuple(tool_map_glyphs(drills))
    foot_y = rear + PAD / 2
    with BuildPart() as holder:
        add(as_part(Pos(0, foot_y, 0) * gridfinity_foot()))
        with BuildSketch(Plane.XY.offset(BASE_H)):
            with Locations((0, foot_y)):
                RectangleRounded(PAD, PAD, CORNER_R)
        extrude(amount=BED_THICKNESS)
        add(
            as_part(
                Pos(0, foot_y, 0)
                * top_chamfer_tool(
                    PAD, PAD, CORNER_R, BASE_H + BED_THICKNESS, EDGE_CHAMFER
                )
            ),
            mode=Mode.SUBTRACT,
        )
        # The front corners leave intact mouth walls even for the tiny bits at
        # the X extremes; the rear retains the Gridfinity pad's 4 mm radius.
        add(_guide_block(rear, height))
        # Extend the rear guide as a hollow first cell: side walls protect
        # projecting shanks but keep the axial mouths and low rail unobstructed.
        # Support the 19 mm roof span in the slicer for this ASA print.
        extension = GRID - BACK_WALL - GUIDE_DEPTH
        for x in (-(PAD - 1) / 2, (PAD - 1) / 2):
            with Locations(
                (x, rear + GRID - extension / 2 - 0.5, BASE_H + BED_THICKNESS)
            ):
                Box(
                    1,
                    extension + 1,
                    height - 1 - BASE_H - BED_THICKNESS,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                )
        with Locations((0, rear + GRID - extension / 2, height - 1)):
            Box(
                PAD,
                extension,
                1,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
        add(stacking_receiver(foot_y, height))
        add(_cover_rail(rear))
        for drill in drills.drills:
            x, z = positions[f"{drill.nominal:g}"]
            _cut_guide(x, z, (drills.cut_d(drill) + c.GUIDE_FIT) / 2, rear)
        for tool in drills.hex_tools:
            x, z = positions[tool.key]
            _cut_guide(x, z, (tool.across_flats + c.GUIDE_FIT) / 3**0.5, rear)
        engrave_tool_map(rear, glyphs)
    return holder.part


def create_preview_for(drills: DrillSet) -> Compound:
    """Show the anchor with the whole tool set posed; no cover is inferred."""
    cells, positions = layout_for(drills)
    base = create_base_for(drills)
    base.label = f"{drills.name}_sideways_asa"
    base.color = c.SHELL_COLOR
    rear = -(cells * GRID - (GRID - PAD)) / 2 + BACK_WALL
    tools = []
    for drill in drills.drills:
        key = f"{drill.nominal:g}"
        bit = create_drill(drill.nominal, drill.length, style=drills.style)
        bit.label = f"drill_{key}mm"
        bit.color = STEEL
        x, z = positions[key]
        tools.append(Pos(x, rear, z) * Rotation(-90, 0, 0) * bit)
    for spec in drills.hex_tools:
        if isinstance(spec, StepDrill):
            bit = create_step_drill(
                spec.across_flats,
                spec.length,
                spec.shank_len,
                spec.d_min,
                spec.head_d,
                spec.step,
            )
        else:
            bit = create_hex_tool(spec.across_flats, spec.length, head_d=spec.head_d)
        bit.label = spec.key
        bit.color = STEEL
        x, z = positions[spec.key]
        tools.append(Pos(x, rear, z) * Rotation(-90, 0, 0) * bit)
    return Compound(label=f"{drills.name} sideways anchor", children=[base, *tools])


def create_closed_for(drills: DrillSet) -> Compound:
    """Inspection scene with the long PETG cover seated around the posed tools."""
    from .sideways_cover import create_cover_for
    from .tools import COVER_GLASS

    preview = create_preview_for(drills)
    cover = create_cover_for(drills)
    cover.label = f"{drills.name}_sideways_petg_cover"
    cover.color = COVER_GLASS
    return Compound(
        label=f"{drills.name} sideways closed holder",
        children=[*preview.children, cover],
    )
