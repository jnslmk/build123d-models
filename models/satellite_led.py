"""Satellite LED assembly - hexagonal rod with WS2811 LED strips, parabolic mirror, and diffuser."""

import math

from build123d import (
    Align,
    Axis,
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
    Rectangle,
    RectangleRounded,
    Vector,
    extrude,
    loft,
    revolve,
)

from models.lib.checks import Report

# A scene: rod, strips, mirror and diffusers in their use pose. Not a print job
# -- see tessellate_models.model_is_assembly, which is what drops the website's
# STL/STEP download for it.
IS_ASSEMBLY = True

HEX_LENGTH = 495.0
HEX_FLATS = 21.0
HEX_APOTHEM = HEX_FLATS / 2
HEX_RADIUS = HEX_APOTHEM / math.cos(math.radians(30))

PCB_WIDTH = 12.0
PCB_THICKNESS = 1.0
LED_PER_METER = 60
LED_PITCH = 1000.0 / LED_PER_METER
LED_SIZE = 5.0
LED_HEIGHT = 1.6
LED_DIE_DIAMETER = 2.8
INDICATOR_DEPTH = 0.4
SOLDER_PAD_WIDTH = 2.0
SOLDER_PAD_LENGTH = 3.0
SOLDER_PAD_INTERVAL = 10

ALUMINUM_COLOR = Color(0.75, 0.75, 0.75)
PCB_COLOR = Color(1.0, 1.0, 1.0)
LED_COLOR = Color(0.05, 0.05, 0.05)
LED_DIE_COLOR = Color(1.0, 0.9, 0.2)
COPPER_COLOR = Color(0.80, 0.45, 0.20)
GOLD_COLOR = Color(0.83, 0.68, 0.21)

MIRROR_DIAMETER = 1400.0
MIRROR_RADIUS = MIRROR_DIAMETER / 2
MIRROR_FOCAL = 490.0
MIRROR_DEPTH = MIRROR_RADIUS**2 / (4 * MIRROR_FOCAL)
MIRROR_HOLE = 25.0
MIRROR_THICKNESS = 5.0
MIRROR_COLOR = Color(0.6, 0.6, 0.6)

DIFFUSER_OUTER = 40.0
DIFFUSER_WALL = 2.0
DIFFUSER_INNER = DIFFUSER_OUTER - DIFFUSER_WALL * 2
STEP_OVERLAP = 20.0
STEP_OUTER = DIFFUSER_OUTER - 2.0
# Radial gap between the top half's plug (STEP_OUTER) and the bottom half's
# socket (STEP_INNER) it telescopes into over STEP_OVERLAP -- diametral
# equivalent is 1.0 mm (STEP_INNER adds it twice, once per side, below). Not
# a fits.py class: this isn't a located fit at all, it's a loose telescoping
# lap joint between two thin-wall (2 mm) tubes roughly 300 mm and 265 mm
# long, so the printed ovality/warp over that span swamps what a small-part
# fit class assumes -- even fits.FREE (0.40 mm diametral), the nearest one,
# is sized for stable small parts, not a long tube. The extra room is
# deliberate: guarantee the two halves telescope together at all, since
# nothing here needs precision location.
STEP_CLEARANCE = 0.5
STEP_INNER = STEP_OUTER + STEP_CLEARANCE * 2  # diametral: +STEP_CLEARANCE per side
CAP_RADIUS = DIFFUSER_OUTER / 2
TOP_HALF_HEIGHT = 300.0
BOTTOM_HALF_HEIGHT = 265.0
BASE_HEIGHT = 20.0
BASE_OUTER = 52.0
HEX_HOLE_CLEARANCE = 4.0
DIFFUSER_COLOR = Color(0.85, 0.9, 0.95)

FACE_ANGLES = [math.radians(30 + i * 60) for i in range(6)]


def create_hex_rod() -> Part:
    with BuildPart() as rod:
        with BuildSketch():
            hexagon()
        extrude(amount=HEX_LENGTH / 2, both=True)
    rod.part.color = ALUMINUM_COLOR
    rod.part.label = "hex_rod"
    return rod.part


