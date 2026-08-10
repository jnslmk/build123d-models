"""Measured and derived numbers for the ASA base + TPU cartridge holder.

One file for all three sets (``wood``, ``metal``, ``stone``): what changes
between them is the drill list and the cover label, and neither is a tolerance.
Everything a set *does* decide for itself lives in ``sets.py``.

No geometry lives here. Everything is either imported from ``drill_storage.box``
(so the Gridfinity envelope and the cover interface cannot drift apart from the
engine every cover is still cut from) or derived from those numbers as an
expression -- never typed as an evaluated result, which is how a relationship
becomes invisible and free to break.

The vertical stack, all in world z with the base's foot on z=0::

    0.0  -  4.4   Gridfinity foot (BASE_H)
    4.4  -  6.0   base floor -- drills bottom out here, on ASA, never on TPU
    6.0  - 29.2   ASA guide bores, free fit as printed -- straight, never gripping
   24.0           SHELL_FOOT_TOP, the shoulder the cover seats on
   29.2           CAVITY_FLOOR_Z -- the collar sits here
   29.2 - 32.7   TPU grip land (LAND_H) -- the only thing that holds a drill
   30.0           cover snap groove (SHELL_FOOT_TOP + SNAP_Z)
   32.7 - 33.2   lead-in cone from the relief down onto the land
   33.2           collar retention bead / base groove (BEAD_Z)
   33.2 - 37.2   TPU relief bore, sliding fit -- clears the drill, grips nothing
   36.0           SHELL_TOTAL_H -- base top
   37.2           collar top, standing CART_PROUD above it to be pinched out

The cartridge is a **collar**, not a block: it reaches exactly as far below the
retention bead as it stands above it (``CART_BELOW_BEAD == CART_ABOVE_BEAD``), and
that reach is the longer of what it has to contain -- land plus lead-in, or the
bead's own ramp. So the TPU is 8.0 mm rather than 37.2, everything below it is ASA
bored at a free fit, and the base guides while the collar grips.

The base is 36 mm, not the 42 mm of the one-material base still in ``box.py``: its
bores no longer come down from the top face, so the height above the cover seat
only has to hold the collar. What did *not* move is ``SHELL_FOOT_TOP``. The seat
feeds ``cover_height_for``, so lowering it would mint a taller cover for these
models alone; leaving it at 24 keeps every cover this package has ever produced
interchangeable with every base. ``checks.py`` asserts that rather than trusting
the coincidence.
"""

from __future__ import annotations

import math

from build123d import Color

from ..lib import fits
from .box import (
    BASE_TOP_CHAMFER,
    BORE_FLOOR_Z,
    BORE_MOUTH_CHAMFER,
    COLLAR_R,
    COLLAR_W,
    FOOT_TOP,
    SNAP_GROOVE_D,
    SNAP_GROOVE_ROOF,
    SNAP_Z,
)

# --- Materials ----------------------------------------------------------------
# The whole point of the variant: the base is rigid and the insert is not. Every
# fit below names which of the two it is cut in, because the same fit class gives
# a different number in each (fits._MATERIAL_OFFSET: ASA -0.15, TPU +0.10).
SHELL_MATERIAL = "asa"
CART_MATERIAL = "tpu"

# Both parts black, matching ``hex.config``: the base prints in black ASA and the
# cartridge in black TPU, so the scene shows the filaments that are actually on
# the shelf. What separates them in a view is the geometry -- the collar sitting
# proud of the base's mouth -- not a colour the print does not have.
SHELL_COLOR = Color(0.1, 0.1, 0.1)
CART_COLOR = Color(0.1, 0.1, 0.1)

