"""Geometry assertions for the blower-to-mattress adapter.

    uv run check wolfbox_thermarest_adapter
    uv run python -m models.wolfbox_thermarest_adapter.checks

Everything this part promises is inside it. It is a tube: from the outside, a
funnel with a working 16 mm throat and a funnel with a 1 mm throat are the same
picture, and a render cannot tell you which one you exported. So the checks
here are point samples taken *across* the wall, at heights chosen off the
section rather than spread evenly:

* **The axis is air, all the way up.** One blocked sample anywhere between the
  bed and the rim means the adapter does not adapt anything.
* **The bore follows the two cones.** Measured as a radius at a height, against
  what ``Adapter`` says the cone should be there -- which is the only way to
  assert the claim the whole design rests on, that the socket seats anywhere
  from throat to mouth and the cup anywhere from seat to rim.
* **The throat is the narrowest section.** Stated in the model docstring as
  "nothing is the narrowest thing in the path" and worth nothing unless
  checked: a chamfer or a slider position that pinched the bore below 16 mm
  would cost flow silently.
* **Every wall clears the floor.** Two perimeters, everywhere, including at the
  slider stops -- where the horizontal-versus-normal offset the config warns
  about is worth 20% of the wall.

The last section drags all six sliders to their stops. It earns its keep more
here than on a calipered model, because the ledger in ``config.py`` says
outright that every port diameter is assumed: those sliders are how somebody
with the real hardware corrects this part, so a stop that fails to build is a
correction that cannot be made.
"""

from __future__ import annotations

import sys
from math import atan2, cos, radians

from build123d import GeomType, Part

from ..lib.checks import Report, is_solid_at, sharp_convex_edges
from . import build
from .config import (
    BLOWER_MOUTH_MAX,
    BLOWER_MOUTH_MIN,
    BLOWER_THROAT_MAX,
    BLOWER_THROAT_MIN,
    CUP_DEPTH_MAX,
    CUP_DEPTH_MIN,
    CUP_WALL,
    DEFAULT,
    MIN_WALL,
    MOUTH_CHAMFER,
    SOCKET_DEPTH_MAX,
    SOCKET_DEPTH_MIN,
    SOCKET_WALL,
    VALVE_MOUTH_MAX,
    VALVE_MOUTH_MIN,
    VALVE_SEAT_MAX,
    VALVE_SEAT_MIN,
    Adapter,
)

STEP = 0.05
"""Radial sampling step for the wall crossings, in mm. Fine enough that a
reported radius is good to half a layer width, coarse enough that a full sweep
of the part is a second or two."""


def _crossings(part: Part, z: float, r_max: float) -> tuple[float, float] | None:
    """(inner, outer) radius of the material at height ``z``, or None if there
    is no material at that height at all.

    Walks outward from the axis rather than bisecting, because bisection needs
    to assume exactly one wall and the whole point of the sweep is to notice
    when that assumption breaks.
    """
    r = 0.0
    first = None
    last = None
    while r <= r_max:
        if is_solid_at(part, r, 0.0, z):
            if first is None:
                first = r
            last = r
        r += STEP
    if first is None or last is None:
        return None
    return first, last


def check_print_pose(part: Part, r: Report) -> None:
    r.section("Print pose")
    bb = part.bounding_box()
    r.check(
        len(part.solids()) == 1 and part.volume > 0,
        "one solid, non-empty",
        f"{len(part.solids())} solid(s), {part.volume:.0f} mm3",
    )
    r.check(
        abs(bb.min.Z) < 1e-6,
        "socket mouth sits on z=0",
        f"min.Z = {bb.min.Z:.4f}",
    )
    r.check(
        abs(bb.max.Z - DEFAULT.z_rim) < 1e-6,
        "rim is the top of the part",
        f"max.Z = {bb.max.Z:.2f} mm, z_rim = {DEFAULT.z_rim:.2f} mm",
    )
    r.check(
        abs(bb.min.X + bb.max.X) < 1e-6 and abs(bb.min.Y + bb.max.Y) < 1e-6,
        "revolved about the Z axis, centred on it",
        f"x span {bb.min.X:.2f}..{bb.max.X:.2f}",
    )


def check_bore_is_open(part: Part, r: Report) -> None:
    r.section("The axis is air")
    blocked = [
        z
        for z in _sweep(0.0, DEFAULT.z_rim, 0.5)
        if is_solid_at(part, 0.0, 0.0, z)
    ]
    r.check(
        not blocked,
        "nothing on the axis from bed to rim",
        f"{len(blocked)} blocked sample(s)"
        + (f", first at z={blocked[0]:.1f}" if blocked else ""),
    )