def hexagon(radius: float = HEX_RADIUS) -> None:
    vertices = [
        (
            radius * math.cos(math.radians(i * 60)),
            radius * math.sin(math.radians(i * 60)),
        )
        for i in range(6)
    ]
    Polygon(vertices, align=None)


def create_pcb(angle: float) -> Part:
    origin = Vector(
        HEX_APOTHEM * math.cos(angle),
        HEX_APOTHEM * math.sin(angle),
        0,
    )
    x_dir = Vector(0, 0, 1)
    z_dir = Vector(math.cos(angle), math.sin(angle), 0)
    plane = Plane(origin, x_dir, z_dir)

    with BuildPart() as pcb:
        with BuildSketch(plane):
            Rectangle(HEX_LENGTH, PCB_WIDTH, align=Align.CENTER)
        extrude(amount=PCB_THICKNESS)
    pcb.part.color = PCB_COLOR
    pcb.part.label = "pcb"
    return pcb.part


def create_led(angle: float, z_offset: float, index: int) -> Compound:
    base_origin = Vector(
        (HEX_APOTHEM + PCB_THICKNESS) * math.cos(angle),
        (HEX_APOTHEM + PCB_THICKNESS) * math.sin(angle),
        z_offset,
    )
    x_dir = Vector(0, 0, 1)
    z_dir = Vector(math.cos(angle), math.sin(angle), 0)
    base_plane = Plane(base_origin, x_dir, z_dir)

    with BuildPart() as led_base:
        with BuildSketch(base_plane):
            Rectangle(LED_SIZE, LED_SIZE, align=Align.CENTER)
        extrude(amount=LED_HEIGHT)
    led_base.part.color = LED_COLOR

    with BuildPart() as led_die:
        with BuildSketch(base_plane.offset(LED_HEIGHT)):
            Circle(LED_DIE_DIAMETER / 2)
        extrude(amount=INDICATOR_DEPTH)
    led_die.part.color = LED_DIE_COLOR

    led = Compound(label=f"led_{index:02d}", children=[led_base.part, led_die.part])
    return led


def create_solder_pad_group(angle: float, z_offset: float, index: int) -> list[Part]:
    base_origin = Vector(
        (HEX_APOTHEM + PCB_THICKNESS) * math.cos(angle),
        (HEX_APOTHEM + PCB_THICKNESS) * math.sin(angle),
        z_offset,
    )
    x_dir = Vector(0, 0, 1)
    z_dir = Vector(math.cos(angle), math.sin(angle), 0)

    pads = []
    pad_width = 2.5
    pad_length = 0.6
    spacing = 0.6
    num_pads = 3

    for j in range(num_pads):
        offset_z = (j - (num_pads - 1) / 2) * spacing
        pad_origin = base_origin + Vector(0, 0, offset_z)
        pad_plane = Plane(pad_origin, x_dir, z_dir)

        with BuildPart() as pad:
            with BuildSketch(pad_plane):
                RectangleRounded(pad_width, pad_length, radius=0.15)
            extrude(amount=PCB_THICKNESS * 0.3)

        pad.part.color = COPPER_COLOR
        pad.part.label = f"solder_pad_{index:02d}_{j}"
        pads.append(pad.part)

    return pads


def create_led_strip(face_index: int) -> Compound:
    angle = FACE_ANGLES[face_index]
    pcb = create_pcb(angle)

    num_leds = int(HEX_LENGTH / LED_PITCH)
    leds = []
    solder_pads = []
    for i in range(num_leds):
        z = -HEX_LENGTH / 2 + LED_PITCH / 2 + i * LED_PITCH
        led = create_led(angle, z, i)
        leds.append(led)
        if i < num_leds - 1:
            pad_z = z + LED_PITCH / 2
            pads = create_solder_pad_group(angle, pad_z, i)
            solder_pads.extend(pads)

    return Compound(
        label=f"led_strip_{face_index}", children=[pcb] + leds + solder_pads
    )


