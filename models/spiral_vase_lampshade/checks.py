"""Geometry assertions for the wave shade.

    uv run check spiral_vase_lampshade
    uv run python -m models.spiral_vase_lampshade.checks

Nothing here is visible in a projection, and one thing here is not visible in a
*render* either: this is a single-wall vase-mode print, so whether the modelled
0.8 mm shell actually got built is the question the whole file is organised
around. It is point-sampled through the solid along the surface's own normal --
not radially, and not re-derived from the same constant the geometry used, since
either shortcut would pass on a part that had quietly stopped honouring
``wall``.

The other assertions are the claims the module docstring makes, turned into
things that can fail:

* the 83 mm register the design is named for is a real circle, not a diameter
  a lobe happens to cross;
* the collar is a foot -- ``collar_wall`` thick for most of its height -- and
  its bore is open;
* the waves are waves: crests where the field says crests, valleys where it
  says valleys, and both *probed on the solid* rather than compared against the
  formula on both sides;
* the twist genuinely rotates the pattern with height, and by ``twist_turns``
  turns rather than that over the lobe count (see ``wave.crest_angle``);
* the pinch genuinely pinches -- a section at an envelope node is round where
  a section at an antinode is not;
* it prints: overhang inside ``MAX_OVERHANG``, footprint inside ``BED_BUDGET``,
  collar on the bed and mouth open at the top.

Every sample goes through one ``solid_probe`` rather than ``is_solid_at``, and
on this part that is the difference between a check that runs and one that does
not: the shell is 168 B-spline faces, and building a fresh solid classifier for
each of the ~90 samples below costs 2.7 seconds a time -- four minutes of
classifier construction to take a millisecond of readings.

The last section is the other kind of assertion. The model is parametric on the
website, so it drags every slider to its stops, past them, and into combinations
nobody would choose, and asserts that what comes back is still one solid. Those
builds run at a coarse ``z_sections``/``facets`` -- resolution is construction,
not design, which is exactly why those two are ``Shade`` fields and not sliders.
"""

from __future__ import annotations

import sys
from dataclasses import replace
from math import acos, cos, degrees, pi, sin
from typing import Callable

from build123d import Part, Vector

from ..lib.checks import (
    Report,
    periodic_seams,
    sharp_convex_edges,
    solid_probe,
)
from . import create_shade, section_heights, wave
from .config import BED_BUDGET, COLLAR_HOLD, DEFAULT, MAX_OVERHANG, Shade
from .wave import outer_point, outward_normal

At = Callable[[float, float, float], bool]

PROBE = 0.2
"""How far off a surface a point has to be before it counts as on the other side.

Bigger than every source of error between the design field and the built solid,
and smaller than half the thinnest wall it is used on. The dominant error is the
ruled loft's chord in z, and it is 0.113 mm, not the 0.005 mm an earlier version
of this note claimed: sampled against ``wave.outer_radius`` at twenty points
across each of the default's 80 bands, that is how far the chord departs from
the field at worst, on the steep part of the fade where the amplitude is coming
up fastest. The periodic spline's error in theta is an order of magnitude under
that (about 0.008 mm at 144 points across six lobes).

So the headroom is a factor of 1.8, not three orders of magnitude -- still
enough for one number to serve everywhere, and still under half of the 0.8 mm
wall, but not enough for the figure to go unmeasured if ``z_sections`` is ever
lowered: the same sampling gives 0.031 mm at 160 sections and 0.368 mm at 40,
which is the inverse-square a chord against a curve should be, and the last of
those would be too big for this constant to still be true.
"""

COARSE = dict(z_sections=16, facets=24)
"""Resolution for the parameter sweep: enough to be a solid, cheap enough to be
built a dozen times. The point of those builds is that they *build*, not what
they look like -- though ``facets`` is still raised with the lobe count, since a
section sampled below two points per lobe is not a coarse version of the curve,
it is a different curve."""


