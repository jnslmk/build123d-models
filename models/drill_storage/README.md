# Drill Storage

Gridfinity drill holders, one per tool set. The original upright holders have
a rigid **ASA base** that guides, a compliant **TPU cartridge** that grips,
and a tall labelled **PETG cover** that snaps over the collar. Separate
sideways wood and metal holders use a single-foot ASA guide and a foot-bearing,
side-removable PETG cover instead; their fit is pending a print trial.

```bash
uv run show drill_storage               # the family: three bases, three covers
uv run show drill_storage.wood          # 2-10 mm brad-point set + countersink
uv run show drill_storage.metal         # 1-10 mm HSS twist + tap + step drill
uv run show drill_storage.stone         # 3-10 mm carbide masonry set
uv run show drill_storage.allen         # 8-piece 50 mm hex-key box
uv run show drill_storage.hex           # 16-piece 1/4" hex-shank driver bits
uv run export drill_storage.wood.base  # STL + STEP for the slicer
uv run check drill_storage.wood         # geometry assertions for one set
uv run export drill_storage.wood.cover_stackable  # alternate stackable PETG lid
uv run show drill_storage.bin           # bin with lid seated, inspection scene
uv run export drill_storage.bin.base    # empty PETG bin, foot-down
uv run export drill_storage.bin.lid     # lift-off stackable PETG lid, socket-down
uv run view drill_storage.dremel        # closed 1×2 inspection scene
uv run export drill_storage.dremel.base    # ASA guide base, foot-down
uv run export drill_storage.dremel.insert  # TPU grip cartridge, land-up
uv run export drill_storage.dremel.cover   # PETG cover, pillow-down
```

## Layout

| module | what it is |
|---|---|
| `box.py` | **The engine.** Gridfinity constants, hole packing, wall legends, `create_cover`, and the one-material `create_base`. Not a model. |
| `config.py` | Every clearance, shared by all three sets: the guide fit, the land fit, the relief, the snap. No geometry. |
| `sets.py` | **The drill sets**, side by side: sizes, lengths, cover label, shank allowance. The only thing a variant decides. |
| `freepack.py` | The layout solver for the one set `pack_rows` cannot lay out in rows. Run by hand; its answer is frozen in `sets.py`. |
| `base.py` / `insert.py` / `cover.py` | The three parts, set-agnostic. Hand them a `DrillSet`. |
| `assembly.py` / `sampler.py` | The scenes: one set assembled, and all three side by side. |
| `tools.py` | Display models of the bits themselves, for those scenes. Not printed. |
| [`wood/`](wood/README.md) [`metal/`](metal/README.md) [`stone/`](stone/README.md) | One package per drill set: the assembled scene, plus `base`, `insert` and `cover` as their own downloadable models. Four modules of naming each. |
| `cover_stackable.py` (in each set package) | Alternate PETG cover with a full-depth Gridfinity foot socket and built-in removable print support. |
| [`allen/`](allen/README.md) [`hex/`](hex/README.md) | The two 1/4" hex-shank sets, sharing one geometry: `drill_storage.allen` is the 1x1 ALLEN key box (8 sockets), `drill_storage.hex` the 1x1 driver-bit box (16 sockets in a 4x4 grid, shaved lead-in clearances). Both rigid base + TPU insert + translucent cover. |
| [`bin/`](bin/) | Parametric general-purpose PETG bin, independently printable body and lift-off stackable lid, plus a seated display scene. |
| [`dremel/`](dremel/) | Independent 1×2 three-part Dremel variant: ASA base, TPU insert and labelled PETG cover, plus the closed inspection scene. |
| `sideways.py` / `sideways_cover.py` / `sideways_checks.py` | Shared horizontal wood/metal guides, foot-bearing covers and physical tool/closure checks. Each `sideways` package is the assembled scene, with separate `sideways.base` and `sideways.cover` prints and an open `sideways.preview`; see the [sideways specification](docs/sideways-specification.md) and [current cover contract](docs/sideways-cad-contract.md). |

Adding a set is a `DrillSet` in `sets.py` and a package copied from
`wood/`. Nothing in the geometry has to know about it.

## How the parts hold together

**Base → cover.** A 41.5 mm body — one Gridfinity pad, and the cover's width
too, so the two are flush with no lip at the seam — steps down to a 39.2 mm
collar that plugs into
the cover's bore on a 0.4 mm diametral slip fit, and a ramped bead inside the
cover clicks into a groove on the collar. The bead is asymmetric on
purpose: a long gentle lead-in below the tip so the cover slides on
progressively, a shorter steeper face above so it still detents going in. The
groove is asymmetric too, and for two different reasons — a 45° roof because
the base prints foot-down and that roof is an overhang, a longer floor so the
bead's whole insertion ramp has somewhere to go.

