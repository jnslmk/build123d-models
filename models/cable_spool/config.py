"""Every number the cable spool is cut from, measured or derived.

The three discs are a **reconstruction** of Printables 27496 ("cable spool
ethernet cable", by rgeissler), measured off the published STLs with the
`stl-reverse-engineering` tooling; `docs/design-notes.md` records what was
measured and how. The clip is **not** a reconstruction -- the original's does
not stay on, and `clip.py` says why -- so its numbers come from `snap-fits`
and `fdm-fits-and-clearances`, not from the mesh.

Two conventions hold throughout:

* **Z is the spool axis**, `z = 0` is the base's bed face, and the assembled
  stack runs `z = 0 .. STACK_H`. Every part is nonetheless *returned* in its
  own print pose, which for the three discs happens to be the same frame and
  for the clip is not.
* **Radii, not diameters.** The spool is 180 mm across and every dimension
  here that names a circle is its radius, because every one of them is used
  as a radius.

Where a number is a clearance it is written as a named fit from
`models.lib.fits` rather than as a bare float, per `AGENTS.md`.
"""

from __future__ import annotations

from math import sqrt

from ..lib import fits

# --------------------------------------------------------------------------
# The disc the three plates are all cut from
# --------------------------------------------------------------------------

OUTER_R = 90.0
"""Rim radius. The spool is 180 mm across -- measured 179.99 on all three STLs."""

RIM_INNER_R = 80.0
"""Where the solid outer ring ends and the six windows begin.

A 10 mm ring, and it is the only part of a disc a clip may bear on: the
original clip's jaws landed at r = 75.5..79.9, i.e. *inside* this circle and
over the windows, so at most angular positions there was nothing under them.
See `docs/design-notes.md`.
"""

SPOKE_RING_R = 32.5
"""Inner end of the windows -- the boundary of the ring that carries the hub."""

SPOKE_HALF_W = 5.0
"""Half the spoke width, and equally the offset of a window's bounding line.

Each window is bounded by two straight chords that pass 5 mm from the axis, so
the six spokes are straight 10 mm bars rather than wedges. Measured: a window
edge sampled at r = 36.5, 55.5 and 74.5 sits on one line, 5.000 mm off-centre.
"""

WINDOW_COUNT = 6
WINDOW_FILLET = 5.0
"""Corner radius where a window's straight side meets its arcs.

Solved from the mesh rather than eyeballed: the fillet leaves the straight
side at z-distance 74.33 from the axis and rejoins the r = 80 arc, and
`sqrt((5+R)^2 + 74.33^2) = 80 - R` has the single solution R = 5.
"""

PLATE_T = 2.0
"""Disc thickness. All three plates."""

WINDOW_CHAMFER = 0.6
"""Break on both faces of every window and of every central bore.

The original chamfers only the middle disc's window mouths. Doing all three on
both faces is a deliberate deviation: the cable crosses these edges on every
turn, and `AGENTS.md` does not allow shipping them raw.
"""

RIM_CHAMFER_H = 1.0
"""Height of the chamfer on each disc's *top* outer edge."""

BASE_RIM_CHAMFER_W = 3.0
MIDDLE_RIM_CHAMFER_W = 2.0
COVER_RIM_CHAMFER_W = 1.0
"""Widths of that chamfer, as measured -- 90 -> 87, 90 -> 88, 90 -> 89 mm.

They are deliberately unequal in the source model and are kept: the deepest
one is on the base, where the cable has to climb over the flange edge, and the
shallowest on the cover, which nothing rubs against.
"""

BED_CHAMFER = 0.6
"""Break on each disc's bed-side outer edge. Relieves elephant's foot, and
gives the clip's lower jaw a lead-in onto the rim."""

# --------------------------------------------------------------------------
# The stack: where each disc sits, and how tall the whole thing is
# --------------------------------------------------------------------------

CHANNEL_H = 7.0
"""Clear height of each of the two cable channels. Fits a 6 mm round patch
cable with room to lie over itself at the crossing."""

MIDDLE_Z = PLATE_T + CHANNEL_H
"""9.0 -- underside of the middle disc, i.e. the top of the hub's lower collar."""

COVER_Z = MIDDLE_Z + PLATE_T + CHANNEL_H
"""18.0 -- underside of the cover, i.e. the top of the hub's four ribs."""

STACK_H = COVER_Z + PLATE_T
"""20.0 -- bed face of the base to top face of the cover. The clip is cut to
this, and it is the one number the clip and the discs have to agree on."""

# --------------------------------------------------------------------------
# The hub
# --------------------------------------------------------------------------

HUB_R = 24.0
"""Outer radius of the hub tube -- the surface the two upper discs slide down."""

