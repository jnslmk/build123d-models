# Design notes — drill_storage.flex

Why this model is shaped the way it is. The numbers themselves live in
`config.py`, next to the geometry that consumes them.

## Contents

- [The rib question](#the-rib-question)
- [Why the land is at the bottom](#why-the-land-is-at-the-bottom)
- [Why the cartridge is full height](#why-the-cartridge-is-full-height)
- [What the shell wall costs](#what-the-shell-wall-costs)
- [Retention, keying, removal](#retention-keying-removal)
- [Open questions](#open-questions)

## The rib question

The question that started this: *if the insert is TPU, does it still need ribs?*

Half of the answer is yes-you-can-drop-them, and it is the obvious half. The
PETG base's ribs exist because PETG has no compliance of its own. `box.py`
lines 187–286 are the record: two full printed generations failed in opposite
directions while someone tuned an interference number, and the diagnosis was that
the ribs were never springs — a 0.8 mm bead standing 0.2 mm proud of its valley is
a lens welded to the wall, and it can only be crushed. The fix was geometric. TPU
supplies that compliance from the bulk material, so the geometry stops earning its
complexity.

The other half is the one that bites. **Retention is friction × contact area**,
and TPU on steel runs μ ≈ 0.5–0.9 — an order of magnitude grabbier than the
rigid-on-steel case the fit ladder was built for. Take a 6 mm bore with the old
14 mm engagement, treat the block as a thick-walled cylinder, and a 0.1 mm radial
interference gives roughly

    p ≈ E·δ/r ≈ 20 MPa × 0.1/3 ≈ 0.67 MPa
    N ≈ p × π·d·h ≈ 0.67 × 377 mm² ≈ 250 N
    F ≈ μN ≈ 175 N ≈ 18 kgf

which is not a drill holder, it is a press fit. Running it backwards from a
pleasant ~10 N gives δ ≈ 0.006 mm radial — about 0.01 mm diametral, which is an
order of magnitude finer than FDM's own run-to-run variation on a small hole.

So the failure mode inverts. In PETG no modelled number was *loose* enough to
stop the fit being position-controlled; in TPU no *printable* number is tight
enough. Both are the same lesson from the `part-joints` skill — when one number
cannot be made to work, the geometry is wrong, not the number.

The geometry fix here is the mirror image of the rib fix. The ribs cut contact
*radially*, replacing a full circle with three line contacts. The land cuts it
*axially*, replacing 14 mm of engagement with 3.5. The two land in the same place:

| | contact |
| --- | --- |
| 3 ribs × ~0.5 mm wide × 14 mm | ≈ 21 mm² |
| full circle, 6 mm bore × 3.5 mm | ≈ 66 mm² nominal, less once the land rolls |

Same order, in a material two decimal orders softer — and the land keeps the one
thing the ribs bought, which is that a single number covers every size, because a
short land in a soft wall is force-controlled rather than position-controlled.

**So: plain round holes, no ribs — but a short land, not a deep bore.** A plain
bore relieved for its full depth would be the worst of both, and a plain bore at
interference for its full depth would weld itself to the drill.

## Why the land is at the bottom

Same reason `RIB_ZONE_H` starts at the bore floor: that is where the plain shank
is. Higher up sit the flutes — two narrow spiral margins over a void — where a
grip feature bears intermittently and, worse, where the hardened spurs broach it
away permanently on the way past.

That argument is *stronger* here, not weaker. It was learned on PETG; TPU is
softer, so a spur that scores PETG will carve TPU.

It also decides the architecture. A gripper plate in a recess in the shell's *top*
face would be a far smaller print and a far easier assembly — and it would grip
the flutes of every short drill in the set. The 2 mm drill in this set is 60 mm
long; standing on a 6 mm floor its shank ends around z=36, well below a top-face
plate at z=39–42.

## Why the cartridge is full height

Once the land has to be low, the cartridge has to reach it, and the cartridge can
only enter through the collar. That rules out the alternative that keeps the ASA
bores: a thin gripper plate cannot be threaded past a shell that already has
full-depth guide bores in it.

So the cartridge carries the whole bore — land at the bottom, relief above — and
the shell has no bores at all. The relief is not incidental: it is what stops the
rest of that 33 mm of TPU from adding friction, and it is what guides the drill,
which is the job the shell's ASA bores would otherwise have done.

The cost is a large TPU print (~33 cm³ solid). Sparse infill makes it bearable.

## What the shell wall costs

The collar is the throat, so bore space is bought from `SHELL_WALL` twice over:

    COLLAR_W 39.2 − 2·SHELL_WALL − CART_SLIP − 2·CART_WALL − 2·CART_MOUTH_CH

The PETG base packs its bores into 34.8 mm. At `SHELL_WALL = 2.0` this model gets
30.9, and that turned out not to be a cosmetic loss: `pack_rows` grades holes into
rows to fit the *width*, and absorbs any vertical shortfall by pulling the rows
together — silently, because it only warns about horizontal overpacking. At 2.0 mm
the 6 mm and 9 mm bores ended up **0.59 mm apart**, under the 0.8 mm a 0.4 mm
nozzle can resolve as a wall, in the softest part of the model.

Nothing in the toolchain complains about that, which is the point worth keeping:
the sharp-edge audit found it, indirectly, as a pair of slivers where two mouth
chamfers intersected. `checks.py` now measures every bore pair directly.

The resolution was to take both walls to their documented floors
(`SHELL_WALL` 1.6 = 4 perimeters, `CART_WALL` 1.0) and to drop `RELIEF_FIT` from a
free fit to a sliding one. That last one is a real trade — the relief would prefer
to be loose — but 0.16 mm of radial clearance still guides fine, and it buys the
bore wall back to 1.36 mm, which now clears its own chamfer budget rather than
merely clearing the printable minimum.

Every remaining minimum in the model lands on exactly 0.80 mm: the flat rim
between the two top chamfers, the collar wall under the cover's snap groove, and
the cavity wall behind the key slot. That is not a coincidence to admire, it is a
set of things that will break together if `SHELL_WALL` moves — hence the checks.

## Retention, keying, removal

**Retention.** A drill leaves the land at maybe 5–15 N; the cartridge weighs about
0.2 N. Without a catch the cartridge comes out with the first drill. The bead goes
on the TPU and the groove in the ASA — the compliant half of a joint carries the
bead, so seating costs a squeeze rather than a wall deflection. The profile is
`box.snap_bead_ring`'s asymmetric ramp (long lead-in below, short retention face
above), reused via a new `outward=True`, for the reason at `box.py:81–89`: a
symmetric half-round bump rises as steeply as it protrudes and fights the user
going on.

The bead sits at z=37 and the cover's groove at z=30, far enough apart that
neither thins the other's ring of collar wall.

**Keying.** The shell's engraved legend is only true in one orientation and a
rounded square goes in four ways. The key rib stands *outside* the cartridge body,
on the +X face — the one face pair carrying no legend — so it can never collide
with a bore however the packer lays them out. `checks.py` asserts that too, since
it is the whole reason the rib is out there rather than notched in.

**Removal.** The cartridge stands 1.2 mm proud of the shell rim so it can be
pinched. Push-out holes through the shell floor were considered and dropped: the
packer places bores wherever it likes, so any fixed hole position risks landing
under one and letting a drill fall through.

## Open questions

- **`LAND_FIT` and `HEX_LAND_FIT` are unmeasured.** Print
  `drill_fit_tester.land` in TPU and record the judgement here. Expect the two to
  diverge — a hex land bears on flats, and full flat-on-flat contact is grabbier
  per mm than a curved wall. The PETG version found the same thing from the other
  side (`HEX_GRIP` 0.25 vs `RIB_GRIP` 0.22).
- **Does 32 mm of TPU relief guide well enough?** 0.16 mm of radial clearance in
  a soft wall over 32 mm should hold a 121 mm drill to a degree or so of lean, but
  that is arithmetic, not a print.
- **Does the ASA cover snap still feel right?** `create_cover` is reused
  unchanged, and `COVER_WALL = 1.2` was sized to flex in PETG. ASA is stiffer and
  more brittle; the bead may want less protrusion. Nothing here changes it, and
  nothing here has tested it.
- **The cartridge is a slow print.** If that becomes the objection rather than a
  footnote, the honest alternative is a 1×2 footprint, which would also give the
  bore layout back the room the shell wall took.
