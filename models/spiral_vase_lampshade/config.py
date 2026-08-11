"""Every number the wave shade is cut from, and the clamps that keep it buildable.

No geometry here. ``Shade`` is the whole design as one frozen object, and
``Shade.of()`` is the only way website input becomes one -- so a slider dragged
to a stop produces a different lamp, never a failed build.

The numbers split into three groups, and they are not equally free:

* **The interface.** ``base_dia`` is 83 mm because that is the published
  requirement of the base this shade is meant to sit on (see README). It is a
  measured constant, not a taste, and the collar exists to hold it.
* **The silhouette.** ``base_dia`` / ``max_dia`` / ``mouth_dia`` / ``height``
  and ``bulge_at`` -- four diameters and where the widest one sits. Between
  them they are the vase you would get with the waves turned off.
* **The wave field.** ``lobes``, ``wave_depth``, ``twist_turns``,
  ``wave_cycles``, ``env_phase`` and ``pinch``. These are the design; the
  silhouette is only what they are wrapped around.
  ``spiral_vase_lampshade.wave`` documents what each one does to the surface.

Every default in the last two groups is **measured off the reference mesh**, not
judged from its photographs: 300 slices of JH's STL, Fourier-decomposed, with the
silhouette least-squares fitted to the mean radius of each. README's "Measured,
not guessed" gives the method and what it changed, which was almost everything.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from math import atan, degrees, pi

from ..lib.fits import MIN_WALL

# --- Constants that are not sliders ------------------------------------------

FADE_IN = 0.10
"""Fraction of the body over which the waves come up from nothing.

Not exposed, because it is the one number holding the shade to its base: at
``t = 0`` the wave amplitude is exactly zero, so the body leaves the collar as a
true circle of ``base_dia`` and the 83 mm interface is a real circle rather than
one a lobe happens to cross. Making it a slider would let the site produce a
shade that no longer meets the spec it is named for.
"""

BASE_CHAMFER = 0.4
"""Elephant's-foot relief on the collar's bottom edges, inside and out.

Built into the loft as two extra sections rather than cut with an OCC edge op --
see ``_collar_sections``. A first layer squashed proud of an 83 mm register is
the difference between the shade sitting flat on its base and rocking on it.

It is taken off *both* edges of the annulus, which is what caps it at a quarter
of the collar wall rather than the half that would still leave a valid solid:
0.4 mm each side of a 2.4 mm foot leaves a 1.6 mm first layer, four beads of a
0.4 mm nozzle wide. At 0.6 it would leave 1.2 mm, and a three-bead first layer
on a part this tall is not enough to hold it down.
"""

COLLAR_HOLD = 0.7
"""Fraction of the collar that keeps its full thickness before thinning to the shell.

The collar is the foot the shade is registered and handled by, so it has to be
a foot for most of its height rather than a wall that starts vanishing at the
first layer. Above this the bore opens out to the shell's own wall, which is
material being *removed* as the part rises -- every layer a subset of the one
below it, so nothing there is printed over air.
"""

LAYER_HEIGHT = 0.2
EXTRUSION_WIDTH = 0.6
"""What the shade is sliced at, and the two numbers the overhang limit is *derived*
from rather than guessed at. The width is the reference design's own
recommendation for the external perimeter; see README."""

MAX_OVERHANG = degrees(atan(EXTRUSION_WIDTH / 2 / LAYER_HEIGHT))
"""Degrees from vertical the outer surface may lean: 56.3, and it is arithmetic.

This started as a flat 45, which is the right rule for a *perimeter* that has to
bridge from the wall below it. Vase mode is not that. It lays one continuous
bead per layer, and each bead is supported by sitting partly on top of the one
under it, so what decides the limit is how far the wall steps sideways in one
layer against how wide the bead is: ``tan(angle) * LAYER_HEIGHT`` against
``EXTRUSION_WIDTH``. Half the bead still landing on its predecessor gives
``atan(width / 2 / layer)`` = 56.3 degrees, and 45 was leaving a third of the
envelope on the table.