# --- Base --------------------------------------------------------------------
# The cartridge enters through the collar, so the collar bore is the throat, and
# SHELL_WALL is what every millimetre of hole space is bought from -- twice over,
# because it comes off both sides. This is the whole price of the two-material
# split: a one-material base packs its bores into 34.8 mm of row, and this one
# into 32.68.
#
# 1.6 mm is 4 perimeters at a 0.4 mm nozzle. It is a *floor*, not a preference:
# raise it to 2.0 and the cartridge loses 0.8 mm of width, the packer keeps the
# same three rows and spends the whole loss on the gaps inside them -- the wood
# set's 9 and 10 mm bores, the tightest pair in the family, close from 1.36 mm to
# 0.96 mm. That is under the 1.0 mm that two CART_MOUTH_CH chamfers alone eat, so
# those two mouths would run together into a sharp sliver, in the softest material
# in the model. pack_rows only warns when a row's gap goes actually *negative*, and
# 0.96 mm is not negative, so nothing complains; checks.py holds every pair to
# PACK_HOLE_WALL instead.
# Under the 0.8 mm snap groove this leaves 0.8 mm, exactly 2 perimeters, which is
# also the documented minimum. Do not raise the groove depth without raising this.
SHELL_WALL = 1.6
CAVITY_W = COLLAR_W - 2 * SHELL_WALL  # 36.0 mm cartridge bore
CAVITY_R = COLLAR_R - SHELL_WALL  # 1.9 -- a true inward offset of the collar

# --- ASA guide bores ----------------------------------------------------------
# Everything below the cartridge is base, and it is bored. The guide's whole job
# is to hold a drill upright over a long span so the short TPU collar does not
# have to; it must therefore grip nothing at all, which is what a free fit means.
# Adjusted for ASA (-0.15 off the PETG baseline), not TPU -- this hole is cut in
# the rigid part.
#
# A free fit in ASA is +0.25 diametral, and that is what the guide asks for. It is
# not what it *gets*: FDM prints a small vertical hole undersize -- a 5 mm hole
# modelled at nominal measured 0.24 mm small on a 0.4 mm nozzle
# (fdm-fits-and-clearances rule 4) -- so a bore cut at +0.25 arrives at roughly
# +0.01 and the drill drags on ASA over 23.2 mm of guide. That is the whole reason
# a drill in this base feels tight, and it is a defect of the modelled number, not
# of the fit class: the guide was specified free and printed as a press fit.
#
# So the undersize is added back. LAND_FIT one section down *exploits* the same
# effect -- a TPU bore at nominal arrives as the interference that grips -- and
# these two are the opposite ends of one printer fact: the land wants the undersize
# and the guide has to cancel it. Neither one is allowed to be an anonymous float,
# so both are written as their fit class plus a named delta.
#
# The ceiling on this is the cavity floor, where two neighbouring guide mouths must
# not run into each other: at +0.49 the closest pair (9 and 10 mm) still keeps
# 1.19 mm, against the 1.10 mm that two GUIDE_MOUTH_CH chamfers plus a sliver need.
# checks.py checks that rather than trusting it, because layout_bores packs on the
# *cartridge's* relieved bore and knows nothing about how wide the guide is cut.
GUIDE_UNDERSIZE_COMP = 0.24
GUIDE_FIT = fits.for_material(fits.FREE, SHELL_MATERIAL) + GUIDE_UNDERSIZE_COMP
#            free fit, ASA (+0.25), plus the hole undersize FDM prints (+0.24),
#            so what ends up in the part is the free fit it was specified as.
GUIDE_FLOOR_Z = BORE_FLOOR_Z  # drills rest on ASA, and the cover math holds
GUIDE_MOUTH_CH = 0.5  # lead-in where a guide opens into the cavity floor

# Both rims of the base's top face are chamfered -- the outer one for looks and
# to lead the cover on, the inner one to lead the cartridge in (part-joints rule
# 1: a lead-in on every mating mouth). They eat into the same SHELL_WALL from
# opposite sides, so they are smaller than the PETG base's 1.0 mm and sized to
# leave exactly the 0.8 mm (2 perimeters) of flat rim that the FDM minimums call
# for. Raising either without raising SHELL_WALL eats that rim; checks.py fails
# if it goes below 0.8.
SHELL_TOP_CHAMFER = 0.4  # outer rim (BASE_TOP_CHAMFER is 1.0 on the solid base)
CAVITY_MOUTH_CH = 0.4  # inner rim -- the cartridge's lead-in
RIM_FLAT = SHELL_WALL - SHELL_TOP_CHAMFER - CAVITY_MOUTH_CH  # 0.8