**Base → cartridge.** The cartridge drops into a 6.8 mm cavity at the top of the
base and clicks in on its own bead — outward, on the TPU, so seating it costs a
squeeze rather than deflecting an ASA wall. The groove that receives it is
shaped exactly like the cover's, and for the same two reasons: a round groove's
roof finishes horizontal, so the lip the cartridge hangs from used to droop into
the groove it bounds — see `docs/design-notes.md`. A key rib on the +X face means it
only goes in one way round, which is what makes the base's engraved legend true.

**Cartridge → bit.** The bore is plain and round, and it grips on a **3.5 mm
land** at the very bottom, on the bit's plain shank. Everything above the land is
relieved and everything below it is ASA. Guiding and gripping are cut on opposite
sides of nominal, deliberately:

| | where | fit | job |
|---|---|---|---|
| ASA guide | 23.2 mm below the cartridge | **+0.49** (free, as printed) | keeps the bit upright, must never rub |
| TPU relief | above the land | +0.32 (sliding) | clears the bit, grips nothing |
| TPU land | 3.5 mm at the cartridge floor | **−0.05** (press, eased) | the only thing that holds a bit |

`checks.py` asserts that ordering. A guide that gripped, or a land that cleared,
would each defeat the split silently.

## The interference is judged, not calculated

`models/lib/fits.py` models rigid-plastic *clearance* fits and says nothing about
an elastomer squeezing a steel shank, so `LAND_FIT` is a judgement made on a
printed cartridge and written down. The first one held — that is why this design
replaced the ribbed PETG bores it grew out of — but harder than a tool tray
wants, so both lands were opened by a named `LAND_EASE` of 0.05 mm.

That record, and what came before it, is in
[`docs/design-notes.md`](docs/design-notes.md). Print a cartridge before
re-cutting one: it is about 7 cm³ and an hour, against 20 cm³ and most of a day
for a base.

## General-purpose bin and stackable lid

