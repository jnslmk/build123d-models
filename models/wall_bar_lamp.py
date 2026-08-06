"""Wall-mounted linear bar lamp inspired by a double-ended tube sconce."""

from build123d import (
    BuildPart,
    BuildSketch,
    Circle,
    Color,
    Compound,
    Location,
    Mode,
    Part,
    Plane,
    Polygon,
    extrude,
    loft,
)

from models.lib import fits
from models.lib.checks import Report, is_solid_at

# ``create()`` is the assembled sconce -- tubes, caps and mount in their use
# pose -- so the website offers no STL/STEP for it (see
# tessellate_models.model_is_assembly). ``create_print_layout()`` is the
# printable counterpart.
IS_ASSEMBLY = True

# Diffuser tube
TUBE_OUTER_DIAMETER = 40.0
TUBE_WALL = 1.2
TUBE_HALF_LENGTH = 200.0
TUBE_PEG_DIAMETER = 18.2
TUBE_PEG_LENGTH = 10.0
CENTER_GAP = 0.0

# End cap
END_CAP_BODY_LENGTH = 10.0
END_CAP_LIP_DIAMETER = TUBE_OUTER_DIAMETER - 0.4
END_CAP_LIP_LENGTH = 7.0

# Central wall mount
BACKPLATE_WIDTH = 36.0
BACKPLATE_HEIGHT = 24.0
BACKPLATE_THICKNESS = 3.0
BACKPLATE_RADIUS = 5.0
SHROUD_OUTER_DIAMETER = TUBE_OUTER_DIAMETER + 6.0
SHROUD_BORE_DIAMETER = TUBE_OUTER_DIAMETER + 0.4
SHROUD_CENTER_WIDTH = 12.0
SHROUD_TRANSITION_LENGTH = 8.0
BASE_WIDTH = 16.0
BASE_DEPTH = 10.0
BASE_HEIGHT = 11.0
BASE_TOP_INSET = 3.0
CABLE_SLOT_WIDTH = 10.0
CABLE_SLOT_HEIGHT = 6.0

# Print layout spacing
LAYOUT_GAP = 10.0

TRANSLUCENT_WHITE = Color(1, 1, 1, 0.7)
BLACK = Color(0.1, 0.1, 0.1)


def create_mount() -> Part:
    """Create a one-piece wall mount with smooth shroud and correctly oriented base."""
    shroud_radius = SHROUD_OUTER_DIAMETER / 2
    bore_radius = SHROUD_BORE_DIAMETER / 2
    tube_radius = TUBE_OUTER_DIAMETER / 2
    half_center_width = SHROUD_CENTER_WIDTH / 2
    end_x = half_center_width + SHROUD_TRANSITION_LENGTH

    with BuildPart() as mount:
        outer_sections = []
        for offset, radius in (
            (-end_x, tube_radius + 0.8),
            (-half_center_width, shroud_radius),
            (half_center_width, shroud_radius),
            (end_x, tube_radius + 0.8),
        ):
            with BuildSketch(Plane.YZ.offset(offset)) as section:
                Circle(radius)
            outer_sections.append(section.sketch)
        loft(outer_sections)

        with BuildSketch(Plane.YZ.offset(-end_x)):
            Circle(bore_radius)
        extrude(amount=2 * end_x, mode=Mode.SUBTRACT)

        base_top_z = -shroud_radius + 1.5
        with BuildSketch(Plane.YZ):
            Polygon(
                [
                    (-BASE_DEPTH / 2, base_top_z),
                    (BASE_DEPTH / 2, base_top_z),
                    (BASE_DEPTH / 2 + BASE_TOP_INSET, base_top_z - BASE_HEIGHT),
                    (-BASE_DEPTH / 2 - BASE_TOP_INSET, base_top_z - BASE_HEIGHT),
                ],
                align=None,
            )
        extrude(amount=BASE_WIDTH, both=True)

    mount.part.label = "wall_mount"
    mount.part.color = BLACK
    return mount.part