# --- Base height -------------------------------------------------------------
# The base does NOT inherit box.BASE_TOTAL_H. That base is 42 mm because its
# bores are sunk from the top face and need the depth; this one grips in a short
# collar at the top and guides in ASA below, so it needs far less.
#
# Only ``SHELL_COLLAR_H`` comes down. ``SHELL_FOOT_TOP`` deliberately stays at
# box.FOOT_TOP, because the seat height feeds ``cover_height_for``: lower it and
# every base needs its own taller cover, and a cover already on the shelf stops
# fitting. The collar is free -- the cover's groove sits at ``FOOT_TOP + SNAP_Z``
# either way, so shortening above that costs the cover nothing. checks.py asserts
# both halves of that.
#
# 36 mm is not a whole Gridfinity Z unit, and does not need to be: what has to
# quantise is the *assembled* envelope (19U / 133 mm), which is set by the seat
# and the cover, not by how tall the base is.
SHELL_FOOT_TOP = FOOT_TOP  # cover seat -- do not lower without a new cover
SHELL_COLLAR_H = 12.0  # was 18.0; the floor is set by the bead, see CART_ABOVE_BEAD
SHELL_TOTAL_H = SHELL_FOOT_TOP + SHELL_COLLAR_H  # 36.0

# --- Cartridge ----------------------------------------------------------------
CART_SLIP = fits.for_material(fits.SLIDING, CART_MATERIAL)  # sliding fit, TPU
CART_W = CAVITY_W - CART_SLIP
CART_R = CAVITY_R - CART_SLIP / 2  # uniform offset, so the corners fit too
CART_WALL = 1.0  # min material between a bore and the outer face. Thin for a
#                  rigid part; fine in TPU, which is meant to give.
CART_PROUD = 1.2  # stands above the base rim so it can be pinched back out
CART_TOP_Z = SHELL_TOTAL_H + CART_PROUD  # 37.2
# (the collar's *height* is derived under "Collar height" below, once the
# features it has to contain have been declared.)

# --- The grip -----------------------------------------------------------------
# This is the whole design argument, so it is written out rather than left to the
# design notes.
#
# The holder this replaced gripped on three compliant ribs cut into a PETG bore,
# because PETG has no compliance of its own; ``docs/design-notes.md`` keeps the
# record of the two printed generations that failed in opposite directions before
# those ribs were reshaped into springs. TPU makes that machinery pointless --
# the bulk material is the spring.
#
# But it does NOT follow that a plain deep bore works. Retention is friction x
# contact area, and TPU on steel runs mu ~ 0.5-0.9. A full-circle interference
# bore over the old 14 mm rib zone reaches tens of kgf at any interference big
# enough to model (>= 0.1 mm); the interference that would give a pleasant ~1 kgf
# is ~0.01 mm diametral, which is finer than FDM can hold. Where PETG had no
# number loose enough, TPU has no printable number tight enough.
#
# So the bore stays plain and round -- no ribs -- and the *contact* is what gets
# shortened: a LAND_H band at the very bottom, with the rest of the bore relieved
# to a free fit and doing nothing but keeping the drill upright. Three ribs over
# 14 mm and one full circle over 3.5 mm have comparable contact area, which is
# why this lands back in the force range the printed rib sweep already calibrated.
#
# The land sits at the bottom because that is the plain shank. Higher up are the
# flutes, whose hardened spurs broach a grip feature away permanently -- and TPU
# is softer than the PETG that lesson was learned on, so the margin is worse, not
# better.
LAND_H = 3.5  # grip band height above the cartridge floor

