"""Geometry assertions for the salad-bowl lamp.

    uv run check salad_bowl_lamp
    uv run python -m models.salad_bowl_lamp.checks

Almost nothing here is visible in a projection. Whether the band clears the bowl,
whether the magnets touch it, whether 0.6 mm of plastic really survives behind a
2 mm pocket in a 2.6 mm wall, whether the band's inside stayed plain, and -- the
one that decides whether the part prints -- which way up the teardrop pockets
point, are all interior facts about a solid, so they get point-sampled rather
than eyeballed. The shade is checked in its own coordinates (underside at z = 0)
and the seating is checked by actually placing it in the bowl.

Two angles recur and are chosen, not arbitrary. Magnets sit every 45 deg and
cross arms every 90 deg, so **0 deg is both a pad and an arm** and **22.5 deg is
neither**. A probe meant to find the band's bare inside face has to be taken
where no arm runs, or it finds the arm and reports a bulge that is not there.
"""

from __future__ import annotations

import sys
from math import cos, radians, sin, sqrt

from build123d import Part, Pos

from ..lib.checks import (
    Report as Report,
    is_periodic_seam as is_periodic_seam,
    is_solid_at as is_solid_at,
    sharp_convex_edges,
)
from ..lib.edges import as_part
from . import config as c
from .bowl import create_bowl
from .fit_test import create as create_fit_test
from .shade import create_shade, pad_planes

PLA_DENSITY = 1.24e-3  # g/mm3

MASS_BUDGET_G = 175.0
"""What the eight magnets are sized against.

Not a measured holding force -- magnet grade and the bowl's own steel decide
that, and neither is known here (see README). It is a budget: the part is
allowed to be a certain weight for a given number of magnets, and a change that
blows through it has to answer for itself rather than quietly halving the margin.

It came down with the magnets. A 6 x 2 disc has well under half the pull of the
8 x 3 this started with, so the 250 g that budget once allowed would have been a
number that no longer stood for anything. 175 g is about 1.3x the part.
"""

BETWEEN = [22.5 + 90.0 * k for k in range(4)]
"""Angles with neither a magnet pad nor a cross arm on them -- see the module docstring."""


def _at(plane, along: float, up: float = 0.0, across: float = 0.0):
    """A point ``along`` mm down a pad's axis, offset in its own plane."""
    p = plane.origin + plane.z_dir * along + plane.y_dir * up + plane.x_dir * across
    return (p.X, p.Y, p.Z)


def _polar(radius: float, angle: float, z: float):
    return (radius * cos(radians(angle)), radius * sin(radians(angle)), z)


def check_bowl(bowl: Part, r: Report) -> None:
    """The mock really is the bowl the numbers describe."""
    r.section("bowl")
    r.check(len(bowl.solids()) == 1, "bowl is one solid", f"{len(bowl.solids())}")

    # The rim plane is the datum every shade dimension is measured from, so it
    # gets probed rather than read off a bounding box -- OCC inflates the box of
    # a spherical face by the sagitta it cannot see, which here is 5 mm.
    rim_wall = c.bowl_inner_radius(0.5) + c.BOWL_WALL / 2
    r.check(is_solid_at(bowl, rim_wall, 0, 0.5), "steel just above the rim plane")
    r.check(not is_solid_at(bowl, rim_wall, 0, -0.5), "nothing below the rim plane")

    for depth in (0.5, c.RIM_INSET, 13.0, 23.0, 60.0):
        radius = c.bowl_inner_radius(depth)
        at = f"depth {depth:.1f}, r {radius:.2f}"
        r.check(is_solid_at(bowl, radius + c.BOWL_WALL / 2, 0, depth), f"steel at {at}")
        r.check(not is_solid_at(bowl, radius - 0.4, 0, depth), f"air inside at {at}")
        r.check(
            not is_solid_at(bowl, radius + c.BOWL_WALL + 0.4, 0, depth),
            f"air outside at {at}",
        )

    r.check(
        not is_solid_at(bowl, 0, 0, c.BOWL_H - c.BOWL_WALL / 2),
        f"the {c.BOWL_HOLE_D:.0f} mm lampholder hole is open at the apex",
    )
    beside = c.BOWL_HOLE_D / 2 + 4.0
    r.check(
        is_solid_at(bowl, beside, 0, c.bowl_outer_height(beside) - c.BOWL_WALL / 2),
        "steel remains beside the hole",
    )
    r.check(
        not is_solid_at(bowl, c.BOWL_HOLE_D / 2 - 2.0, 0, c.bowl_outer_height(0) - 0.4),
        "the hole is the diameter it claims",
    )