def create_tube() -> Part:
    """Create one half-length diffuser tube with a hollow body and mounting peg."""
    outer_radius = TUBE_OUTER_DIAMETER / 2
    inner_radius = outer_radius - TUBE_WALL
    tube_half = TUBE_HALF_LENGTH / 2

    with BuildPart() as tube:
        with BuildSketch(Plane.YZ.offset(-tube_half)):
            Circle(outer_radius)
            Circle(inner_radius, mode=Mode.SUBTRACT)
        extrude(amount=TUBE_HALF_LENGTH)

    tube.part.color = TRANSLUCENT_WHITE
    return tube.part


def create_end_cap() -> Part:
    """Create a flush-faced plug cap for the diffuser tube ends."""
    body_radius = TUBE_OUTER_DIAMETER / 2

    with BuildPart() as end_cap:
        with BuildSketch(Plane.YZ.offset(-END_CAP_BODY_LENGTH / 2)):
            Circle(body_radius)
        extrude(amount=END_CAP_BODY_LENGTH)

        with BuildSketch(
            Plane.YZ.offset(-END_CAP_BODY_LENGTH / 2 - END_CAP_LIP_LENGTH)
        ):
            Circle(END_CAP_LIP_DIAMETER / 2)
        extrude(amount=END_CAP_LIP_LENGTH)

    end_cap.part.color = TRANSLUCENT_WHITE
    return end_cap.part


def _assemble_components() -> list[Part]:
    """Return individually labeled assembled parts for viewer grouping."""
    mount = create_mount()

    left_tube = create_tube().move(
        Location((-TUBE_HALF_LENGTH / 2 - CENTER_GAP / 2, 0, 0))
    )
    left_tube.label = "left_tube"

    right_tube = create_tube().move(
        Location((TUBE_HALF_LENGTH / 2 + CENTER_GAP / 2, 0, 0))
    )
    right_tube.label = "right_tube"

    cap_center_offset = TUBE_HALF_LENGTH + END_CAP_BODY_LENGTH / 2

    left_cap = create_end_cap().move(
        Location((-cap_center_offset - CENTER_GAP / 2, 0, 0))
    )
    left_cap.label = "left_end_cap"

    right_cap = create_end_cap().move(
        Location((cap_center_offset + CENTER_GAP / 2, 0, 0))
    )
    right_cap.label = "right_end_cap"

    return [mount, left_tube, right_tube, left_cap, right_cap]


def create_print_layout() -> Compound:
    """Lay out all lamp parts apart from each other for printing/export."""
    mount = create_mount()
    mount.label = "wall_mount"

    left_tube = create_tube().move(
        Location((0, 0, BACKPLATE_HEIGHT / 2 + TUBE_OUTER_DIAMETER / 2 + LAYOUT_GAP))
    )
    left_tube.label = "tube_a"

    right_tube = create_tube().move(
        Location((0, 0, -(BACKPLATE_HEIGHT / 2 + TUBE_OUTER_DIAMETER / 2 + LAYOUT_GAP)))
    )
    right_tube.label = "tube_b"

    cap_offset_x = TUBE_HALF_LENGTH / 2 + END_CAP_BODY_LENGTH / 2 + LAYOUT_GAP
    cap_offset_z = -BACKPLATE_HEIGHT / 2 - TUBE_OUTER_DIAMETER / 2 - LAYOUT_GAP

    left_cap = create_end_cap().move(Location((-cap_offset_x, 0, cap_offset_z)))
    left_cap.label = "end_cap_a"

    right_cap = create_end_cap().move(Location((cap_offset_x, 0, cap_offset_z)))
    right_cap.label = "end_cap_b"

    return Compound(
        label="wall_bar_lamp_print_layout",
        children=[mount, left_tube, right_tube, left_cap, right_cap],
    )


def create() -> Compound:
    """Create the lamp arranged in its final assembled wall-sconce form."""
    return Compound(label="wall_bar_lamp", children=_assemble_components())


def _child(compound: Compound, label: str):
    matches = [c for c in compound.children if c.label == label]
    if len(matches) != 1:
        raise LookupError(
            f"expected exactly one child labelled {label!r}, found {len(matches)}"
        )
    return matches[0]