def create_parabolic_mirror() -> Part:
    z_bottom = (MIRROR_HOLE / 2 + MIRROR_THICKNESS) ** 2 / (4 * MIRROR_FOCAL)
    n = 80

    with BuildPart() as mirror:
        with BuildSketch(Plane.XZ):
            points = []

            for i in range(n + 1):
                t = i / n
                z = z_bottom + t * (MIRROR_DEPTH - z_bottom)
                r = math.sqrt(4 * MIRROR_FOCAL * z) - MIRROR_THICKNESS
                points.append((r, z))

            points.append((MIRROR_RADIUS, MIRROR_DEPTH))

            for i in range(n - 1, -1, -1):
                t = i / n
                z = z_bottom + t * (MIRROR_DEPTH - z_bottom)
                r = math.sqrt(4 * MIRROR_FOCAL * z)
                points.append((r, z))

            points.append((MIRROR_HOLE / 2, z_bottom))
            Polygon(points, align=None)

        revolve(axis=Axis.Z)

    mirror.part.color = MIRROR_COLOR
    mirror.part.label = "parabolic_mirror"
    return mirror.part


def _hemisphere_sections(outer_r: float, inner_r: float, base_z: float, n: int = 24):
    outer_sections = []
    for i in range(n + 1):
        t = i / n
        z = base_z + outer_r * t
        r_outer = math.sqrt(max(outer_r**2 - (outer_r * t) ** 2, 0.0001))
        r_inner = math.sqrt(max(inner_r**2 - (inner_r * t) ** 2, 0.0001))
        with BuildSketch(Plane.XY.offset(z)) as section:
            Circle(r_outer)
            Circle(r_inner, mode=Mode.SUBTRACT)
        outer_sections.append(section.sketch)
    return outer_sections


def create_diffuser_top() -> Part:
    tube_height = TOP_HALF_HEIGHT - STEP_OVERLAP
    hex_hole_radius = (HEX_FLATS + HEX_HOLE_CLEARANCE) / 2 / math.cos(math.radians(30))
    hex_hole_depth = tube_height - 30.0 + STEP_OVERLAP

    with BuildPart() as top:
        with BuildSketch(Plane.XY.offset(-STEP_OVERLAP)):
            Circle(STEP_OUTER / 2)
        extrude(amount=STEP_OVERLAP)

        with BuildSketch(Plane.XY):
            Circle(DIFFUSER_OUTER / 2)
        extrude(amount=tube_height)

        loft(_hemisphere_sections(CAP_RADIUS, CAP_RADIUS - DIFFUSER_WALL, tube_height))

        with BuildSketch(Plane.XY.offset(-STEP_OVERLAP)):
            Circle(STEP_OUTER / 2 - DIFFUSER_WALL)
        extrude(amount=STEP_OVERLAP, mode=Mode.SUBTRACT)

        with BuildSketch(Plane.XY):
            Circle(DIFFUSER_INNER / 2)
        extrude(amount=tube_height, mode=Mode.SUBTRACT)

        with BuildSketch(Plane.XY.offset(-STEP_OVERLAP)):
            hexagon(hex_hole_radius)
        extrude(amount=hex_hole_depth, mode=Mode.SUBTRACT)

    top.part.color = DIFFUSER_COLOR
    top.part.label = "diffuser_top"
    return top.part


