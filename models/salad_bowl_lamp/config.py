"""Every measured and derived number for the salad-bowl lamp, in one place.

**Material is white PLA**, not the repo's PETG default (``AGENTS.md`` asks a
model that deviates to say so). Nothing here flexes, latches or carries load in
service -- the shade hangs from magnets and is otherwise decorative -- so PLA's
brittleness costs nothing and its dimensional tightness is why ``MAGNET_FIT``
below comes out where it does.

The numbers live on ``Lamp``, a frozen value object, rather than as module
constants, because the model is parametric on the website: a slider hands
``Lamp.of()`` a dict and gets back a *valid* lamp. Every derived quantity is a
method on the same object, so there is no way to change a diameter and leave a
radius behind. ``DEFAULT`` is the lamp this repo actually built, and it is what
``uv run check`` and every export use.

Two coordinate systems, and keeping them apart is the whole trick:

* **Bowl (upright).** ``z = 0`` at the outside of the bottom pole, ``z = bowl_h``
  at the rim plane. This is the bowl as a bowl, and it is what ``bowl_r`` is
  solved in.
* **Lamp (inverted).** The bowl is turned over to be the shade, so the rim plane
  is at the *bottom*. ``depth`` throughout this module means millimetres
  measured **up from the rim plane, into the dome** -- the direction the printed
  shade is inserted. ``bowl_inner_radius(depth)`` is the only bridge between the
  two, and every shade dimension is derived through it.

The bowl is a **spherical cap**, and that is not a modelling assumption laid on
top of the measurements -- it is forced by them. One sphere passes through a
200 mm rim circle and touches a plane 95 mm below it, and there is only one:
``bowl_r`` solves ``(D/2)^2 + (H - R)^2 = R^2``. It lands at 100.13 mm, a hair
over the rim's own 100 mm radius, which is the same as saying the bowl is very
slightly shallower than a true hemisphere. That matches the photographs.

With one exception, and it is the exception the band is shaped around: **there is
a bulge just inside the mouth**, 4 mm across and standing 1 mm proud of the
sphere with rounded transitions. The band meets it with a notch -- the bottom
5.8 mm of its outer face cut back 1.3 mm, full depth over the bulge and then
ramped at 45 deg back onto the sphere -- rather than by being made smaller
everywhere. So the seat is still the sphere over 17 of the band's 23 mm, the
magnets still sit mid-band on bare steel, and the band now reaches down to the
rim plane instead of starting 3 mm above it. What that costs, and the condition
it carries, are on ``bead_w`` where the numbers are.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from math import cos, pi, sqrt

from ..lib import fits

MATERIAL = "pla"

MAGNET_FIT = fits.for_material(fits.FREE, MATERIAL)
"""0.30 mm diametral. FREE, not SNUG, and not a press fit at all.

The part-joints skill wants +0.2--0.3 mm for a magnet pocket, and FREE-in-PLA
lands exactly on the top of that band. A sintered magnet chips rather than
deforms, so the pocket must never be the thing holding it. Glue is.
"""

MIN_BACKING = 0.4
"""Plastic that must survive behind a seated magnet: one line at a 0.4 mm nozzle.

The floor, not a target. The default lamp sat exactly on it while the discs were
2 mm thick; at 1 mm they leave 1.4 mm behind them and the floor is no longer what
sets the wall. It stays because the wall slider is still clamped against it, and
because it is the number a thicker disc runs into first. It is enough because the
backing is never the loaded part: in service the magnet is pulled *outward* onto the steel
and the glue holds it, so the backing only has to keep the disc in its hole while
the shade is carried to the bowl. It is also why ``Lamp.of`` thickens the wall
rather than shallowing the pocket when a slider would breach it -- a pocket
shallower than its magnet leaves the disc standing proud, and a magnet held off
the steel by even a few tenths is the one failure this joint cannot survive.
"""

BEAD_CLEAR = fits.for_material(fits.FREE, MATERIAL)
"""0.30 mm, and **radial** rather than diametral -- the one place in this model a
fit class is read that way, so it is said here rather than left to be inferred.

