"""Measured and derived numbers for the ASA shell + TPU cartridge holder.

No geometry lives here. Everything is either imported from ``drill_storage.box``
(so the Gridfinity envelope and the cover interface cannot drift apart from the
PETG version) or derived from those numbers as an expression -- never typed as an
evaluated result, which is how a relationship becomes invisible and free to
break.

The vertical stack, all in world z with the shell's foot on z=0::

    0.0  -  4.4   Gridfinity foot (BASE_H)
    4.4  -  6.0   shell floor -- drills bottom out here, on ASA, never on TPU
    6.0  - 30.8   ASA guide bores, free fit -- hold the drill straight, no grip
   24.0           FOOT_TOP, the shoulder the cover seats on
   30.0           cover snap groove (FOOT_TOP + SNAP_Z)
   30.8           CAVITY_FLOOR_Z -- the cartridge sits here
   30.8 - 34.3   TPU grip land (LAND_H) -- the only thing that holds a drill
   34.3 - 34.8   lead-in cone from the relief down onto the land
   34.8 - 43.2   TPU relief bore, sliding fit -- clears the drill, grips nothing
   37.0           cartridge retention bead / shell groove (BEAD_Z)
   42.0           BASE_TOTAL_H, 6U -- shell top
   43.2           cartridge top, standing CART_PROUD above it to be pinched out

The cartridge is a **collar**, not a block: it reaches exactly as far below the
retention bead as it stands above it (``CART_BELOW_BEAD == CART_ABOVE_BEAD``), so
the bead sits on its mid-plane and the TPU is 12.4 mm rather than 37.2. Everything
below that is ASA, bored at a free fit -- the shell guides, the collar grips, and
the two jobs stop sharing a part.

Because the drill still stands on ``BORE_FLOOR_Z`` and the cover still seats on
``FOOT_TOP``, ``cover_height_for`` returns the same answer it does for the PETG
base -- so an already-printed ``drill_storage.wood`` cover fits this shell.
``checks.py`` asserts that rather than trusting the coincidence.
"""

from __future__ import annotations

from build123d import Color

from ...lib import fits
from ..box import (
    BASE_TOP_CHAMFER,
    BASE_TOTAL_H,
    BORE_FLOOR_Z,
    BORE_MOUTH_CHAMFER,
    COLLAR_R,
    COLLAR_W,
    SNAP_GROOVE_R,
)

# --- Materials ----------------------------------------------------------------
# The whole point of the variant: the shell is rigid and the insert is not. Every
# fit below names which of the two it is cut in, because the same fit class gives
# a different number in each (fits._MATERIAL_OFFSET: ASA -0.15, TPU +0.10).
SHELL_MATERIAL = "asa"
CART_MATERIAL = "tpu"

SHELL_COLOR = Color(0.62, 0.64, 0.67)  # matches box.BASE_COLOR -- same family
CART_COLOR = Color(0.25, 0.55, 0.72)  # a distinctly different part, on purpose

# --- Shell --------------------------------------------------------------------
# The cartridge enters through the collar, so the collar bore is the throat, and
# SHELL_WALL is what every millimetre of hole space is bought from -- twice over,
# because it comes off both sides. This is the whole price of the two-material
# split: the PETG base packs its bores into 34.8 mm, and this one into 32.1.
#
# 1.6 mm is 4 perimeters at a 0.4 mm nozzle. It is a *floor*, not a preference:
# at 2.0 mm the packer runs out of vertical room and silently compresses the rows
# until the 6 mm and 9 mm bores are 0.59 mm apart -- thinner than a printable
# wall, in the softest material in the model. pack_rows only warns about
# horizontal overpacking, so nothing complains; checks.py checks it instead.
# Under the 0.8 mm snap groove this leaves 0.8 mm, exactly 2 perimeters, which is
# also the documented minimum. Do not raise the groove depth without raising this.
SHELL_WALL = 1.6
CAVITY_W = COLLAR_W - 2 * SHELL_WALL  # 36.0 mm cartridge bore
CAVITY_R = COLLAR_R - SHELL_WALL  # 1.9 -- a true inward offset of the collar

# --- ASA guide bores ----------------------------------------------------------
# Everything below the cartridge is shell, and it is bored. The guide's whole job
# is to hold a drill upright over a long span so the short TPU collar does not
# have to; it must therefore grip nothing at all, which is what a free fit means.
# Adjusted for ASA (-0.15 off the PETG baseline), not TPU -- this hole is cut in
# the rigid part.
GUIDE_FIT = fits.for_material(fits.FREE, SHELL_MATERIAL)  # free fit, ASA
GUIDE_FLOOR_Z = BORE_FLOOR_Z  # drills rest on ASA, and the cover math holds
GUIDE_MOUTH_CH = 0.5  # lead-in where a guide opens into the cavity floor

