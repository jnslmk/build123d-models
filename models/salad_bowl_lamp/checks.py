"""Geometry assertions for the salad-bowl lamp.

    uv run check salad_bowl_lamp
    uv run python -m models.salad_bowl_lamp.checks

Almost nothing here is visible in a projection. Whether the band's notch clears
the bulge in the mouth, whether the magnets touch the steel, whether the backing
behind a pocket really survives it, whether the band's inside stayed plain, and -- the
one that decides whether the part prints -- which way up the teardrop pockets
point, are all interior facts about a solid, so they get point-sampled rather
than eyeballed. The shade is checked in its own coordinates (underside at z = 0)
and the seating is checked by actually placing it in the bowl.

Two angles recur and are chosen, not arbitrary. Magnets sit every 45 deg and
cross arms every 90 deg, so **0 deg is both a pad and an arm** and **22.5 deg is
neither**. A probe meant to find the band's bare inside face has to be taken
where no arm runs, or it finds the arm and reports a bulge that is not there.

Most of this measures ``DEFAULT`` -- the lamp this repo actually built, and the
one every export is. ``check_parameters`` is the other kind: the model is
parametric on the website, so the last section drags the sliders to their stops,
past their stops, and into combinations nobody would choose, and asserts that
what comes back is still a printable part. A clamp that silently stopped
clamping would show up there and nowhere else.
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
from .bowl import create_bowl
from .config import DEFAULT, LAMP_PARAMS, MIN_BACKING, MIN_GAP, Lamp
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
number that no longer stood for anything. 175 g is about 1.4x the part.

**The discs have since gone to 5 x 1 and this number has not moved, which is a
debt rather than a decision.** A 5 x 1 has roughly a third of a 6 x 2's pull, so
eight of them are holding 141 g on a good deal less margin than 175 g was meant
to describe -- and the part grew, too, when the band was taken down to the rim.
The budget cannot simply follow the magnets down: 141 g of part is 141 g of part,
and a budget under it would fail on the part it was written for. So what has to
answer for itself is the magnet count, on the bowl, with ``fit_test``: if eight
5 x 1 discs slide, the fix is more of them or thicker ones, and this number gets
rewritten around whatever that turns out to be.
"""

BETWEEN = [22.5 + 90.0 * k for k in range(4)]
"""Angles with neither a magnet pad nor a cross arm on them -- see the module docstring."""



def _at(plane, along: float, up: float = 0.0, across: float = 0.0):
    """A point ``along`` mm down a pad's axis, offset in its own plane."""
    p = plane.origin + plane.z_dir * along + plane.y_dir * up + plane.x_dir * across
    return (p.X, p.Y, p.Z)


def _polar(radius: float, angle: float, z: float):
    return (radius * cos(radians(angle)), radius * sin(radians(angle)), z)


def check_bowl(bowl: Part, lamp: Lamp, r: Report) -> None:
    """The mock really is the bowl the numbers describe."""
    r.section("bowl")
    r.check(len(bowl.solids()) == 1, "bowl is one solid", f"{len(bowl.solids())}")

    # The rim plane is the datum every shade dimension is measured from, so it
    # gets probed rather than read off a bounding box -- OCC inflates the box of
    # a spherical face by the sagitta it cannot see, which here is 5 mm.
    rim_wall = lamp.bowl_inner_radius(0.5) + lamp.bowl_wall / 2
    r.check(is_solid_at(bowl, rim_wall, 0, 0.5), "steel just above the rim plane")
    r.check(not is_solid_at(bowl, rim_wall, 0, -0.5), "nothing below the rim plane")

    # Half a millimetre in from the shade's underside rather than level with it.
    # With no reveal that datum is the rim plane itself, where the rim's own
    # fillet and the bulge's buried end face meet: a probe there lands on a
    # corner and answers about the tolerance, not the steel. The rim plane has
    # its own two checks above, taken from either side of it on purpose.
    for depth in sorted({0.5, lamp.rim_inset + 0.5, 13.0, 23.0, 60.0}):
        radius = lamp.bowl_inner_radius(depth)
        clear = lamp.bowl_clear_radius(depth)  # the bulge, where there is one
        at = f"depth {depth:.1f}, r {radius:.2f}"
        r.check(is_solid_at(bowl, radius + lamp.bowl_wall / 2, 0, depth), f"steel at {at}")
        r.check(not is_solid_at(bowl, clear - 0.4, 0, depth), f"air inside at {at}")
        r.check(
            not is_solid_at(bowl, radius + lamp.bowl_wall + 0.4, 0, depth),
            f"air outside at {at}",
        )

    r.check(
        not is_solid_at(bowl, 0, 0, lamp.bowl_h - lamp.bowl_wall / 2),
        f"the {lamp.bowl_hole_d:.0f} mm lampholder hole is open at the apex",
    )
    beside = lamp.bowl_hole_d / 2 + 4.0
    r.check(
        is_solid_at(bowl, beside, 0, lamp.bowl_outer_height(beside) - lamp.bowl_wall / 2),
        "steel remains beside the hole",
    )
    r.check(
        not is_solid_at(bowl, lamp.bowl_hole_d / 2 - 2.0, 0, lamp.bowl_outer_height(0) - 0.4),
        "the hole is the diameter it claims",
    )