def _polar(at: At, radius: float, theta: float, z: float) -> bool:
    return at(radius * cos(theta), radius * sin(theta), z)


def check_pose(part: Part, shade: Shade, r: Report) -> None:
    r.section("print pose")
    bb = part.bounding_box()
    r.check(
        abs(bb.min.Z) < 0.01,
        "collar sits on the build plate (min z = 0)",
        f"min z = {bb.min.Z:.4f} mm",
    )
    r.check(
        abs(bb.max.Z - shade.height) < 0.01,
        "overall height is `height` -- no lip, nothing above the mouth",
        f"{bb.max.Z:.2f} mm vs {shade.height:.2f} mm",
    )
    r.check(
        len(part.solids()) == 1,
        "one continuous shell, not a split or disjoint solid",
        f"{len(part.solids())} solid(s)",
    )
    width = max(bb.max.X - bb.min.X, bb.max.Y - bb.min.Y)
    r.check(
        width <= BED_BUDGET,
        "footprint fits the small-printer bed budget",
        f"{width:.1f} mm across vs {BED_BUDGET:.0f} mm budget",
    )


def check_base_register(at: At, shade: Shade, r: Report) -> None:
    """The 83 mm interface: a real circle, at the right diameter, up the collar
    and across the join into the body."""
    r.section("83 mm base register")
    for z, where in (
        (shade.chamfer() + 0.2, "collar"),
        (shade.collar_h - 0.2, "collar top"),
    ):
        inside = all(
            _polar(at, shade.base_r - PROBE, 2 * pi * k / 8, z) for k in range(8)
        )
        outside = any(
            _polar(at, shade.base_r + PROBE, 2 * pi * k / 8, z) for k in range(8)
        )
        r.check(
            inside,
            f"{where}: material inside the register all the way round",
            f"8 angles at r = {shade.base_r - PROBE:.2f} mm, z = {z:.1f} mm",
        )
        r.check(
            not outside,
            f"{where}: nothing outside the register at any angle",
            f"8 angles at r = {shade.base_r + PROBE:.2f} mm, z = {z:.1f} mm",
        )

    # The body leaves the collar as a circle too -- that is what FADE_IN buys,
    # and it is the assertion that would fail if the fade were made a slider
    # and dragged to zero.
    just_above = 0.4
    t = just_above / shade.body_h
    spread = max(
        abs(wave.outer_radius(shade, 2 * pi * k / 32, t) - shade.base_r)
        for k in range(32)
    )
    r.check(
        spread < 0.05,
        "the body leaves the collar circular -- waves faded to nothing at t = 0",
        f"worst deviation {spread:.4f} mm, {just_above:.1f} mm above the collar",
    )


def check_collar(at: At, shade: Shade, r: Report) -> None:
    r.section("collar")
    z = shade.collar_h * COLLAR_HOLD * 0.5
    bore = shade.base_r - shade.collar_wall
    r.check(
        _polar(at, bore + PROBE, 0.0, z),
        "collar is `collar_wall` thick where it is held",
        f"solid at r = {bore + PROBE:.2f} mm, z = {z:.1f} mm",
    )
    r.check(
        not _polar(at, bore - PROBE, 0.0, z),
        "collar bore is open -- it is a foot, not a plug",
        f"void at r = {bore - PROBE:.2f} mm",
    )
    r.check(
        not at(0.0, 0.0, z),
        "the axis is clear through the collar, for the light",
        f"void on the axis at z = {z:.1f} mm",
    )
    # The chamfer is drawn as a change of section, so if it went missing the
    # loft would still succeed -- which is exactly why it is asserted.
    ch = shade.chamfer()
    r.check(
        not _polar(at, shade.base_r - ch + PROBE, 0.0, 0.05),
        "elephant's-foot chamfer took: the first layer is back from the register",
        f"void at r = {shade.base_r - ch + PROBE:.2f} mm, z = 0.05 mm",
    )