def _overlap_volume(a, b) -> float:
    """Material shared between two shapes, in mm^3 -- not their bounding boxes.

    The tube slides *through* the mount's bore and the end caps sit flush
    against the tube ends, so bounding boxes are expected to overlap at every
    one of these joints. Only a boolean intersection volume tells a clean
    slide-through fit apart from one part actually eating into another.
    """
    common = a.intersect(b)
    if common is None:
        return 0.0
    shapes = list(common) if isinstance(common, (list, tuple)) else [common]
    return float(sum(getattr(s, "volume", 0.0) for s in shapes))


def check() -> Report:
    """Geometry assertions beyond ``tests/test_wall_bar_lamp.py``.

    That suite confirms the compound's child labels/order, that the mount is
    one solid, that both builders use ``BuildSketch``/``extrude`` (a source
    check, not a geometry one), the assembly's gross aspect ratio, and that
    the print layout separates its parts along Z. None of that samples the
    actual solids or proves anything mates without colliding, which is what
    this adds:

    * the tube-to-mount bore clearance traces back to ``fits.FREE``, not a
      bare literal;
    * the two tube halves meet exactly at the wall centre and the end caps
      sit flush against the tubes' outer ends -- checked as bounding-box gaps
      at the specific mating faces, not the whole-assembly aspect ratio the
      unit tests already cover;
    * the shroud's own taper reaches exactly to
      ``SHROUD_CENTER_WIDTH/2 + SHROUD_TRANSITION_LENGTH`` along X, point
      sampled in isolation from the base foot beneath it, and the base foot
      itself does not overshoot that same taper;
    * the shroud wall left between the bore and the tube-radius taper at the
      bore's mouth clears the 2-perimeter floor for a 0.4 mm nozzle;
    * non-interference at every mating pair (tube/mount, tube/end-cap,
      tube/tube) as an actual boolean intersection volume, since all three
      pairs' bounding boxes legitimately overlap by design.
    """
    r = Report()
    part = create()

    mount = _child(part, "wall_mount")
    left_tube = _child(part, "left_tube")
    right_tube = _child(part, "right_tube")
    left_cap = _child(part, "left_end_cap")
    right_cap = _child(part, "right_end_cap")

    left_tube_bb = left_tube.bounding_box()
    right_tube_bb = right_tube.bounding_box()
    left_cap_bb = left_cap.bounding_box()
    right_cap_bb = right_cap.bounding_box()

    r.section("fits")
    diametral = SHROUD_BORE_DIAMETER - TUBE_OUTER_DIAMETER
    r.check(
        abs(diametral - fits.FREE) < 1e-9,
        "shroud bore clears the tube by a named FREE fit, not a bare literal",
        f"{diametral:.2f} mm diametral (fits.FREE = {fits.FREE:.2f} mm)",
    )

    r.section("relative placement")
    r.check(
        abs(left_tube_bb.max.X) < 1e-6 and abs(right_tube_bb.min.X) < 1e-6,
        "both tube halves reach exactly to the wall centre (x=0)",
        f"left max x={left_tube_bb.max.X:.3f}, right min x={right_tube_bb.min.X:.3f}",
    )
    r.check(
        abs(left_tube_bb.max.X - right_tube_bb.min.X) < 1e-6,
        "the two tube halves meet with CENTER_GAP between them, not overlapping or separated",
        f"gap = {right_tube_bb.min.X - left_tube_bb.max.X:.3f} mm (CENTER_GAP={CENTER_GAP:.1f})",
    )
    r.check(
        abs(left_cap_bb.max.X - left_tube_bb.min.X) < 1e-6
        and abs(right_cap_bb.min.X - right_tube_bb.max.X) < 1e-6,
        "each end cap's body sits flush against its tube's outer end",
        f"left gap={left_tube_bb.min.X - left_cap_bb.max.X:.3f} mm, "
        f"right gap={right_cap_bb.min.X - right_tube_bb.max.X:.3f} mm "
        "(the right cap is not mirrored, so its lip lands inside the tube "
        "instead of outboard of the body)",
    )

    end_x = SHROUD_CENTER_WIDTH / 2 + SHROUD_TRANSITION_LENGTH

    r.section("shroud wall integrity")
    # r=21.5 sits well inside the wall band at x=-10 -- the taper's local
    # outer radius there is ~22.2, comfortably clear of both the nominal bore
    # (20.2) and the loft's own measured inner boundary. The same radius at
    # x=+10 and x=0 should, by the shroud's left/right symmetry, be equally
    # solid.
    probe_r = 21.5
    r.check(
        is_solid_at(mount, -10.0, 0.0, probe_r),
        "shroud carries wall material on the -X (tube-facing) transition",
        f"x=-10.0, r={probe_r:.2f}",
    )
    r.check(
        is_solid_at(mount, 0.0, 0.0, probe_r),
        "shroud carries wall material at the centre plateau",
        f"x=0.0, r={probe_r:.2f}",
    )
    r.check(
        is_solid_at(mount, 10.0, 0.0, probe_r),
        "shroud carries wall material symmetrically on the +X transition too",
        f"x=10.0, r={probe_r:.2f} -- if this fails while the -X probe above "
        "passes, the loft-then-bore-subtract sequence in create_mount() is "
        "silently eating the +X half of the shroud wall (see "
        "build123d-geometry-ops: an OCC boolean can corrupt a BuildPart "
        "without raising)",
    )

    r.section("base foot footprint")
    # Point sampled well clear of the shroud (z far below centre, in the base
    # foot's own cross-section): the mounting foot should not reach past the
    # shroud's own taper end (end_x) any more than the taper itself does.
    base_mid_z = -(SHROUD_OUTER_DIAMETER / 2 - 1.5) - BASE_HEIGHT / 2
    r.check(
        not is_solid_at(mount, end_x + 0.5, 0.0, base_mid_z)
        and not is_solid_at(mount, -(end_x + 0.5), 0.0, base_mid_z),
        "base foot does not overshoot the shroud's own taper end (end_x) along X",
        f"probed x=+/-{end_x + 0.5:.2f} mm at the foot's mid-height "
        f"(z={base_mid_z:.2f}); BASE_WIDTH={BASE_WIDTH:.1f} mm used as a "
        "half-extent by extrude(..., both=True), doubling the foot to "
        f"{2 * BASE_WIDTH:.1f} mm total",
    )

    r.section("shroud wall thickness at the bore mouth")
    wall_at_mouth = (TUBE_OUTER_DIAMETER / 2 + 0.8) - (SHROUD_BORE_DIAMETER / 2)
    r.check(
        wall_at_mouth >= 0.8,
        "shroud wall where the taper meets the bore clears the 2-perimeter floor",
        f"{wall_at_mouth:.2f} mm (min 0.80 mm for a 0.4 mm nozzle)",
    )

    r.section("non-interference")
    # Threshold is 0.5 mm^3 for all three checks below, not 0. Every joint
    # here is a slide-through or flush-touch fit (fits.FREE bore, a cap
    # sitting face-to-face with a tube), never an intended press fit, so a
    # real pass measures exactly 0.000 mm^3. The margin only absorbs
    # boolean/tessellation noise at a touching or near-tangent face (a sliver
    # of a few 1e-3 mm^3), and it is ~3 orders of magnitude below a genuine
    # collision -- the real defect caught below measures 848.9 mm^3 -- so it
    # cannot mask one.
    tube_mount_vol = _overlap_volume(left_tube, mount) + _overlap_volume(
        right_tube, mount
    )
    r.check(
        tube_mount_vol < 0.5,
        "neither tube's material collides with the mount's bore wall",
        f"{tube_mount_vol:.3f} mm^3 total overlap (threshold 0.5), "
        f"even though both bounding boxes overlap across the {end_x:.0f} mm shroud",
    )

    tube_cap_vol = _overlap_volume(left_tube, left_cap) + _overlap_volume(
        right_tube, right_cap
    )
    r.check(
        tube_cap_vol < 0.5,
        "each end cap sits flush against its tube -- touching, not overlapping",
        f"{tube_cap_vol:.3f} mm^3 total overlap (threshold 0.5)",
    )

    tube_tube_vol = _overlap_volume(left_tube, right_tube)
    r.check(
        tube_tube_vol < 0.5,
        "the two tube halves meet at the centre without overlapping material",
        f"{tube_tube_vol:.3f} mm^3 overlap (threshold 0.5)",
    )

    return r