def check_bead(bowl: Part, shade: Part, lamp: Lamp, r: Report) -> None:
    """The bulge is on the bowl, and the band's notch clears it seated, all round.

    **Seated is the whole claim, and that is a real limit rather than a gap in
    the checking.** The band's seat is the bowl's own sphere, which is a
    millimetre wider than the bulge leaves at that depth, so no assertion here
    can say the shade is pushed straight down past it -- it is not, and a check
    that claimed otherwise would be measuring a lamp this is not. It goes in
    tilted, past a bulge that is one lump rather than a ring (``config.bead_w``),
    and how much room the taper gives it to tilt is arithmetic on the seat's own
    slope, not a property of this solid. What *is* asserted here is the part that
    a boolean can settle: that the notch is deep enough, tall enough, and
    everywhere the bulge could be, since the shade may come to rest at any
    azimuth.
    """
    r.section("bulge and notch")
    throat = lamp.bead_throat_radius()
    crest = lamp.bead_depth + lamp.bead_w / 2

    r.check(
        is_solid_at(bowl, throat + 0.2, 0, crest),
        f"the bulge is there, {lamp.bead_h:.1f} mm proud over {lamp.bead_w:.1f} mm",
        f"leaves r {throat:.2f} against a {lamp.bowl_inner_radius(crest):.2f} mm sphere",
    )
    r.check(
        not is_solid_at(bowl, throat - 0.2, 0, crest),
        "and the mouth is open inboard of it",
    )

    # The notch has to outlast the bulge in both directions: deeper than it
    # everywhere it stands proud, and still at full depth past its far edge.
    seated = as_part(Pos(0, 0, lamp.rim_inset) * shade)
    steps = 24
    gaps = []
    for i in range(steps + 1):
        depth = lamp.bead_depth + i * lamp.bead_w / steps
        z = depth - lamp.rim_inset
        if not 0.0 <= z <= lamp.band_h:
            continue
        gaps.append((depth, lamp.bowl_clear_radius(depth) - lamp.band_outer_radius(z)))
    tightest = min(gaps, key=lambda g: g[1])
    r.check(
        tightest[1] >= lamp.bead_clear - 1e-9,
        "the notch clears the bulge over every millimetre of it",
        f"tightest {tightest[1]:.2f} mm at depth {tightest[0]:.2f}, asked for "
        f"{lamp.bead_clear:.2f} mm",
    )
    r.check(
        lamp.band_notch_top() >= lamp.bead_depth + lamp.bead_w - lamp.rim_inset,
        "and is still at full depth past the bulge's far edge",
        f"notch full to {lamp.band_notch_top():.2f} mm, bulge ends at "
        f"{lamp.bead_depth + lamp.bead_w - lamp.rim_inset:.2f} mm",
    )

    # Round the whole bowl, not just at one angle: the shade is free to come to
    # rest at any azimuth, so the mock's ring is the envelope of everywhere the
    # lump could be and the seated part has to miss all of it.
    fouled = (seated & bowl).volume
    r.check(
        fouled < 1.0,
        "the seated shade touches no part of that ring, at any angle",
        f"{fouled:.3f} mm3 of overlap",
    )
    r.check(
        lamp.band_notch_ramp_top() + 1e-9 < lamp.pad_depth_z - lamp.pocket_d / 2,
        "the notch is finished well below the lowest magnet bore",
        f"ramp ends at {lamp.band_notch_ramp_top():.2f} mm, bores start at "
        f"{lamp.pad_depth_z - lamp.pocket_d / 2:.2f} mm",
    )