# Both rims of the shell's top face are chamfered -- the outer one for looks and
# to lead the cover on, the inner one to lead the cartridge in (part-joints rule
# 1: a lead-in on every mating mouth). They eat into the same SHELL_WALL from
# opposite sides, so they are smaller than the PETG base's 1.0 mm and sized to
# leave exactly the 0.8 mm (2 perimeters) of flat rim that the FDM minimums call
# for. Raising either without raising SHELL_WALL eats that rim; checks.py fails
# if it goes below 0.8.
SHELL_TOP_CHAMFER = 0.4  # outer rim (BASE_TOP_CHAMFER is 1.0 on the solid base)
CAVITY_MOUTH_CH = 0.4  # inner rim -- the cartridge's lead-in
RIM_FLAT = SHELL_WALL - SHELL_TOP_CHAMFER - CAVITY_MOUTH_CH  # 0.8

# --- Cartridge ----------------------------------------------------------------
# Declared before the cartridge because the collar's height is *derived* from it:
# the bead is the collar's mid-plane, so this one number places the TPU. The rest
# of the retention geometry is further down, under "Retention".
BEAD_Z = 37.0  # world z. Clear of the cover's groove at FOOT_TOP + SNAP_Z = 30,
#                so the two never thin the same piece of collar wall.

CART_SLIP = fits.for_material(fits.SLIDING, CART_MATERIAL)  # sliding fit, TPU
CART_W = CAVITY_W - CART_SLIP
CART_R = CAVITY_R - CART_SLIP / 2  # uniform offset, so the corners fit too
CART_WALL = 1.0  # min material between a bore and the outer face. Thin for a
#                  rigid part; fine in TPU, which is meant to give.
CART_PROUD = 1.2  # stands above the shell rim so it can be pinched back out
CART_TOP_Z = BASE_TOTAL_H + CART_PROUD  # 43.2

# The cartridge is a collar centred on its own retention bead: it reaches exactly
# as far below the bead as it stands above it. That is what sets its height --
# nothing else -- so moving BEAD_Z or CART_PROUD moves the whole collar rather
# than silently stretching one side of it.
#
# The alternative was a full-height block filling the cavity to the shell floor,
# 37.2 mm of TPU doing two jobs. Guiding a drill over a long span wants a rigid
# wall and grip wants a compliant one, and the block was a compromise at both.
# Splitting them costs nothing: the ASA below guides, the collar grips.
CART_ABOVE_BEAD = CART_TOP_Z - BEAD_Z  # 6.2
CART_BELOW_BEAD = CART_ABOVE_BEAD  # symmetric, by definition
CART_H = CART_ABOVE_BEAD + CART_BELOW_BEAD  # 12.4

CAVITY_FLOOR_Z = BEAD_Z - CART_BELOW_BEAD  # 30.8 -- the collar sits here
CAVITY_H = BASE_TOTAL_H - CAVITY_FLOOR_Z  # 11.2
GUIDE_H = CAVITY_FLOOR_Z - GUIDE_FLOOR_Z  # 24.8 of ASA guide under the collar

# --- The grip -----------------------------------------------------------------
# This is the whole design argument, so it is written out rather than left to the
# design notes.
#
# The PETG base grips on three compliant ribs because PETG has no compliance of
# its own: box.py:187-286 is the record of two printed generations that failed in
# opposite directions until the ribs were reshaped into springs. TPU makes that
# machinery pointless -- the bulk material is the spring.
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
# The land sits at the bottom for the same reason RIB_ZONE_H does: that is the
# plain shank. Higher up are the flutes, whose hardened spurs broach a grip
# feature away permanently -- and TPU is softer than the PETG that lesson was
# learned on, so the margin is worse, not better.
LAND_H = 3.5  # grip band height above the cartridge floor

# Press fit, TPU -- i.e. modelled at nominal, because for_material(PRESS, "tpu")
# is -0.10 + 0.10 = 0.00. That is deliberate, not a no-op: FDM prints a small
# vertical hole 0.1-0.3 mm undersize, so a bore modelled at nominal arrives as a
# real interference fit, and *that* undersize is the interference here.
#
# UNVERIFIED. The fit ladder in models/lib/fits.py models rigid-plastic clearance
# fits; it does not model elastomer interference, and no TPU coupon has been
# printed yet. Treat this as the centre of a sweep, not an answer -- print
# ``drill_fit_tester.land`` and judge it, exactly as RIB_GRIP was settled.
#
# LAND_EXTRA_GRIP takes it *below* the ladder's tightest class, which is a thing
# the ladder cannot express: PRESS is the bottom rung, and in TPU it lands on
# nominal. The extra is deliberate interference on top of the print undersize,
# and it is named rather than folded into a literal so the coupon can be read as
# "how far from LAND_FIT", not "what absolute number was typed".
#
# It is also what makes the contrast the design depends on legible in one place:
# the ASA guide below is cut LOOSE (GUIDE_FIT, +0.25) and the TPU collar TIGHT
# (-0.10). checks.py asserts that ordering, because a guide that grips or a land
# that clears would each quietly defeat the split.
LAND_EXTRA_GRIP = 0.10
LAND_FIT = fits.for_material(fits.PRESS, CART_MATERIAL) - LAND_EXTRA_GRIP