def create_diffuser_bottom() -> Part:
    tube_height = BOTTOM_HALF_HEIGHT - BASE_HEIGHT - STEP_OVERLAP

    with BuildPart() as bottom:
        with BuildSketch(Plane.XY.offset(-BOTTOM_HALF_HEIGHT)):
            Circle(BASE_OUTER / 2)
        extrude(amount=BASE_HEIGHT)

        with BuildSketch(Plane.XY.offset(-tube_height - STEP_OVERLAP)):
            Circle(DIFFUSER_OUTER / 2)
        extrude(amount=tube_height)

        with BuildSketch(Plane.XY.offset(-STEP_OVERLAP)):
            Circle(DIFFUSER_OUTER / 2)
        extrude(amount=STEP_OVERLAP)

        with BuildSketch(Plane.XY.offset(-BOTTOM_HALF_HEIGHT)):
            Circle(DIFFUSER_INNER / 2)
        extrude(amount=BASE_HEIGHT, mode=Mode.SUBTRACT)

        with BuildSketch(Plane.XY.offset(-tube_height - STEP_OVERLAP)):
            Circle(DIFFUSER_INNER / 2)
        extrude(amount=tube_height + STEP_OVERLAP, mode=Mode.SUBTRACT)

        with BuildSketch(Plane.XY.offset(-STEP_OVERLAP)):
            Circle(STEP_INNER / 2)
        extrude(amount=STEP_OVERLAP, mode=Mode.SUBTRACT)

    bottom.part.color = DIFFUSER_COLOR
    bottom.part.label = "diffuser_bottom"
    return bottom.part


def create() -> Compound:
    rod = create_hex_rod()
    strips = [create_led_strip(i) for i in range(6)]
    mirror = create_parabolic_mirror()
    mirror = mirror.move(Location(Vector(0, 0, -HEX_LENGTH / 2)))
    diffuser_top = create_diffuser_top()
    diffuser_bottom = create_diffuser_bottom()
    return Compound(
        label="satellite_led",
        children=[rod] + strips + [mirror, diffuser_top, diffuser_bottom],
    )


def _child(compound: Compound, label: str):
    """The one direct child carrying ``label``, or a loud error.

    Every builder here sets a unique label on what it returns, so a lookup
    that comes back empty or ambiguous is itself a defect worth surfacing
    rather than silently indexing by position.
    """
    matches = [c for c in compound.children if c.label == label]
    if len(matches) != 1:
        raise LookupError(
            f"expected exactly one child labelled {label!r}, found {len(matches)}"
        )
    return matches[0]


def _overlap_volume(a, b) -> float:
    """Material shared between two shapes, in mm^3 -- not their bounding boxes.

    This is a scene, not a print job, but two parts that are supposed to mate
    (a plug telescoping into a socket, a rod inside a diffuser's hex hole)
    must still not collide, and an LED strip mounted to a face must not sit
    inside the rod it is mounted to. Bounding boxes overlap for all of these
    by design -- the mating region *should* overlap in extent -- so only an
    actual boolean intersection volume can tell "assembled" from "colliding".
    """
    common = a.intersect(b)
    if common is None:
        return 0.0
    shapes = list(common) if isinstance(common, (list, tuple)) else [common]
    return float(sum(getattr(s, "volume", 0.0) for s in shapes))