HUB_BORE_R = 22.0
"""Inner radius of the hub tube: a 2 mm wall."""

HUB_RIB_R = 25.0
"""Outer radius of the four guide ribs and of the lower collar.

One radius does two jobs. Below `MIDDLE_Z` it is a full collar and the middle
disc lands on it; above that it survives only as four ribs, which the middle
disc's four relief pockets slide past and the cover -- which has none -- lands
on at `COVER_Z`.
"""

HUB_LINER_R = 21.0
"""How far *in* the wall is thickened behind each guide rib.

Measured on the source hub, which runs r = 21..25 through the rib sectors and
r = 22..24 between them. Only the sectors that carry a disc get the liner.
"""

HUB_COLLAR_R = 25.6
"""Outer radius of the lower collar only.

0.6 mm fatter than the ribs, and every bit of that is spent on the chamfer
that breaks its top edge: the middle disc lands on the annulus this leaves,
and a chamfer cut into a 25.0 collar would have eaten the seat instead of the
corner. The ribs cannot be widened the same way -- the middle disc's relief
pockets have to slide past them.
"""

HUB_RIB_COUNT = 4
HUB_RIB_ARC = 34.5
"""Angular width of one rib, degrees. Measured 34.5 on the source hub."""

HUB_RIB_PHASE = 45.0
"""Angle of the first rib's centre. Puts the ribs between the cable slots."""

CABLE_SLOT_ARC = 33.0
"""Width of the slot down the hub, degrees. The cable's end is pushed through
it before the first turn is wound, so the tail is anchored at the middle."""

CABLE_SLOT_PHASE = 270.0
KEY_SLOT_PHASE = 90.0
"""The second slot, diametrically opposite. It exists only above `MIDDLE_Z`,
where it takes the middle disc's key so the disc cannot rotate on the hub."""

BORE_FILLET = 0.8
"""Radius on the vertical corners inside the hub bore -- slot walls and rib
liner ends. The cable's tail passes them on its way to the anchor."""

RIB_FILLET = 0.5
"""Radius on a guide rib's four vertical corners, drawn into its sketch. Half
the rib's own 1.5 mm radial depth, so the two ends of it still meet."""

SLOT_FILLET = 1.0
"""Radius on the corners of the sketch each hub slot is cut from."""

SPINDLE_R = 2.2
"""Radius of the post standing on the diametral rib at the middle of the hub."""

SPINDLE_BORE_R = 1.25
"""A 2.5 mm hole down the post: drop a nail or a length of filament through it
and the spool turns on it while you wind."""

SPINDLE_SOLID_Z = 3.0
"""How far up the post is solid before the bore starts. Keeps the bore from
being a hole in the middle of the first layers."""

DIAMETRAL_RIB_W = 2.0 * SPINDLE_R + 1.0
"""Width of the rib across the base's central bore that carries the post.

Widened from the source's 2.9 mm until the post is strictly inside it. At 2.9
the post stands proud of its own rib on both sides, leaving two bare arcs of
cylinder meeting the bed face at 90 degrees with nothing to break them
against; at exactly `2*SPINDLE_R` the two are tangent, which is worse -- OCC
leaves a zero-width sliver edge at each tangency.
"""

SPINDLE_CHAMFER = 0.4
"""Break on the spindle post's top edge and on both mouths of its bore."""

# --------------------------------------------------------------------------
# Clearances between the discs and the hub
# --------------------------------------------------------------------------

DISC_BORE_FIT = fits.SLIDING
"""Disc bore to hub tube. The discs must drop down the hub by hand and stay
concentric once there; that is the definition of a sliding fit."""

DISC_RELIEF_FIT = fits.FREE
"""Middle-disc relief pocket to guide rib. This one only has to *miss* the
rib on the way past, and a rib is a much rougher surface than a bore."""

MIDDLE_BORE_R = HUB_R + DISC_BORE_FIT / 2
"""24.11 -- both upper discs. The cover uses the same bore, which is what
stops it at the rib tops."""

MIDDLE_RELIEF_R = HUB_RIB_R + DISC_RELIEF_FIT / 2
"""25.2 -- four pockets in the middle disc's bore, on the rib centres."""

MIDDLE_RELIEF_ARC = HUB_RIB_ARC + 6.0
"""Angular width of one relief pocket. The 6 deg is rotational slack: the disc
is dropped on by hand and nothing indexes it but eye."""

MIDDLE_KEY_R = HUB_BORE_R + DISC_BORE_FIT / 2
"""22.11 -- how far the middle disc's two keys reach into the hub's slots."""