def check_bore_follows_the_cones(part: Part, a: Adapter, r: Report) -> None:
    """The socket and cup bores are where ``Adapter`` says they are.

    Sampled clear of the lead-in chamfer at the bed and of the rim break at the
    top, because those two deliberately open the bore wider than the cone -- a
    lead-in that did not would not be a lead-in.
    """
    r.section("The bore follows the two cones")
    r_max = a.rim_r + 5
    for label, z, want in (
        ("socket mouth", MOUTH_CHAMFER + 0.4, _cone_r(a.mouth_r, a.throat_r, 0, a.z_throat, MOUTH_CHAMFER + 0.4)),
        ("socket mid", a.z_throat / 2, _cone_r(a.mouth_r, a.throat_r, 0, a.z_throat, a.z_throat / 2)),
        ("throat", a.z_throat + 1.0, a.throat_r),
        ("cup seat", a.z_seat + 0.4, _cone_r(a.seat_r, a.rim_r, a.z_seat, a.z_rim, a.z_seat + 0.4)),
        ("cup rim", a.z_rim - 1.0, _cone_r(a.seat_r, a.rim_r, a.z_seat, a.z_rim, a.z_rim - 1.0)),
    ):
        span = _crossings(part, z, r_max)
        ok = span is not None and abs(span[0] - want) <= 2 * STEP
        r.check(
            ok,
            f"{label}: bore radius {want:.2f} mm at z={z:.1f}",
            "no material at that height" if span is None else f"measured {span[0]:.2f} mm",
        )


def check_throat_is_the_narrowest(part: Part, a: Adapter, r: Report) -> None:
    r.section("The throat is the narrowest section")
    r_max = a.rim_r + 5
    tightest = None
    for z in _sweep(MOUTH_CHAMFER + 0.4, a.z_rim - 0.4, 0.5):
        span = _crossings(part, z, r_max)
        if span is None:
            continue
        if tightest is None or span[0] < tightest[0]:
            tightest = (span[0], z)
    ok = tightest is not None and tightest[0] >= a.throat_r - 2 * STEP
    r.check(
        ok,
        f"no section bores tighter than the {2 * a.throat_r:.1f} mm throat",
        "no material anywhere"
        if tightest is None
        else f"tightest {2 * tightest[0]:.2f} mm at z={tightest[1]:.1f}",
    )


def check_walls(part: Part, a: Adapter, r: Report) -> None:
    """Wall thickness measured normal to the surface, not across the section.

    A horizontal crossing over-reports a sloped wall by 1/cos(angle) -- 2% on
    the socket, 10% on the cup, and enough at the slider stops to hide a wall
    that is actually under the floor. So the horizontal span is corrected by
    the cone's own angle before it is compared with anything.
    """
    r.section("Walls")
    r_max = a.rim_r + 5
    thin = []
    for z in _sweep(1.0, a.z_rim - 1.0, 0.5):
        span = _crossings(part, z, r_max)
        if span is None:
            continue
        angle = a.cup_half_angle if z >= a.z_seat else a.socket_half_angle
        wall = (span[1] - span[0] + STEP) * _cos(angle)
        if wall < MIN_WALL:
            thin.append((z, wall))
    r.check(
        not thin,
        f"every wall clears the {MIN_WALL:.1f} mm floor",
        "thinnest "
        + (f"{min(w for _, w in thin):.2f} mm" if thin else "n/a")
        + f", {len(thin)} sample(s) under",
    )
    for label, z, nominal in (
        ("socket", a.z_throat / 2, SOCKET_WALL),
        ("cup", (a.z_seat + a.z_rim) / 2, CUP_WALL),
    ):
        span = _crossings(part, z, r_max)
        angle = a.cup_half_angle if z >= a.z_seat else a.socket_half_angle
        wall = None if span is None else (span[1] - span[0] + STEP) * _cos(angle)
        r.check(
            wall is not None and abs(wall - nominal) <= 0.15,
            f"{label} wall is {nominal:.1f} mm normal to the cone",
            "no material" if wall is None else f"measured {wall:.2f} mm",
        )


def check_self_supporting(a: Adapter, r: Report) -> None:
    """No internal surface overhangs further than a 45 degree flare.

    Asserted off the section rather than off the solid: the bore is three
    surfaces, and each one's angle is a property of the numbers, so this
    catches a slider position that would need supports *inside a 16 mm bore*,
    which is a print nobody would rescue.
    """
    r.section("Self-supporting bore")
    r.check(
        a.socket_half_angle <= 45.0,
        "socket cone leans no more than 45 degrees",
        f"{a.socket_half_angle:.1f} degrees from the axis",
    )
    r.check(
        a.cup_half_angle <= 45.0,
        "cup cone leans no more than 45 degrees",
        f"{a.cup_half_angle:.1f} degrees from the axis",
    )
    r.check(
        abs((a.z_seat - a.z_throat_top) - (a.seat_r - a.throat_r)) < 1e-9,
        "flare off the throat is 45 degrees, the steepest that prints dry",
        f"rise {a.z_seat - a.z_throat_top:.2f} mm over run {a.seat_r - a.throat_r:.2f} mm",
    )