def check_shade_body(shade: Part, r: Report) -> None:
    """One connected part, the height that was asked for, at the stated wall."""
    r.section("shade body")
    solids = len(shade.solids())
    r.check(solids == 1, "rings and cross fuse into one solid", f"{solids} solid(s)")

    box = shade.bounding_box()
    r.check(abs(box.min.Z) < 1e-6, "sits on z = 0 in print pose", f"{box.min.Z:.4f}")
    r.check(abs(box.max.Z - c.BAND_H) < 1e-6, "20 mm tall", f"{box.max.Z:.3f}")

    mass = shade.volume * PLA_DENSITY
    r.check(
        mass < MASS_BUDGET_G,
        "within the mass budget the magnets are sized against",
        f"{mass:.0f} g of PLA, budget {MASS_BUDGET_G:.0f} g",
    )

    # Every ring is WALL thick and the gaps between them are open, sampled where
    # neither a cross arm nor a pad can be mistaken for a ring.
    mid = c.BAND_H / 2
    for radius in c.ring_radii():
        for probe, want, label in (
            (radius - c.WALL / 2, True, "solid"),
            (radius + 0.5, False, "clear outside"),
            (radius - c.WALL - 0.5, False, "clear inside"),
        ):
            got = is_solid_at(shade, *_polar(probe, BETWEEN[0], mid))
            r.check(got is want, f"ring r={radius:.1f} {label}")


def check_eye(shade: Part, r: Report) -> None:
    """The innermost circle is a circle: the cross stops at it, not through it."""
    r.section("eye")
    mid = c.BAND_H / 2
    eye = c.EYE_D / 2

    # Along both arm axes and the diagonal between them, and at the very centre
    # where the two arms used to meet.
    for angle in (0.0, 90.0, 180.0, 270.0, 45.0):
        r.check(
            not is_solid_at(shade, *_polar(eye / 2, angle, mid)),
            f"the eye is clear of the cross at {angle:.0f} deg",
        )
    r.check(not is_solid_at(shade, 0.0, 0.0, mid), "the eye is clear at the centre")

    # The sharpest test of ARM_EMBED: an arm that started a hair too far in would
    # break the eye's cylinder here, on the arm's own axis, just inside the face.
    for angle in (0.0, 90.0, 180.0, 270.0):
        for z in (0.5, mid, c.BAND_H - 0.5):
            r.check(
                not is_solid_at(shade, *_polar(eye - 0.2, angle, z)),
                f"the eye's face is unbroken at {angle:.0f} deg, z={z:.1f}",
            )

    # ...and the arm is still there, on the far side of the hub.
    r.check(
        is_solid_at(shade, *_polar(eye + c.WALL / 2, 0.0, mid)),
        "the hub itself is solid on the arm's axis",
    )
    r.check(
        is_solid_at(shade, *_polar(c.hub_outer_radius() + 1.0, 0.0, mid)),
        "an arm leaves the hub and carries on outward",
    )
    r.check(
        not is_solid_at(shade, *_polar(c.hub_outer_radius() + 1.0, BETWEEN[0], mid)),
        "and there is air between the arms",
    )


def check_band_wall(shade: Part, r: Report) -> None:
    """The band is one even wall, and its inside face has nothing standing on it.

    This is the brief's "no bulges on the inside" made falsifiable. Probed
    radially between the arms, where the only thing that could be inboard of
    ``band_inner_radius`` is a boss, and along each pocket's own axis, where the
    only thing that could be behind a magnet is the same.
    """
    r.section("band wall")
    for angle in BETWEEN:
        for z in (1.0, c.BAND_H / 2, c.BAND_H - 1.0):
            inner = c.band_inner_radius(z)
            at = f"{angle:.1f} deg, z={z:.0f}"
            r.check(
                is_solid_at(shade, *_polar(inner + 0.3, angle, z)),
                f"band is material at its inside face at {at}",
            )
            r.check(
                not is_solid_at(shade, *_polar(inner - 0.3, angle, z)),
                f"nothing bulges inboard of the band at {at}",
            )

    # 2.6 mm measured the way the pocket is bored, which is the measurement that
    # decides whether the pocket breaks out -- not the radial one, which reads
    # 2.65 at the bottom and 2.71 at the top because the normal is not radial.
    for i, plane in enumerate(pad_planes()):
        r.check(
            is_solid_at(shade, *_at(plane, c.WALL - 0.2, across=4.0)),
            f"wall {i} is a full {c.WALL} mm along the pocket axis",
        )
        r.check(
            not is_solid_at(shade, *_at(plane, c.WALL + 0.3, across=4.0)),
            f"wall {i} ends there -- no boss behind the magnet",
        )


