"""Measured and derived numbers for the ASA shell + TPU cartridge holder.

No geometry lives here. Everything is either imported from ``drill_storage.box``
(so the Gridfinity envelope and the cover interface cannot drift apart from the
PETG version) or derived from those numbers as an expression -- never typed as an
evaluated result, which is how a relationship becomes invisible and free to
break.

The vertical stack, all in world z with the shell's foot on z=0::

    0.0  -  4.4   Gridfinity foot (BASE_H)
    4.4  -  6.0   shell floor -- drills bottom out here, on ASA, never on TPU
    6.0  - 29.2   ASA guide bores, free fit as printed -- straight, never gripping
   24.0           SHELL_FOOT_TOP, the shoulder the cover seats on
   29.2           CAVITY_FLOOR_Z -- the collar sits here
   29.2 - 32.7   TPU grip land (LAND_H) -- the only thing that holds a drill
   30.0           cover snap groove (SHELL_FOOT_TOP + SNAP_Z)
   32.7 - 33.2   lead-in cone from the relief down onto the land
   33.2           collar retention bead / shell groove (BEAD_Z)
   33.2 - 37.2   TPU relief bore, sliding fit -- clears the drill, grips nothing
   36.0           SHELL_TOTAL_H -- shell top
   37.2           collar top, standing CART_PROUD above it to be pinched out

The cartridge is a **collar**, not a block: it reaches exactly as far below the
retention bead as it stands above it (``CART_BELOW_BEAD == CART_ABOVE_BEAD``), and
that reach is the longer of what it has to contain -- land plus lead-in, or the
bead's own ramp. So the TPU is 8.0 mm rather than 37.2, everything below it is ASA
bored at a free fit, and the shell guides while the collar grips.

The base is 36 mm, not the PETG base's 42: its bores no longer come down from the
top face, so the height above the cover seat only has to hold the collar. What did
*not* move is ``SHELL_FOOT_TOP``. The seat feeds ``cover_height_for``, so lowering
it would mint a taller cover for this model alone; leaving it at 24 means
``cover_height_for`` returns the same 109 mm it does for the PETG base and an
already-printed ``drill_storage.wood`` cover still fits. ``checks.py`` asserts that
rather than trusting the coincidence.
"""

from __future__ import annotations

from build123d import Color

from ...lib import fits
from ..box import (
    BASE_TOP_CHAMFER,
    BORE_FLOOR_Z,
    BORE_MOUTH_CHAMFER,
    COLLAR_R,
    COLLAR_W,
    FOOT_TOP,
    SNAP_GROOVE_R,
    SNAP_Z,
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
# have to; it must therefore grip nothing at all.
#
# This fit is stated as what the *printed part* should have, and converted to a
# number to cut, because the two differ by more than the fit itself. FDM prints a
# small vertical hole undersize -- a 5 mm hole modelled at nominal measured
# 0.24 mm small on a 0.4 mm nozzle (fdm-fits-and-clearances rule 4) -- so a bore
# cut at a free fit in ASA (+0.25) arrives at roughly +0.01. That is the tightness
# a drill can feel: zero clearance over 23.2 mm of guide, in the one place the
# design wants no contact at all.
#
# What it wants instead is *a little* looser than zero, not a full free fit's
# 0.25 mm of real slop rattling a 121 mm drill. That is SNUG by definition --
# goes together by hand, no perceptible play -- so SNUG is what the part gets, and
# the undersize is what turns it into a number to cut.
#
# ``for_material`` is deliberately NOT applied on top. Its ASA offset (-0.15) is
# the same physical story GUIDE_UNDERSIZE_COMP already tells -- a rigid-material
# hole coming out under nominal -- and stacking both lands at +0.19, tighter than
# the +0.25 that was already too tight. The undersize is the measured version of
# that correction, so it is the one that stands.
#
# LAND_FIT one section down *exploits* the same printer fact -- a TPU bore at
# nominal arrives as the interference that grips. One effect, opposite signs: the
# land wants the undersize and the guide has to cancel it. Neither is allowed to
# be an anonymous float, so both are a fit class plus a named delta.
#
# The ceiling is the cavity floor, where two neighbouring guide mouths must not run
# into each other: at +0.34 the closest pair (9 and 10 mm) keeps 1.34 mm, against
# the 1.10 mm that two GUIDE_MOUTH_CH chamfers plus a sliver need. checks.py checks
# that rather than trusting it, because layout_bores packs on the *cartridge's*
# relieved bore and knows nothing about how wide the guide is cut.
GUIDE_PRINTED_FIT = fits.SNUG  # snug fit -- what the bore has once it is printed
GUIDE_UNDERSIZE_COMP = 0.24  # what FDM takes back out of a small vertical hole
GUIDE_FIT = GUIDE_PRINTED_FIT + GUIDE_UNDERSIZE_COMP  # 0.34 -- what gets cut
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

# --- Shell height -------------------------------------------------------------
# The base does NOT inherit box.BASE_TOTAL_H. The PETG base is 42 mm because its
# bores are sunk from the top face and need the depth; this one grips in a short
# collar at the top and guides in ASA below, so it needs far less.
#
# Only ``SHELL_COLLAR_H`` comes down. ``SHELL_FOOT_TOP`` deliberately stays at
# box.FOOT_TOP, because the seat height feeds ``cover_height_for``: lower it and
# this model needs its own taller cover, and an already-printed
# ``drill_storage.wood`` cover stops fitting. The collar is free -- the cover's
# groove sits at ``FOOT_TOP + SNAP_Z`` either way, so shortening above that costs
# the cover nothing. checks.py asserts both halves of that.
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
CART_PROUD = 1.2  # stands above the shell rim so it can be pinched back out
CART_TOP_Z = SHELL_TOTAL_H + CART_PROUD  # 37.2
# (the collar's *height* is derived under "Collar height" below, once the
# features it has to contain have been declared.)

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
# the ASA guide below is cut LOOSE (GUIDE_FIT, +0.34) and the TPU collar TIGHT
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
# drops with the shell rim, BEAD_Z follows it down, and the cavity floor with it.
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
GROOVE_SEPARATION = BEAD_Z - (SHELL_FOOT_TOP + SNAP_Z)  # 3.2, vs 1.6 required

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
    "FOOT_TOP",
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
    "GROOVE_SEPARATION",
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
    "GUIDE_PRINTED_FIT",
    "GUIDE_UNDERSIZE_COMP",
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
    "SHELL_COLLAR_H",
    "SHELL_FOOT_TOP",
    "SHELL_GROOVE_R",
    "SHELL_MATERIAL",
    "SHELL_TOP_CHAMFER",
    "SHELL_TOTAL_H",
    "SNAP_Z",
    "SHELL_WALL",
    "relieved_bore_r",
]