Measuring the reference mesh is what forced the correction: it leans 50.8
degrees at its steepest, comfortably printable and comfortably over the old
limit. A budget that the design it is modelled on would have failed was
measuring the budget, not the design.

Still deliberately *not* clamped in ``Shade.of``. The sliders can reach 84
degrees (a 300 mm profile on a 60 mm height will do it) and that shape still
builds -- it just does not print. Clamping would be this module overruling a
shape somebody explicitly asked for; the honest move is to hold the *design* to
the budget and let an experiment be an experiment.
"""

BED_BUDGET = 180.0
"""Millimetres square the default has to fit, and it is the small-printer number.

Not the widest bed in the world -- the point of a budget is to be the one that
binds. The default measures 149 mm across, so the shade fits a Prusa Mini or an
Ender 3 as readily as the 256 mm machines the reference lamp targets.
"""

CURVATURE_SAFETY = 0.5
"""How much of a crest's curvature radius the wall is allowed to eat.

The inner surface is a true inward offset of the outer one, and an inward offset
self-intersects as soon as it is pushed further than the radius of curvature of
a convex crest. Half of it is the margin ``Shade.of`` clamps ``wave_depth``
against; see ``_max_wave_depth``.
"""

Z_SECTIONS = 80
FACETS = 144
"""Loft resolution: sections up the body, points around each one.

Both are construction, not design, so neither is a slider -- but they are
``Shade`` fields rather than module constants so ``checks.py`` can build a dozen
cheap variants when it drags the sliders to their stops, without mutating global
state to do it.

144 is measured, not chosen for comfort, and it is four times what this model
first shipped with. The binding feature is not the crest but the **valley**: at
six lobes and a depth of 0.44 the section's radius of curvature in the notch
between two lobes falls to about 1.0 mm on a 28 mm radius, and a periodic spline
through 8 points per lobe simply does not go where the field says. Probed on the
built solid at four ridges and valleys, 48 points put half of them in the wrong
place and 144 put none.

That is the whole reason this is the slowest model in the roster -- about 56
seconds against 32 at the old setting. It buys a surface that its own checks can
hold to the field, which the cheap setting could not.

``Z_SECTIONS`` also decides what the shade *looks like in a renderer*, which is
not the same question as what it measures. A ruled loft through 81 body sections
is 82 separate B-spline faces stacked 2.24 mm apart, and consecutive faces meet
at a real break in the surface normal -- 7 degrees at the calmest point of the
body, 17 at the top of the fade, 8.9 on average. The solid is only 0.113 mm off
the field there (``checks.PROBE``), so the *print* cannot show it, but a mesh
carries no normals across a face boundary, so every renderer shows all 82 of them
as fine horizontal banding. The website welds them back together at load
(``smoothNormals`` in ``website/index.html``); anything else looking at the STL
or the STEP will not, and is not wrong to.