# Press fit, TPU -- i.e. modelled at nominal, because for_material(PRESS, "tpu")
# is -0.10 + 0.10 = 0.00. That is deliberate, not a no-op: FDM prints a small
# vertical hole 0.1-0.3 mm undersize, so a bore modelled at nominal arrives as a
# real interference fit, and *that* undersize is the interference here.
#
# LAND_EXTRA_GRIP takes it *below* the ladder's tightest class, which is a thing
# the ladder cannot express: PRESS is the bottom rung, and in TPU it lands on
# nominal. The extra is deliberate interference on top of the print undersize,
# and it is named rather than folded into a literal so a printed cartridge can be
# read as "how far from LAND_FIT", not "what absolute number was typed".
#
# LAND_EASE then gives some of it back. The first cartridge printed to these
# numbers holds -- that is the finding, and it is why this design replaced the
# ribbed one -- but it holds harder than a tool tray wants: a drill should come
# out to a straight pull, not to a pull that lifts the base off the baseplate
# with it. So both lands open by one named step. It is deliberately small, half
# of LAND_EXTRA_GRIP: the useful band between "falls out" and "fights you" is
# narrow in an elastomer, the printer's own hole undersize (0.1-0.3 mm) is wider
# than this correction, and a second small step is cheap while a cartridge cut
# too loose is a reprint. Ease again before reaching for LAND_H.
#
# The contrast the design depends on survives it, and is legible in one place:
# the ASA guide below is cut LOOSE (GUIDE_FIT, +0.49) and the TPU collar TIGHT
# (-0.05). checks.py asserts that ordering, because a guide that grips or a land
# that clears would each quietly defeat the split.
LAND_EXTRA_GRIP = 0.10
LAND_EASE = 0.05  # opened by this much from the first printed cartridge
LAND_FIT = fits.for_material(fits.PRESS, CART_MATERIAL) - LAND_EXTRA_GRIP + LAND_EASE

# --- Small-bore undersize taper ----------------------------------------------
# The land *exploits* the printer's hole undersize as its interference: a bore
# modelled at nominal arrives 0.1-0.3 mm small (measured 0.24 mm at 5 mm, rule 4
# of fdm-fits-and-clearances), and that undersize is the grip. The catch is that
# the undersize is a roughly constant absolute offset, so its bite scales
# inversely with the hole: 0.25 mm is 2.5% of a 10 mm bore and 25% of a 1 mm one.
# Below about 4 mm a small land stops being a press fit and becomes a wall the
# drill cannot enter at all -- the metal set's 1 and 1.5 mm bores printed tight
# enough that the bits would not go in.
#
# So below ``SMALL_BORE_COMP_THRESHOLD`` the land is eased by a linear taper:
# ``SMALL_BORE_COMP_SLOPE`` mm of extra diametral clearance per millimetre the
# hole falls short of the threshold -- +0.30 at 1 mm, +0.20 at 2 mm, +0.10 at
# 3 mm, nothing at 4 mm and up. At the smallest end that returns the whole
# measured undersize, which is the point: the bores that cannot be entered at
# all are the ones that get the most. The slope is deliberately modest and is a
# calibration knob, not a law -- the taper trades grip for insertability on
# exactly the sizes that need it, and a set opts in via
# ``DrillSet.small_bore_comp`` rather than every set carrying it. Raise the
# slope if a small bore still refuses a bit; drop it if one rattles.
SMALL_BORE_COMP_THRESHOLD = 4.0  # mm; at and below this, ease the land
SMALL_BORE_COMP_SLOPE = 0.10  # mm of extra diametral clearance per mm below


def small_bore_comp(d: float) -> float:
    """Extra diametral clearance for a bore of diameter ``d`` under the
    small-bore taper: ``0`` at the threshold and above, growing linearly below."""
    return max(0.0, SMALL_BORE_COMP_SLOPE * (SMALL_BORE_COMP_THRESHOLD - d))


# Sliding fit, TPU -- the relief above the land. It carries no grip at all, only
# guidance, so what it wants is to be as loose as the space allows: any drag up
# here is friction the user pays on every insertion and gets no retention back
# for. A free fit is what it would prefer, and it does not fit -- FREE widens
# every bore by 0.09 mm of radius, and the packer pays for that out of the gaps
# between them: the wood set's 9 and 10 mm bores, the tightest pair in the family,
# close from 1.36 mm to 1.09 mm, which is under the 1.10 mm PACK_HOLE_WALL two
# mouth chamfers are budgeted. Sliding still leaves 0.16 mm of radial clearance
# and keeps that pair at 1.36 mm, which is a better trade in a material this soft.
# If the drills ever feel like they drag, take it from SHELL_WALL, not from here.
RELIEF_FIT = fits.for_material(fits.SLIDING, CART_MATERIAL)