def check_wall(at: At, shade: Shade, r: Report) -> None:
    """Four samples through the shell, along its own outward normal.

    Along the normal rather than the radius because on a lobed section the two
    differ by up to ~30 degrees, and a radial probe would confirm a 0.8 mm wall
    on geometry that only has 0.69 -- see ``wave.outward_normal``.
    """
    r.section("vase-mode wall")
    r.check(
        shade.wall >= 0.79,
        "wall clears the two-perimeter floor for a 0.4 mm nozzle",
        f"{shade.wall:.2f} mm",
    )
    # Spread across heights and angles on purpose: a crest, a valley, a flank,
    # one near each end of the body.
    for theta, t, label in (
        (0.0, 0.08, "low band, crest"),
        (pi / 5, 0.30, "lower body, valley"),
        (0.7, 0.50, "widest band, flank"),
        (2.0, 0.72, "upper body"),
        (4.0, 0.97, "at the mouth"),
    ):
        x, y = outer_point(shade, theta, t)
        nx, ny = outward_normal(shade, theta, t)
        z = shade.collar_h + shade.body_h * t
        where = f"theta = {degrees(theta):.0f} deg, z = {z:.0f} mm"

        def sample(depth: float, x=x, y=y, nx=nx, ny=ny, z=z) -> bool:
            return at(x - depth * nx, y - depth * ny, z)

        r.check(sample(PROBE), f"{label}: material just inside the outer surface", where)
        r.check(
            not sample(-PROBE), f"{label}: void just outside the outer surface", where
        )
        r.check(sample(shade.wall / 2), f"{label}: solid at mid-wall", where)
        r.check(
            not sample(shade.wall + PROBE),
            f"{label}: hollow past the bore, one wall in",
            f"{where}, wall = {shade.wall:.2f} mm",
        )


def check_waves(at: At, shade: Shade, r: Report) -> None:
    """The lobes are really there, and really where the field says they are.

    Every probe here sits within a wall of a surface, and that is forced rather
    than fussy: this part is a 0.8 mm shell, so "somewhere up the side of a
    lobe" is not material, it is the cavity, and the classifier reports it void
    for the same reason it reports free air void. Only three radii on a given
    ray mean anything -- just inside a surface, just outside it, and the far
    side of the bore -- so the assertions are built from those.

    The middle probe is the one that carries the claim. Taken at the *ridge's*
    radius but on the *valley's* ray, it is in free air only because the two
    radii differ; on a shade whose waves had gone flat it would land on the
    surface and read solid.
    """
    r.section("wave field")
    t = _envelope_antinode(shade)  # where the lobes run deepest
    z = shade.collar_h + shade.body_h * t
    profile = wave.silhouette(shade, t)
    ridge = wave.ridge_angle(shade, t)
    valley = ridge + pi / shade.lobes  # half a lobe round from a ridge
    r_ridge = wave.outer_radius(shade, ridge, t)
    r_valley = wave.outer_radius(shade, valley, t)

    r.check(
        _polar(at, r_ridge - PROBE, ridge, z) and not _polar(at, r_ridge + PROBE, ridge, z),
        "the ridge's surface is where the field puts it",
        f"r = {r_ridge:.1f} mm at theta = {degrees(ridge):.0f} deg, standing "
        f"{r_ridge - profile:.1f} mm proud of the {profile:.1f} mm profile",
    )
    r.check(
        not _polar(at, r_ridge - PROBE, valley, z),
        "at the ridge's radius, half a lobe round, there is open air",
        f"void at r = {r_ridge - PROBE:.1f} mm, theta = {degrees(valley):.0f} deg -- "
        f"{r_ridge - r_valley:.1f} mm of lobe between the two",
    )
    r.check(
        _polar(at, r_valley - PROBE, valley, z) and r_valley < profile,
        "the valley's surface is cut inside the profile, not merely level with it",
        f"r = {r_valley:.1f} mm vs profile {profile:.1f} mm",
    )