def check_seat(shade: Part, bowl: Part, r: Report) -> None:
    """The band's face *is* the bowl's inner surface, and the part drops in."""
    r.section("seat")
    # Sampled *between* the pads: on a pad's own axis the seat is correctly not
    # there, because that is exactly where the pocket is.
    for angle in BETWEEN:
        for z in (1.0, c.BAND_H / 2, c.BAND_H - 1.0):
            face = c.band_outer_radius(z)
            at = f"{angle:.1f} deg, z={z:.0f}"
            r.check(
                is_solid_at(shade, *_polar(face - 0.2, angle, z)),
                f"band reaches the seat at {at}",
            )
            r.check(
                not is_solid_at(shade, *_polar(face + 0.2, angle, z)),
                f"band stops at the seat at {at}",
            )

    r.check(
        abs(c.SEAT_CLEAR) < 1e-9,
        "the seat is a taper, with no clearance to lose the magnets in",
        f"SEAT_CLEAR = {c.SEAT_CLEAR:.2f} mm",
    )

    # Each magnet's own face sits on the sphere -- probed beside the pocket,
    # since on the axis there is (correctly) nothing but pocket.
    beside = c.POCKET_D / 2 + 2.0
    for i, plane in enumerate(pad_planes()):
        r.check(
            is_solid_at(shade, *_at(plane, 0.5, across=beside)),
            f"pad {i} is material right up to the steel",
        )
        r.check(
            not is_solid_at(shade, *_at(plane, -0.3, across=beside)),
            f"pad {i} stops at the steel",
        )

    seated = as_part(Pos(0, 0, c.RIM_INSET) * shade)
    r.check(
        seated.bounding_box().min.Z >= c.RIM_INSET - 1e-6,
        "the shade stays inside the rim",
        f"lowest point {seated.bounding_box().min.Z:.2f} mm above it",
    )
    fouled = (seated & bowl).volume
    r.check(
        fouled < 1.0,
        "the shade seats without cutting into the steel",
        f"{fouled:.3f} mm3 of overlap",
    )


def check_pockets(shade: Part, r: Report) -> None:
    """A magnet's worth of hole, a backing that survives it, and a roof on top."""
    r.section("magnet pockets")
    bore = c.POCKET_D / 2
    backing = c.pad_backing()

    for i, plane in enumerate(pad_planes()):
        tag = f"pocket {i}"
        r.check(not is_solid_at(shade, *_at(plane, c.MAGNET_T / 2)), f"{tag} is hollow")
        r.check(
            not is_solid_at(shade, *_at(plane, c.MAGNET_T - 0.2)),
            f"{tag} is open to full magnet depth",
        )
        r.check(
            is_solid_at(shade, *_at(plane, c.MAGNET_T + 0.2)),
            f"{tag} has a floor at exactly the magnet's thickness",
        )
        r.check(
            is_solid_at(shade, *_at(plane, c.MAGNET_T + backing - 0.3)),
            f"{tag} keeps its {backing:.1f} mm of backing",
        )
        # The floor is whole, not just present on the axis. Off-axis the wall has
        # more to give, not less -- both faces are spheres about one centre --
        # so a hole here would mean the pocket had been bored somewhere the band
        # is not, which is the failure the even wall exists to prevent.
        for up in (-bore + 0.3, 0.0, bore - 0.3, bore * sqrt(2) - 0.3):
            r.check(
                is_solid_at(shade, *_at(plane, c.MAGNET_T + 0.2, up=up)),
                f"{tag} floor is unbroken {up:+.1f} mm up",
            )
        # Bore width, and -- the print-critical one -- that the teardrop's roof
        # is above the bore and not beside it. A pocket built on a plane whose
        # y axis had flipped would pass every test but this one, and would print
        # with a sagging bridge right where the magnet has to sit flat.
        deep = c.MAGNET_T / 2
        r.check(
            not is_solid_at(shade, *_at(plane, deep, across=bore - 0.3)),
            f"{tag} is {c.POCKET_D:.1f} mm across",
        )
        r.check(
            is_solid_at(shade, *_at(plane, deep, across=bore + 0.6)),
            f"{tag} is bounded sideways",
        )
        r.check(
            not is_solid_at(shade, *_at(plane, deep, up=bore + 0.5)),
            f"{tag} roof is above the bore",
        )
        r.check(
            is_solid_at(shade, *_at(plane, deep, up=-(bore + 0.5))),
            f"{tag} has no roof below it",
        )


