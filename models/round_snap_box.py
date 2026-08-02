"""Round box with a snap-on lid that closes flush.

The box has a *stepped* rim (a rabbet): the top of the box wall is recessed
inward to a thin lip. The lid drops over that lip and its outer face sits flush
with the box's lower body -- so when closed the assembly is one continuous
cylinder with no lip standing proud. This works by spending the wall budget
asymmetrically: the box body wall is thick, the lid wall is thin, and the two
plus the joint clearance add up to the body wall.

    body_wall = lip_wall + clearance + lid_wall

A continuous bead on the lip and a matching bead inside the lid skirt interlock
to snap the box shut; both beads live inside the joint, so they never break the
flush exterior.

Two parts, both returned already in print pose (box floor-down, lid mouth-up).
Exterior horizontal rings (box bottom, lid top) get 45 chamfers -- clean edges
that also fight elephant's foot on the bed.
"""

from build123d import (
    Align,
    Axis,
    BuildPart,
    Compound,
    Cylinder,
    Locations,
    Mode,
    Part,
    Pos,
    Rotation,
    SortBy,
    Torus,
    chamfer,
    export_step,
    export_stl,
)
from ocp_vscode import show

# --- Box interior (the two numbers the user actually cares about) -----------
INNER_DIA = 78.0  # ID of the box
INNER_HEIGHT = 20.0  # usable depth from the floor up

# --- Walls (asymmetric so the closed box is flush) --------------------------
BODY_WALL = 2.4  # box lower body wall (thick: carries the lip + lid + gap)
LID_WALL = 1.2  # lid wall + top (thin: nests into the recess)
FLOOR = 2.4  # box floor thickness
# Radial gap between lip and lid inner wall -- diametral equivalent is 0.6 mm
# (fits.py's classes are diametral; this one is per-side, so double it before
# comparing). That is looser than fits.FREE (0.40 mm diametral, PETG
# baseline), the nearest class. Deliberate, not an error: the joint is ~83 mm
# across (out_r ~41.4 mm), near the scaling rule's +0.05 mm/100 mm threshold,
# and the lid skirt must also flex enough to ride over the retaining bead
# (BEAD, radial) on the way to snapping home -- the bead/SNAP pair sets true
# centring and retention, so this gap only has to clear the lip without
# binding, not locate anything precisely.
CLEARANCE = 0.3  # radial gap between lip and lid inner wall
# lip_wall = BODY_WALL - LID_WALL - CLEARANCE  (derived; keep it >= ~0.8)

# --- Snap fit ----------------------------------------------------------------
BEAD = 0.4  # radial protrusion of each interlocking bead
BEAD_DROP = 3.0  # box bead centre, measured down from the box rim
SNAP = 1.0  # how far the seated lid bead sits below the box bead
LIP_H = 8.0  # recessed lip height / lid engagement depth

# --- Edges -------------------------------------------------------------------
RING_CHAMFER = 0.8  # 45 chamfer on the exterior bottom/top rings
LEAD_IN = 0.4  # small lead-in chamfer at the joint mouths

# UI schema for the parametric web app. See tessellate_models.model_params().
PARAMS = [
    {
        "name": "inner_dia",
        "label": "Inner diameter (mm)",
        "type": "number",
        "min": 20.0,
        "max": 200.0,
        "step": 0.5,
        "default": INNER_DIA,
    },
    {
        "name": "inner_height",
        "label": "Inner height (mm)",
        "type": "number",
        "min": 5.0,
        "max": 120.0,
        "step": 0.5,
        "default": INNER_HEIGHT,
    },
    {
        "name": "body_wall",
        "label": "Box body wall (mm)",
        "type": "number",
        "min": 1.8,
        "max": 5.0,
        "step": 0.1,
        "default": BODY_WALL,
    },
    {
        "name": "lid_wall",
        "label": "Lid wall (mm)",
        "type": "number",
        "min": 0.8,
        "max": 3.0,
        "step": 0.1,
        "default": LID_WALL,
    },
    {
        "name": "clearance",
        "label": "Joint clearance (mm)",
        "type": "number",
        "min": 0.1,
        "max": 0.6,
        "step": 0.05,
        "default": CLEARANCE,
    },
    {
        "name": "bead",
        "label": "Snap bead size (mm)",
        "type": "number",
        "min": 0.2,
        "max": 0.6,
        "step": 0.05,
        "default": BEAD,
    },
]


def _chamfer_edge(builder, edge, size):
    """Chamfer one edge, isolating an OCC failure so it can't cascade."""
    saved = builder.part
    try:
        chamfer(edge, length=size)
    except Exception as exc:  # noqa: BLE001 -- OCC edge ops are flaky
        builder.part = saved
        print(f"warning: chamfer skipped ({exc})")


def _dims(inner_dia, body_wall, lid_wall, clearance):
    """Shared radii so box and lid stay mated."""
    inner_r = inner_dia / 2
    out_r = inner_r + body_wall  # flush outer radius (box body & lid)
    lid_inner_r = out_r - lid_wall  # lid bore
    lip_r = lid_inner_r - clearance  # recessed lip outer radius
    return inner_r, out_r, lid_inner_r, lip_r