TWIST_BANDS = (0.15, 0.40)
"""Two heights the twist is measured between, and they are chosen, not arbitrary.

Both sit inside the *same* half of the envelope -- the default's first positive
lobe, which runs from the collar to half height -- and both sit where it is
strong (0.81 and 0.59 of full depth), which matters twice over. The lobes are
deep there, so a probe has real material to find or miss; and because the sign
is the same at both, the ridge's movement between them is the twist and nothing
else. Straddling a node instead would fold half a lobe of crest/valley inversion
into the answer, and the check would then pass on a shade with no twist at all.
"""


def check_twist(at: At, shade: Shade, r: Report) -> None:
    """The pattern rotates with height, and by ``twist_turns`` turns of it.

    The discriminating probe is the last: material at the high band's own ridge
    angle, *nothing* at the low band's. Sampling each band at its own ridge only
    shows a ridge exists at both heights, which would pass just as happily with
    the twist set to zero.

    The radius those two are taken at cannot be a fixed fraction of the lobe
    depth, because how far the ridge moves is itself a slider: at the default's
    gentle 0.05 turns the ridge shifts 9.4 degrees where the lobes are 72 apart,
    so a probe halfway up the lobe would still find material at the stale angle
    and the check would quietly become vacuous. It is derived from the shift
    instead -- halfway between the carrier at the stale angle and its peak --
    and the margin that leaves is asserted before it is relied on.
    """
    r.section("twist")
    t_low, t_high = TWIST_BANDS
    z_high = shade.collar_h + shade.body_h * t_high

    stale = wave.ridge_angle(shade, t_low)
    fresh = wave.ridge_angle(shade, t_high)

    # The high band's surface at its own ridge, and at the angle the ridge used
    # to be at. How far apart those two radii are is what this check has to
    # spend, and it is asserted before it is spent: if a future twist_turns made
    # the shift small enough for them to close up, both probes below would land
    # on the same surface and agree with each other while proving nothing.
    r_fresh = wave.outer_radius(shade, fresh, t_high)
    r_stale = wave.outer_radius(shade, stale, t_high)
    gap = r_fresh - r_stale
    r.check(
        gap > 5 * PROBE,
        "the twist is big enough for this to discriminate at all",
        f"the ridge shifts {degrees(fresh - stale):.2f} deg between the bands, "
        f"dropping the surface {gap:.2f} mm at the old angle (need "
        f"{5 * PROBE:.1f} mm)",
    )

    for t, label in ((t_low, "low band"), (t_high, "high band")):
        z = shade.collar_h + shade.body_h * t
        ridge = wave.ridge_angle(shade, t)
        surface = wave.outer_radius(shade, ridge, t)
        r.check(
            _polar(at, surface - PROBE, ridge, z)
            and not _polar(at, surface + PROBE, ridge, z),
            f"{label}: a ridge stands where the twist puts it",
            f"surface at r = {surface:.1f} mm, theta = {degrees(ridge):.1f} deg, "
            f"z = {z:.0f} mm",
        )

    r.check(
        not _polar(at, r_fresh - PROBE, stale, z_high),
        "the high band has no ridge at the low band's angle -- it really moved",
        f"void at r = {r_fresh - PROBE:.1f} mm, theta = {degrees(stale):.1f} deg, "
        f"z = {z_high:.0f} mm, where the surface has fallen back to "
        f"{r_stale:.1f} mm",
    )

    # `twist_turns` means turns of the pattern, not turns divided by the lobe
    # count. This one is a claim about the field rather than the solid, and is
    # here because it is what would have caught the carrier being written the
    # obvious way round -- `cos(lobes * theta + 2 pi * twist * t)` -- which
    # every probe above would have passed without complaint.
    moved = degrees(wave.crest_angle(shade, t_high) - wave.crest_angle(shade, t_low))
    expected = -360.0 * shade.twist_turns * (t_high - t_low)
    r.check(
        abs(moved - expected) < 1e-9,
        "the ridge turned by `twist_turns` turns of the *pattern*",
        f"{moved:.3f} deg over {t_high - t_low:.2f} of the height, expected "
        f"{expected:.3f} deg -- independent of the {shade.lobes} lobes",
    )


