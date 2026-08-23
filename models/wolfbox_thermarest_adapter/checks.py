"""Geometry assertions for both blower-to-mattress adapters.

    uv run check wolfbox_thermarest_adapter
    uv run python -m models.wolfbox_thermarest_adapter.checks

Everything these parts promise is inside them. They are tubes: from the
outside, a funnel with a working 16 mm throat and a funnel with a 1 mm throat
are the same picture, and a render cannot tell you which one you exported. So
the checks here are point samples taken *across* the wall, at heights read off
each part's own bore profile rather than spread evenly:

* **The axis is air, all the way up.** One blocked sample anywhere between the
  bed and the rim means the adapter does not adapt anything.
* **The bore follows its profile.** Measured as a radius at a height, against
  what ``bore_profile`` says the surface should be there -- which is the only
  way to assert the claim both designs rest on, that a cone seats wherever it
  happens to meet the thing it is put on.
* **The throat is the narrowest section.** Stated in both docstrings as
  "nothing is the narrowest thing in the path" and worth nothing unless
  checked: a chamfer or a slider position that pinched the bore would cost flow
  silently.
* **Every wall clears the floor.** Two perimeters, everywhere, including at the
  slider stops -- where the horizontal-versus-normal offset the config warns
  about is worth 20% of the wall.
* **Nothing in the bore overhangs past 45 degrees.** Only the segments where
  the bore *narrows* as it rises can overhang at all, and the deflate
  adapter's shoulder sits exactly on the limit -- which makes it the one number
  in either part that a careless slider could turn into a print that needs
  supports inside a 20 mm bore.

The parameter section drags every slider on both parts to its stops. It earns
its keep more here than on a calipered model, because the ledger in
``config.py`` says outright that every port diameter is assumed: those sliders
are how somebody with the real hardware corrects these parts, so a stop that
fails to build is a correction that cannot be made.

**Both parts are measured through one set of functions.** They differ only in
how many cones their bore is made of -- two for the inflate adapter, four for
the deflate one -- and a check written against ``bore_profile`` does not care,
so a claim proved for one is proved for the other in the same words.
"""

from __future__ import annotations

import sys
from math import atan2, cos, degrees, radians
from typing import Callable

from build123d import GeomType, Part, Vector

from ..lib.checks import Report, sharp_convex_edges, solid_probe
from . import bore_profile, build
from . import deflate as deflate_model
from .config import (
    BLOWER_MOUTH_MAX,
    BLOWER_MOUTH_MIN,
    BLOWER_THROAT_MAX,
    BLOWER_THROAT_MIN,
    BODY_MOUTH_MAX,
    BODY_MOUTH_MIN,
    BODY_SEAT_MAX,
    BODY_SEAT_MIN,
    CAP_DEPTH_MAX,
    CAP_DEPTH_MIN,
    CAP_WALL,
    CUP_DEPTH_MAX,
    CUP_DEPTH_MIN,
    CUP_WALL,
    DEFAULT,
    INTAKE_DEFAULT,
    MIN_WALL,
    MOUTH_CHAMFER,
    NECK_WALL,
    SOCKET_DEPTH_MAX,
    SOCKET_DEPTH_MIN,
    SOCKET_WALL,
    VALVE_MOUTH_MAX,
    VALVE_MOUTH_MIN,
    VALVE_SEAT_MAX,
    VALVE_SEAT_MIN,
    Adapter,
    IntakeAdapter,
)
from .profile import Point, local_half_angle

STEP = 0.05
"""Radial sampling step for the wall crossings, in mm. Fine enough that a
reported radius is good to half a layer width, coarse enough that a full sweep
of both parts is a second or two."""

Probe = Callable[[Vector], bool]


def _crossings(inside: Probe, z: float, r_max: float) -> tuple[float, float] | None:
    """(inner, outer) radius of the material at height ``z``, or None if there
    is no material at that height at all.

    Walks outward from the axis rather than bisecting, because bisection needs
    to assume exactly one wall and the whole point of the sweep is to notice
    when that assumption breaks. Takes a probe from ``solid_probe`` rather than
    calling ``is_solid_at``: at this step size one sweep is several hundred
    samples of the same solid, and a classifier built per sample is the
    difference between a check that runs in seconds and one that runs in
    minutes.
    """
    r = 0.0
    first = None
    last = None
    while r <= r_max:
        if inside(Vector(r, 0.0, z)):
            if first is None:
                first = r
            last = r
        r += STEP
    if first is None or last is None:
        return None
    return first, last