# The hex land, for a countersink's, a tap's or a step drill's shank. It gets
# its own constant
# because a hex land bears on flats rather than on a curved wall, and full
# flat-on-flat contact is grabbier per mm of engagement -- the ribbed design
# found the same thing from the other side, wanting more interference on the hex
# than on the round bores, and these two should be expected to diverge again.
#
# It carries the same LAND_EASE, because a tool that has to be worked out of the
# tray is the same complaint whatever its shank is. Starting from the press fit
# (nominal in TPU) that lands it just *over* nominal -- which is not the clearance
# it looks like: a bore this size still prints 0.1-0.3 mm under, so the real
# contact is interference either way. Ease is measured against what the printer
# delivers, not against the model.
HEX_LAND_FIT = fits.for_material(fits.PRESS, CART_MATERIAL) + LAND_EASE

# Lead-in at each bore mouth on the cartridge's top face. Smaller than the
# engine's BORE_MOUTH_CHAMFER (0.8): two neighbouring mouths each want their
# chamfer to form without running into each other, and this cartridge has less
# room to give than a one-material base. It is the chamfer's own doing, because
# it sets PACK_HOLE_WALL: at 0.8 the budget rises to 1.7 mm, the packer re-deals
# the wood set into four rows to try to honour it and cannot -- it comes back
# with the 6 and 9 mm mouths 1.23 mm apart, against the 1.6 mm two 0.8 chamfers
# eat between them, so they overlap into a sharp sliver. At 0.5 the budget is
# 1.1 mm, the three-row layout stands, and the tightest pair in any set (wood
# 9|10 at 1.36 mm, metal 5|8 at 1.55 mm) clears the 1.0 mm the two chamfers take.
# A lead-in in TPU has an easier job anyway: the material gives.
CART_MOUTH_CH = 0.5

LAND_LEAD_IN = CART_MOUTH_CH  # cone from the relief down onto the land

# Relief at the very bottom of each bore, where the land meets the cartridge's
# underside. Two jobs: it chamfers what would otherwise be a raw square edge
# (house rule -- chamfer horizontal edges), and it backs off the last printed
# layer, whose crown can squeeze the bore's exit -- the drill passes through
# here into the guide. (The *bed* side of a bore is its mouth, now the insert
# prints top-face-down, and the mouth cones are what absorb the first layer's
# elephant's foot.) It comes out of LAND_H, so the land that actually bears is
# LAND_H - BORE_FOOT_RELIEF.
BORE_FOOT_RELIEF = 0.3
EFFECTIVE_LAND_H = LAND_H - BORE_FOOT_RELIEF

# --- Retention ----------------------------------------------------------------
# A drill leaves the land at maybe 5-15 N; the cartridge weighs about 0.2 N. So
# without a catch the cartridge simply comes out with the first drill. The bead
# goes on the TPU and the groove in the ASA -- the compliant half of a joint
# carries the bead, so seating it costs a squeeze rather than a wall deflection.
#
# The profile is box.snap_bead_ring's asymmetric ramp (outward=True), for the
# reason recorded on box.snap_bead_ring: a symmetric half-round bump fights the user
# going on, because it rises as steeply as it protrudes.
CART_BEAD = 0.6  # radial protrusion of the TPU bead
BEAD_LEAD_IN = 2.4  # gentle insertion ramp below the tip
BEAD_BACK = 1.1  # steeper retention face above it
BEAD_TIP_FLAT = 0.3
BEAD_ENGAGEMENT = CART_BEAD - CART_SLIP / 2  # 0.44 mm of real overlap