# Sliding fit, TPU -- the relief above the land. It carries no grip at all, only
# guidance, so what it wants is to be as loose as the space allows: any drag up
# here is friction the user pays on every insertion and gets no retention back
# for. A free fit is what it would prefer, and it does not fit -- FREE widens
# every bore by 0.09 mm of radius, which is enough to squeeze the row pitch until
# the 6 mm and 9 mm bores are 0.99 mm apart. Sliding still leaves 0.16 mm of
# radial clearance and buys back a 1.36 mm wall, which is a better trade in a
# material this soft. If the drills ever feel like they drag, take it from
# SHELL_WALL, not from here.
RELIEF_FIT = fits.for_material(fits.SLIDING, CART_MATERIAL)

# Press fit, TPU -- as LAND_FIT, but it gets its own constant because a hex land
# bears on flats rather than on a curved wall, and full flat-on-flat contact is
# grabbier per mm of engagement. The PETG version found the same thing from the
# other side (HEX_GRIP 0.25 vs RIB_GRIP 0.22), so expect these two to diverge
# once both have been on a coupon. Equally UNVERIFIED.
HEX_LAND_FIT = fits.for_material(fits.PRESS, CART_MATERIAL)

# Lead-in at each bore mouth on the cartridge's top face. Smaller than the base's
# BORE_MOUTH_CHAMFER (0.8): two neighbouring mouths each want their chamfer to
# form without running into each other, and this cartridge's row pitch is tighter
# than the base's -- at 0.8 the 6 mm and 9 mm mouths overlap and leave a sharp
# sliver between them. 0.5 clears the 1.23 mm those two actually have, and a
# lead-in in TPU has an easier job anyway: the material gives.
CART_MOUTH_CH = 0.5

LAND_LEAD_IN = CART_MOUTH_CH  # cone from the relief down onto the land

# Relief at the very bottom of each bore, where the land meets the bed face.
# Two jobs: it chamfers what would otherwise be a raw square edge (house rule --
# chamfer horizontal edges), and it backs off the first layer, whose elephant's
# foot squeezes inward and would otherwise make the bottom of the land grip
# tighter than anything modelled here. It comes out of LAND_H, so the land that
# actually bears is LAND_H - BORE_FOOT_RELIEF.
BORE_FOOT_RELIEF = 0.3
EFFECTIVE_LAND_H = LAND_H - BORE_FOOT_RELIEF

# --- Retention ----------------------------------------------------------------
# A drill leaves the land at maybe 5-15 N; the cartridge weighs about 0.2 N. So
# without a catch the cartridge simply comes out with the first drill. The bead
# goes on the TPU and the groove in the ASA -- the compliant half of a joint
# carries the bead, so seating it costs a squeeze rather than a wall deflection.
#
# The profile is box.snap_bead_ring's asymmetric ramp (outward=True), for the
# reason recorded at box.py:81-89: a symmetric half-round bump fights the user
# going on, because it rises as steeply as it protrudes.
CART_BEAD = 0.6  # radial protrusion of the TPU bead
BEAD_LEAD_IN = 2.4  # gentle insertion ramp below the tip
BEAD_BACK = 1.1  # steeper retention face above it
BEAD_TIP_FLAT = 0.3
SHELL_GROOVE_R = SNAP_GROOVE_R  # same round pocket the cover's bead drops into
BEAD_ENGAGEMENT = CART_BEAD - CART_SLIP / 2  # 0.44 mm of real overlap

# --- Keying -------------------------------------------------------------------
# The shell's engraved wall legend only tells the truth in one orientation, and a
# rounded square goes in four ways. The key rib stands *outside* the cartridge
# body, on the +X face, so it can never collide with a bore however the packer
# lays them out -- and +X is the one face pair that carries no legend.
KEY_W = 2.4
KEY_D = 0.8  # how far the rib stands proud of the cartridge / into the shell
#              wall, leaving SHELL_WALL - KEY_D = 0.8 mm behind the slot
KEY_ROOT = 1.0  # how far it reaches back *into* the cartridge, so the rounded
#                 profile still meets the wall along its whole length
KEY_FILLET = 0.6  # vertical edges are filleted, not left square
KEY_LEAD_IN = 0.4  # lofted bottom -- the rib is the first thing to enter the slot
KEY_SLIP = fits.for_material(fits.SLIDING, CART_MATERIAL)  # sliding fit, TPU

# --- Bore layout --------------------------------------------------------------
# The packing envelope is the cartridge, not the collar, and it is tighter than
# the PETG base's: the shell wall and the cartridge wall both come out of the
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


__all__ = [
    "BASE_TOP_CHAMFER",
    "BASE_TOTAL_H",
    "BEAD_BACK",
    "BEAD_ENGAGEMENT",
    "BEAD_LEAD_IN",
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
    "HEX_LAND_FIT",
    "KEY_D",
    "KEY_FILLET",
    "KEY_LEAD_IN",
    "KEY_ROOT",
    "KEY_SLIP",
    "KEY_W",
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
    "SHELL_GROOVE_R",
    "SHELL_MATERIAL",
    "SHELL_TOP_CHAMFER",
    "SHELL_WALL",
    "relieved_bore_r",
]