def check_print_pose(part: Part, top: float, r: Report) -> None:
    bb = part.bounding_box()
    r.check(
        len(part.solids()) == 1 and part.volume > 0,
        "one solid, non-empty",
        f"{len(part.solids())} solid(s), {part.volume:.0f} mm3",
    )
    r.check(
        abs(bb.min.Z) < 1e-6,
        "mouth sits on z=0",
        f"min.Z = {bb.min.Z:.4f}",
    )
    r.check(
        abs(bb.max.Z - top) < 1e-6,
        "rim is the top of the part",
        f"max.Z = {bb.max.Z:.2f} mm, z_rim = {top:.2f} mm",
    )
    r.check(
        abs(bb.min.X + bb.max.X) < 1e-6 and abs(bb.min.Y + bb.max.Y) < 1e-6,
        "revolved about the Z axis, centred on it",
        f"x span {bb.min.X:.2f}..{bb.max.X:.2f}",
    )


def check_bore_is_open(inside: Probe, top: float, r: Report) -> None:
    blocked = [z for z in _sweep(0.0, top, 0.5) if inside(Vector(0.0, 0.0, z))]
    r.check(
        not blocked,
        "nothing on the axis from bed to rim",
        f"{len(blocked)} blocked sample(s)"
        + (f", first at z={blocked[0]:.1f}" if blocked else ""),
    )


def check_bore_follows_the_profile(
    inside: Probe, bore: list[Point], r_max: float, r: Report
) -> None:
    """The bore is where ``bore_profile`` says it is, on every segment.

    Three samples per segment rather than a hand-picked list, so a part whose
    bore grows a cone (which is exactly what the deflate adapter did to the
    inflate adapter's) is covered without anybody remembering to add a row.
    Sampled clear of the lead-in chamfer at the bed and of the rim break at the
    top, because those two deliberately open the bore wider than the cone -- a
    lead-in that did not would not be a lead-in.
    """
    low, high = MOUTH_CHAMFER + 0.4, bore[-1][1] - 0.6
    for want, z in _bore_samples(bore, low, high):
        span = _crossings(inside, z, r_max)
        ok = span is not None and abs(span[0] - want) <= 2 * STEP
        r.check(
            ok,
            f"bore radius {want:.2f} mm at z={z:.1f}",
            "no material at that height" if span is None else f"measured {span[0]:.2f} mm",
        )


def check_throat_is_the_narrowest(
    inside: Probe, throat_r: float, top: float, r_max: float, r: Report
) -> None:
    tightest = None
    for z in _sweep(MOUTH_CHAMFER + 0.4, top - 0.4, 0.5):
        span = _crossings(inside, z, r_max)
        if span is None:
            continue
        if tightest is None or span[0] < tightest[0]:
            tightest = (span[0], z)
    ok = tightest is not None and tightest[0] >= throat_r - 2 * STEP
    r.check(
        ok,
        f"no section bores tighter than the {2 * throat_r:.1f} mm throat",
        "no material anywhere"
        if tightest is None
        else f"tightest {2 * tightest[0]:.2f} mm at z={tightest[1]:.1f}",
    )


def check_walls(
    inside: Probe,
    bore: list[Point],
    nominals: tuple[tuple[str, float, float], ...],
    r_max: float,
    r: Report,
) -> None:
    """Wall thickness measured normal to the surface, not across the section.

    A horizontal crossing over-reports a sloped wall by 1/cos(angle) -- 2% on
    the inflate adapter's socket, 10% on its cup, 41% across either part's
    45 degree steps, and enough at the slider stops to hide a wall that is
    actually under the floor. So the horizontal span is corrected by the slope
    of whichever bore segment spans that height before it is compared with
    anything.
    """
    top = bore[-1][1]
    thin = []
    for z in _sweep(1.0, top - 1.0, 0.5):
        span = _crossings(inside, z, r_max)
        if span is None:
            continue
        wall = (span[1] - span[0] + STEP) * _cos(local_half_angle(bore, z))
        if wall < MIN_WALL:
            thin.append((z, wall))
    r.check(
        not thin,
        f"every wall clears the {MIN_WALL:.1f} mm floor",
        "thinnest "
        + (f"{min(w for _, w in thin):.2f} mm" if thin else "n/a")
        + f", {len(thin)} sample(s) under",
    )
    for label, z, nominal in nominals:
        span = _crossings(inside, z, r_max)
        wall = (
            None
            if span is None
            else (span[1] - span[0] + STEP) * _cos(local_half_angle(bore, z))
        )
        r.check(
            wall is not None and abs(wall - nominal) <= 0.15,
            f"{label} wall is {nominal:.1f} mm normal to the surface",
            "no material" if wall is None else f"measured {wall:.2f} mm",
        )


