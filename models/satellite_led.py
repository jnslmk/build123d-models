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
    export_step,
    export_stl,
    extrude,
    loft,
    revolve,
)
from ocp_vscode import show

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
STEP_CLEARANCE = 0.5
STEP_INNER = STEP_OUTER + STEP_CLEARANCE * 2
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


def main() -> None:
    part = create()
    show(part)
    export_step(part, "exports/satellite_led.step")
    export_stl(part, "exports/satellite_led.stl")


if __name__ == "__main__":
    main()
