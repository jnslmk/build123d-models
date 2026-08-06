# Design notes — drill_storage.flex

Why this model is shaped the way it is. The numbers themselves live in
`config.py`, next to the geometry that consumes them.

## Contents

- [The rib question](#the-rib-question)
- [Why the land is at the bottom](#why-the-land-is-at-the-bottom)
- [Why the cartridge is a short collar](#why-the-cartridge-is-a-short-collar)
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

It also decides how far up the land can move — see the table below, which is the
live constraint on this design now that the collar is short.

## Why the cartridge is a short collar

The first version made the cartridge a full-height block filling the cavity to
the shell floor: 37.2 mm of TPU carrying both the grip and the guide. That was one
part doing two jobs with opposite requirements. Guiding a 121 mm drill over a long
span wants a *rigid* wall; gripping it wants a *compliant* one. A block is a
compromise at both, and an expensive one — 33 cm³ of slow filament.

Splitting them costs nothing. The shell is solid ASA below the cavity and bored at
`GUIDE_FIT` (+0.34 cut: a snug fit in the *part*, plus the 0.24 mm a hole prints
undersize) for 23.2 mm, which is the guide. The TPU is a **collar** centred
on its own retention bead — it reaches exactly as far below the bead as it stands
above it — and that reach is the longer of what it must contain (land plus lead-in,
or the bead's own ramp), so the collar comes out 8.0 mm and does nothing but grip,
over a 3.5 mm land.

| | TPU | ASA |
|---|---|---|
| full-height block, 42 mm base | 33.2 cm³ | 20.4 cm³ |
| collar + bored shell, 42 mm base | 11.3 cm³ | 43.1 cm³ |
| collar + bored shell, **36 mm base** | **7.4 cm³** | **40.3 cm³** |

Two thirds of the *slow* half went away and the guiding got better rather than
worse. The base then came down as well — 42 → **36 mm** — because with the bores no
longer sunk from the top face, the height above the cover seat only has to hold the
collar. That is a free 6 mm: the cover's groove sits at `SHELL_FOOT_TOP + SNAP_Z`,
so shortening *above* the seat costs the cover nothing.

The seat itself deliberately did not move. `SHELL_FOOT_TOP` feeds
`cover_height_for`, so lowering it to 18 would save another ~6 cm³ but mint a
115 mm cover for this model alone and end the shared-cover property. `checks.py`
asserts the seat is still where the PETG base's is, so that trade cannot be made by
accident.

The base is no longer a whole Gridfinity Z unit, and does not need to be — what has
to quantise is the assembled envelope, still 19U / 133 mm.

### The cost: the land moved up, and the small sizes got tighter

The land was at world z 6.0–9.5 — the very bottom of the bore, deep in the plain
shank of every bit in the set. It is now at **29.2–32.7**, because that is where
the bottom of a bead-centred collar lands. That is nearer the flute boundary on the
smallest drills, and how near depends on which bits you own:

| d | jobber shank top | margin | brad-point shank top | margin |
|---|---|---|---|---|
| 2 | 31.0 | **−1.7** | 42.0 | +9.3 |
| 2.5 | 33.0 | +0.3 | 38.0 | +5.3 |
| 3 | 34.0 | +1.3 | 39.0 | +6.3 |
| 3.5 | 37.0 | +4.3 | 37.0 | +4.3 |
| 10 | 52.0 | +19.3 | 40.0 | +7.3 |

Against the **brad-point** lengths this set actually uses
(`assemblies/wood.DRILL_LENGTHS`) every size clears by at least 4.3 mm. Against DIN
338 **jobber** lengths only the 2 mm is still short, and by 1.7 mm rather than the
3.3 it was before the base came down to 36 — shortening the base moves the land
*down*, so it improves this margin rather than costing it. `bores-and-ribs.md` is
where the flute warning comes from: hardened spurs broach a grip feature away
permanently, and TPU is softer than the PETG that lesson was learned on.

So it is fine for the wood set as specified and **marginal** for a jobber twist set
like `drill_storage.metal`. Neither table is measured off real bits; both are
reference figures. Measure the shank on the smallest drill you own before printing
a collar for a set other than this one.

Mitigations, if it bites: shorten `SHELL_COLLAR_H` further (the whole collar, and
therefore the land, follows the rim down — but the bead has to stay clear of the
cover's groove at z=30, and `GROOVE_SEPARATION` is down to 3.2 mm), or raise
`GUIDE_FLOOR_Z` so the bits stand higher — which changes `bore_floor_z` and
therefore the cover height, so it costs the shared cover.

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
free fit to a sliding one. That was a real trade when the relief still had to guide
the drill; since the guiding moved into the ASA below, it costs nothing at all —
the relief now only has to *clear*, and 0.16 mm of radial clearance clears. It buys
the bore wall back to 1.36 mm, which clears its own chamfer budget rather than
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
- **Is the land now on the flutes of the small drills?** See the table above —
  it depends on the bits, and neither reference table is measured. This is the
  open question the collar geometry created, and the cheapest way to close it is
  a caliper on a 2 mm drill.
- **Does the ASA cover snap still feel right?** `create_cover` is reused
  unchanged, and `COVER_WALL = 1.2` was sized to flex in PETG. ASA is stiffer and
  more brittle; the bead may want less protrusion. Nothing here changes it, and
  nothing here has tested it.
- **Does 23.2 mm of ASA guide plus a 3.5 mm land hold a drill straight enough?**
  The guide is cut at +0.34 diametral — a snug fit plus the hole undersize, so it
  should *print* at about +0.10 rather than arriving at +0.01 — over a long span,
  which should be far better than the old all-TPU arrangement, but that is
  arithmetic, not a print. It gives up 0.045 mm of radial location against the
  bore as it was cut before: taken alone, a drill in the guide can tilt
  `atan(0.34 / 23.2)` ≈ 0.8°, against 0.6°. Compensating all the way to a printed
  *free* fit was tried and backed out — +0.49 cut, 1.2° — because 0.25 mm of real
  clearance is slop under a 121 mm drill, and the guide's job is to hold it
  straight. Snug is the target: a little looser than zero, no more.
- **The bore layout is still cramped by the shell wall.** If it ever needs to give
  more back, the honest alternative is a 1×2 footprint.
