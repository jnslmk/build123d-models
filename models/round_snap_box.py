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
)

from models.lib import fits
from models.lib.checks import Report, is_solid_at, sharp_convex_edges

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


def check() -> Report:
    """Pin the joint's clearance, bead engagement and wall budget on the defaults.

    Runs against the ``PARAMS`` defaults (``create_box()``/``create_lid()`` with
    no arguments), same as ``uv run check round_snap_box`` and the website's
    first render. The bead/undercut numbers here are the worked example the
    ``snap-fits`` skill (``references/annular.md``) builds around this exact
    file -- see that skill before changing the strain assertions below.
    """
    r = Report()
    inner_r, out_r, lid_inner_r, lip_r = _dims(
        INNER_DIA, BODY_WALL, LID_WALL, CLEARANCE
    )
    box = create_box()
    lid = create_lid()
    probe = 0.05
    MIN_WALL = 0.8  # 2 perimeters at a 0.4 mm nozzle -- fdm-fits-and-clearances
    rim_z = FLOOR + INNER_HEIGHT  # top of the box wall
    shoulder_z = rim_z - LIP_H  # where the body steps in to the lip

    r.section("walls")
    lip_wall = BODY_WALL - LID_WALL - CLEARANCE
    # Point-sample the built box, not just the _dims() arithmetic: the earlier
    # version of this check re-derived lip_r - inner_r from the same formula
    # _dims() already uses, so it could never disagree with itself no matter
    # what create_box() actually built. Sample away from the bead (z_probe is
    # 3 mm clear of bead_z) so the bead's own protrusion doesn't confuse the
    # reading.
    z_probe = shoulder_z + 2.0
    r.check(
        not is_solid_at(box, inner_r - probe, 0, z_probe)
        and is_solid_at(box, inner_r + probe, 0, z_probe)
        and is_solid_at(box, lip_r - probe, 0, z_probe)
        and not is_solid_at(box, lip_r + probe, 0, z_probe),
        "the lip wall is actually built from inner_r to lip_r",
        f"sampled at z={z_probe:.2f} mm: open below {inner_r:.2f}, solid "
        f"{inner_r:.2f}-{lip_r:.2f}, open above {lip_r:.2f} mm -- matches "
        f"lip_wall = BODY_WALL - LID_WALL - CLEARANCE = {lip_wall:.2f} mm",
    )
    r.check(
        lip_wall >= MIN_WALL - 1e-9,
        "the rabbet lip clears the 2-perimeter wall floor",
        f"{lip_wall:.2f} mm (min {MIN_WALL} mm) -- {BODY_WALL} - {LID_WALL} - "
        f"{CLEARANCE}; the flush geometry silently thins this if LID_WALL or "
        "CLEARANCE is raised without BODY_WALL following",
    )
    r.check(
        BODY_WALL >= MIN_WALL - 1e-9 and LID_WALL >= MIN_WALL - 1e-9,
        "body and lid walls each clear the 2-perimeter floor",
        f"body {BODY_WALL} mm, lid {LID_WALL} mm (min {MIN_WALL} mm)",
    )
    r.check(
        FLOOR >= MIN_WALL - 1e-9,
        "floor clears the 2-perimeter floor",
        f"{FLOOR} mm (min {MIN_WALL} mm)",
    )

    r.section("fit")
    diametral_clearance = 2 * CLEARANCE  # CLEARANCE is per-side; fits.py is diametral
    r.check(
        diametral_clearance > fits.FREE,
        "lip-to-lid clearance is looser than fits.FREE (deliberate -- see "
        "CLEARANCE's own comment: the joint is near the scaling rule's "
        "threshold and the lid skirt must also flex over the bead)",
        f"{diametral_clearance:.2f} mm diametral vs fits.FREE={fits.FREE:.2f} mm",
    )

    r.section("bead / undercut")
    bead_z = rim_z - BEAD_DROP
    # Point-sample the built solids for the bead's actual peak/trough radius,
    # rather than trusting the arithmetic alone -- this is what would catch a
    # BEAD_DROP or LIP_H drift that moves the bead off the lip entirely.
    box_bead_peak = lip_r + BEAD
    r.check(
        is_solid_at(box, box_bead_peak - probe, 0, bead_z)
        and not is_solid_at(box, box_bead_peak + probe, 0, bead_z),
        "box bead protrudes exactly BEAD past the lip",
        f"solid to r={box_bead_peak:.2f} mm at z={bead_z:.2f} mm",
    )
    # The lid is returned in print pose (mouth up); its bead sits at
    # LID_WALL + BEAD_DROP + SNAP from the bed in that pose (derived from the
    # same flip the seated-assembly transform below re-derives independently).
    lid_bead_z_print_pose = LID_WALL + BEAD_DROP + SNAP
    lid_bead_trough = lid_inner_r - BEAD
    r.check(
        not is_solid_at(lid, lid_bead_trough - probe, 0, lid_bead_z_print_pose)
        and is_solid_at(lid, lid_bead_trough + probe, 0, lid_bead_z_print_pose),
        "lid bead protrudes exactly BEAD into the bore",
        f"open to r={lid_bead_trough:.2f} mm at z={lid_bead_z_print_pose:.2f} mm",
    )

    # Peak diametral interference the two beads ride over each other with --
    # the box bead's OD against the lid bead's ID, not the single-bead
    # approximation (y = 2*BEAD) that ignores the lid cutting its own bead.
    # box_bead_peak and lid_bead_trough are not re-derived arithmetic here:
    # they are exactly the two radii the point-sample checks just above this
    # confirmed the built solids actually stop at (within `probe`), so y is
    # grounded in the real geometry rather than in _dims()-style algebra that
    # could never disagree with itself. (An earlier version of this function
    # also asserted y == 4*BEAD - 2*CLEARANCE here; that assertion recomputed
    # the same expression on both sides and could not fail against any
    # create_box()/create_lid() output, so it was removed rather than kept as
    # a check that couldn't check anything.)
    y = 2 * (box_bead_peak - lid_bead_trough)
    d = 2 * lip_r
    epsilon = 100 * y / d  # percent hoop strain
    # PETG (Prusament), from the snap-fits skill's materials.md: flexural
    # modulus 1.7 GPa, elongation at yield 5.1% -> ceiling = 1/3 of that; the
    # repeated-use figure is Covestro's 0.60x derate for "frequent separation
    # and rejoining". AGENTS.md defaults every model to PETG unless stated
    # otherwise, and this box states no other material.
    petg_one_shot_pct = 1.7
    petg_repeated_pct = 1.0
    r.check(
        epsilon <= petg_one_shot_pct + 1e-9,
        "peak hoop strain stays under PETG's one-shot ceiling",
        f"{epsilon:.2f}% vs {petg_one_shot_pct}% ceiling (y={y:.2f} mm, d={d:.1f} mm)",
    )
    r.check(
        epsilon <= petg_repeated_pct + 1e-9,
        "peak hoop strain stays under PETG's repeated-use ceiling",
        f"{epsilon:.2f}% vs {petg_repeated_pct}% ceiling -- this is the "
        "double-bead peak, not the single-bead y=2*BEAD approximation the "
        "module's own comments use; snap-fits/references/annular.md's own "
        "worked example for this file gives the same ~1.25% and calls the "
        "load-sharing from the thin lid/lip walls headroom, not a designed-in "
        "derate, so this is left failing rather than argued away",
    )

    r.section("closed-state interference")
    seat_shift = rim_z + LID_WALL
    seated_lid = Pos(0, 0, seat_shift) * Rotation(180, 0, 0) * lid
    r.check(
        abs(seated_lid.bounding_box().min.Z - shoulder_z) < 1e-6,
        "seated lid's skirt bottom lands exactly on the box's shoulder",
        f"{seated_lid.bounding_box().min.Z:.3f} mm vs shoulder {shoulder_z:.3f} mm",
    )
    common = box.intersect(seated_lid)
    shapes = (
        []
        if common is None
        else (list(common) if isinstance(common, list) else [common])
    )
    vol = sum(s.volume for s in shapes)
    r.check(
        vol > 0,
        "box and lid interfere when seated (the retention itself)",
        f"{vol:.2f} mm^3",
    )
    r.check(
        len(shapes) == 1,
        "the interference is one contiguous region, not scattered clashes",
        f"{len(shapes)} region(s)",
    )
    if shapes:
        ib = shapes[0].bounding_box()
        r.check(
            ib.size.Z < BEAD_DROP,
            "the interference is confined near the bead, not the whole joint",
            f"{ib.size.Z:.2f} mm tall (bead centres BEAD_DROP={BEAD_DROP} mm apart)",
        )
        max_r = ib.size.X / 2
        r.check(
            abs(max_r - box_bead_peak) < 0.05,
            "the interference's radial extent matches the box bead's peak",
            f"{max_r:.2f} mm vs bead peak {box_bead_peak:.2f} mm",
        )

    r.section("edges")

    def on_shoulder(e) -> bool:
        b = e.bounding_box()
        return abs(b.min.Z - shoulder_z) < 0.05 and abs(b.max.Z - shoulder_z) < 0.05

    box_allow = (
        (
            on_shoulder,
            "lid mouth seats flat-on-flat on this shoulder -- box-closures says "
            "explicitly: do not chamfer it",
        ),
    )
    bad_box = sharp_convex_edges(box, allow=box_allow)
    r.check(
        not bad_box,
        "box has no unexplained sharp convex edges",
        f"{len(bad_box)} found" if bad_box else "all treated or named",
    )

    # The lid's own mouth-outer edge, in its print pose (mouth up), sits at
    # z = LIP_H + LID_WALL. Replaying the seated-assembly transform above on
    # this edge alone lands it at (r=out_r, z=shoulder_z) -- exactly the same
    # seam as the box's on_shoulder exception above, verified below rather
    # than asserted on faith. It is the same flush exterior mating edge seen
    # from the lid's side, not a second defect: chamfering it would cut a
    # groove into the promised flush seam (see the module docstring's "one
    # continuous cylinder with no lip standing proud").
    lid_mouth_outer_z = LIP_H + LID_WALL
    seated_z = seat_shift - lid_mouth_outer_z  # Rotation(180,0,0) negates z
    r.check(
        abs(seated_z - shoulder_z) < 1e-6,
        "the lid's mouth-outer edge lands on the box's shoulder when seated",
        f"seated z={seated_z:.3f} mm vs shoulder {shoulder_z:.3f} mm -- same "
        "seam as on_shoulder above, confirmed by replaying the seating "
        "transform on the edge's own z instead of assuming it",
    )

    def on_flush_seam(e) -> bool:
        b = e.bounding_box()
        return (
            abs(b.min.Z - lid_mouth_outer_z) < 0.05
            and abs(b.max.Z - lid_mouth_outer_z) < 0.05
        )

    lid_allow = (
        (
            on_flush_seam,
            "same seam as the box's on_shoulder exception, seen from the "
            "lid's side (verified above by replaying the seating transform) "
            "-- chamfering it would break the flush mate",
        ),
    )
    bad_lid = sharp_convex_edges(lid, allow=lid_allow)
    r.check(
        not bad_lid,
        "lid has no unexplained sharp convex edges",
        f"{len(bad_lid)} found" if bad_lid else "all treated or named",
    )

    return r