# --- The groove that receives the bead ----------------------------------------
# The bead's negative, cut into the ASA cavity wall -- and a *chamfered* pocket
# rather than the half-round pocket it used to be, for a reason that is
# about the print rather than about the fit.
#
# The base prints foot-down, cavity up, so every downward-facing surface inside
# the cavity is an overhang, and this groove's roof was the steepest one on the
# part that is not a 45 deg Gridfinity bevel or an engraved glyph. A half-round
# roof is an arc, and an arc's last stretch is horizontal however small its
# radius: closing a 0.8 mm pocket on a circle leaves the topmost 0.2 mm layer to
# span 0.53 mm of roof in one step -- a 69 deg overhang -- so the lip that holds
# the cartridge down came out drooped into the groove it was supposed to bound.
# That lip is the whole retention feature, so a print defect there is a fit
# defect too, and it is what this shape was changed to fix.
#
# The roof is a straight ramp instead, rising exactly as far as the groove is
# deep: 45 deg from vertical at every layer rather than only on average, which
# is the difference that matters -- the arc averages 45 too and still finishes
# horizontal. ``checks.py`` measures the angle off the built solid rather than
# trusting this arithmetic.
#
# Retention survives the change, which is the point of doing it this way rather
# than by shrinking the groove. What holds the cartridge down is the *bead's*
# own back face -- 0.6 mm of reach over 0.95 mm of rise, ~32 deg off the pull
# axis -- bearing on the groove's top lip. The roof behind that lip never
# touched the bead and does not have to; all it owes the joint is to stay out
# of the way, which a 45 deg ramp does more reliably than a drooping arc. The
# lip itself moves up by GROOVE_ROOF - GROOVE_D = 0.15 mm, so the cartridge
# gains that much lost motion before the catch bites, against a slip fit that
# already gives it 0.16 mm sideways.
#
# The depth is named for what it is. It used to be ``SHELL_GROOVE_R``, a radius,
# because a half-round pocket has nothing else to be described by; there is no
# radius here any more, and calling the number one invited the next reader to
# reach for a swept circle again. It is still the same 0.8 mm the cover's groove
# is cut at, and still the same 0.8 mm of wall left behind it.
GROOVE_D = SNAP_GROOVE_D  # 0.8 -- depth unchanged, so is the wall behind it
GROOVE_TIP_FLAT = BEAD_TIP_FLAT  # flat at the deepest point, as on the bead
GROOVE_ROOF_RISE = GROOVE_D  # rise == depth, i.e. 45 deg from vertical
GROOVE_ROOF = GROOVE_TIP_FLAT / 2 + GROOVE_ROOF_RISE  # 0.95 above BEAD_Z
GROOVE_ROOF_OVERHANG = math.degrees(math.atan2(GROOVE_D, GROOVE_ROOF_RISE))  # 45.0
MAX_OVERHANG = 45.0  # what FDM prints unsupported, and what the roof is held to

# The floor faces *upward*, so it costs the print nothing and is free to be
# shaped for the fit instead -- and this is the second thing the reshape fixes.
# The bead's insertion ramp is 2.25 mm long where the half-round groove's lower
# half was 0.8, so the last stretch of that ramp had nowhere to go and sat
# permanently crushed against the groove's bottom lip: up to 0.27 mm of
# interference, on a bead whose entire engagement is 0.44. The ramp only stands
# proud of the cartridge's own slip gap over its upper part, so the floor
# reaches the wall exactly where it does, and below that the cavity's slip is
# already clearance enough. The bead seats now instead of jamming short.
BEAD_RAMP_H = BEAD_LEAD_IN - BEAD_TIP_FLAT / 2  # 2.25, the ramp's true rise
GROOVE_FLOOR = BEAD_LEAD_IN - BEAD_RAMP_H * (CART_SLIP / 2) / CART_BEAD  # 1.80

# --- Collar height ------------------------------------------------------------
# The collar is centred on its own retention bead: it reaches exactly as far below
# the bead as it stands above it. Everything here derives from that plus the
# features the reach has to contain, so the collar comes out as short as it can
# be rather than as tall as some number happens to say.
#
# What the reach must cover, below the bead:
#   * the grip land and the cone that leads into it  (LAND_H + LAND_LEAD_IN)
#   * the bead's own gentle insertion ramp           (BEAD_LEAD_IN)
# whichever is longer. Above the bead the same reach comfortably covers
# BEAD_BACK plus CART_PROUD. checks.py asserts all three.
#
# This is why shortening SHELL_COLLAR_H shortens the *collar* too: CART_TOP_Z
# drops with the base rim, BEAD_Z follows it down, and the cavity floor with it.
# Nothing here is typed twice.
CART_ABOVE_BEAD = max(LAND_H + LAND_LEAD_IN, BEAD_LEAD_IN)  # 4.0
CART_BELOW_BEAD = CART_ABOVE_BEAD  # symmetric, by definition
CART_H = CART_ABOVE_BEAD + CART_BELOW_BEAD  # 8.0

