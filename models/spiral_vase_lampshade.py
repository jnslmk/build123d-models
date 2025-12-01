"""Spiral vase lampshade with twisted ribs and breathing wave profile."""

import math

from build123d import (
    BuildLine,
    BuildPart,
    BuildSketch,
    Circle,
    Mode,
    Part,
    Plane,
    Spline,
    extrude,
    loft,
    make_face,
)

# Overall dimensions
BASE_DIAMETER = 150.0
TOP_DIAMETER = 100.0
HEIGHT = 200.0
WALL_THICKNESS = 0.8

# Wave breathing effect
WAVE_AMPLITUDE = 12.0  # ±12mm radial modulation
WAVE_CYCLES = 3  # number of in/out cycles over height

# Twisted rib pattern
NUM_RIBS = 8
RIB_DEPTH = 3.0  # radial protrusion
TWIST_ANGLE = 90.0  # degrees of rotation over full height

# Top ring lip
LIP_INWARD = 15.0
LIP_HEIGHT = 5.0

# Resolution
Z_SECTIONS = 30  # number of loft sections
ANGULAR_POINTS = 64  # points per cross-section


def _radius_at_height(z: float) -> float:
    """Calculate base radius at height z (before rib modulation)."""
    t = z / HEIGHT
    base_r = BASE_DIAMETER / 2
    top_r = TOP_DIAMETER / 2
    linear_r = base_r + t * (top_r - base_r)

    # Add wave breathing modulation
    wave = WAVE_AMPLITUDE * math.sin(2 * math.pi * WAVE_CYCLES * t)
    return linear_r + wave


def _rib_modulation(angle: float, z: float) -> float:
    """Calculate rib protrusion at given angle and height."""
    t = z / HEIGHT
    twisted_angle = angle - math.radians(TWIST_ANGLE) * t

    # 8 ribs evenly spaced - smooth cosine bumps
    rib_phase = NUM_RIBS * twisted_angle
    modulation = (math.cos(rib_phase) + 1) / 2  # 0 to 1
    modulation = modulation**2  # sharpen peaks
    return RIB_DEPTH * modulation


def _generate_section_points(z: float, inner: bool = False) -> list[tuple[float, float]]:
    """Generate points for a cross-section at height z."""
    points = []
    base_r = _radius_at_height(z)

    for i in range(ANGULAR_POINTS):
        angle = 2 * math.pi * i / ANGULAR_POINTS
        rib = _rib_modulation(angle, z)
        r = base_r + rib
        if inner:
            r -= WALL_THICKNESS
        x = r * math.cos(angle)
        y = r * math.sin(angle)
        points.append((x, y))

    return points


def _create_section_sketch(z: float, inner: bool = False) -> BuildSketch:
    """Create a sketch for a cross-section at height z."""
    points = _generate_section_points(z, inner)
    plane = Plane.XY.offset(z)

    with BuildSketch(plane) as sketch:
        with BuildLine():
            Spline(points, periodic=True)
        make_face()

    return sketch


def create() -> Part:
    """Create a spiral vase lampshade with twisted ribs and wave profile.

    The lampshade features:
    - 8 twisted ribs spiraling 90° from bottom to top
    - Wave "breathing" profile with 3 cycles (±12mm)
    - Tapered shape from 150mm base to 100mm top
    - Inward ring lip at top for pendant mounting
    - 0.8mm wall thickness for vase mode printing
    """
    # Generate cross-sections at different heights for outer and inner walls
    outer_sketches = []
    inner_sketches = []

    for i in range(Z_SECTIONS + 1):
        z = HEIGHT * i / Z_SECTIONS
        outer_sketches.append(_create_section_sketch(z, inner=False))
        inner_sketches.append(_create_section_sketch(z, inner=True))

    with BuildPart() as builder:
        # Create outer shell by lofting
        loft([s.sketch for s in outer_sketches])

        # Hollow out by subtracting inner loft
        loft([s.sketch for s in inner_sketches], mode=Mode.SUBTRACT)

        # Add ring lip at top for pendant mounting
        # Create a ring that goes inward from the top edge
        r_top = _radius_at_height(HEIGHT) + RIB_DEPTH * 0.5
        r_lip_inner = r_top - LIP_INWARD

        with BuildSketch(Plane.XY.offset(HEIGHT)):
            Circle(r_top)
            Circle(r_lip_inner, mode=Mode.SUBTRACT)
        extrude(amount=LIP_HEIGHT)

    return builder.part