def check_shade_body(shade: Part, lamp: Lamp, r: Report) -> None:
    """One connected part, the height that was asked for, at the stated wall."""
    r.section("shade body")
    solids = len(shade.solids())
    r.check(solids == 1, "rings and cross fuse into one solid", f"{solids} solid(s)")

    box = shade.bounding_box()
    r.check(abs(box.min.Z) < 1e-6, "sits on z = 0 in print pose", f"{box.min.Z:.4f}")
    r.check(abs(box.max.Z - lamp.band_h) < 1e-6, f"{lamp.band_h:.0f} mm tall", f"{box.max.Z:.3f}")

    mass = shade.volume * PLA_DENSITY
    r.check(
        mass < MASS_BUDGET_G,
        "within the mass budget the magnets are sized against",
        f"{mass:.0f} g of PLA, budget {MASS_BUDGET_G:.0f} g",
    )

    # Every ring is WALL thick and the gaps between them are open, sampled where
    # neither a cross arm nor a pad can be mistaken for a ring.
    mid = lamp.band_h / 2
    for radius in lamp.ring_radii():
        for probe, want, label in (
            (radius - lamp.wall / 2, True, "solid"),
            (radius + 0.5, False, "clear outside"),
            (radius - lamp.wall - 0.5, False, "clear inside"),
        ):
            got = is_solid_at(shade, *_polar(probe, BETWEEN[0], mid))
            r.check(got is want, f"ring r={radius:.1f} {label}")


def check_eye(shade: Part, lamp: Lamp, r: Report) -> None:
    """The innermost circle is a circle: the cross stops at it, not through it."""
    r.section("eye")
    mid = lamp.band_h / 2
    eye = lamp.eye_d / 2

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
        for z in (0.5, mid, lamp.band_h - 0.5):
            r.check(
                not is_solid_at(shade, *_polar(eye - 0.2, angle, z)),
                f"the eye's face is unbroken at {angle:.0f} deg, z={z:.1f}",
            )

    # ...and the arm is still there, on the far side of the hub.
    r.check(
        is_solid_at(shade, *_polar(eye + lamp.wall / 2, 0.0, mid)),
        "the hub itself is solid on the arm's axis",
    )
    r.check(
        is_solid_at(shade, *_polar(lamp.hub_outer_radius() + 1.0, 0.0, mid)),
        "an arm leaves the hub and carries on outward",
    )
    r.check(
        not is_solid_at(shade, *_polar(lamp.hub_outer_radius() + 1.0, BETWEEN[0], mid)),
        "and there is air between the arms",
    )


def check_band_wall(shade: Part, lamp: Lamp, r: Report) -> None:
    """The band is one even wall, and its inside face has nothing standing on it.

    This is the brief's "no bulges on the inside" made falsifiable. Probed
    radially between the arms, where the only thing that could be inboard of
    ``band_inner_radius`` is a boss, and along each pocket's own axis, where the
    only thing that could be behind a magnet is the same.
    """
    r.section("band wall")
    for angle in BETWEEN:
        for z in (1.0, lamp.band_h / 2, lamp.band_h - 1.0):
            inner = lamp.band_inner_radius(z)
            at = f"{angle:.1f} deg, z={z:.0f}"
            r.check(
                is_solid_at(shade, *_polar(inner + 0.3, angle, z)),
                f"band is material at its inside face at {at}",
            )
            r.check(
                not is_solid_at(shade, *_polar(inner - 0.3, angle, z)),
                f"nothing bulges inboard of the band at {at}",
            )

    # The wall measured the way the pocket is bored, which is the measurement
    # that decides whether the pocket breaks out -- not the radial one, which on
    # the default lamp reads 2.41 at the bottom and 2.51 at the top, because the
    # surface normal is not radial.
    for i, plane in enumerate(pad_planes(lamp)):
        r.check(
            is_solid_at(shade, *_at(plane, lamp.wall - 0.2, across=4.0)),
            f"wall {i} is a full {lamp.wall:.1f} mm along the pocket axis",
        )
        r.check(
            not is_solid_at(shade, *_at(plane, lamp.wall + 0.3, across=4.0)),
            f"wall {i} ends there -- no boss behind the magnet",
        )