A fit class is a diametral allowance because the usual case is a shaft in a bore,
where the two are concentric and the error splits over both sides. This is not
that. What the notch has to clear is a lump on one wall of a spun bowl that is
out of round by more than any printer error, so what matters is the worst single
azimuth, not the average of two opposite ones. Read radially, FREE-in-PLA leaves
0.30 mm all round the bulge, and the only thing more of it costs is a slightly
deeper notch in a skirt that touches nothing.
"""

NOTCH_MARGIN = 0.5
"""How far past the bulge's far edge the notch stays at full depth.

The bulge is measured off a bowl by hand and it does not end on a line. Half a
millimetre of overrun before the ramp starts is what keeps a bulge measured a
touch short from meeting the ramp instead of the notch.
"""

MIN_GAP = 2.0  # narrowest air a ring is allowed to leave its neighbour
MIN_EYE = 12.0  # smallest centre hole worth calling an eye
WALL_RANGE = (1.2, 6.0)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


@dataclass(frozen=True)
class Lamp:
    """One lamp: a bought bowl, and the grille that hangs in it.

    Construct it directly for a known-good set of numbers (``DEFAULT``), or
    through ``of()`` for anything a slider touched.
    """

    # --- The bought bowl -----------------------------------------------------
    # IKEA stainless salad bowl, as measured, plus the hole drilled through its
    # bottom for the lamp holder. Only bowl_hole_d is free of consequence: it is
    # where the flex and the socket pass, and the shade never sees it.
    bowl_d: float = 200.0
    bowl_h: float = 95.0
    bowl_wall: float = 0.8  # spun sheet; nominal, and the shade only needs it to exist
    bowl_hole_d: float = 42.0

    # --- The bulge inside the mouth ------------------------------------------
    # Measured on the bowl: a bulge just inside the opening, 4 mm across,
    # standing 1 mm proud of the sphere with rounded transitions at both ends.
    # The band answers it with a notch round its bottom rather than by being made
    # smaller, and that is a choice with a condition attached: **it assumes the
    # bulge is a lump, not a ring.** A shade whose seat is on the sphere is
    # 1 mm wider than a continuous ring of this height would leave, so it could
    # never be pushed through one; past a single lump it tilts in, which the
    # taper gives it room to do (5 mm down the seat the bore is already 1 mm
    # wider than the part). The mock draws the bulge as a full ring anyway --
    # the shade can come to rest at any azimuth, so the ring is the envelope of
    # everywhere the lump could be, and the notch has to clear all of it.
    # ``bead_h = 0`` removes both and gives back the plain taper seat.
    bead_w: float = 4.0
    bead_h: float = 1.0
    bead_depth: float = 0.0  # from the rim plane to the bulge's near edge
    bead_clear: float = BEAD_CLEAR

    # --- The printed shade ---------------------------------------------------
    band_h: float = 23.0  # every ring and every cross arm
    wall: float = 2.4  # radial on a ring, tangential on an arm, normal on the band
    chamfer: float = 0.6  # every horizontal edge, cut in the revolved profile
    rim_inset: float = 0.0
    seat_clear: float = 0.0
    eye_d: float = 45.0
    ring_count: int = 5
    arm_embed: float = 0.5

    # --- Magnets -------------------------------------------------------------
    # Round N42-class discs, glued into pockets around the outer band, meeting
    # the steel face-on with nothing between them.
    magnet_d: float = 5.0
    magnet_t: float = 1.0
    magnet_count: int = 8
    magnet_fit: float = MAGNET_FIT
    pocket_lead_in: float = 0.5  # 45 deg all round the mouth, lofted, per the house rule

    # -- Construction ---------------------------------------------------------

    @classmethod
    def of(cls, **kwargs) -> Lamp:
        """Build a lamp from website input, clamped so the geometry stays valid.

        Every slider on the site lands here, and the contract is that *no*
        combination of them can produce a part that fails to build -- so this
        clamps rather than raises. The order below is the dependency order and
        is not arbitrary: the wall has to settle before the band's height can be
        held inside the dome, the band before the rings can be spaced, and the
        rings before the eye has a maximum at all.

        Where two inputs fight, the one that gets moved is the one whose being
        wrong is *safe*. A wall too thin for its magnet grows; a magnet never
        shrinks into a pocket it does not fill.
        """
        v = {f.name: kwargs.get(f.name, f.default) for f in fields(cls)}

        # The cap, first, because every other limit is measured inside it. Depth
        # is capped at a hemisphere: past that the rim is no longer the widest
        # circle, and a shade that fits the seat cannot be got in through it.
        v["bowl_d"] = _clamp(v["bowl_d"], 60.0, 400.0)
        v["bowl_h"] = _clamp(v["bowl_h"], v["bowl_d"] / 8, v["bowl_d"] / 2)
        v["bowl_wall"] = _clamp(v["bowl_wall"], 0.2, 3.0)
        v["bowl_hole_d"] = _clamp(v["bowl_hole_d"], 4.0, v["bowl_d"] / 2)

        # The bulge, next, because it is measured on the bowl rather than chosen
        # and the notch is cut from it. Only its own sanity is enforced here: it
        # has to fit inside the dome it sits in.
        v["bead_depth"] = _clamp(v["bead_depth"], 0.0, 0.25 * v["bowl_h"])
        v["bead_w"] = _clamp(v["bead_w"], 0.0, 0.25 * v["bowl_h"])
        v["bead_h"] = _clamp(v["bead_h"], 0.0, min(5.0, 0.05 * v["bowl_d"]))
        v["bead_clear"] = _clamp(v["bead_clear"], 0.0, 2.0)

        # Wall, magnet and notch, settled together. Two things eat the wall from
        # opposite sides -- the pocket from outside (MIN_BACKING) and the notch
        # from the same side lower down (fits.MIN_WALL of skirt has to survive
        # it) -- and in both cases what moves is the wall, for the reason
        # MIN_BACKING gives: a magnet never shrinks into a pocket it does not
        # fill, and a notch never stops short of the bulge it exists to clear.
        v["magnet_t"] = _clamp(v["magnet_t"], 0.5, 8.0)
        notch = v["bead_h"] + v["bead_clear"] if v["bead_h"] > 0 and v["bead_w"] > 0 else 0.0
        v["wall"] = _clamp(
            max(v["wall"], v["magnet_t"] + MIN_BACKING, notch + fits.MIN_WALL), *WALL_RANGE
        )
        v["magnet_t"] = min(v["magnet_t"], v["wall"] - MIN_BACKING)

        # How much of the dome the band may occupy. band_inner_radius stays real
        # exactly while rim_inset + band_h < bowl_h - bowl_wall - wall, which is
        # the whole constraint once the algebra cancels; 0.85 keeps the band off
        # the point where its inside face closes to nothing.
        headroom = v["bowl_h"] - v["bowl_wall"] - v["wall"]
        v["rim_inset"] = _clamp(v["rim_inset"], 0.0, 0.4 * headroom)
        v["band_h"] = _clamp(v["band_h"], 4.0, 0.85 * (headroom - v["rim_inset"]))
        v["chamfer"] = _clamp(v["chamfer"], 0.0, min(v["wall"], v["band_h"]) / 3)

        # Rings, then the eye: the eye is what gives way, because dropping a ring
        # changes the design and narrowing the hole does not. Only if the eye
        # would fall below MIN_EYE does a ring go instead.
        v["ring_count"] = int(_clamp(round(v["ring_count"]), 2, 12))
        probe = cls(**v)
        while v["ring_count"] > 2 and probe._max_eye_d() < MIN_EYE:
            v["ring_count"] -= 1
            probe = cls(**v)
        v["eye_d"] = _clamp(v["eye_d"], MIN_EYE, max(MIN_EYE, probe._max_eye_d()))

        # An arm's flat inner end has to stay buried in the hub's wall: not just
        # its axis but its corners, which sit wall/2 off to each side and so a
        # little further out than the embed alone suggests.
        eye_r = v["eye_d"] / 2
        corner = sqrt((eye_r + v["wall"]) ** 2 - (v["wall"] / 2) ** 2) - eye_r
        v["arm_embed"] = _clamp(v["arm_embed"], 0.1, max(0.1, corner - 0.1))

        # Magnets last: their size is bounded by the band they sit in, their
        # lead-in by the pocket it breaks the mouth of, and their number by the
        # circle they sit on. That order is load-bearing -- the lead-in widens
        # the mouth, so how many pockets fit cannot be answered before it.
        probe = cls(**v)
        v["magnet_d"] = _clamp(v["magnet_d"], 2.0, max(2.0, probe._max_magnet_d()))
        v["pocket_lead_in"] = _clamp(
            v["pocket_lead_in"], 0.0, min(1.0, v["magnet_t"] / 2, v["magnet_d"] / 4)
        )
        probe = cls(**v)
        v["magnet_count"] = int(_clamp(round(v["magnet_count"]), 1, probe._max_magnets()))
        return cls(**v)

    def _max_eye_d(self) -> float:
        """Largest eye that still leaves MIN_GAP of air between every ring."""
        inner_rings = self.ring_count - 2
        span = inner_rings * self.wall + (inner_rings + 1) * MIN_GAP
        return 2 * (self.band_inner_radius(0.0) - self.wall - span)

    def _max_magnet_d(self) -> float:
        """Largest disc whose teardrop peak still clears the band's top edge.

        The peak, not the bore, is what runs out of room: it stands
        ``pocket_d/2 * sqrt(2)`` above the axis, and the axis is at mid-height.
        """
        room = self.band_h / 2 - self.chamfer - 0.5
        return 2 * room / sqrt(2) - self.magnet_fit

    def _max_magnets(self) -> int:
        """How many pockets fit round the seat without running into each other.

        Measured at the *mouth*, which is ``pocket_lead_in`` wider each side than
        the bore -- two pockets whose bores clear each other by a millimetre can
        still have their lead-ins meet, and what that leaves is a scallop in the
        seat rather than two pockets.
        """
        pitch = self.pocket_d + 2 * self.pocket_lead_in + 1.0
        return max(1, int(2 * pi * self.pad_face_radius() / pitch))

    # -- The bought bowl ------------------------------------------------------

    @property
    def bowl_r(self) -> float:
        """Outside radius of the spherical cap. Solved, not measured -- see the module docstring."""
        return ((self.bowl_d / 2) ** 2 + self.bowl_h**2) / (2 * self.bowl_h)

    @property
    def bowl_r_in(self) -> float:
        """Inside radius. The shade fits *this* sphere, the one a wall smaller."""
        return self.bowl_r - self.bowl_wall

    @property
    def rim_drop(self) -> float:
        """How far the sphere's centre sits beyond the rim plane (5.13 mm), always positive.

        Upright that is *above* the rim; inverted it is *below* it. It is the
        term that turns a depth into a distance from the centre, so it appears in
        every radius below and in the shade's pad normals.
        """
        return self.bowl_r - self.bowl_h

    def bowl_inner_radius(self, depth: float) -> float:
        """Inside radius of the inverted bowl, ``depth`` mm above the rim plane.

        ``depth = 0`` is the rim itself (99.20 mm on the default lamp, *not* 100
        -- the steel is on the outside of that number). It shrinks by 3.7 mm over
        the shade's 20 mm, which is why the shade's outer band follows an arc
        rather than being a cylinder: 3.7 mm of taper is far too much to absorb
        in a clearance.
        """
        dz = depth + self.rim_drop
        if abs(dz) >= self.bowl_r_in:
            raise ValueError(f"depth {depth} is past the top of the dome")
        return sqrt(self.bowl_r_in**2 - dz**2)

    def bead_protrusion(self, depth: float) -> float:
        """How far the bulge stands proud of the sphere, ``depth`` mm in from the rim.

        Zero outside the bulge, ``bead_h`` across its crest, and a raised cosine
        in between -- which is what "round transitions" has to mean here, since
        no single arc can leave the sphere and arrive at the crest tangent to
        both. The transition is ``bead_h`` long at each end, so a 4 mm bulge
        standing 1 mm proud is 1 mm of blend, 2 mm of crest, 1 mm of blend; a
        bulge too shallow to fit two of those is all blend and no crest.
        """
        if self.bead_h <= 0.0 or self.bead_w <= 0.0:
            return 0.0
        x = depth - self.bead_depth
        if x <= 0.0 or x >= self.bead_w:
            return 0.0
        run = min(self.bead_h, self.bead_w / 2)
        if x < run:
            return self.bead_h * (1 - cos(pi * x / run)) / 2
        if x > self.bead_w - run:
            return self.bead_h * (1 - cos(pi * (self.bead_w - x) / run)) / 2
        return self.bead_h

    def bowl_clear_radius(self, depth: float) -> float:
        """The bowl's inside with the bulge counted in -- what is actually open."""
        return self.bowl_inner_radius(depth) - self.bead_protrusion(depth)

    def bead_throat_radius(self) -> float:
        """The narrowest circle in the bowl: 97.99 mm on the default lamp.

        Sampled across the bulge rather than solved, because where it pinches is
        not where the crest is thickest. The bowl is still narrowing as the bulge
        runs inward, so the tightest point sits at the crest's *far* edge -- and
        if the bulge were ever shallow and wide enough for the sphere's own taper
        to outrun the blend, it would move again. Sampling finds it either way.

        Reported rather than designed to. **The band is wider than this**: its
        seat is on the sphere, which is 1 mm bigger than the bulge leaves at that
        depth, so a shade cannot be pushed straight down a bore of this size. It
        goes in tilted, past a bulge that is one lump rather than a ring -- see
        ``bead_w``'s comment on the fields, and ``checks.check_bead`` for what is
        and is not asserted about it.
        """
        if self.bead_h <= 0.0 or self.bead_w <= 0.0:
            return self.bowl_inner_radius(self.bead_depth)
        steps = 64
        return min(
            self.bowl_clear_radius(self.bead_depth + i * self.bead_w / steps)
            for i in range(steps + 1)
        )

    def bowl_outer_height(self, radius: float) -> float:
        """Height above the rim plane of the bowl's *outside* at ``radius``, inverted.

        The dome's own profile. Only ``checks.py`` uses it, to put a probe on the
        steel near the lampholder hole rather than in the air above it -- at
        25 mm out the dome has already dropped 3 mm from its apex, which is more
        than the wall is thick.
        """
        return sqrt(self.bowl_r**2 - radius**2) - self.rim_drop

    # -- The printed shade ----------------------------------------------------

    @property
    def pocket_d(self) -> float:
        return self.magnet_d + self.magnet_fit

    @property
    def pad_depth_z(self) -> float:
        """Height of the pocket axis. Mid-band, so the magnets pull on a single
        circle through the part's own centre of mass and nothing tips.

        11.5 mm on the default lamp, against a notch that has finished by 5.8 mm,
        so every bore is well clear of it and lands on bare sphere. That is not
        left to luck -- ``checks.py`` asserts the gap rather than assuming a
        23 mm band always has one.
        """
        return self.band_h / 2

    def band_notch_depth(self) -> float:
        """How far the notch is cut back from the seat: the bulge, plus clearance.

        1.30 mm on the default lamp. Radial, and measured from the sphere the
        rest of the band lies on, because that is the surface the bulge itself
        stands proud of.
        """
        if self.bead_h <= 0.0 or self.bead_w <= 0.0:
            return 0.0
        return self.bead_h + self.bead_clear

    def band_notch_top(self) -> float:
        """How far up the band the notch stays at full depth: 4.5 mm by default.

        The bulge's own far edge plus ``NOTCH_MARGIN``, measured in the band's
        own coordinates -- so a reveal above the rim, if there is one, shortens
        the notch rather than moving it.
        """
        if self.band_notch_depth() <= 0.0:
            return 0.0
        top = self.bead_depth + self.bead_w + NOTCH_MARGIN - self.rim_inset
        return _clamp(top, 0.0, self.band_h)

    def band_notch_ramp_top(self) -> float:
        """Where the notch has ramped back out to the seat: 5.8 mm by default.

        The notch does not step back out, it ramps at 45 deg, which is why this
        stands one ``band_notch_depth`` above ``band_notch_top``. A step would
        leave a horizontal face pointing at the bed with 1.3 mm of nothing under
        it -- the band prints from this end, so that face is an overhang, and a
        45 deg run is the house answer to one.
        """
        if self.band_notch_depth() <= 0.0:
            return 0.0
        return _clamp(self.band_notch_top() + self.band_notch_depth(), 0.0, self.band_h)

    def band_skirt(self) -> float:
        """What is left of the wall below the notch: 1.10 mm on the default lamp.

        The notch is cut from the outside only, so this is the wall less the
        notch's depth. ``Lamp.of`` will not let it fall below ``fits.MIN_WALL``
        -- a deeper bulge grows the wall rather than thinning this away.
        """
        return self.wall - self.band_notch_depth()

    def skirt_chamfer(self) -> float:
        """The chamfer the band's bottom edges get, which is not the part's.

        A 0.6 mm chamfer needs 1.2 mm of face to be taken off both corners of,
        and the skirt has 1.10 mm. Cut at full size the two would meet 0.05 mm up
        and leave a raw 90 deg knife edge running right round the part -- built
        exactly that, and ``checks.sharp_convex_edges`` is what found it. A third
        of the skirt leaves the same proportion of flat between them that the
        rest of the part's edges have.
        """
        return min(self.chamfer, max(0.0, self.band_skirt() / 3))

    def band_setback(self, z: float) -> float:
        """How far the band's outer face is held off the seat at ``z``.

        Full depth over the bulge, nothing above the ramp, and a straight run
        between. This is the *only* place the band leaves the bowl's sphere:
        everything above ``band_notch_ramp_top`` is seat, which is what makes
        the taper a taper over 17 of the band's 23 mm.
        """
        depth = self.band_notch_depth()
        if depth <= 0.0:
            return 0.0
        top, ramp = self.band_notch_top(), self.band_notch_ramp_top()
        if z <= top:
            return depth
        if z >= ramp:
            return 0.0
        return depth * (ramp - z) / (ramp - top)

    def _seat_sphere(self, z: float) -> float:
        """Where the band's outer face lies with nothing cut out of it."""
        return self.bowl_inner_radius(self.rim_inset + z) - self.seat_clear

    def pad_backing(self) -> float:
        """Material left behind a seated magnet, on the pocket's own axis.

        Derived, not chosen, and on the default lamp it is exactly ``MIN_BACKING``
        -- a 2 mm magnet in a 2.4 mm wall leaves 0.4 mm. The case for that being
        enough is in ``MIN_BACKING``.

        Off-axis it is thicker: both faces are spheres about the same centre, so
        the pocket's flat floor sits a further 0.05 mm clear at the bore's edge
        and 0.10 mm at the teardrop's peak. That is why the pocket cannot break
        out through the inside face anywhere, which ``checks.py`` asserts point
        by point.
        """
        return self.wall - self.magnet_t

    def band_outer_radius(self, z: float) -> float:
        """The band's outer face, ``z`` mm up from the shade's underside.

        The bowl's own inner sphere, less ``seat_clear`` -- which is zero, and
        that is the design -- everywhere except the bottom 5.8 mm, where
        ``band_setback`` cuts the notch that lets the bulge in the mouth pass.
        17 of the band's 23 mm are seat, the notch touches nothing, and the
        surface is one continuous sphere from the ramp's top to the band's.

        The mating surfaces converge at 10.5 deg, so a shade printed a few tenths oversize
        does not bind, it comes to rest a couple of millimetres shallower; one
        printed undersize sits deeper. Either way every magnet lands on steel,
        which a clearance fit cannot promise: hold force collapses with air gap,
        and a spun bowl is out of round by more than any gap worth leaving.

        ``seat_clear`` is kept as a named field at zero rather than deleted,
        because "no clearance here" is a decision ``checks.py`` asserts and a
        later reader is owed.

        A revolved arc, not a chord: a straight cone between the same two ends
        would sag 0.5 mm away from the steel at mid-height, turning a seat that
        beds down over its whole height into one that touches at two rims.
        """
        return self._seat_sphere(z) - self.band_setback(z)

    def band_inner_radius(self, z: float) -> float:
        """The band's inside face: the seat's sphere again, ``wall`` smaller.

        Concentric with the outer face rather than parallel to a chord of it, so
        the band is exactly ``wall`` thick measured the only way that matters
        here -- along the surface normal, which is the direction the magnet
        pockets are bored. A chord-sided band looks the same from below and is
        not the same part: it runs half a millimetre fat at mid-height and,
        worse, *thin* at the ends, and a pocket in the thin place breaks out
        through the inside.

        It also settles what the brief asked for directly: with both faces on the
        same centre there is nothing to bulge inward, because a bulge is what a
        band of uneven thickness needs in order to swallow a pocket.

        **This face does not follow the notch**, so the band is genuinely thinner
        over the bottom 4.5 mm -- 1.11 mm against 2.41 mm. That is the shape the
        notch was asked for, and it is the right way round of the two: the skirt
        below the bulge carries no magnets and no load, while stepping the inside
        as well would push a matching ridge into the one face a hand takes hold
        of when the shade is lifted out. 1.11 mm is still three lines at a 0.4 mm
        nozzle and comfortably over ``fits.MIN_WALL``; what it costs is first-
        layer grip on a 200 mm ring, which is what the README's brim is for.
        """
        centre_offset = self.rim_inset + z + self.rim_drop
        return sqrt((self.bowl_r_in - self.seat_clear - self.wall) ** 2 - centre_offset**2)

    def pad_face_radius(self) -> float:
        """Radius at which a magnet meets the steel: the band's face, at pad height.

        The magnet is flush with the tangent plane there, and the spherical face
        around it falls away from that plane by 0.03 mm across the magnet's own
        5 mm. So the magnet -- not the plastic -- is what touches, which is the
        whole point of putting the pocket here rather than under a printed cap.

        Mid-band puts it far above the notch, so it reads the sphere and not the
        setback: a pad radius taken off the notch would be a magnet held a
        millimetre off the steel.
        """
        return self.band_outer_radius(self.pad_depth_z)

    def sphere_centre_z(self) -> float:
        """The bowl's sphere centre in *shade-local* coordinates -- below z = 0.

        A pocket's axis is a radius of this point, which is what makes each
        pocket square to the steel rather than merely near it, and each magnet's
        face tangent to it rather than merely close. It is also the centre both
        of the band's faces are struck from, so a pocket bored on this axis meets
        the inside face square as well.
        """
        return -(self.rim_inset + self.rim_drop)

    def ring_gap(self) -> float:
        """Radial air between neighbouring rings, and it is one number by choice.

        Evenly spaced reads as concentric; anything else reads as a mistake. The
        band's inner radius at the *bottom* is the datum because that is where
        the band is widest, so that is where the gap is largest -- it closes by
        3.8 mm over the height, which is invisible from below and is the price of
        a band that follows the bowl.
        """
        span = self.band_inner_radius(0.0) - self.hub_outer_radius()
        inner_rings = self.ring_count - 2
        return (span - inner_rings * self.wall) / (inner_rings + 1)

    def hub_outer_radius(self) -> float:
        return self.eye_d / 2 + self.wall

    def ring_radii(self) -> list[float]:
        """Outer radii of every ring *except* the band, widest first, hub last."""
        gap = self.ring_gap()
        start = self.band_inner_radius(0.0)
        radii = [
            start - (i + 1) * gap - i * self.wall for i in range(self.ring_count - 2)
        ]
        return [*radii, self.hub_outer_radius()]

    def arm_root_radius(self) -> float:
        """Where a cross arm begins: just inside the hub's inner face.

        The cross does not cross the innermost circle -- it is four arms hung off
        the hub, not two diameters through it -- so this is the end that has to
        be hidden rather than finished. Buried ``arm_embed`` inside the hub it is
        swallowed whole: it never reaches the eye (which stays a clean cylinder)
        and it never reaches the hub's outer face (where it would leave a
        coincident face for the fuse to reconcile).
        """
        return self.eye_d / 2 + self.arm_embed

    def arm_reach(self) -> float:
        """Outer end of a cross arm, before the seat envelope trims it back."""
        return self.band_outer_radius(0.0) + 1.0