def _envelope_node(shade: Shade) -> float | None:
    """The lowest height inside the body where the envelope crosses zero.

    ``(1 - pinch) + pinch * cos(2 pi m t + phase) = 0`` has a solution exactly
    when ``pinch >= 0.5`` -- below that the constant term never lets the cosine
    reach it, which is the algebraic form of "the lobes never invert".

    The phase has to be carried through, and the default is the case that proves
    it: at ``env_phase = -pi/2`` the first node sits at exactly half height,
    where the phase-free formula would have put it a quarter of the way up and
    every probe taken there would have been measuring a lobe at full depth while
    calling it a node.
    """
    if shade.pinch < 0.5 or shade.wave_cycles <= 0:
        return None
    turn = 2 * pi * shade.wave_cycles
    base = acos(-(1 - shade.pinch) / shade.pinch)
    # Both branches of the arccos, each shifted into [0, 1] by whole periods.
    for raw in (base, -base):
        for k in range(int(shade.wave_cycles) + 2):
            node = (raw - shade.env_phase + 2 * pi * k) / turn
            if 0.02 < node < 0.98:
                return node
    return None


def _envelope_antinode(shade: Shade) -> float:
    """Where the envelope is furthest from zero -- the deepest lobes in the body."""
    ts = [i / 400 for i in range(401)]
    return max(ts, key=lambda t: abs(wave.envelope(shade, t)) * wave.fade(t))


def check_pinch(at: At, shade: Shade, r: Report) -> None:
    """At an envelope node the section is round; at an antinode it is not.

    One probe recipe, two heights, opposite answers -- which is what makes this
    a test of the envelope rather than of two unrelated things. The recipe is
    "take the ridge's own surface radius, then look for material there on the
    *valley's* ray". On a round section the valley is at that radius too, so it
    reads solid; on a lobed one the valley has fallen 29 mm inside it and the
    probe is in open air.
    """
    r.section("pinch")
    node = _envelope_node(shade)
    if node is None:
        r.check(
            shade.pinch <= 0.5,
            "no envelope node exists, which only makes sense below pinch = 0.5",
            f"pinch = {shade.pinch:.2f}",
        )
        return

    bands = ((_envelope_antinode(shade), "antinode", False), (node, "node", True))
    for t, label, expect_round in bands:
        z = shade.collar_h + shade.body_h * t
        ridge = wave.ridge_angle(shade, t)
        valley = ridge + pi / shade.lobes
        r_ridge = wave.outer_radius(shade, ridge, t)
        r_valley = wave.outer_radius(shade, valley, t)
        got = _polar(at, r_ridge - PROBE, valley, z)
        r.check(
            got is expect_round,
            f"{label} (t = {t:.3f}): the section is "
            + ("pinched back to round" if expect_round else "lobed"),
            f"ridge at r = {r_ridge:.1f} mm, valley at r = {r_valley:.1f} mm, "
            f"{r_ridge - r_valley:.1f} mm apart; envelope = "
            f"{wave.envelope(shade, t):+.3f}",
        )