def check_fit_test(band: Part, shade: Part, r: Report) -> None:
    """The test print is the shade's own seat, with the grille left off."""
    r.section("fit test")
    r.check(len(band.solids()) == 1, "the band is one solid", f"{len(band.solids())}")

    box, shade_box = band.bounding_box(), shade.bounding_box()
    r.check(
        abs(box.max.X - shade_box.max.X) < 1e-6 and abs(box.max.Z - c.BAND_H) < 1e-6,
        "same diameter and height as the shade it tests",
        f"{2 * box.max.X:.2f} mm across, {box.max.Z:.2f} mm tall",
    )

    mid = c.BAND_H / 2
    face, inner = c.band_outer_radius(mid), c.band_inner_radius(mid)
    for angle in BETWEEN:
        r.check(
            is_solid_at(band, *_polar(face - 0.2, angle, mid)),
            f"seat is intact at {angle:.1f} deg",
        )
    # Probed on the arm axes as well as between them: the grille really is gone,
    # not merely thinned, and the band is the same band either way.
    for angle in (0.0, 45.0, 90.0, BETWEEN[0]):
        r.check(
            not is_solid_at(band, *_polar(inner - 0.5, angle, mid)),
            f"nothing inboard of the band at {angle:.1f} deg",
        )

    for i, plane in enumerate(pad_planes()):
        r.check(
            not is_solid_at(band, *_at(plane, c.MAGNET_T / 2)),
            f"pocket {i} came with it",
        )

    ratio = band.volume / shade.volume
    r.check(
        ratio < 0.35,
        "cheap enough to be worth printing first",
        f"{band.volume * PLA_DENSITY:.0f} g, {100 * ratio:.0f}% of the shade",
    )


def check_edges(shade: Part, r: Report) -> None:
    """The house rule, made falsifiable: no raw square edge ships.

    The unmeasurable edges get a stronger treatment than an ``allow`` list. Every
    revolved face here closes on itself, and OCC lists one face twice for the
    seam where it does, so ``interior_angle`` has no second surface to take a
    dihedral against and correctly answers ``None``. Rather than excusing those
    edges by where they sit, which is how a predicate in this repo has already
    gone stale once, this asserts the *reason*: every edge this check could not
    measure must be one of those seams. A new unmeasurable edge that is not a
    seam fails the run.
    """
    r.section("edges")
    survey = sharp_convex_edges(shade)
    r.check(
        not survey.sharp,
        "no untreated sharp convex edges",
        ", ".join(f"{e.length:.1f} mm at {e.center()}" for e in survey.sharp[:6]),
    )
    unexplained = [e for e in survey.unclassifiable if not is_periodic_seam(shade, e)]
    r.check(
        not unexplained,
        "every unmeasurable edge is a face closing on itself",
        f"{len(survey.unclassifiable)} seam(s)"
        + (
            ""
            if not unexplained
            else "; unexplained: "
            + ", ".join(f"{e.length:.1f} mm at {e.center()}" for e in unexplained[:6])
        ),
    )


def run() -> Report:
    r = Report()
    bowl = create_bowl()
    shade = create_shade()
    band = create_fit_test()
    check_bowl(bowl, r)
    check_shade_body(shade, r)
    check_eye(shade, r)
    check_band_wall(shade, r)
    check_seat(shade, bowl, r)
    check_pockets(shade, r)
    check_fit_test(band, shade, r)
    check_edges(shade, r)
    return r


def main() -> None:
    r = run()
    print(r.render())
    sys.exit(1 if r.failures else 0)


if __name__ == "__main__":
    main()