MIDDLE_KEY_ARC = 25.0
"""Angular width of a key, against a 33 deg slot: 4 deg of slack a side."""

# --------------------------------------------------------------------------
# The clip
# --------------------------------------------------------------------------

CLIP_COUNT = 3
"""How many the spool takes, evenly spaced. Three is what the source model
ships and it is the right number: three points fix a circle."""

CLIP_WRAP = 30.0
"""Angular span of one clip, degrees -- 47 mm of arc at the rim.

Not a styling choice. It is set from below by the detent arm, which needs
`DETENT_L` of arc to reach its strain limit, plus its root block and its
release tab. The original clip spanned 24 mm and was *straight*, so on a 90 mm
radius it stood 0.8 mm off the rim in the middle and touched only at its two
corners.
"""

CLIP_FIT = fits.FREE
"""Clip bore to rim. The clip is pushed on over a 180 mm circle that may have
printed a few tenths oversize, and it locates on its detent, not on this
surface."""

CLIP_BORE_R = OUTER_R + CLIP_FIT / 2
"""90.2 -- the radius of the clip's inner face, which rides on the rim."""

CLIP_SPINE_T = 3.2
"""Radial thickness of the back of the clip -- the wall that spans both cable
channels and keeps the outer turn from lifting out."""

CLIP_OUTER_R = CLIP_BORE_R + CLIP_SPINE_T
"""93.4 -- the clip's own outside. It stands 3.4 mm proud of the rim."""

CLIP_JAW_T = 4.0
"""Thickness of the lower jaw, and so how far the clips hold the spool off a
table. It is rigid on purpose: all of the clip's compliance is in the detent
arm and none of it is in the jaws.

It is also what sets the room the detent arm has to bend into, since below the
arm is either air or, with the spool laid flat, the table. `CLIP_JAW_T -
DETENT_H = 2.2 mm` of travel against the 1.8 mm the arm needs to ride over its
own tooth, so a clip goes *on* with the spool flat on a bench. Taking one back
*off* wants the arm pressed near its free end, which travels further than the
tooth does -- lift the spool for that.
"""

CLIP_JAW_INNER_R = 80.0
"""How far in the lower jaw reaches. Exactly `RIM_INNER_R`: the jaw covers the
whole 10 mm rim ring and stops where the windows start, because past that
point there is nothing under it to bear on."""

CLIP_TOP_JAW_T = 2.4
CLIP_TOP_JAW_R = 84.4
"""How far in the upper jaw reaches over the cover, and how thick it is."""

CLIP_TOP_JAW_LEDGE_R = 86.4
"""Where the 45 degree relief under the upper jaw starts.

Everything outboard of it -- r 86.4..90.2, so 3.8 mm -- is a flat ledge
printed in mid-air, which is about as far as a printer will carry an
unsupported edge cleanly. Everything inboard is taken back at 45 degrees so it
is self-supporting. What is left flat, r 86.4..89, is what actually sits on
the cover, and all of it is on the rim ring.
"""

CLIP_TIP_BREAK = 0.2
"""Break on the upper jaw's nose. Small, because the tip face it breaks is
only `CLIP_TOP_JAW_T - (CLIP_TOP_JAW_LEDGE_R - CLIP_TOP_JAW_R)` = 0.4 mm tall
-- what is left of the jaw once the 45 degree relief has taken its share."""

CLIP_EDGE_CHAMFER = 0.8
"""Break on the clip's exposed horizontal edges, drawn into the revolve
profile rather than chased with `chamfer()` afterwards."""

CLIP_LEAD_IN = 1.2
"""Lead-in at the mouth of the lower jaw, so the rim wedges in rather than
butting against a square corner."""

CLIP_STACK_CLEAR = 0.15
"""Axial slack between the jaws and the 20 mm stack. Deliberately a clearance
and not a preload: a clamp that relies on squeezing PETG for months is a clamp
that relies on PETG not creeping, and it does creep. The clip is held on by its
detent, not by pinching."""

# -- the detent arm --------------------------------------------------------

DETENT_H = 1.8
"""Thickness of the arm, `h` in the cantilever formulas. Over the 1.6 mm FDM
floor for a snap arm (four perimeters at a 0.4 mm nozzle)."""

DETENT_INNER_R = 71.0
DETENT_OUTER_R = 79.0
"""The arm's radial extent, and so `b = 8.0 mm` -- over the 6 mm floor. Its
outer edge stops 1.0 mm short of the lower jaw, which is the slot that lets it
bend at all; the tooth on top of it overhangs that slot by 0.85 mm, which it
can do because it sits above the jaw's top face rather than beside it."""

DETENT_ROOT_ARC = 2.5
"""Angular width of the block that roots the arm into the spine and jaw."""