def check_printability(at: At, part: Part, shade: Shade, r: Report) -> None:
    r.section("printability")
    worst, where = -180.0, (0.0, 0.0)
    for i in range(201):
        t = i / 200
        for j in range(120):
            theta = 2 * pi * j / 120
            angle = wave.overhang_angle(shade, theta, t)
            if angle > worst:
                worst, where = angle, (theta, t)
    z = shade.collar_h + shade.body_h * where[1]
    r.check(
        worst <= MAX_OVERHANG,
        "steepest overhang stays inside the vase-mode budget",
        f"{worst:.1f} deg from vertical at theta = {degrees(where[0]):.0f} deg, "
        f"z = {z:.0f} mm (budget {MAX_OVERHANG:.0f} deg)",
    )

    bb = part.bounding_box()
    r.check(
        not at(0.0, 0.0, bb.max.Z - 1.0),
        "the mouth is open -- no lip, nothing for vase mode to step over",
        f"void on the axis 1 mm below the rim (z = {bb.max.Z - 1.0:.1f} mm)",
    )
    predicted = shade.footprint()
    measured = max(bb.max.X - bb.min.X, bb.max.Y - bb.min.Y)
    r.check(
        measured <= predicted + 0.5,
        "`Shade.footprint()` bounds the real footprint rather than under-calling it",
        f"predicted <= {predicted:.1f} mm, measured {measured:.1f} mm",
    )


def check_edges(part: Part, shade: Shade, r: Report) -> None:
    """The house sharp-edge rule, with the three exceptions this part really has.

    All three are stated rather than merely not noticed, which is the whole
    point of ``allow``, and all three are artefacts of building a shell out of
    lofted periodic splines rather than decisions anybody made:

    * the **mouth**, where a vase-mode rim is one bead thick;
    * the **horizontal joins** between one ruled loft patch and the next;
    * the **vertical seam** up each of those patches, where a periodic surface
      closes on itself. Its two "adjacent" faces are the same face, so there is
      no second surface to take a dihedral against and ``interior_angle`` can
      only answer ``None`` -- 163 of the part's 334 edges, every one of them
      unmeasurable for the same documented reason.

    Note what is *not* exempted: the collar's own two bottom edges are real
    edges of the design, they are chamfered, and ``check_collar`` additionally
    probes the solid to prove the chamfer took -- an angle that measures 135
    degrees is weaker evidence than material that is not there.
    """
    rim = part.bounding_box().max.Z
    levels = section_heights(shade)
    seams = [z for z in levels if 0.01 < z < rim - 0.01]

    def at_rim(edge) -> bool:
        # center() is safe for this test even on a closed periodic edge, where
        # it is famously not the arc centre: the whole edge lies in one z plane,
        # so whatever x and y it returns, the z is the plane's.
        return edge.center().Z > rim - 0.01

    def at_seam(edge) -> bool:
        z = edge.center().Z
        return any(abs(z - s) < 1e-6 for s in seams)

    is_seam = periodic_seams(part)

    def at_patch_seam(edge) -> bool:
        """A same-face closure seam, *and* one that spans exactly one loft patch.

        The second half is the scoping ``is_periodic_seam``'s own docstring asks
        every caller for. A same-face seam is necessary evidence that no dihedral
        could have been measured, not sufficient evidence that the edge is
        harmless -- a genuine near-tangent sliver can satisfy it too -- so the
        exemption is narrowed to seams that are where construction says they must
        be: running from one section plane to the very next, which is the whole
        extent of a single ruled patch.

        Scoped that way rather than by "roughly vertical", which was tried and
        is wrong: this surface overhangs up to 41.6 degrees, so a seam over the
        shoulder of a lobe leans a long way off vertical while being no less a
        seam. Endpoints on consecutive section planes is the real property, it
        does not soften as the geometry gets steeper, and a horizontal sliver
        (both endpoints on one plane) still fails it.
        """
        if not is_seam(edge):
            return False
        z0, z1 = (edge @ 0).Z, (edge @ 1).Z
        low, high = min(z0, z1), max(z0, z1)
        return any(
            abs(low - a) < 1e-6 and abs(high - b) < 1e-6
            for a, b in zip(levels, levels[1:])
        )

    allow = (
        (
            at_rim,
            "the mouth: a vase-mode rim is one bead thick, so a chamfer there is "
            "neither printable by a spiralising perimeter nor meaningful once it is",
        ),
        (
            at_seam,
            "the horizontal seams between ruled loft patches -- not edges of the "
            "design but of how the surface is built, each one an interior join in "
            "what the print sees as a single continuous wall",
        ),
        (
            at_patch_seam,
            "the vertical seam closing each periodic loft surface: its two "
            "adjacent faces are one and the same face, so no dihedral angle "
            "exists to measure rather than one existing and being sharp",
        ),
    )
    r.section("edge treatment")
    r.check(
        len(seams) == len(levels) - 2,
        "the seam exemption names loft joins only, not the bed or the mouth",
        f"{len(seams)} of {len(levels)} section heights exempt",
    )
    survey = sharp_convex_edges(part, allow=allow)
    r.check(
        not survey.sharp,
        "no untreated sharp convex edges outside the named exception",
        f"{len(survey.sharp)} found"
        + (f": lengths {[round(e.length, 1) for e in survey.sharp]}" if survey.sharp else ""),
    )
    r.check(
        not survey.unclassifiable,
        "every edge could be measured",
        f"{len(survey.unclassifiable)} unclassifiable",
    )