`drill_storage.bin.base` is a separate PETG container with half-cell X/Y sizes
and body height in 7 mm units. Its wall defaults to 1 mm (two 0.4 mm
perimeters with a small reserve). The 1×2×3U default has a closed 1 mm plate
under each foot and a hollow rising into the open cavity: the foot boundaries
form a shallow raised seam on the interior floor, rather than exposed
underside ribs or a continuous floor above the feet. `bottom_thickness=0`
uses the wall thickness; a larger value thickens the print-bed plates. There
are no mouse-ear brims. Optional features include solid feet, half-grid foot
placement, magnet pockets, dividers, label tabs and scoops. The controls and
default base profile follow the
[Gridfinity Bin Generator](https://sitnikov.github.io/gridfinity-bin-generator/);
this body retains this repository's Gridfinity foot envelope and independently
built PETG geometry. Its 0.6 mm flat landing strip supports the separate
`drill_storage.bin.lid` with a locating skirt. The lid lifts off rather than
snapping shut; it is not sealed. It receives matching full or half Gridfinity
feet in a 2.5 mm socket on its exposed face. See the
[empty-bin specification](docs/empty-bin-specification.md), the
[accepted body contract](docs/empty-bin-cad-contract.md), and the
[current lid contract](docs/lid-cad-contract.md).

`grid_x` and `grid_y` accept half-cell increments. `half_grid_base` replaces
full feet with half-cell feet; otherwise `half_grid_right` and `half_grid_top`
choose which edge gets a partial foot. `ultra_light_base` opens the closed
feet into the storage cavity; disabling it makes the feet and raised floor
solid. Magnet pockets are cut in full-cell feet only (requesting magnets
with `half_grid_base` is rejected); `magnet_diameter` defaults to 6.15 mm
nominal and receives a PETG sliding-fit allowance. The divider switch is on
by default but both `dividers_x/y` are zero, leaving the default cavity
undivided. `labels`, `label_for_each_section`, `label_position`,
`label_width/depth`, and `ultra_light_labels` control inward label tabs.
`scoops` and `scoop_radius` add curved retrieval ramps at each Y section's
floor. Labels and scoops are off by default; they consume interior space.

Lightweight label ribs use the generator's default density of one support
about every 13 mm. Optional dividers and scoops stay above the stackable
lid's foot socket clearance; unlike the default empty bin, their first
layers can bridge an open foot cavity. Check those variants in the slicer
or use a solid base if a continuous backing is needed.

`lid_height` is the **whole print-part height in millimetres**, default 6.5 mm:
2.5 mm socket depth, 1 mm roof above it, and a 3 mm plug skirt below the
bin rim. Raising it thickens the roof; it does not deepen the skirt and foul
labels or dividers. The 1 mm body wall and lid skirt have a PETG sliding fit.
Interior fixtures stop 3.6 mm below the rim to leave room for the skirt.
The lid is printed **top-down, skirt up**. Its `support` checkbox defaults
to on, adding a breakaway lattice beneath each socket. Remove each lattice
and its four small attachment nibs before stacking. Turn `support` off to
export a clean socket if using slicer supports or after verifying the
unsupported ~37 mm bridge on your printer. The bin base is displayed black
and the lid translucent, matching the other drill-storage sets; STL carries
geometry only, not color. `drill_storage.bin` shows the closed two-part scene
after support removal; export the two leaf models separately to print them.

## Dremel tool holder

`drill_storage.dremel` is a closed inspection scene of three separately
printable parts: a rigid ASA guide base, a removable TPU grip insert, and a
translucent PETG cover for tools up to 50 mm long. It is not an STL print job;
export the `.base`, `.insert`, and `.cover` leaf models separately.

The 1×2 base has two Gridfinity feet, a flat cover seat at z=24, and 55
compensated free-fit guides ending on an ASA floor at z=8. The 8 mm TPU
cartridge has matching through-bores, each with a short gripping land and a
relieved upper section. Its outward retention bead snaps into the base's
inner groove; the cartridge can be lifted from its proud rim.

The labelled PETG cover snaps over the base's rectangular collar and sits
flush with the full-width body. Its assembled top is 10U (70 mm), giving
10 mm clearance above a 50 mm tool standing on the guide floor. It prints
pillow-top down with its open mouth up; the inverted print-pose lettering
reads upright when the cover is seated. All three parts require individual
prints in their specified materials. Tool heads wider than the 7 mm pitch
can prevent filling every one of the 55 positions simultaneously. Printed
TPU grip and cover snap effort/durability remain to be calibrated.
See the [Dremel specification](docs/dremel-specification.md) and
[CAD contract](docs/dremel-cad-contract.md).

## Stackable cover option

Each of the five tool sets also offers `<set>.cover_stackable`: a separate PETG
cover snapping onto the original collar while receiving the **entire 4.4 mm**
of another holder's 1×1 foot. The unchanged base, smooth cover and main cover
wall remain 41.5 mm wide; only the stackable cover's top lip widens by 0.25 mm
per side to the drawing's 42 mm grid pitch. Its assembled top is at
7U + 4.4 mm, so the fully seated foot gives exactly 7U stack pitch. The lip
mouth has PETG sliding clearance but only about **0.14 mm nominal wall per
side**: this is a user-accepted experimental exception, not proven printable,
durable, or free of adjacent-cell interference under print tolerances.
Do not load a stack until a printed fit/durability and neighbouring-holder
trial succeeds. Keep the original smooth cover for a 41.5 mm envelope and
support-free printing.

The stackable cover prints **socket-down, mouth-up**. Each of the five leaf
models has an on-by-default `support` checkbox that adds a breakaway lattice
under its full-depth socket floor. Turn it off for a clean socket if using
slicer supports or after verifying the unsupported bridge on your printer.
When enabled, remove the lattice and all four attachment nibs before seating
another holder. The cap and longest-tool
clearance remain budgeted below the receiver. See
[the stackable-cover specification](docs/stackable-cover-specification.md) and
[the current CAD contract](docs/stackable-cover-cad-contract.md).

## Printing

The existing smooth parts need no supports. Every part comes off `create()` in
its print pose; stackable covers include an experimental thin lip and removable
support lattice requiring a slicer and print trial.

- **Base — ASA**, foot down, cavity up. 36 mm tall. ASA wants an enclosure; a
  42 mm footprint is not fussy, but a draught will still lift the foot's corners.
- **Cartridge — TPU**, top face down, bores down. 8 mm tall, every bore a through
  hole, so nothing to bridge and nothing to drain. Keep the perimeter count up:
  the grip land *is* a perimeter, and its diameter is the whole fit.
- **Cover — PETG**, pillow top on the bed, mouth up.

Smooth-cover heights are quantised: `cover_height_for()` selects the smallest
whole Gridfinity Z unit (7 mm) that clears the longest tool, giving assembled
smooth heights of 19U wood, 20U metal and 23U stone. Stackable tops instead
reach a 7U + 4.4 mm datum and recess an upper foot by 4.4 mm. Covers remain
interchangeable across bases with the same collar/seat; a taller one leaves
more air.

## Assembly

1. Drop the cartridge into the base, **key rib on the +X face** lined up with
   the slot in the cavity wall. It only goes one way.
2. Push until the retention bead clicks into the groove near the top. It takes a
   squeeze; TPU compresses 0.44 mm of engagement without complaint.
3. Bits go in **shank first**, pass through the collar, and bottom out on the
   base's ASA floor 23.2 mm below — soft plastic creeps under a point load.

To swap sets, pinch the 1.2 mm of cartridge standing proud of the base rim and
pull. Note that the guide bores live in the base, so a genuinely different set
needs both halves reprinted; the cartridge alone only re-does the grip.