DETENT_L = 24.0
"""Arm length root-to-tooth, mm of arc at the arm's mid-radius.

This is the number `CLIP_WRAP` is derived from. Sizing, all from `snap-fits`
with PETG at `eps = 1.0%` (repeated use -- a clip gets taken off and put back
on) and `E_s = 1700 MPa` flexural:

    y    = DETENT_TOOTH_H = 1.8 mm       the undercut the arm rides over
    eps  = y*h / (0.67*l^2)
         = 1.8*1.8 / (0.67*576) = 0.84%           <= 1.0%     OK
    P    = (b*h^2/6) * (E_s*eps/l)
         = (8.0*3.24/6) * (1700*0.0084/24) = 2.6 N
    W    = P*(mu + tan a)/(1 - mu*tan a)
         = 2.6 * (0.5+1)/(1-0.5) = 7.7 N          push-on force, mu = 0.5

`l/h = 13.3`, above the 10:1 the slender-beam formula wants. The arm is left at
constant section rather than tapered to `h/2`: the 1.63x that would buy is
deflection this arm does not need, and a taper along a 24 mm *arc* is a loft
where everything else here is a revolve.
"""

DETENT_TOOTH_H = 1.8
"""Height of the tooth above the arm, and so the deflection to fit the clip.

Both floors from `snap-fits` bind here: `y >= 1.2 mm`, and `y >= h` or the arm
is stiffer than its own undercut and gouges instead of riding over.
"""

DETENT_TOOTH_ARC = 7.35
"""Angular width of the tooth, degrees -- 10 mm of arc at r = 78."""

DETENT_TOOTH_OUTER_R = 79.85
"""The locking face, 0.15 mm inside the window wall it catches on.

It is a *vertical* face and that is not an oversight. The wall it engages is
the window's own r = 80 boundary, which stands 2 mm tall inside a plate that is
2 mm thick; there is no room to slope the catch back and still have it reach
that wall, so the joint is captive by construction rather than by choice. Push
the arm down to take a clip off -- see the README.
"""

DETENT_TOOTH_INNER_R = 76.0
"""Inner end of the tooth's flat top. The face from here down to
`DETENT_TOOTH_INNER_R - DETENT_TOOTH_H` is the back of the tooth and never
touches anything."""

DETENT_LEAD_ANGLE = 45.0
"""Lead-in on the tooth's outer face, degrees. What the base disc's own rim
rides up as the clip is pushed on, and the reason `W` above is 3x `P` and not
more."""

DETENT_LEAD_Z = 0.4
"""How much of the tooth's outer face stays vertical below the lead-in. The
window wall's own chamfer is `WINDOW_CHAMFER` deep, so the catch has to start
below that to have anything square to bear against."""
DETENT_ROOT_FILLET = 1.0
"""0.6*h, the optimum in every design guide, rounded up to a radius a 0.4 mm
nozzle draws cleanly."""

# --------------------------------------------------------------------------
# Derived, and the derivations that would otherwise be scattered
# --------------------------------------------------------------------------

WINDOW_APEX_R = SPOKE_HALF_W / 0.5
"""10.0 -- where a window's two bounding chords meet.

They are 120 deg apart and each passes `SPOKE_HALF_W` from the axis, so the
wedge between them has its apex at `SPOKE_HALF_W / cos(60 deg)`. Far inside
`SPOKE_RING_R`, which is why the window reads as an annular sector.
"""

WINDOW_HALF_ANGLE = 30.0
"""Half-angle of that wedge, degrees."""


def window_half_width(r: float) -> float:
    """Tangential half-width of a window at radius `r`, ignoring the fillets.

    Used by the checks to prove the clip's detent tooth clears the spokes at
    the radius it engages, which is the one thing that decides whether a clip
    can be seated at a given angle.
    """
    if r <= WINDOW_APEX_R:
        return 0.0
    return (0.5 * r - SPOKE_HALF_W) / sqrt(0.75)


WINDOW_PHASE = 0.0
"""Angle of the first window's centre."""


def clip_angles() -> list[float]:
    """Where the clips go: centred on alternate windows.

    `CLIP_COUNT` of them at 120 deg, which lands each on a window centre
    because the windows are 60 deg apart. That matters -- the detent tooth
    drops into a window, so a clip put down over a spoke will not lock.
    """
    return [WINDOW_PHASE + 120.0 * i for i in range(CLIP_COUNT)]

ARM_EDGE_CHAMFER = 0.4
"""Break on the detent arm's four long edges, drawn into its profile."""

CLIP_END_FILLET = 2.0
"""Radius on the four long vertical edges at the ends of the clip's arc."""
