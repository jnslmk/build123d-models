# Design notes — drill_storage

Why these models are shaped the way they are. The numbers themselves live in
`config.py` (the clearances, shared by all three sets) and `sets.py` (what each
set is), next to the geometry that consumes them.

## Contents

- [What came before: the ribbed bore](#what-came-before-the-ribbed-bore)
- [The rib question](#the-rib-question)
- [Why the land is at the bottom](#why-the-land-is-at-the-bottom)
- [Why the cartridge is a short collar](#why-the-cartridge-is-a-short-collar)
- [What the shell wall costs](#what-the-shell-wall-costs)
- [Retention, keying, removal](#retention-keying-removal)
- [Three sets, one design](#three-sets-one-design)
- [Judgements from printed parts](#judgements-from-printed-parts)
- [Open questions](#open-questions)

## What came before: the ribbed bore

This section is history, and it is kept because the code it describes has been
deleted. Every holder in this package used to be **one PETG part**, and it
gripped each bit on three compliant ribs standing into an otherwise relieved
bore. Two full sets were printed and both fought back, in opposite directions:

| | grip law | verdict |
|---|---|---|
| v1 | `0.04·d`, min 0.15 | 9/10 mm too tight, 8 mm and under too loose |
| v2 | 0.34 flat, falling | 8/9/10 mm too loose, 6 mm and under too tight |

Those reports are consistent, and the reason was never the interference number.
The ribs were not springs: the bead stood only 0.2 mm proud of its valley while
being 0.8 mm wide, so each "rib" was a shallow lens welded to the wall over
nearly its full width. It could not deflect, only be crushed — v2 asked a 2 mm
bore to squash 85% of its rib away and a 10 mm bore to engage 25% of one, and
the whole usable travel between *rattles* and *jams* was about 0.1 mm of radius,
finer than FDM's own run-to-run variation on a small hole.

The fix was geometric rather than numeric — make the bead mostly proud of the
valley so it meets the wall on a narrow neck and behaves like a stub spring, and
one absolute interference then covers every size, because grip becomes
force-controlled rather than position-controlled. That worked, and a printed
sweep settled it at 0.22 diametral, with a measured small-bore compensation
table underneath 5 mm where the nozzle cannot trace the bead tip out of a tight
concave notch.

It also took **three rounds of printed coupons** to get there, and every size
below 5 mm was revised upward at least once. The two-material version replaced
all of it. What is worth carrying forward is not the numbers but the shape of
the mistake: *when no single number can be made to work, the geometry is wrong,
not the number* — which is exactly the reasoning that produced the short land
below.

## The rib question

The question that started this: *if the insert is TPU, does it still need ribs?*

Half of the answer is yes-you-can-drop-them, and it is the obvious half. The
ribs existed because PETG has no compliance of its own, and the section above is
the record of what that cost. TPU supplies that compliance from the bulk
material, so the geometry stops earning its complexity.

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

Same reason the old rib band started at the bore floor: that is where the plain
shank is. Higher up sit the flutes — two narrow spiral margins over a void — where a
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
`GUIDE_FIT` (free, plus the 0.24 mm a hole prints undersize, so it is free in the
*part* and not only in the model) for 23.2 mm, which is the guide. The TPU is a **collar** centred
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
115 mm cover for these models alone and end the shared-cover property.
`checks.py` asserts the seat is still where the engine puts it, so that trade
cannot be made by accident.

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

Against the **brad-point** lengths `sets.WOOD` assumes, every size clears by at
least 4.3 mm. Against DIN 338 **jobber** lengths — which is what `sets.METAL`
is — only the 2 mm is short, and by 1.7 mm rather than the 3.3 it was before the
base came down to 36; shortening the base moves the land *down*, so it improves
this margin rather than costing it. `bores-and-ribs.md` is where the flute
warning comes from: hardened spurs broach a grip feature away permanently, and
TPU is softer than the PETG that lesson was learned on.

`sets.METAL` has no 2 mm problem in practice because its 2 mm drill is 49 mm
long, not the 31 mm shank-top the jobber table assumes for the shortest stubby
— but neither table is measured off real bits. Measure the shank on the smallest
drill you own before printing a cartridge for a set of your own.

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
above), reused via `outward=True`, for the reason recorded on that function: a
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

## Three sets, one design

`wood`, `metal` and `stone` are the same shell, the same cartridge and the same
cover, cut for different tools. Everything that differs is in `sets.py`, and it
is deliberately a short list: which sizes, how long they are, what the cover
says, and one thing that is not obvious.

**A masonry bit's shank is under its nominal size.** The carbide tip is brazed
across the top and stands proud on every side — that is what lets the bit cut a
hole its own shank passes freely through — so a bore cut to the printed size
grips 0.2 mm of air. `sets.STONE` carries a `shank_allowance` of 0.20 mm and
every bore, ASA guide and TPU land alike, is cut to `nominal − allowance`. The
engraved legend still reads the nominal size, because that is what the bit is
sold as. This costs nothing: bits go in shank-first and the tip never enters the
tray.

It also caps that set at 10 mm. Masonry bits above it are commonly sold with a
*reduced* shank — a 12 mm bit on a 10 mm shank, to fit a 10 mm chuck — which is
a different allowance for each size rather than one for the set, and a 12 mm
legend over a 10 mm bore is a label that lies.

The wood and metal sets have no allowance: a twist or brad-point drill's shank
*is* its nominal size, ground h8.

## Judgements from printed parts

The one instrument that settles a fit here is a printed cartridge. Recorded in
order, newest last:

| what was printed | judgement | what changed |
|---|---|---|
| wood cartridge, `LAND_FIT = −0.10` | holds — and this is why the ribbed design was dropped — but harder than a tool tray wants; a drill lifts the shell off the baseplate on the way out | `LAND_EASE = 0.05` added, opening both the round and hex lands by one named step |

`LAND_EASE` is deliberately half of `LAND_EXTRA_GRIP`: the useful band between
*falls out* and *fights you* is narrow in an elastomer, and the printer's own
hole undersize (0.1–0.3 mm) is wider than the correction. Ease again before
reaching for `LAND_H` — a shorter land changes the contact area, which is the
thing that was reasoned about above, while the ease only trims the interference.

## Open questions

- **Is the eased land right?** `LAND_EASE` has been modelled, not printed. The
  next cartridge answers it; write the answer into the table above.
- **The hex land has never been judged on its own.** It carries the same ease as
  the round bores, but a hex land bears on flats, and full flat-on-flat contact
  is grabbier per mm than a curved wall. The ribbed design found the same thing
  from the other side, wanting more interference on the hex than on the round
  bores. Expect these two to diverge again.
- **Is the land now on the flutes of the small drills?** See the table above —
  it depends on the bits, and neither reference table is measured. This is the
  open question the collar geometry created, and the cheapest way to close it is
  a caliper on a 2 mm drill.
- **Does the ASA cover snap still feel right?** `create_cover` is reused
  unchanged, and `COVER_WALL = 1.2` was sized to flex in PETG. ASA is stiffer and
  more brittle; the bead may want less protrusion. Nothing here changes it, and
  nothing here has tested it.
- **Does 23.2 mm of ASA guide plus a 3.5 mm land hold a drill straight enough?**
  The guide is cut at +0.49 diametral — a free fit plus the hole undersize, so it
  should *print* free rather than arriving at +0.01 — over a long span, which
  should be far better than the old all-TPU arrangement, but that is arithmetic,
  not a print. It also gives up 0.12 mm of radial location: taken alone, a drill
  in the guide can now tilt `atan(0.49 / 23.2)` ≈ 1.2°, against 0.6° before. The
  guide is not what locates a drill in the end — it stands on the floor and is
  held at the TPU land, 3.5 mm of it, at the top of the stack — but if a bit ever
  rattles visibly in the shell, this is the number that bought it.
- **The bore layout is still cramped by the shell wall.** If it ever needs to give
  more back, the honest alternative is a 1×2 footprint.
