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

from models.lib.checks import Report, is_solid_at

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


def _generate_section_points(
    z: float, inner: bool = False
) -> list[tuple[float, float]]:
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


def check() -> Report:
    """Geometry assertions for the spiral-vase print.

    This is a single-wall vase-mode print, so the assertion that matters most
    is that the modelled 0.8 mm wall is what actually got built -- point
    sampled through the shell, not re-derived from the same constant the
    geometry used, since that would pass even if ``create()`` stopped
    honouring ``WALL_THICKNESS``. Also checks: the part is one continuous
    hollow shell (no accidental solid disc at the base or a split shell),
    the taper direction (150 mm base to 100 mm top), that the rib pattern
    genuinely twists 90 deg from bottom to top, and the top lip's opening for
    a pendant cable.
    """
    r = Report()
    part = create()
    bb = part.bounding_box()

    r.section("print pose")
    r.check(
        abs(bb.min.Z) < 0.01,
        "sits on the build plate (min z = 0)",
        f"min z = {bb.min.Z:.3f} mm",
    )
    r.check(
        len(part.solids()) == 1,
        "is a single continuous solid, not a split or disjoint shell",
        f"{len(part.solids())} solid(s)",
    )

    r.section("vase-mode wall thickness")
    # Two perimeters of a 0.4 mm nozzle is the floor below which a wall does
    # not slice as a wall at all -- it merges with whatever is next to it.
    r.check(
        WALL_THICKNESS >= 0.79,
        "wall clears the 2-perimeter floor for a 0.4 mm nozzle",
        f"{WALL_THICKNESS:.2f} mm (min 0.80 mm)",
    )
    r.check(
        WALL_THICKNESS <= 1.2,
        "wall stays thin enough to still read as vase-mode single-wall",
        f"{WALL_THICKNESS:.2f} mm",
    )

    def probe_shell(z: float, angle: float, label: str) -> None:
        """Point-sample the actual solid at (z, angle): outer surface at the
        radius the formula predicts, and a hollow gap WALL_THICKNESS inside
        it. Proves the built loft -- not just the formula -- has the wall the
        module docstring promises."""
        r_outer = _radius_at_height(z) + _rib_modulation(angle, z)
        ux, uy = math.cos(angle), math.sin(angle)

        def at(radius: float) -> tuple[float, float, float]:
            return (ux * radius, uy * radius, z)

        r.check(
            is_solid_at(part, *at(r_outer - 0.2)),
            f"{label}: material just inside the outer wall",
            f"r={r_outer:.2f} at z={z:.1f}, angle={math.degrees(angle):.0f} deg",
        )
        r.check(
            not is_solid_at(part, *at(r_outer + 0.2)),
            f"{label}: void just outside the outer wall",
            f"r={r_outer:.2f}",
        )
        r_inner = r_outer - WALL_THICKNESS
        r.check(
            not is_solid_at(part, *at(r_inner - 0.2)),
            f"{label}: hollow past the inner wall (WALL_THICKNESS in)",
            f"r={r_inner:.2f}",
        )
        r.check(
            is_solid_at(part, *at((r_outer + r_inner) / 2)),
            f"{label}: solid mid-wall between inner and outer surfaces",
            f"r={(r_outer + r_inner) / 2:.2f}",
        )

    probe_shell(HEIGHT * 5 / Z_SECTIONS, 0.0, "low band")
    probe_shell(HEIGHT * 15 / Z_SECTIONS, math.pi / 3, "mid band")
    probe_shell(HEIGHT * 25 / Z_SECTIONS, math.pi, "high band")

    r.section("taper")
    # sin(2*pi*WAVE_CYCLES*t) is exactly 0 at t=0 and t=1, so a point just off
    # each end is unaffected by the wave and only varies with the rib (0..3
    # mm) -- an honest place to compare base and top radius.
    z_base, z_top = 0.3, HEIGHT - 0.3
    angle = 0.7
    r_base = _radius_at_height(z_base) + _rib_modulation(angle, z_base)
    r_top = _radius_at_height(z_top) + _rib_modulation(angle, z_top)
    r.check(
        r_base - r_top > 15.0,
        "base radius is substantially larger than the top radius (150->100mm taper)",
        f"base r={r_base:.1f} mm, top r={r_top:.1f} mm, diff={r_base - r_top:.1f} mm",
    )
    probe_shell(z_base, angle, "taper: base")
    probe_shell(z_top, angle, "taper: top")

    r.section("rib twist")
    i_low, i_high = 3, 27
    z_low, z_high = HEIGHT * i_low / Z_SECTIONS, HEIGHT * i_high / Z_SECTIONS
    t_low, t_high = i_low / Z_SECTIONS, i_high / Z_SECTIONS
    peak_low = math.radians(TWIST_ANGLE) * t_low
    peak_high = math.radians(TWIST_ANGLE) * t_high
    probe_shell(z_low, peak_low, "twist: low-band rib peak")
    probe_shell(z_high, peak_high, "twist: high-band rib peak")

    # At the high band, the untwisted angle (0 deg) must NOT be where the rib
    # peak now sits -- proving the pattern actually rotated with height,
    # rather than every rib staying fixed at its bottom angular position.
    r_peak_high = _radius_at_height(z_high) + _rib_modulation(peak_high, z_high)
    r_untwisted_high = _radius_at_height(z_high) + _rib_modulation(0.0, z_high)
    r.check(
        r_peak_high - r_untwisted_high > 1.0,
        "at the high band, the rib peak has moved away from its bottom-band angle",
        f"peak r={r_peak_high:.2f} mm vs angle=0 r={r_untwisted_high:.2f} mm",
    )
    # A solid-probed twist-rate check: the low band's own peak radius (just
    # inside it, matching probe_shell's convention) is real material at the
    # low band's peak angle -- but sampled at the *high* band's peak angle,
    # at the *same* low-band height, it must be void. If the rib pattern
    # didn't genuinely rotate by TWIST_ANGLE with height (e.g. TWIST_ANGLE
    # were 0, so the two peak angles coincide), this would still be solid --
    # unlike the deleted check it replaces, this touches the built loft, not
    # just the formula on both sides of a comparison.
    r_peak_low = _radius_at_height(z_low) + _rib_modulation(peak_low, z_low)
    probe_r = r_peak_low - 0.2
    ux, uy = math.cos(peak_high), math.sin(peak_high)
    r.check(
        not is_solid_at(part, ux * probe_r, uy * probe_r, z_low),
        "low band's peak radius is not reached at the high band's peak angle -- the peak really rotated",
        f"z={z_low:.1f}, angle={math.degrees(peak_high):.0f} deg probed at r={probe_r:.2f} "
        f"(low band's own peak radius, less the usual 0.2 mm probe offset)",
    )

    r.section("top lip")
    r_lip_outer = _radius_at_height(HEIGHT) + RIB_DEPTH * 0.5
    r_lip_inner = r_lip_outer - LIP_INWARD
    z_lip = HEIGHT + LIP_HEIGHT / 2
    r.check(
        is_solid_at(part, (r_lip_outer + r_lip_inner) / 2, 0.0, z_lip),
        "lip ring is solid between its inner and outer radius",
        f"r={(r_lip_outer + r_lip_inner) / 2:.1f} mm at z={z_lip:.1f}",
    )
    r.check(
        not is_solid_at(part, r_lip_inner - 3.0, 0.0, z_lip),
        "lip opens inward, clear for a pendant cable/mount",
        f"void at r={r_lip_inner - 3.0:.1f} mm",
    )
    r.check(
        not is_solid_at(part, r_lip_outer + 3.0, 0.0, z_lip),
        "lip does not extend past its own outer radius",
        f"void at r={r_lip_outer + 3.0:.1f} mm",
    )
    r.check(
        abs(bb.max.Z - (HEIGHT + LIP_HEIGHT)) < 0.5,
        "overall height matches HEIGHT + LIP_HEIGHT",
        f"{bb.max.Z:.2f} mm vs {HEIGHT + LIP_HEIGHT:.2f} mm expected",
    )

    return r