def create_box(
    inner_dia: float = INNER_DIA,
    inner_height: float = INNER_HEIGHT,
    body_wall: float = BODY_WALL,
    lid_wall: float = LID_WALL,
    clearance: float = CLEARANCE,
    bead: float = BEAD,
) -> Part:
    """The box body: prints floor-down, open mouth up (its natural pose)."""
    inner_r, out_r, _, lip_r = _dims(inner_dia, body_wall, lid_wall, clearance)
    rim_z = FLOOR + inner_height  # top of the wall
    shoulder_z = rim_z - LIP_H  # where the body steps in to the lip
    bead_z = rim_z - BEAD_DROP

    with BuildPart() as box:
        # Lower body at the full (flush) outer radius, base on the bed.
        Cylinder(out_r, shoulder_z, align=(Align.CENTER, Align.CENTER, Align.MIN))
        # Recessed lip on top, at the smaller radius -> forms the seat shoulder.
        with Locations((0, 0, shoulder_z)):
            Cylinder(lip_r, LIP_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
        # Hollow the cavity out above the floor.
        with Locations((0, 0, FLOOR)):
            Cylinder(
                inner_r,
                inner_height,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )
        # External retaining bead on the lip (inner half merges into the lip).
        with Locations((0, 0, bead_z)):
            Torus(lip_r, bead, mode=Mode.ADD)

        # Exterior bottom ring: 45 chamfer (clean edge + elephant's-foot relief).
        bottom = box.faces().sort_by(Axis.Z).first
        _chamfer_edge(box, bottom.edges().sort_by(SortBy.RADIUS).last, RING_CHAMFER)
        # Lead-in on the lip's outer top edge so the lid funnels on.
        top = box.faces().sort_by(Axis.Z).last
        _chamfer_edge(box, top.edges().sort_by(SortBy.RADIUS).last, LEAD_IN)

    return box.part


def create_lid(
    inner_dia: float = INNER_DIA,
    inner_height: float = INNER_HEIGHT,
    body_wall: float = BODY_WALL,
    lid_wall: float = LID_WALL,
    clearance: float = CLEARANCE,
    bead: float = BEAD,
) -> Part:
    """The snap-on lid; returned flipped to its print pose (mouth up)."""
    _, out_r, lid_inner_r, _ = _dims(inner_dia, body_wall, lid_wall, clearance)
    lid_total = LIP_H + LID_WALL  # skirt + top

    # Seated: lid interior top meets box rim, so the box bead lands at
    # lid-frame z = LIP_H - BEAD_DROP; the lid bead sits SNAP below that.
    lid_bead_z = LIP_H - BEAD_DROP - SNAP

    with BuildPart() as lid:
        # Solid outer at the flush radius, mouth at z=0, closed top up.
        Cylinder(out_r, lid_total, align=(Align.CENTER, Align.CENTER, Align.MIN))
        # Interior the lip slides into.
        Cylinder(
            lid_inner_r,
            LIP_H,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT,
        )
        # Internal retaining bead (inner half protrudes into the bore).
        with Locations((0, 0, lid_bead_z)):
            Torus(lid_inner_r, bead, mode=Mode.ADD)

        # Lead-in on the mouth's inner edge (helps it catch the lip).
        mouth = lid.faces().sort_by(Axis.Z).first
        _chamfer_edge(lid, mouth.edges().sort_by(SortBy.RADIUS).first, LEAD_IN)
        # Exterior top ring: 45 chamfer (ends up on the bed once flipped).
        top = lid.faces().sort_by(Axis.Z).last
        _chamfer_edge(lid, top.edges().sort_by(SortBy.RADIUS).last, RING_CHAMFER)

    # Print pose: flip so the open mouth faces up, then re-seat on z=0.
    part = Rotation(180, 0, 0) * lid.part
    return Pos(0, 0, -part.bounding_box().min.Z) * part


def create(
    inner_dia: float = INNER_DIA,
    inner_height: float = INNER_HEIGHT,
    body_wall: float = BODY_WALL,
    lid_wall: float = LID_WALL,
    clearance: float = CLEARANCE,
    bead: float = BEAD,
) -> Compound:
    """Box + lid laid out side by side, each in its own print pose."""
    box = create_box(inner_dia, inner_height, body_wall, lid_wall, clearance, bead)
    lid = create_lid(inner_dia, inner_height, body_wall, lid_wall, clearance, bead)
    gap = inner_dia + 2 * body_wall + 20
    return Compound(children=[box, Pos(gap, 0, 0) * lid])


def main() -> None:
    box = create_box()
    lid = create_lid()
    gap = INNER_DIA + 2 * BODY_WALL + 20
    show(Compound(children=[box, Pos(gap, 0, 0) * lid]))
    export_step(box, "exports/round_snap_box.step")
    export_stl(box, "exports/round_snap_box.stl")
    export_step(lid, "exports/round_snap_box_lid.step")
    export_stl(lid, "exports/round_snap_box_lid.stl")


if __name__ == "__main__":
    main()