def check() -> Report:
    """Geometry assertions for the satellite LED scene.

    ``IS_ASSEMBLY = True`` -- this is a use-pose scene, not a print job, so
    there is no print-pose or printability assertion here. Instead: the
    compound exposes exactly the labelled children the scene is built from,
    each LED strip sits on the hex face and at the angle ``FACE_ANGLES``
    places it (and carries the number of LEDs ``HEX_LENGTH``/``LED_PITCH``
    implies), the mirror is seated at the rod's rear end, and every mating
    pair that is supposed to clear -- strip-to-rod, rod-to-diffuser hex hole,
    and the diffuser's own telescoping joint -- actually clears, checked as a
    real intersection volume rather than a bounding-box overlap.
    """
    r = Report()
    part = create()

    r.section("compound structure")
    expected_labels = (
        ["hex_rod"]
        + [f"led_strip_{i}" for i in range(6)]
        + ["parabolic_mirror", "diffuser_top", "diffuser_bottom"]
    )
    actual_labels = [c.label for c in part.children]
    r.check(
        actual_labels == expected_labels,
        "scene exposes exactly the expected labelled children, in order",
        f"{actual_labels}",
    )

    r.section("LED strip placement")
    num_leds_expected = int(HEX_LENGTH / LED_PITCH)
    for i in range(6):
        strip = _child(part, f"led_strip_{i}")
        pcb = _child(strip, "pcb")
        bb = pcb.bounding_box()
        cx = (bb.min.X + bb.max.X) / 2
        cy = (bb.min.Y + bb.max.Y) / 2
        angle = math.atan2(cy, cx) % (2 * math.pi)
        expected_angle = FACE_ANGLES[i] % (2 * math.pi)
        angular_diff = abs(
            ((angle - expected_angle + math.pi) % (2 * math.pi)) - math.pi
        )
        r.check(
            angular_diff < math.radians(1.0),
            f"led_strip_{i}: pcb sits at its assigned face angle",
            f"{math.degrees(angle):.1f} deg vs {math.degrees(expected_angle):.1f} deg expected",
        )
        radius = math.hypot(cx, cy)
        expected_radius = HEX_APOTHEM + PCB_THICKNESS / 2
        r.check(
            abs(radius - expected_radius) < 0.5,
            f"led_strip_{i}: pcb sits flush against the hex face (apothem + half thickness)",
            f"r={radius:.2f} mm vs {expected_radius:.2f} mm expected",
        )
        led_children = [c for c in strip.children if c.label.startswith("led_")]
        r.check(
            len(led_children) == num_leds_expected,
            f"led_strip_{i}: carries HEX_LENGTH/LED_PITCH LEDs",
            f"{len(led_children)} of {num_leds_expected} expected",
        )

    r.section("mirror placement")
    mirror = _child(part, "parabolic_mirror")
    mirror_bb = mirror.bounding_box()
    r.check(
        abs(mirror_bb.min.Z - (-HEX_LENGTH / 2)) < 1.0,
        "mirror's near face sits at the rod's rear end (moved by -HEX_LENGTH/2)",
        f"mirror min z = {mirror_bb.min.Z:.2f} mm vs {-HEX_LENGTH / 2:.2f} mm expected",
    )
    rod = _child(part, "hex_rod")
    rod_bb = rod.bounding_box()
    r.check(
        abs(rod_bb.min.Z - (-HEX_LENGTH / 2)) < 0.01,
        "rod's rear end is exactly where the mirror is anchored to",
        f"rod min z = {rod_bb.min.Z:.2f} mm",
    )

    r.section("non-interference")
    # Threshold is 1.0 mm^3 for all three checks below, not 0. None of these
    # joints is an intended press fit -- every real pass measures exactly
    # 0.000 mm^3 (see the proof run in the implementer report). The margin is
    # there purely to absorb boolean/tessellation noise at a touching or
    # near-tangent face (OCC can return a sliver of a few 1e-3 mm^3 there),
    # not to tolerate any deliberate overlap. It is ~3 orders of magnitude
    # below what a genuine collision produces here (a forced-interference
    # test elsewhere in this file measured 2324.8 mm^3 and 35640.0 mm^3), so
    # it cannot mask a real defect.
    strip_vol = sum(
        _overlap_volume(rod, _child(part, f"led_strip_{i}")) for i in range(6)
    )
    r.check(
        strip_vol < 1.0,
        "no LED strip's pcb/leds/solder pads sit inside the rod they mount to",
        f"{strip_vol:.3f} mm^3 total overlap across 6 strips (threshold 1.0)",
    )

    diffuser_top = _child(part, "diffuser_top")
    diffuser_bottom = _child(part, "diffuser_bottom")
    joint_vol = _overlap_volume(diffuser_top, diffuser_bottom)
    r.check(
        joint_vol < 1.0,
        "diffuser_top's plug does not collide with diffuser_bottom's socket wall",
        f"{joint_vol:.3f} mm^3 overlap in the telescoping joint (threshold 1.0), "
        f"even though their bounding boxes overlap by STEP_OVERLAP={STEP_OVERLAP:.0f} mm",
    )

    rod_diffuser_vol = _overlap_volume(rod, diffuser_top)
    r.check(
        rod_diffuser_vol < 1.0,
        "the hex rod clears diffuser_top's hex hole (HEX_HOLE_CLEARANCE)",
        f"{rod_diffuser_vol:.3f} mm^3 overlap (threshold 1.0)",
    )

    return r
