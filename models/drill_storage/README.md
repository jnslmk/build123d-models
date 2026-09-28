# Drill Storage

Gridfinity drill holders, one per tool set. Each is three printed parts in three
filaments: a rigid **ASA base** that guides, a compliant **TPU cartridge** that
grips, and a tall labelled **PETG cover** that snaps over the collar.

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
| `cover_stackable.py` (in each set package) | Alternate PETG cover with a Gridfinity foot socket and built-in removable print support. |
| [`allen/`](allen/README.md) [`hex/`](hex/README.md) | The two 1/4" hex-shank sets, sharing one geometry: `drill_storage.allen` is the 1x1 ALLEN key box (8 sockets), `drill_storage.hex` the 1x1 driver-bit box (16 sockets in a 4x4 grid, shaved lead-in clearances). Both rigid base + TPU insert + translucent cover. |
| [`bin/`](bin/) | Parametric general-purpose PETG bin, independently printable body and lift-off stackable lid, plus a seated display scene. |

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
perimeters with a small reserve). The bin defaults to an open cavity; optional
features include hollow or solid feet, half-grid foot placement, magnet
pockets, dividers, label tabs and scoops. The controls correspond to the
[Gridfinity Bin Generator](https://sitnikov.github.io/gridfinity-bin-generator/)
options; this body uses this repository's Gridfinity foot and independently built
PETG geometry. Its 0.6 mm flat landing strip supports the separate
`drill_storage.bin.lid` with a locating skirt. The lid lifts off rather than
snapping shut; it is not sealed. It receives matching full or half Gridfinity
feet in a 2.5 mm socket on its exposed face. See the
[empty-bin specification](docs/empty-bin-specification.md), the
[accepted body contract](docs/empty-bin-cad-contract.md), and the
[current lid contract](docs/lid-cad-contract.md).

`grid_x` and `grid_y` accept half-cell increments. `half_grid_base` replaces
full feet with half-cell feet; otherwise `half_grid_right` and `half_grid_top`
choose which edge gets a partial foot. `ultra_light_base` hollows and braces
the feet. Magnet pockets are cut in full-cell feet only (requesting magnets
with `half_grid_base` is rejected); `magnet_diameter` is nominal and receives
a PETG sliding-fit allowance. `dividers_x/y` partition the cavity when
`dividers` is on. `labels`, `label_for_each_section`, `label_position`,
`label_width/depth`, and `ultra_light_labels` control inward label tabs.
`scoops` and `scoop_radius` add curved retrieval ramps at each Y section's
floor. Labels and scoops are off by default; they consume interior space.

`lid_height` is the **whole print-part height in millimetres**, default 6.5 mm:
2.5 mm socket depth, 1 mm roof above it, and a 3 mm plug skirt below the
bin rim. Raising it thickens the roof; it does not deepen the skirt and foul
labels or dividers. The 1 mm body wall and lid skirt have a PETG sliding fit.
Interior fixtures stop 3.6 mm below the rim to leave room for the skirt.
The lid is printed **top-down, skirt up**. Each socket includes its own
breakaway lattice; remove it and the four small attachment nibs before
stacking. `drill_storage.bin` shows the closed two-part scene **after**
support removal; export the two leaf models separately to print them.

## Stackable cover option

Each of the five sets also offers `<set>.cover_stackable`: a separate cover that
snaps onto the same collar as the smooth cover and seats the lower 2.5 mm of
another 1×1 Gridfinity foot. It preserves the 41.5 mm side-by-side footprint.
The socket has a sliding PETG fit and a lead-in; the stacked foot's upper bevel
remains visible above the lid. Keep the smooth cover if stacking is not needed.

The stackable lid prints **socket-down, mouth-up**, with a shallow breakaway
lattice included under the socket ceiling. Remove the lattice and its four
small attachment nibs after printing, before stacking a holder. The extra
socket depth is included when sizing the roof, so the assembled height still
lands on a 7 mm Gridfinity unit without sacrificing tip clearance; some sets
grow by one unit. See [the accepted stackable-cover specification](docs/stackable-cover-specification.md)
and [the current CAD contract](docs/stackable-cover-cad-contract.md).

## Printing

The existing smooth parts need no supports. Every part comes off `create()` in
its print pose; stackable covers include their own removable support lattice.

- **Base — ASA**, foot down, cavity up. 36 mm tall. ASA wants an enclosure; a
  42 mm footprint is not fussy, but a draught will still lift the foot's corners.
- **Cartridge — TPU**, top face down, bores down. 8 mm tall, every bore a through
  hole, so nothing to bridge and nothing to drain. Keep the perimeter count up:
  the grip land *is* a perimeter, and its diameter is the whole fit.
- **Cover — PETG**, pillow top on the bed, mouth up.

Cover heights are quantised: `cover_height_for()` picks the smallest whole
Gridfinity Z unit (7 mm) that still swallows the longest tool standing on the
base floor, so the assembled holder always sits on a unit boundary — 19U for
wood, 20U for metal, 23U for stone. **The covers are interchangeable**, because
every base keeps the same seat height; a taller one simply leaves more air.

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
