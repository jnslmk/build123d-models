"""Foot-down horizontal drill guides and their tool layout.

The ASA guide supports shanks along Y and seats a removable TPU cartridge at
its mouths. The foot-bearing PETG cover slides over the guide's forward collar.
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
    Pos,
    Polygon,
    RectangleRounded,
    Rotation,
    Sphere,
    Text,
    add,
    extrude,
    loft,
)
from models.lib.edges import as_part, top_chamfer_tool
from models.lib import fits
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

# The front-facing cartridge recess leaves at least 1 mm ASA around the
# insert. The 0.2 mm entry bevel preserves 0.8 mm at its narrowest rim.
INSERT_DEPTH = c.CART_H
INSERT_WALL = 1.0
INSERT_LEAD = 0.2
INSERT_CORNER_R = 1.0
INSERT_CATCH_R = 0.65  # one rounded TPU key/catch in a shallow ASA dimple
INSERT_CATCH_OFFSET = 0.0  # pocket leaves 0.35 mm at the thinnest ASA point


COLLAR_START = GRID - 3.0  # overlap with the rear guide's first-cell walls
COLLAR_END = GRID + 4.0  # male reach into the hollow PETG cover
COLLAR_WALL = 0.8  # two ASA perimeters; tool-clearance scallops are cut below
COLLAR_CLEAR = fits.SLIDING  # sliding fit, PETG cover over ASA collar
COLLAR_ROOF = 1.0
COLLAR_LEAD = 0.3  # 45-degree male lead-in at the cover entry
# The 4 mm axial collar cannot carry the upright holder's full perimeter ring:
# its scalloped 0.8 mm walls would be erased by a groove. A short floor catch
# uses the open space between the wood and metal tool paths instead.
DETENT_X = 2.0
DETENT_W = 8.0
DETENT_Y = GRID + 2.5
DETENT_BEAD = 0.30  # PETG: 0.19 mm engagement beyond the 0.11 mm radial gap
DETENT_GROOVE = 0.36  # ASA: added floor backing keeps 0.8 mm behind the groove
DETENT_LEAD = 1.1  # gentle insertion ramp facing the cover's open mouth (-Y)
DETENT_BACK = 0.5  # shorter retention face towards the closed end (+Y)
DETENT_FLAT = 0.15  # printable flat instead of a knife-edge bead
LABEL_SIZE = 12.0  # bold WOOD/METAL capitals render ~9 mm tall on the cover
LABEL_DEPTH = 0.5  # stays within the 1 mm PETG cover wall
TOOL_LABEL_SIZE = 4.2  # bold digits render just over 3 mm tall
TOOL_LABEL_DEPTH = 0.8  # leaves 1.2 mm of the ASA guide's 2 mm back wall
TOOL_LABEL_MARGIN = 0.4  # flat rear face ends at PAD/2 - CORNER_R


def cover_detent(rear: float, *, groove: bool):
    """Matching axial bead/groove on the bed-facing collar and cover floor."""
    y = rear + DETENT_Y
    # Embed the bead's root into the PETG bed so the fuse has a real overlap.
    root = 0 if groove else 0.05
    z = BASE_H + BED_THICKNESS + (COLLAR_CLEAR / 2 if groove else -root)
    depth = DETENT_GROOVE if groove else DETENT_BEAD + root
    # On insertion (-Y), the bead's negative-Y face meets the collar first.
    # The short positive-Y face is the retention barrier during withdrawal.
    with BuildPart() as catch:
        with BuildSketch(Plane.YZ.offset(DETENT_X)):
            Polygon(
                (y - DETENT_LEAD - (0.1 if groove else 0), z),
                (y - DETENT_FLAT / 2, z + depth),
                (y + DETENT_FLAT / 2, z + depth),
                (y + DETENT_BACK + (0.1 if groove else 0), z),
                align=None,
            )
        extrude(amount=DETENT_W)
    return catch.part


def _detent_backing(rear: float):
    """Reinforce the ASA floor under the groove without raw top edges."""
    y = rear + DETENT_Y + (DETENT_BACK - DETENT_LEAD) / 2
    z = BASE_H + BED_THICKNESS + COLLAR_CLEAR / 2 + COLLAR_WALL - 0.1
    sections = []
    for height, inset in ((0, 0), (DETENT_GROOVE - 0.1, 0), (DETENT_GROOVE + 0.1, 0.2)):
        with BuildSketch(Plane.XY.offset(z + height)) as profile:
            with Locations((DETENT_X + DETENT_W / 2, y)):
                RectangleRounded(
                    DETENT_W + 0.4 - 2 * inset,
                    DETENT_LEAD + DETENT_BACK + 1.0 - 2 * inset,
                    0.25 - inset,
                )
        sections.append(profile.sketch)
    with BuildPart() as backing:
        loft(sections=sections, ruled=True)
    return backing.part


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


def _cover_collar(rear: float, height: float, drills: DrillSet, positions):
    """Wide male rim inside the cover mouth, relieved around the tool paths."""
    outer_w = PAD - 2.0 - COLLAR_CLEAR
    bottom = BASE_H + BED_THICKNESS + COLLAR_CLEAR / 2
    top = height - COLLAR_ROOF - COLLAR_CLEAR / 2
    with BuildPart() as collar:
        with BuildSketch(Plane.XZ.offset(-(rear + COLLAR_END - COLLAR_LEAD))):
            with Locations((0, (bottom + top) / 2)):
                RectangleRounded(outer_w, top - bottom, 1.0)
        extrude(amount=COLLAR_END - COLLAR_START - COLLAR_LEAD)
        with BuildSketch(Plane.XZ.offset(-(rear + COLLAR_END))):
            with Locations((0, (bottom + top) / 2)):
                RectangleRounded(
                    outer_w - 2 * COLLAR_LEAD,
                    top - bottom - 2 * COLLAR_LEAD,
                    1.0 - COLLAR_LEAD,
                )
        with BuildSketch(Plane.XZ.offset(-(rear + COLLAR_END - COLLAR_LEAD))):
            with Locations((0, (bottom + top) / 2)):
                RectangleRounded(outer_w, top - bottom, 1.0)
        loft(ruled=True)
        with BuildSketch(Plane.XZ.offset(-(rear + COLLAR_END + 0.01))):
            with Locations((0, (bottom + top) / 2)):
                RectangleRounded(
                    outer_w - 2 * COLLAR_WALL,
                    top - bottom - 2 * COLLAR_WALL,
                    0.2,
                )
        extrude(amount=COLLAR_END - COLLAR_START + 0.02, mode=Mode.SUBTRACT)
        # Adjacent shanks have only a small margin at the guide's outside
        # corners; scallop the collar rather than narrowing their free path.
        for drill in drills.drills:
            x, z = positions[f"{drill.nominal:g}"]
            with Locations((x, rear + (COLLAR_START + COLLAR_END) / 2, z)):
                Cylinder(
                    (drills.cut_d(drill) + c.GUIDE_FIT) / 2,
                    COLLAR_END - COLLAR_START + 0.2,
                    rotation=(90, 0, 0),
                    mode=Mode.SUBTRACT,
                )
        for tool in drills.hex_tools:
            x, z = positions[tool.key]
            with Locations((x, rear + (COLLAR_START + COLLAR_END) / 2, z)):
                Cylinder(
                    max(
                        tool.head_d / 2 + COLLAR_CLEAR,
                        (tool.across_flats + c.GUIDE_FIT) / 3**0.5,
                    ),
                    COLLAR_END - COLLAR_START + 0.2,
                    rotation=(90, 0, 0),
                    mode=Mode.SUBTRACT,
                )
    return collar.part


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
    """Continuous foot-width shell, rounded at the rear and cover-facing ends."""
    length = GRID
    sections = []
    for z, inset in (
        (BASE_H, 0.0),
        (height - GUIDE_TOP_CHAMFER, 0.0),
        (height, GUIDE_TOP_CHAMFER),
    ):
        with BuildSketch(Plane.XY.offset(z)) as profile:
            with Locations((0, rear + length / 2)):
                RectangleRounded(PAD - 2 * inset, length - 2 * inset, CORNER_R - inset)
            with Locations((0, rear + length - 4)):
                RectangleRounded(PAD - 2 * inset, 8 - 2 * inset, FRONT_CORNER_R - inset)
        sections.append(profile.sketch)
    with BuildPart() as guide:
        loft(sections=sections, ruled=True)
    return guide.part


def _insert_seat(rear: float, height: float):
    """Subtractive cartridge pocket, open toward the horizontal bit mouths."""
    front = rear + BACK_WALL + GUIDE_DEPTH
    floor = BASE_H + INSERT_WALL
    roof = height - INSERT_WALL
    with BuildPart() as seat:
        with BuildSketch(Plane.XZ.offset(-(front + 0.01))):
            with Locations((0, (floor + roof) / 2)):
                RectangleRounded(
                    PAD - 2 * (INSERT_WALL - INSERT_LEAD),
                    roof - floor + 2 * INSERT_LEAD,
                    INSERT_CORNER_R + INSERT_LEAD,
                )
        with BuildSketch(Plane.XZ.offset(-(front - INSERT_LEAD))):
            with Locations((0, (floor + roof) / 2)):
                RectangleRounded(
                    PAD - 2 * INSERT_WALL,
                    roof - floor,
                    INSERT_CORNER_R,
                )
        loft(ruled=True)
        with BuildSketch(Plane.XZ.offset(-(front - INSERT_LEAD))):
            with Locations((0, (floor + roof) / 2)):
                RectangleRounded(
                    PAD - 2 * INSERT_WALL,
                    roof - floor,
                    INSERT_CORNER_R,
                )
        extrude(amount=INSERT_DEPTH - INSERT_LEAD)
    return seat.part


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
        # One continuous outer skin replaces the butt-jointed guide and thin
        # extension walls. Open the forward span down to the bed, preserving
        # the 1 mm side walls and roof that carry the rear stacking receiver.
        cavity_start = rear + BACK_WALL + GUIDE_DEPTH
        with Locations((0, (cavity_start + rear + GRID) / 2, BASE_H + BED_THICKNESS)):
            Box(
                PAD - 2,
                GRID - BACK_WALL - GUIDE_DEPTH + 0.02,
                height - 1 - BASE_H - BED_THICKNESS,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )
        add(stacking_receiver(foot_y, height))
        # Hidden ties fuse the narrowed collar to the full-width shell across
        # its small clearance without splitting the exposed outer face.
        for sign in (-1, 1):
            with Locations(
                (sign * (PAD / 2 - 1.1), rear + GRID - 1.5, BASE_H + BED_THICKNESS + 1)
            ):
                Box(
                    1,
                    3,
                    height - BASE_H - BED_THICKNESS - 2,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                )
        add(_cover_collar(rear, height, drills, positions))
        # Back the floor groove with two full ASA perimeters. This pad sits
        # between the tool paths, with a chamfered top for support removal.
        add(_detent_backing(rear))
        add(cover_detent(rear, groove=True), mode=Mode.SUBTRACT)
        add(_insert_seat(rear, height), mode=Mode.SUBTRACT)
        front_y = rear + BACK_WALL + GUIDE_DEPTH
        catch_y = front_y - INSERT_DEPTH / 2
        catch_z = (BASE_H + height) / 2
        with Locations(
            (
                -(PAD / 2 - INSERT_WALL + INSERT_CATCH_OFFSET),
                catch_y,
                catch_z - 2,
            )
        ):
            Sphere(INSERT_CATCH_R, mode=Mode.SUBTRACT)
        for drill in drills.drills:
            x, z = positions[f"{drill.nominal:g}"]
            _cut_guide(x, z, (drills.cut_d(drill) + c.GUIDE_FIT) / 2, rear)
        for tool in drills.hex_tools:
            x, z = positions[tool.key]
            _cut_guide(x, z, (tool.across_flats + c.GUIDE_FIT) / 3**0.5, rear)
        engrave_tool_map(rear, glyphs)
    return holder.part


def create_preview_for(drills: DrillSet) -> Compound:
    """Show the seated TPU insert and the whole horizontal tool set without cover."""
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
    from .sideways_insert import seated_insert_for

    return Compound(
        label=f"{drills.name} sideways open holder",
        children=[base, seated_insert_for(drills), *tools],
    )


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