BEAD_Z = CART_TOP_Z - CART_ABOVE_BEAD  # 33.2 world z
CAVITY_FLOOR_Z = BEAD_Z - CART_BELOW_BEAD  # 29.2 -- the collar sits here
CAVITY_H = SHELL_TOTAL_H - CAVITY_FLOOR_Z  # 6.8
GUIDE_H = CAVITY_FLOOR_Z - GUIDE_FLOOR_Z  # 23.2 of ASA guide under the collar

# The two grooves cut into opposite faces of the same SHELL_WALL, so they must not
# overlap in z or nothing is left between them. The cover's is at
# SHELL_FOOT_TOP + SNAP_Z; this is the clearance the bead's groove keeps from it.
GROOVE_SEPARATION = BEAD_Z - (SHELL_FOOT_TOP + SNAP_Z)  # 3.2, centre to centre
# ...but centres are no longer the thing to compare, because this groove is not
# symmetric about BEAD_Z any more: its floor reaches 1.8 mm down and its roof
# only 0.95 mm up. So the gap is measured lip to lip, which is what the wall
# between them actually is. 0.6 mm of full-thickness wall, and shrinking as
# GROOVE_FLOOR grows -- checks.py fails before it reaches zero.
GROOVE_LIP_GAP = (BEAD_Z - GROOVE_FLOOR) - (
    SHELL_FOOT_TOP + SNAP_Z + SNAP_GROOVE_ROOF
)

# --- Keying -------------------------------------------------------------------
# The base's engraved wall legend only tells the truth in one orientation, and a
# rounded square goes in four ways. The key rib stands *outside* the cartridge
# body, on the +X face, so it can never collide with a bore however the packer
# lays them out -- and +X is the one face pair that carries no legend.
KEY_W = 2.4
KEY_D = 0.8  # how far the rib stands proud of the cartridge / into the base
#              wall, leaving SHELL_WALL - KEY_D = 0.8 mm behind the slot
KEY_ROOT = 1.0  # how far it reaches back *into* the cartridge, so the rounded
#                 profile still meets the wall along its whole length
KEY_FILLET = 0.6  # vertical edges are filleted, not left square
KEY_MOUTH_FILLET = 0.15  # the *other* end of the same slot: a small fillet
#                 tangent to the cavity wall itself, at the slot's mouth. This is
#                 deliberately its own, smaller radius rather than a second use of
#                 KEY_FILLET: it has to sit flush with the cavity wall (radius
#                 anchored exactly at CAVITY_W/2, not offset from it) to blend
#                 tangentially -- any offset short of that leaves the mouth's own
#                 arc crossing the wall mid-curve, at an angle strictly *less*
#                 favourable than a plain unfilleted corner (a acute "feather"
#                 edge, not a blunt one -- confirmed 80 deg at the old 0.5 mm
#                 offset, worse than the 90 deg a bare square corner leaves). Sized
#                 to leave KEY_D - KEY_MOUTH_FILLET - KEY_FILLET = 0.05 mm of flat
#                 run between the two fillets, so both fit inside the slot's real
#                 0.8 mm depth without the "over" hack the far corner still needs.
KEY_LEAD_IN = 0.4  # lofted bottom -- the rib is the first thing to enter the slot
KEY_SLIP = fits.for_material(fits.SLIDING, CART_MATERIAL)  # sliding fit, TPU