def check_seat(shade: Part, bowl: Part, lamp: Lamp, r: Report) -> None:
    """The band's face *is* the bowl's inner surface, and the part drops in.

    Everywhere above the bulge's notch, which is 17 of the band's 23 mm -- inside
    the notch the face is deliberately not on the sphere, and ``check_bead`` owns
    that. The claim that has to hold either way is the one that mattered in the
    first place: every magnet lands on steel.
    """
    r.section("seat")
    r.check(
        lamp.band_setback(lamp.pad_depth_z) < 1e-9,
        "the magnet circle sits on the sphere, clear of the notch",
        f"pads at z={lamp.pad_depth_z:.2f}, notch done by "
        f"{lamp.band_notch_ramp_top():.2f} mm",
    )
    # Sampled *between* the pads: on a pad's own axis the seat is correctly not
    # there, because that is exactly where the pocket is.
    for angle in BETWEEN:
        for z in (1.0, lamp.band_h / 2, lamp.band_h - 1.0):
            face = lamp.band_outer_radius(z)
            at = f"{angle:.1f} deg, z={z:.0f}"
            r.check(
                is_solid_at(shade, *_polar(face - 0.2, angle, z)),
                f"band reaches its outer face at {at}",
            )
            r.check(
                not is_solid_at(shade, *_polar(face + 0.2, angle, z)),
                f"band stops there at {at}",
            )

    r.check(
        abs(lamp.seat_clear) < 1e-9,
        "the seat is a taper, with no clearance to lose the magnets in",
        f"SEAT_CLEAR = {lamp.seat_clear:.2f} mm",
    )

    # Each magnet's own face sits on the sphere -- probed beside the pocket,
    # since on the axis there is (correctly) nothing but pocket.
    beside = lamp.pocket_d / 2 + 2.0
    for i, plane in enumerate(pad_planes(lamp)):
        r.check(
            is_solid_at(shade, *_at(plane, 0.5, across=beside)),
            f"pad {i} is material right up to the steel",
        )
        r.check(
            not is_solid_at(shade, *_at(plane, -0.3, across=beside)),
            f"pad {i} stops at the steel",
        )

    seated = as_part(Pos(0, 0, lamp.rim_inset) * shade)
    r.check(
        seated.bounding_box().min.Z >= lamp.rim_inset - 1e-6,
        "the shade stays inside the rim",
        f"lowest point {seated.bounding_box().min.Z:.2f} mm above it",
    )
    fouled = (seated & bowl).volume
    r.check(
        fouled < 1.0,
        "the shade seats without cutting into the steel",
        f"{fouled:.3f} mm3 of overlap",
    )