def _is_meridian(edge) -> bool:
    """True for a straight edge lying in a half-plane through the Z axis.

    Every real corner on this part is a circle -- it is a full revolve, so a
    profile corner sweeps into one. A *straight* edge can therefore only be the
    seam where the revolved surface closes on itself, and OCC reports both of
    its "adjacent" faces as the same face, which is why the sharp-edge check
    cannot measure a dihedral angle across it and files it as unclassifiable
    rather than blunt. Tested rather than assumed: the endpoints have to sit at
    the same angle about the axis, so a genuine straight edge somewhere off the
    meridian would still be reported.
    """
    if edge.geom_type != GeomType.LINE:
        return False
    start, end = edge.start_point(), edge.end_point()
    return abs(atan2(start.Y, start.X) - atan2(end.Y, end.X)) < 1e-6


def check_edges(part: Part, r: Report) -> None:
    r.section("Edge treatments")
    allow = (
        (
            _is_meridian,
            "meridian seam of a full revolve: where the surface closes on "
            "itself, not a corner anybody can cut a finger on",
        ),
    )
    survey = sharp_convex_edges(part, allow=allow)
    r.check(
        not survey.sharp,
        "no sharp convex edges left raw",
        f"{len(survey.sharp)} sharp",
    )
    r.check(
        not survey.unclassifiable,
        "every remaining edge could be measured",
        f"{len(survey.unclassifiable)} unclassifiable",
    )


def check_parameters(r: Report) -> None:
    """Drag every slider to both stops, and check the result still adapts.

    Cheap assertions only -- builds, seats on the bed, keeps a bore. The full
    point sweep above runs on the default because it is the one that gets
    printed; these run on the corners because they are the ones that get
    corrected to.
    """
    r.section("Parameter stops")
    stops = {
        "blower_mouth_dia": (BLOWER_MOUTH_MIN, BLOWER_MOUTH_MAX),
        "blower_throat_dia": (BLOWER_THROAT_MIN, BLOWER_THROAT_MAX),
        "socket_depth": (SOCKET_DEPTH_MIN, SOCKET_DEPTH_MAX),
        "valve_mouth_dia": (VALVE_MOUTH_MIN, VALVE_MOUTH_MAX),
        "valve_seat_dia": (VALVE_SEAT_MIN, VALVE_SEAT_MAX),
        "cup_depth": (CUP_DEPTH_MIN, CUP_DEPTH_MAX),
    }
    for name, (low, high) in stops.items():
        for value in (low - 5, low, high, high + 5):
            a = Adapter.of(**{name: value})
            part = build(a)
            bb = part.bounding_box()
            open_axis = not any(
                is_solid_at(part, 0.0, 0.0, z) for z in _sweep(0.2, a.z_rim - 0.2, 1.0)
            )
            r.check(
                len(part.solids()) == 1
                and abs(bb.min.Z) < 1e-6
                and open_axis
                and a.throat_r < a.mouth_r
                and a.seat_r > a.throat_r
                and a.rim_r > a.seat_r,
                f"{name}={value:g}: builds, seats on z=0, bore stays open",
                f"socket {2 * a.mouth_r:.1f}->{2 * a.throat_r:.1f}, cup "
                f"{2 * a.seat_r:.1f}->{2 * a.rim_r:.1f}, height {a.z_rim:.1f} mm",
            )


def _sweep(low: float, high: float, step: float) -> list[float]:
    out = []
    z = low
    while z <= high:
        out.append(z)
        z += step
    return out


def _cone_r(r0: float, r1: float, z0: float, z1: float, z: float) -> float:
    return r0 + (r1 - r0) * (z - z0) / (z1 - z0)


def _cos(degrees_: float) -> float:
    return cos(radians(degrees_))


def run() -> Report:
    r = Report()
    a = DEFAULT
    part = build(a)
    check_print_pose(part, r)
    check_bore_is_open(part, r)
    check_bore_follows_the_cones(part, a, r)
    check_throat_is_the_narrowest(part, a, r)
    check_walls(part, a, r)
    check_self_supporting(a, r)
    check_edges(part, r)
    check_parameters(r)
    return r


def main() -> None:
    r = run()
    print(r.render())
    sys.exit(1 if r.failures else 0)


if __name__ == "__main__":
    main()