# --- Bore layout --------------------------------------------------------------
# The packing envelope is the cartridge, not the collar, and it is tighter than
# a one-material base's: the base wall and the cartridge wall both come out of the
# same 39.2 mm collar. Bores are packed by their *relieved* radius, which is what
# is actually cut -- smaller than ribbed_valley_r, which claws some of it back.
PACK_HALF_W = CART_W / 2
PACK_CORNER_R = CART_R
# Two mouth chamfers plus a hair, the same rule the base's HOLE_WALL follows --
# but computed from this cartridge's own CART_MOUTH_CH, not inherited as a number.
PACK_HOLE_WALL = 2 * CART_MOUTH_CH + 0.1
PACK_WALL_CLEARANCE = CART_WALL + CART_MOUTH_CH  # material + a formed lead-in


def relieved_bore_r(d: float) -> float:
    """The radius actually cut for a drill of diameter ``d`` -- the relief, not
    the land, because the relief is the wider of the two and so is the footprint
    the packer has to fit. The ``footprint_r`` handed to ``layout_bores``.
    """
    return (d + RELIEF_FIT) / 2


def land_bore_r(d: float, ease: float = 0.0) -> float:
    """The radius actually cut for a drill of diameter ``d`` at its grip land --
    the press fit, plus a named size-dependent ease (``small_bore_comp``) where
    one applies. The land, not the relief: the relief stays the wider footprint,
    so this never feeds the packer and never moves a hole.
    """
    return (d + LAND_FIT + ease) / 2


__all__ = [
    "BASE_TOP_CHAMFER",
    "FOOT_TOP",
    "BEAD_BACK",
    "BEAD_ENGAGEMENT",
    "BEAD_LEAD_IN",
    "BEAD_RAMP_H",
    "BEAD_TIP_FLAT",
    "BEAD_Z",
    "BORE_FLOOR_Z",
    "BORE_FOOT_RELIEF",
    "BORE_MOUTH_CHAMFER",
    "CART_ABOVE_BEAD",
    "CART_BEAD",
    "CART_BELOW_BEAD",
    "CART_COLOR",
    "CART_H",
    "CART_MOUTH_CH",
    "CART_MATERIAL",
    "CART_PROUD",
    "CART_R",
    "CART_SLIP",
    "GROOVE_D",
    "GROOVE_FLOOR",
    "GROOVE_LIP_GAP",
    "GROOVE_ROOF",
    "GROOVE_ROOF_OVERHANG",
    "GROOVE_ROOF_RISE",
    "GROOVE_SEPARATION",
    "GROOVE_TIP_FLAT",
    "MAX_OVERHANG",
    "CART_TOP_Z",
    "CART_W",
    "CART_WALL",
    "CAVITY_FLOOR_Z",
    "CAVITY_H",
    "CAVITY_MOUTH_CH",
    "CAVITY_R",
    "CAVITY_W",
    "EFFECTIVE_LAND_H",
    "GUIDE_FIT",
    "GUIDE_FLOOR_Z",
    "GUIDE_H",
    "GUIDE_MOUTH_CH",
    "GUIDE_UNDERSIZE_COMP",
    "HEX_LAND_FIT",
    "KEY_D",
    "KEY_FILLET",
    "KEY_LEAD_IN",
    "KEY_MOUTH_FILLET",
    "KEY_ROOT",
    "KEY_SLIP",
    "KEY_W",
    "LAND_EASE",
    "LAND_EXTRA_GRIP",
    "LAND_FIT",
    "LAND_H",
    "LAND_LEAD_IN",
    "PACK_CORNER_R",
    "PACK_HALF_W",
    "PACK_HOLE_WALL",
    "PACK_WALL_CLEARANCE",
    "RELIEF_FIT",
    "RIM_FLAT",
    "SHELL_COLOR",
    "SMALL_BORE_COMP_SLOPE",
    "SMALL_BORE_COMP_THRESHOLD",
    "SHELL_COLLAR_H",
    "SHELL_FOOT_TOP",
    "SHELL_MATERIAL",
    "SHELL_TOP_CHAMFER",
    "SHELL_TOTAL_H",
    "SNAP_Z",
    "SHELL_WALL",
    "land_bore_r",
    "relieved_bore_r",
    "small_bore_comp",
]
