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
from models.lib.gridfinity import (
    BASE_H,
    CORNER_R,
    GRID,
    HEIGHT_UNIT,
    PAD,
    gridfinity_foot,
)
from . import config as c
from .box import (
    add_stacking_lip,
    cut_stacking_socket,
)
from .sets import DrillSet, StepDrill
from .tools import STEEL, create_drill, create_hex_tool, create_step_drill

# Frozen X/Z positions minimize squared movement from the previous layout while
# clearing the continuous collar aperture (X +/-18.48, Z 7.27..32.73, R 0.2).
# Reserve max(body radius + COLLAR_CLEAR, compensated ASA guide radius), plus
# >=0.05 mm at the aperture; full tool-body gaps remain >=1.4 mm and outer
# side/floor/roof walls >=1.2 mm. STEP reserves R8 + COLLAR_CLEAR only through
# the collar: its R10 shoulder lies behind it, but still sets body/wall budgets.
# STEP's full shoulder also clears the raised bed (Z 6.11) by >=0.11 mm.
WOOD_XZ = {
    "2": (2.81, 31.43),
    "2.5": (-9.16, 8.82),
    "3": (-16.68, 30.93),
    "3.5": (-16.43, 11.58),
    "4": (13.49, 30.43),
    "5": (15.68, 20.67),
    "6": (-1.69, 19.87),
    "7": (4.91, 15.51),
    "8": (-3.09, 11.57),
    "9": (13.68, 12.07),
    "10": (6.87, 25.23),
    "CSK": (-11.32, 17.95),
}
METAL_XZ = {
    "1": (17.30, 20.25),
    "1.5": (-10.44, 31.44),
    "2": (17.02, 31.27),
    "2.5": (-8.21, 28.85),
    "3": (10.12, 30.87),
    "4": (-3.83, 30.43),
    "5": (3.61, 10.07),
    "6": (-15.18, 29.39),
    "8": (14.18, 25.27),
    "10": (3.57, 26.42),
    "TAP": (12.37, 14.23),
    "STEP": (-9.30, 16.23),
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
COLLAR_CLEAR = fits.SLIDING  # sliding fit, PETG cover over ASA collar
COLLAR_ROOF = 1.0
COLLAR_LEAD = 0.3  # 45-degree male lead-in at the cover entry
# A continuous, backed collar carries the same closed-loop detent as the
# upright holders; the tool layout clears its inner aperture without scallops.
DETENT_Y = GRID + 2.5
DETENT_BEAD = 0.30  # PETG: 0.19 mm engagement beyond the 0.11 mm radial gap
DETENT_GROOVE = 0.36  # 0.17 mm radial relief beyond the bead's 0.19 mm engagement
COLLAR_WALL = DETENT_GROOVE + 0.8  # groove depth plus two ASA backing perimeters
DETENT_LEAD = 1.1  # gentle insertion ramp facing the cover's open mouth (-Y)
DETENT_BACK = 0.5  # shorter retention face towards the closed end (+Y)
DETENT_FLAT = 0.15  # printable flat instead of a knife-edge bead
LABEL_SIZE = 12.0  # bold WOOD/METAL capitals render ~9 mm tall on the cover
LABEL_DEPTH = 0.5  # stays within the 1 mm PETG cover wall
TOOL_LABEL_SIZE = 4.2  # bold digits render just over 3 mm tall
TOOL_LABEL_DEPTH = 0.8  # leaves 1.2 mm of the ASA guide's 2 mm back wall
TOOL_LABEL_MARGIN = 0.4  # flat rear face ends at PAD/2 - CORNER_R
# Lettering uses rectangular ink bounds rather than circular tool envelopes.
# Small map offsets keep decimal labels distinct without moving their bores.
_TOOL_LABEL_OFFSETS = {
    ("wood", "2.5"): (0.0, -0.65),
    ("metal", "1.5"): (1.3, 0.0),
    ("metal", "2.5"): (0.0, -1.80),
}


def cover_detent(rear: float, *, groove: bool):
    """Ramped closed-loop bead/groove, including all four rounded corners."""
    gap = COLLAR_CLEAR / 2
    width = PAD - 2.0 - (COLLAR_CLEAR if groove else 0)
    bottom = BASE_H + BED_THICKNESS + (gap if groove else 0)
    top = 5 * HEIGHT_UNIT - COLLAR_ROOF - (gap if groove else 0)
    radius = 1.0 if groove else 1.0 + gap
    depth = DETENT_GROOVE if groove else DETENT_BEAD
    y = rear + DETENT_Y
    axial_clear = 0.1 if groove else 0
    sections = []
    for offset, inset in (
        (-DETENT_LEAD - axial_clear, 0),
        (-DETENT_FLAT / 2, depth),
        (DETENT_FLAT / 2, depth),
        (DETENT_BACK + axial_clear, 0),
    ):
        with BuildSketch(Plane.XZ.offset(-(y + offset))) as section:
            with Locations((0, (bottom + top) / 2)):
                RectangleRounded(
                    width - 2 * inset, top - bottom - 2 * inset, radius - inset
                )
        sections.append(section.sketch)
    # The square-ish outside embeds the ring into the existing PETG shell and
    # bed. The inner loft follows parallel offsets of the ASA rounded perimeter.
    with BuildPart() as ring:
        with BuildSketch(Plane.XZ.offset(-(y + DETENT_BACK + axial_clear))):
            with Locations((0, (bottom + top) / 2)):
                RectangleRounded(width + 0.1, top - bottom + 0.1, 0.2)
        extrude(amount=DETENT_LEAD + DETENT_BACK + 2 * axial_clear)
        loft(sections=sections, ruled=True, mode=Mode.SUBTRACT)
    return ring.part


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
        dx, dz = _TOOL_LABEL_OFFSETS.get((drills.name, key), (0.0, 0.0))
        x = min(flat_half - bounds.max.X, max(-flat_half - bounds.min.X, hole_x + dx))
        yield key, x, z + dz, glyph


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


def _cover_collar(rear: float, height: float):
    """Continuous backed male rim inside the cover mouth."""
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
        with BuildSketch(Plane.XZ.offset(-(rear + COLLAR_END - 0.2))):
            with Locations((0, (bottom + top) / 2)):
                RectangleRounded(
                    outer_w - 2 * COLLAR_WALL,
                    top - bottom - 2 * COLLAR_WALL,
                    0.2,
                )
        extrude(amount=COLLAR_END - COLLAR_START - 0.19, mode=Mode.SUBTRACT)
        # Bevel the new continuous aperture's exposed rim as well as the
        # outside: a 0.66 mm free edge remains where the two bevels meet.
        with BuildSketch(Plane.XZ.offset(-(rear + COLLAR_END - 0.2))):
            with Locations((0, (bottom + top) / 2)):
                RectangleRounded(
                    outer_w - 2 * COLLAR_WALL,
                    top - bottom - 2 * COLLAR_WALL,
                    0.2,
                )
        with BuildSketch(Plane.XZ.offset(-(rear + COLLAR_END + 0.01))):
            with Locations((0, (bottom + top) / 2)):
                RectangleRounded(
                    outer_w - 2 * COLLAR_WALL + 0.42,
                    top - bottom - 2 * COLLAR_WALL + 0.42,
                    0.41,
                )
        loft(ruled=True, mode=Mode.SUBTRACT)
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
        add(_cover_collar(rear, height))
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