def check_parameters(r: Report) -> None:
    """Drag every slider to its stop, past it, and into bad company."""
    r.section("parameter range")
    cases = [
        ("all defaults, coarse", {}),
        ("deepest waves", {"wave_depth": 0.9, "lobes": 3}),
        ("most lobes, deep", {"lobes": 40, "wave_depth": 0.9}),
        ("no waves at all", {"wave_depth": 0.0, "pinch": 0.0}),
        ("full pinch, many cycles", {"pinch": 1.0, "wave_cycles": 20.0}),
        ("wound tight", {"twist_turns": 9.0, "lobes": 12}),
        ("wound the other way", {"twist_turns": -9.0}),
        ("squat and wide", {"max_dia": 900.0, "height": 1.0, "mouth_dia": 400.0}),
        ("tall and thin", {"max_dia": 10.0, "height": 900.0, "mouth_dia": 1.0}),
        ("wall thicker than the collar", {"wall": 9.0, "collar_wall": 0.1}),
        ("collar taller than the shade", {"collar_h": 500.0, "height": 70.0}),
        ("mouth wider than the bulge", {"mouth_dia": 300.0, "max_dia": 60.0}),
        (
            "everything at zero",
            dict.fromkeys(
                ("wave_depth", "pinch", "wave_cycles", "twist_turns", "bulge_at"), 0.0
            ),
        ),
    ]
    for label, kwargs in cases:
        shade = Shade.of(**{**kwargs, **COARSE})
        # Two points per lobe is the floor below which the sampled section is a
        # different curve rather than a coarse one, so coarseness gives way to
        # the lobe count rather than the other way round.
        shade = replace(shade, facets=max(shade.facets, 6 * shade.lobes))
        try:
            part = create_shade(shade)
        except Exception as exc:  # noqa: BLE001 -- the whole point is that it must not
            r.check(False, f"{label}: builds", f"raised {type(exc).__name__}: {exc}")
            continue
        r.check(
            len(part.solids()) == 1 and part.volume > 0,
            f"{label}: builds one solid with volume",
            f"{len(part.solids())} solid(s), {part.volume / 1000:.1f} cm3, "
            f"wave_depth clamped to {shade.wave_depth:.3f}",
        )


def run() -> Report:
    r = Report()
    shade = DEFAULT
    part = create_shade(shade)

    # One classifier for every sample below; see the module docstring.
    probe = solid_probe(part)

    def at(x: float, y: float, z: float) -> bool:
        return probe(Vector(x, y, z))

    check_pose(part, shade, r)
    check_base_register(at, shade, r)
    check_collar(at, shade, r)
    check_wall(at, shade, r)
    check_waves(at, shade, r)
    check_twist(at, shade, r)
    check_pinch(at, shade, r)
    check_printability(at, part, shade, r)
    check_edges(part, shade, r)
    check_parameters(r)
    return r


def main() -> None:
    r = run()
    print(r.render())
    sys.exit(1 if r.failures else 0)


if __name__ == "__main__":
    main()