def check_pockets(shade: Part, lamp: Lamp, r: Report) -> None:
    """A magnet's worth of hole, a backing that survives it, and a roof on top."""
    r.section("magnet pockets")
    bore = lamp.pocket_d / 2
    backing = lamp.pad_backing()

    for i, plane in enumerate(pad_planes(lamp)):
        tag = f"pocket {i}"
        r.check(not is_solid_at(shade, *_at(plane, lamp.magnet_t / 2)), f"{tag} is hollow")
        r.check(
            not is_solid_at(shade, *_at(plane, lamp.magnet_t - 0.2)),
            f"{tag} is open to full magnet depth",
        )
        r.check(
            is_solid_at(shade, *_at(plane, lamp.magnet_t + 0.2)),
            f"{tag} has a floor at exactly the magnet's thickness",
        )
        r.check(
            is_solid_at(shade, *_at(plane, lamp.magnet_t + backing - 0.3)),
            f"{tag} keeps its {backing:.1f} mm of backing",
        )
        # The floor is whole, not just present on the axis. Off-axis the wall has
        # more to give, not less -- both faces are spheres about one centre --
        # so a hole here would mean the pocket had been bored somewhere the band
        # is not, which is the failure the even wall exists to prevent.
        for up in (-bore + 0.3, 0.0, bore - 0.3, bore * sqrt(2) - 0.3):
            r.check(
                is_solid_at(shade, *_at(plane, lamp.magnet_t + 0.2, up=up)),
                f"{tag} floor is unbroken {up:+.1f} mm up",
            )
        # Bore width, and -- the print-critical one -- that the teardrop's roof
        # is above the bore and not beside it. A pocket built on a plane whose
        # y axis had flipped would pass every test but this one, and would print
        # with a sagging bridge right where the magnet has to sit flat.
        deep = lamp.magnet_t / 2
        r.check(
            not is_solid_at(shade, *_at(plane, deep, across=bore - 0.3)),
            f"{tag} is {lamp.pocket_d:.1f} mm across",
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


def check_fit_test(band: Part, shade: Part, lamp: Lamp, r: Report) -> None:
    """The test print is the shade's own seat, with the grille left off."""
    r.section("fit test")
    r.check(len(band.solids()) == 1, "the band is one solid", f"{len(band.solids())}")

    box, shade_box = band.bounding_box(), shade.bounding_box()
    r.check(
        abs(box.max.X - shade_box.max.X) < 1e-6 and abs(box.max.Z - lamp.band_h) < 1e-6,
        "same diameter and height as the shade it tests",
        f"{2 * box.max.X:.2f} mm across, {box.max.Z:.2f} mm tall",
    )

    mid = lamp.band_h / 2
    face, inner = lamp.band_outer_radius(mid), lamp.band_inner_radius(mid)
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

    for i, plane in enumerate(pad_planes(lamp)):
        r.check(
            not is_solid_at(band, *_at(plane, lamp.magnet_t / 2)),
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


SLIDER_CASES: list[tuple[str, dict]] = [
    # The default lamp is not in here: everything above already measures it, and
    # each case below is a whole shade built from scratch.
    # A cereal bowl: everything small at once, which is where a fixed minimum
    # (MIN_GAP, MIN_EYE) starts fighting a derived maximum.
    (
        "small bowl",
        dict(bowl_d=120, bowl_h=55, band_h=12, wall=2.0, ring_count=3, eye_d=25,
             magnet_d=4, magnet_t=1.5, magnet_count=5, rim_inset=2),
    ),
    # A mixing bowl with as much grille as the sliders allow.
    (
        "big bowl, many rings",
        dict(bowl_d=320, bowl_h=150, band_h=30, wall=4.0, ring_count=10, eye_d=110,
             magnet_d=12, magnet_t=3.5, magnet_count=16, rim_inset=6),
    ),
    # Two rings is the floor: the band and the hub, with no inner ring at all,
    # so ring_gap() divides by one and ring_radii() returns a single radius.
    ("two rings", dict(ring_count=2, eye_d=140)),
    # Nothing here is a sensible number. All of it has to come back valid.
    (
        "every slider past its stop",
        dict(bowl_d=1e4, bowl_h=1e-3, bowl_wall=99, bowl_hole_d=1e4, band_h=1e4,
             wall=0.0, chamfer=99, rim_inset=1e4, eye_d=1e4, ring_count=999,
             arm_embed=99, magnet_d=1e4, magnet_t=1e4, magnet_count=999,
             pocket_lead_in=99),
    ),
    # ...and the same from the other side.
    (
        "every slider below its stop",
        dict(bowl_d=0, bowl_h=0, bowl_wall=0, bowl_hole_d=0, band_h=0, wall=0,
             chamfer=-5, rim_inset=-5, eye_d=0, ring_count=-9, arm_embed=-9,
             magnet_d=0, magnet_t=0, magnet_count=0, pocket_lead_in=-9),
    ),
]


def check_parameters(r: Report) -> None:
    """The sliders cannot produce a part that fails to build, or a silly one.

    Two claims, and the first is the one that rots quietly: **the website's
    defaults are this model.** ``PARAMS`` carries its own copy of every default
    for the UI to render before anything is built, so a number changed in
    ``Lamp`` and not in the slider -- or the reverse -- would leave the page
    drawing a part nobody designed. Comparing the two objects catches that;
    reading the code does not.

    The second is that ``Lamp.of`` really clamps. Each case below is built, not
    merely constructed, because the invariants that matter are geometric: a ring
    spacing that went negative or a pocket that outgrew its band does not raise
    in ``of()``, it raises -- or worse, does not raise -- in OCC.
    """
    r.section("parameters")

    slider_defaults = {p["name"]: p["default"] for p in LAMP_PARAMS}
    r.check(
        Lamp.of(**slider_defaults) == DEFAULT,
        "the website's own defaults rebuild the default lamp",
        f"{len(slider_defaults)} sliders",
    )
    r.check(
        Lamp.of() == DEFAULT,
        "and so does an empty parameter set",
    )
    for p in LAMP_PARAMS:
        lo, hi = Lamp.of(**{p["name"]: p["min"]}), Lamp.of(**{p["name"]: p["max"]})
        r.check(
            lo.pad_backing() >= MIN_BACKING - 1e-9
            and hi.pad_backing() >= MIN_BACKING - 1e-9,
            f"{p['name']} keeps the magnet's backing at either stop",
            f"{lo.pad_backing():.2f} / {hi.pad_backing():.2f} mm",
        )

    for label, kwargs in SLIDER_CASES:
        lamp = Lamp.of(**kwargs)
        r.check(lamp.ring_gap() >= MIN_GAP - 1e-9, f"{label}: rings keep their air",
                f"{lamp.ring_gap():.2f} mm")
        r.check(min(lamp.ring_radii()) > 0, f"{label}: every ring has a radius")
        r.check(
            lamp.rim_inset + lamp.band_h < lamp.bowl_h - lamp.bowl_wall - lamp.wall,
            f"{label}: the band stays inside the dome",
        )

        shade = create_shade(lamp)
        box = shade.bounding_box()
        r.check(len(shade.solids()) == 1, f"{label}: builds one solid",
                f"{len(shade.solids())} solid(s)")
        r.check(
            abs(box.min.Z) < 1e-6 and abs(box.max.Z - lamp.band_h) < 1e-6,
            f"{label}: comes out in print pose",
            f"z {box.min.Z:.3f}..{box.max.Z:.3f}, band_h {lamp.band_h:.2f}",
        )
        # Half a magnet pitch, not BETWEEN: these lamps carry anywhere from one
        # magnet to sixteen, and at sixteen the pads land on 22.5 deg themselves.
        mid = lamp.band_h / 2
        r.check(
            is_solid_at(
                shade,
                *_polar(lamp.band_outer_radius(mid) - 0.3, 180.0 / lamp.magnet_count, mid),
            ),
            f"{label}: the seat is there",
        )
        r.check(
            not is_solid_at(shade, 0.0, 0.0, mid),
            f"{label}: the eye is still open",
        )


def run() -> Report:
    r = Report()
    lamp = DEFAULT
    bowl = create_bowl(lamp)
    shade = create_shade(lamp)
    band = create_fit_test()
    check_bowl(bowl, lamp, r)
    check_bead(bowl, shade, lamp, r)
    check_shade_body(shade, lamp, r)
    check_eye(shade, lamp, r)
    check_band_wall(shade, lamp, r)
    check_seat(shade, bowl, lamp, r)
    check_pockets(shade, lamp, r)
    check_fit_test(band, shade, lamp, r)
    check_edges(shade, r)
    check_parameters(r)
    return r


def main() -> None:
    r = run()
    print(r.render())
    sys.exit(1 if r.failures else 0)


if __name__ == "__main__":
    main()