Raising this is not the fix for that. The break falls off as 1/N where the cost
rises as N: 320 sections would still band, at four times the build.
"""


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _crest_curvature_radius(radius: float, depth: float, lobes: int) -> float:
    """Radius of curvature at a wave crest, in the plane of a cross-section.

    For the polar curve ``r(theta) = R (1 + a cos(n theta))`` the standard
    formula ``(r^2 + 2 r'^2 - r r'') / (r^2 + r'^2)^(3/2)`` collapses at the
    crest (where ``r' = 0``) to ``(1 + a + a n^2) / (R (1 + a)^2)``. This is its
    reciprocal, and it is the number the wall has to stay under: ``n`` enters
    squared, so doubling the lobe count is four times as punishing as doubling
    the depth.
    """
    return radius * (1 + depth) ** 2 / (1 + depth + depth * lobes**2)


def _max_wave_depth(radius: float, lobes: int, wall: float) -> float:
    """Deepest wave whose inward wall offset still cannot cross itself.

    Bisected rather than solved, because the closed form is a cubic and this
    runs once per build. ``_crest_curvature_radius`` falls monotonically in
    ``depth`` (the lobe-count term grows faster than the ``(1 + a)^2`` numerator
    for any ``lobes >= 2``), which is what makes bisection valid here.
    """
    ceiling = 0.45

    def fits(depth: float) -> bool:
        return wall <= CURVATURE_SAFETY * _crest_curvature_radius(radius, depth, lobes)

    if fits(ceiling):
        return ceiling
    low, high = 0.0, ceiling
    for _ in range(40):
        mid = (low + high) / 2
        if fits(mid):
            low = mid
        else:
            high = mid
    return low


@dataclass(frozen=True)
class Shade:
    """One wave shade. Frozen, so two of them can be built in one process."""

    # -- The interface to the base -------------------------------------------
    base_dia: float = 83.0
    collar_h: float = 6.5
    collar_wall: float = 2.4

    # -- Silhouette -----------------------------------------------------------
    # These three are the *wave-free* profile -- the vase you would get with
    # wave_depth at zero. Crests stand proud of them by wave_depth of the local
    # radius, so the part's real footprint is nearer max_dia * (1 + wave_depth):
    # 115 mm of profile measures 157 mm across the bed. `footprint` derives it.
    #
    # Every number in this block and the next is measured off the reference
    # mesh rather than judged from its photographs -- see README, "Measured,
    # not guessed". The silhouette three are a least-squares fit of the two
    # smoothsteps in `wave.silhouette` to the mean radius of 279 slices, which
    # they track to 0.95 mm rms.
    max_dia: float = 115.5
    mouth_dia: float = 84.0
    height: float = 185.8
    bulge_at: float = 0.477

    # -- Wave field -----------------------------------------------------------
    lobes: int = 6
    wave_depth: float = 0.44
    twist_turns: float = -0.19
    wave_cycles: float = 1.0
    env_phase: float = -1.5708  # -90 deg: a node at the collar, not an antinode
    pinch: float = 1.0

    # -- Shell ----------------------------------------------------------------
    # Vase mode prints one bead per layer and the slicer's external extrusion
    # width decides how fat that bead is (the reference design asks for 0.6 mm).
    # MIN_WALL is the *modelled* wall -- what the inner surface is offset by,
    # and what makes the shade a shell rather than a surface.
    wall: float = MIN_WALL

    # -- Construction resolution (not sliders; see Z_SECTIONS) ----------------
    z_sections: int = Z_SECTIONS
    facets: int = FACETS

    @classmethod
    def of(cls, **kwargs) -> Shade:
        """Build a shade from website input, clamped so the geometry stays valid.

        Every slider on the site lands here, and the contract is that no
        combination of them can produce a part that fails to build -- so this
        clamps rather than raises. The order is the dependency order: the
        silhouette has to settle before there is a smallest radius, the wall
        before the crest curvature means anything, and both before
        ``wave_depth`` has a ceiling at all.

        Where two inputs fight, the one that moves is the one whose being wrong
        is *safe*. A shade with shallower waves than asked for is still a
        lampshade; one whose inner surface has crossed itself is not a solid.
        """
        v = {f.name: kwargs.get(f.name, f.default) for f in fields(cls)}

        # The interface first: it is the one number this design is named for,
        # and the collar is sized inside it.
        v["base_dia"] = _clamp(v["base_dia"], 40.0, 300.0)
        v["height"] = _clamp(v["height"], 60.0, 400.0)
        v["collar_h"] = _clamp(v["collar_h"], 2.0, v["height"] / 3)
        v["wall"] = _clamp(v["wall"], 0.4, 3.0)
        # The collar is the thick foot the shade is registered by, so it is
        # never thinner than the shell it carries -- and never so thick it
        # closes the bore.
        v["collar_wall"] = _clamp(
            max(v["collar_wall"], v["wall"]), v["wall"], v["base_dia"] / 4
        )

        v["max_dia"] = _clamp(v["max_dia"], 40.0, 400.0)
        v["mouth_dia"] = _clamp(v["mouth_dia"], 20.0, 400.0)
        v["bulge_at"] = _clamp(v["bulge_at"], 0.15, 0.85)

        # Waves. lobes is an integer count of crests round the section, so a
        # dragged float has to land on one before it can size anything.
        v["lobes"] = int(_clamp(round(v["lobes"]), 2, 16))
        v["wave_cycles"] = _clamp(v["wave_cycles"], 0.0, 8.0)
        v["twist_turns"] = _clamp(v["twist_turns"], -1.0, 1.0)
        v["pinch"] = _clamp(v["pinch"], 0.0, 1.0)
        v["env_phase"] = _clamp(v["env_phase"], -pi, pi)

        # The depth ceiling depends on everything above: the wall is offset
        # inward from the tightest crest anywhere on the body, and the tightest
        # crest sits on the smallest silhouette radius.
        smallest = min(v["base_dia"], v["max_dia"], v["mouth_dia"]) / 2
        ceiling = _max_wave_depth(smallest, v["lobes"], v["wall"])
        v["wave_depth"] = _clamp(v["wave_depth"], 0.0, ceiling)

        v["z_sections"] = int(_clamp(round(v["z_sections"]), 8, 200))
        v["facets"] = int(_clamp(round(v["facets"]), 12, 240))
        return cls(**v)

    # -- Derived ---------------------------------------------------------------

    @property
    def body_h(self) -> float:
        """Height of the wavy part: everything above the collar."""
        return self.height - self.collar_h

    @property
    def base_r(self) -> float:
        return self.base_dia / 2

    def chamfer(self) -> float:
        """Elephant's-foot relief, held inside the collar it is cut from."""
        return min(BASE_CHAMFER, self.collar_wall / 4, self.collar_h / 3)

    def footprint(self) -> float:
        """Roughly how much bed this needs, profile plus the crests on it.

        An upper bound, not a measurement: it assumes a crest at full envelope
        sits on the widest point of the profile, which is only true when
        ``wave_cycles`` happens to put an antinode there. ``checks`` measures
        the real bounding box and holds it under ``BED_BUDGET``; this is for
        deciding, before a 12-second loft, whether a set of sliders is even in
        the right neighbourhood.
        """
        return self.max_dia * (1.0 + self.wave_depth)


DEFAULT = Shade()
"""The shade this repo builds: 83 mm foot, 158 mm at its widest, 200 mm tall.

Five lobes, a fifth of a turn of twist and two wave cycles up the body -- the
combination tuned against the reference photographs (see README). Every export
and every assertion in ``checks.py`` is this object; the sliders exist so the
same design can be cut to another base, not to change what "the model" means.
"""


# --- Website parameters -------------------------------------------------------


def _num(name: str, label: str, low: float, high: float, step: float) -> dict:
    return {
        "name": name,
        "label": label,
        "type": "number",
        "min": low,
        "max": high,
        "step": step,
        "default": getattr(DEFAULT, name),
    }


PARAMS = [
    _num("base_dia", "Base diameter (mm)", 40.0, 300.0, 1.0),
    _num("max_dia", "Profile at its widest (mm)", 40.0, 400.0, 1.0),
    _num("mouth_dia", "Profile at the mouth (mm)", 20.0, 400.0, 1.0),
    _num("height", "Height (mm)", 60.0, 400.0, 5.0),
    _num("bulge_at", "Widest point (fraction of height)", 0.15, 0.85, 0.01),
    _num("lobes", "Lobes around", 2, 16, 1),
    _num("wave_depth", "Wave depth (fraction of radius)", 0.0, 0.45, 0.01),
    _num("twist_turns", "Twist (turns over the height)", -1.0, 1.0, 0.01),
    _num("wave_cycles", "Wave cycles up the body", 0.0, 8.0, 0.25),
    _num("pinch", "Pinch between cycles", 0.0, 1.0, 0.05),
    _num("env_phase", "Where the cycles sit (rad)", -3.15, 3.15, 0.05),
    _num("wall", "Wall (mm)", 0.4, 3.0, 0.1),
    _num("collar_h", "Base collar height (mm)", 2.0, 40.0, 0.5),
    _num("collar_wall", "Base collar wall (mm)", 0.8, 6.0, 0.1),
]
"""Every slider that reaches this geometry.

``FADE_IN`` and the loft resolution are deliberately absent -- the first because
it is what holds the shade to its 83 mm interface, the second two because they
are construction rather than design.
"""