DEFAULT = Lamp()
"""The lamp this repo built: a 20 cm IKEA bowl, eight 5 x 1 discs, a 2.4 mm wall.

Every export, every render and every assertion in ``checks.py`` is this object.
The sliders exist so the same design can be cut for a different bowl; they do not
change what "the model" means here.
"""


# --- Website parameters ------------------------------------------------------
# Grouped so each model can offer the sliders that actually reach its geometry
# and no others: the bowl's drilled hole means nothing to the grille, and the
# grille's ring count means nothing to the band on its own.


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


BOWL_SHAPE_PARAMS = [
    _num("bowl_d", "Bowl diameter (mm)", 60.0, 400.0, 1.0),
    _num("bowl_h", "Bowl depth (mm)", 20.0, 200.0, 1.0),
    _num("bowl_wall", "Bowl wall (mm)", 0.2, 3.0, 0.1),
    # The bulge belongs with the bowl's shape rather than with the band's, even
    # though it is the band it changes: it is measured off the bowl in front of
    # you. Take a rolled lip's height off with a caliper, or set it to 0 for a
    # bowl whose mouth is plain, and the band re-cuts itself either way.
    _num("bead_w", "Rim bead width (mm)", 0.0, 20.0, 0.5),
    _num("bead_h", "Rim bead height (mm)", 0.0, 5.0, 0.1),
]
BOWL_PARAMS = [*BOWL_SHAPE_PARAMS, _num("bowl_hole_d", "Lampholder hole (mm)", 4.0, 120.0, 1.0)]
BAND_PARAMS = [
    _num("band_h", "Band height (mm)", 4.0, 60.0, 0.5),
    _num("wall", "Wall thickness (mm)", *WALL_RANGE, 0.1),
    _num("rim_inset", "Reveal above the rim (mm)", 0.0, 30.0, 0.5),
]
MAGNET_PARAMS = [
    _num("magnet_d", "Magnet diameter (mm)", 2.0, 20.0, 0.5),
    _num("magnet_t", "Magnet thickness (mm)", 0.5, 8.0, 0.5),
    _num("magnet_count", "Magnets", 1, 24, 1),
]
GRILLE_PARAMS = [
    _num("eye_d", "Centre eye diameter (mm)", MIN_EYE, 200.0, 1.0),
    _num("ring_count", "Rings", 2, 12, 1),
]

SEAT_PARAMS = [*BOWL_SHAPE_PARAMS, *BAND_PARAMS, *MAGNET_PARAMS]
"""Everything the outer band alone is built from -- ``fit_test``'s sliders."""

SHADE_PARAMS = [*SEAT_PARAMS, *GRILLE_PARAMS]
LAMP_PARAMS = [*BOWL_PARAMS, *BAND_PARAMS, *MAGNET_PARAMS, *GRILLE_PARAMS]