def check_self_supporting(bore: list[Point], r: Report) -> None:
    """No internal surface overhangs further than 45 degrees.

    Asserted off the profile rather than off the solid, because the bore is a
    handful of straight segments and each one's angle is a property of the
    numbers -- which is what catches a slider position that would need supports
    *inside a 20 mm bore*, a print nobody would rescue.

    Only the segments where the bore **narrows** as it rises are overhangs at
    all: there the material grows inward over the air below it. A segment that
    widens as it rises is the opposite -- each layer is set back from the one
    under it -- and is unconditionally printable however steep it is, which is
    why the cup, at 23 degrees or at 45, never appears here.
    """
    steepest = 0.0
    where = None
    for (r0, z0), (r1, z1) in zip(bore, bore[1:], strict=False):
        if z1 <= z0 or r1 >= r0:
            continue
        angle = degrees(atan2(r0 - r1, z1 - z0))
        if angle > steepest:
            steepest, where = angle, (z0, z1)
    r.check(
        steepest <= 45.0 + 1e-9,
        "every narrowing bore segment overhangs 45 degrees or less",
        f"steepest {steepest:.1f} degrees"
        + (f" over z={where[0]:.1f}..{where[1]:.1f}" if where else " (none narrows)"),
    )


def _is_meridian(edge) -> bool:
    """True for a straight edge lying in a half-plane through the Z axis.

    Every real corner on these parts is a circle -- they are full revolves, so
    a profile corner sweeps into one. A *straight* edge can therefore only be
    the seam where the revolved surface closes on itself, and OCC reports both
    of its "adjacent" faces as the same face, which is why the sharp-edge check
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


def check_parameters(
    of: Callable[..., Adapter | IntakeAdapter],
    make: Callable[..., Part],
    bore_of: Callable[..., list[Point]],
    stops: dict[str, tuple[float, float]],
    r: Report,
) -> None:
    """Drag every slider to both stops, and check the result still adapts.

    Cheap assertions only -- builds, seats on the bed, keeps an open bore that
    never narrows past 45 degrees. The full point sweep above runs on the
    defaults because those are what get printed; these run on the corners
    because those are what get corrected to.
    """
    for name, (low, high) in stops.items():
        for value in (low - 5, low, high, high + 5):
            a = of(**{name: value})
            part = make(a)
            bb = part.bounding_box()
            inside = solid_probe(part)
            bore = bore_of(a)
            open_axis = not any(
                inside(Vector(0.0, 0.0, z)) for z in _sweep(0.2, a.z_rim - 0.2, 1.0)
            )
            rising = all(z1 > z0 for (_, z0), (_, z1) in zip(bore, bore[1:], strict=False))
            overhang = max(
                (
                    degrees(atan2(r0 - r1, z1 - z0))
                    for (r0, z0), (r1, z1) in zip(bore, bore[1:], strict=False)
                    if z1 > z0 and r1 < r0
                ),
                default=0.0,
            )
            r.check(
                len(part.solids()) == 1
                and abs(bb.min.Z) < 1e-6
                and open_axis
                and rising
                and overhang <= 45.0 + 1e-9,
                f"{name}={value:g}: builds, seats on z=0, bore stays open",
                f"bore {2 * bore[0][0]:.1f}->{2 * bore[-1][0]:.1f}, height "
                f"{a.z_rim:.1f} mm, steepest overhang {overhang:.1f} deg",
            )


def _bore_samples(bore: list[Point], low: float, high: float) -> list[Point]:
    """Three (radius, height) samples per bore segment, inside [low, high]."""
    out: list[Point] = []
    for (r0, z0), (r1, z1) in zip(bore, bore[1:], strict=False):
        if z1 <= z0:
            continue
        for f in (0.25, 0.5, 0.75):
            z = z0 + (z1 - z0) * f
            if low <= z <= high:
                out.append((r0 + (r1 - r0) * f, z))
    return out


def _sweep(low: float, high: float, step: float) -> list[float]:
    out = []
    z = low
    while z <= high:
        out.append(z)
        z += step
    return out


def _cos(degrees_: float) -> float:
    return cos(radians(degrees_))


def _run_part(
    r: Report,
    label: str,
    part: Part,
    bore: list[Point],
    throat_r: float,
    nominals: tuple[tuple[str, float, float], ...],
) -> None:
    """Every point-sampled claim, for one built part."""
    inside = solid_probe(part)
    top = bore[-1][1]
    r_max = max(p[0] for p in bore) + 5

    r.section(f"{label}: print pose")
    check_print_pose(part, top, r)
    r.section(f"{label}: the axis is air")
    check_bore_is_open(inside, top, r)
    r.section(f"{label}: the bore follows its profile")
    check_bore_follows_the_profile(inside, bore, r_max, r)
    r.section(f"{label}: the throat is the narrowest section")
    check_throat_is_the_narrowest(inside, throat_r, top, r_max, r)
    r.section(f"{label}: walls")
    check_walls(inside, bore, nominals, r_max, r)
    r.section(f"{label}: self-supporting bore")
    check_self_supporting(bore, r)
    r.section(f"{label}: edge treatments")
    check_edges(part, r)


def run() -> Report:
    r = Report()

    a = DEFAULT
    _run_part(
        r,
        "inflate",
        build(a),
        bore_profile(a),
        a.throat_r,
        (
            ("socket", a.z_throat / 2, SOCKET_WALL),
            ("cup", (a.z_seat + a.z_rim) / 2, CUP_WALL),
        ),
    )

    d = INTAKE_DEFAULT
    _run_part(
        r,
        "deflate",
        deflate_model.build(d),
        deflate_model.bore_profile(d),
        d.throat_r,
        (
            ("tail cap", d.z_cap / 2, CAP_WALL),
            ("neck", (d.z_throat + d.z_throat_top) / 2, NECK_WALL),
            ("cup", (d.z_seat + d.z_rim) / 2, CUP_WALL),
        ),
    )

    r.section("inflate: parameter stops")
    check_parameters(
        Adapter.of,
        build,
        bore_profile,
        {
            "blower_mouth_dia": (BLOWER_MOUTH_MIN, BLOWER_MOUTH_MAX),
            "blower_throat_dia": (BLOWER_THROAT_MIN, BLOWER_THROAT_MAX),
            "socket_depth": (SOCKET_DEPTH_MIN, SOCKET_DEPTH_MAX),
            "valve_mouth_dia": (VALVE_MOUTH_MIN, VALVE_MOUTH_MAX),
            "valve_seat_dia": (VALVE_SEAT_MIN, VALVE_SEAT_MAX),
            "cup_depth": (CUP_DEPTH_MIN, CUP_DEPTH_MAX),
        },
        r,
    )

    r.section("deflate: parameter stops")
    check_parameters(
        IntakeAdapter.of,
        deflate_model.build,
        deflate_model.bore_profile,
        {
            "body_mouth_dia": (BODY_MOUTH_MIN, BODY_MOUTH_MAX),
            "body_seat_dia": (BODY_SEAT_MIN, BODY_SEAT_MAX),
            "cap_depth": (CAP_DEPTH_MIN, CAP_DEPTH_MAX),
            "valve_mouth_dia": (VALVE_MOUTH_MIN, VALVE_MOUTH_MAX),
            "valve_seat_dia": (VALVE_SEAT_MIN, VALVE_SEAT_MAX),
            "cup_depth": (CUP_DEPTH_MIN, CUP_DEPTH_MAX),
        },
        r,
    )
    return r


def main() -> None:
    r = run()
    print(r.render())
    sys.exit(1 if r.failures else 0)


if __name__ == "__main__":
    main()
