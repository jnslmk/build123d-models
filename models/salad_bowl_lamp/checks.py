"""Geometry assertions for the salad-bowl lamp.

    uv run check salad_bowl_lamp
    uv run python -m models.salad_bowl_lamp.checks

Almost nothing here is visible in a projection. Whether the band clears the bowl,
whether the pads touch it, whether a 3 mm magnet has 3 mm of plastic behind it,
and -- the one that decides whether the part prints -- which way up the teardrop
pockets point, are all interior facts about a solid, so they get point-sampled
rather than eyeballed. The shade is checked in its own coordinates (underside at
z = 0) and the seating is checked by actually placing it in the bowl.
"""

from __future__ import annotations

import sys

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
from .shade import create_shade, pad_planes

PLA_DENSITY = 1.24e-3  # g/mm3

MASS_BUDGET_G = 250.0
"""What the eight magnets are sized against.

Not a measured holding force -- magnet grade and the bowl's own steel decide
that, and neither is known here (see README). It is a budget: the part is
allowed to be a certain weight for a given number of magnets, and a change that
blows through it has to answer for itself rather than quietly halving the margin.
"""


def _at(plane, along: float, up: float = 0.0, across: float = 0.0):
    """A point ``along`` mm down a pad's axis, offset in its own plane."""
    p = plane.origin + plane.z_dir * along + plane.y_dir * up + plane.x_dir * across
    return (p.X, p.Y, p.Z)


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
    r.check(mass < MASS_BUDGET_G, "within the mass budget the magnets are sized against", f"{mass:.0f} g of PLA, budget {MASS_BUDGET_G:.0f} g")

    # Every ring is WALL thick and the gaps between them are open, sampled at
    # 22.5 deg where neither a cross arm nor a pad can be mistaken for a ring.
    from math import cos, radians, sin

    ang = radians(22.5)
    mid = c.BAND_H / 2
    for radius in c.ring_radii():
        for probe, want, label in (
            (radius - c.WALL / 2, True, "solid"),
            (radius + 0.5, False, "clear outside"),
            (radius - c.WALL - 0.5, False, "clear inside"),
        ):
            got = is_solid_at(shade, probe * cos(ang), probe * sin(ang), mid)
            r.check(got is want, f"ring r={radius:.1f} {label}")

    r.check(
        not is_solid_at(shade, c.EYE_D / 2 - 1.0, c.EYE_D / 2 - 1.0, mid),
        "the middle eye is open",
    )
    # ...but the cross runs through it, which is what ties the hub to the rest.
    r.check(is_solid_at(shade, c.EYE_D / 4, 0, mid), "the cross crosses the eye")


def check_seat(shade: Part, bowl: Part, r: Report) -> None:
    """The band's face *is* the bowl's inner surface, and the part drops in."""
    r.section("seat")
    from math import cos, radians, sin

    # Sampled *between* the bosses: on a boss's own axis the seat is correctly
    # not there, because that is exactly where the pocket is.
    step = 360.0 / c.MAGNET_COUNT
    for angle in (step / 2, 3 * step / 2, 5 * step / 2):
        for z in (1.0, c.BAND_H / 2, c.BAND_H - 1.0):
            face = c.band_outer_radius(z)
            ux, uy = cos(radians(angle)), sin(radians(angle))
            at = f"{angle:.0f} deg, z={z:.0f}"
            r.check(
                is_solid_at(shade, (face - 0.2) * ux, (face - 0.2) * uy, z),
                f"band reaches the seat at {at}",
            )
            r.check(
                not is_solid_at(shade, (face + 0.2) * ux, (face + 0.2) * uy, z),
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
        # The boss is the whole reason a 3 mm magnet fits a 3 mm band.
        r.check(
            is_solid_at(shade, *_at(plane, c.WALL + 1.0, across=4.0)),
            f"boss {i} carries material past the band",
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
    """A magnet's worth of hole, a wall's worth of plastic, and a roof on top."""
    r.section("magnet pockets")
    bore = c.POCKET_D / 2

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
            is_solid_at(shade, *_at(plane, c.MAGNET_T + c.PAD_BACKING - 0.3)),
            f"{tag} keeps its {c.PAD_BACKING:.0f} mm of backing",
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


def check_edges(shade: Part, r: Report) -> None:
    """The house rule, made falsifiable: no raw square edge ships.

    The unmeasurable edges get a stronger treatment than an ``allow`` list. Every
    revolved face here -- the seat's sphere, and each of the eight boss cones --
    closes on itself, and OCC lists one face twice for the seam where it does, so
    ``interior_angle`` has no second surface to take a dihedral against and
    correctly answers ``None``. Rather than excusing those edges by where they
    sit, which is how a predicate in this repo has already gone stale once, this
    asserts the *reason*: every edge this check could not measure must be one of
    those seams. A new unmeasurable edge that is not a seam fails the run.
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
    check_bowl(bowl, r)
    check_shade_body(shade, r)
    check_seat(shade, bowl, r)
    check_pockets(shade, r)
    check_edges(shade, r)
    return r


def main() -> None:
    r = run()
    print(r.render())
    sys.exit(1 if r.failures else 0)


if __name__ == "__main__":
    main()
