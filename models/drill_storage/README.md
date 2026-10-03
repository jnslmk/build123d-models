# Drill Storage

Gridfinity drill holders, one per tool set. The original upright holders have
a rigid **ASA base** that guides, a compliant **TPU cartridge** that grips,
and a tall labelled **PETG cover** that snaps over the collar. The separate
sideways wood and metal holders also use three individually printable parts:
a single-foot ASA guide, a keyed TPU grip cartridge, and a foot-bearing,
side-removable PETG cover that slides over a broad ASA collar. WOOD / METAL is
engraved on each cover; individual sizes and CSK / TAP / STEP are mapped on
the guide's rear face. Full-depth top sockets align with all feet for a 5U
stacking pitch; their fit, thin lips and stack strength await a print trial.

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
uv run view drill_storage.dremel.cover_stackable  # alternate 1×2 PETG cover
uv run export drill_storage.dremel.cover_stackable  # sockets down; built-in support on
```

## Layout

| module | what it is |
|---|---|
| `box.py` | **The engine.** Hole packing, wall legends, `create_cover`, and the one-material `create_base`. Not a model. |
| [`models.lib.gridfinity`](../lib/gridfinity.py) | Shared standard dimensions, `gridfinity_foot(size_x=PAD, size_y=PAD)` and `gridfinity_foot_cavity(size_x, size_y, wall, bottom, seams, seam_chamfer=0.2)`. The existing ruled profiles are unchanged; `seams` is ordered −X, +X, −Y, +Y. |
| `config.py` | Every clearance, shared by all three sets: the guide fit, the land fit, the relief, the snap. No geometry. |
| `sets.py` | **The drill sets**, side by side: sizes, lengths, cover label, shank allowance. The only thing a variant decides. |
| `freepack.py` | The layout solver for the one set `pack_rows` cannot lay out in rows. Run by hand; its answer is frozen in `sets.py`. |
| `base.py` / `insert.py` / `cover.py` | The three parts, set-agnostic. Hand them a `DrillSet`. |
| `assembly.py` / `sampler.py` | The scenes: one set assembled, and all three side by side. |
| `tools.py` | Display models of the bits themselves, for those scenes. Not printed. |
| [`wood/`](wood/README.md) [`metal/`](metal/README.md) [`stone/`](stone/README.md) | One package per drill set: the assembled scene, plus `base`, `insert` and `cover` as their own downloadable models. Four modules of naming each. |
| `cover_stackable.py` (in each set package) | Alternate PETG cover with a full-depth Gridfinity foot socket: one-piece with removable support by default, or separately printed glue-on lips. |
| [`allen/`](allen/README.md) [`hex/`](hex/README.md) | The two 1/4" hex-shank sets, sharing one geometry: `drill_storage.allen` is the 1x1 ALLEN key box (8 sockets), `drill_storage.hex` the 1x1 driver-bit box (16 sockets in a 4x4 grid, shaved lead-in clearances). Both rigid base + TPU insert + translucent cover. |
| [`bin/`](bin/) | Parametric general-purpose PETG bin, independently printable body and lift-off stackable lid, plus a seated display scene. |
| [`dremel/`](dremel/) | Independent 1×2 three-part Dremel variant: ASA base, TPU insert, smooth labelled PETG cover and a separate stackable cover option; the closed inspection scene retains the smooth cover. |
| `sideways.py` / `sideways_insert.py` / `sideways_cover.py` / `sideways_checks.py` | Shared horizontal wood/metal guides, keyed TPU grip cartridges, foot-bearing collar-over-base covers, rear-face tool maps and one 4.4 mm stacking receiver per cell. Each `sideways` package is the assembled scene, with separate `.base`, `.insert` and `.cover` prints and an open `.preview`; see the [sideways specification](docs/sideways-specification.md) and [current CAD contract](docs/sideways-cad-contract.md). |

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

**Bin lid → bin.** The lid's 3 mm skirt plugs into the bin's cavity on a 0.22 mm
diametral sliding fit, and a ramped bead on the skirt's outer wall clicks into a
groove in the bin's inner wall. The bead is on the compliant skirt — a thin PETG
tube that flexes inward — and the groove is on the rigid 1 mm bin wall, so the
snap costs a gentle squeeze rather than deflecting the bin. The bead's lead-in
ramp is on the insertion side so the lid slides on progressively; its 45°
retention face detents without being a knife edge.

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
perimeters with a small reserve). The 1×2×5U (35 mm body height) default has a closed 1 mm plate
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
`drill_storage.bin.lid` with a locating skirt. The lid snaps shut on a
bead-and-groove detent; it is not sealed. It receives matching full or half
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
to on, adding a connected sacrificial lattice and rounded perimeter backing
rail beneath each socket. The bin-lid support revision uses two weak tabs
at straight rail midpoints: reach through the open socket to cut these,
then peel the rail/lattice inward without levering against the finished rim.
Trim any roof-side remnants without altering the foot seat before stacking.
The 0.4×0.8 mm tabs, 0.6 mm per-side wall separation and retained 0.2 mm
roof gap are **print-trial candidates**, not proven calibrated PETG settings.
The recorded 0.4 mm-nozzle / 0.2 mm-layer PETG slice preserves the gaps and tabs;
easier removal and reduced short-side sag still await physical trials.
Family rollout waits for acceptance of this bin-lid anchor. Turn `support`
off to export the unchanged clean socket for slicer supports or a
printer-verified unsupported approximately 37 mm bridge. The bin base is displayed black
and the lid translucent, matching the other drill-storage sets; STL carries
geometry only, not color. `drill_storage.bin` shows the closed two-part scene
after support removal; export the two leaf models separately to print them.

## Dremel tool holder

`drill_storage.dremel` is a closed inspection scene of three separately
printable parts: a rigid ASA guide base, a removable TPU grip insert, and a
translucent PETG cover for tools up to 50 mm long. It is not an STL print job;
export the `.base`, `.insert`, and `.cover` leaf models separately.

The 1×2 base has 55 positions in six columns at 6 mm horizontal pitch.
Rows are 7 mm apart within each foot, with no sockets over the gap between
the two feet. The ASA guide floor is z=3; the flat cover seat remains z=24.
Nominal diameters run in ascending x-major groups:
1.0 mm ×1, 1.5 mm ×1, 2.0 mm ×1,
2.35 mm ×10, 2.9 mm ×25, and 3.1 mm ×17. These include the owned
inventory of 1, 1, 1, 6, 21, and 11 tools respectively, plus 14 spare
positions: four at 2.35 mm, four at 2.9 mm, and six at 3.1 mm.
The ASA guides and matching TPU through-bores use the family's
diameter-dependent small-bore compensation; each TPU bore retains its
short gripping land and relieved upper section. The 8 mm cartridge's
outward retention bead snaps into the base's inner groove and it can be
lifted from its proud rim. The repacked base requires its matching new TPU
insert; the previous 5×11 insert is incompatible. Retention and snap interfaces remain unchanged.

The labelled PETG cover snaps over the base's rectangular collar and sits
flush with the full-width body. Its assembled top is 10U (70 mm), giving
15 mm clearance above a 50 mm tool standing on the lowered guide floor. It prints
pillow-top down with its open mouth up; the inverted print-pose lettering
reads upright when the cover is seated. All three parts require individual
prints in their specified materials. Tool heads wider than the 6 mm horizontal
pitch can prevent filling every one of the 55 positions simultaneously. The user
accepted the purpose, inventory and spare allocation on 2026-09-30.
The updated assembly gate verifies all bore sizes, guide floors and seated
non-interference; the CAD contract records the evidence. Printed TPU grip
and cover snap effort/durability remain to be calibrated.

The separate `drill_storage.dremel.cover_stackable` retains the smooth cover's
label and snap, ASA base and TPU insert. Its two full-depth 4.4 mm sockets
are centred at Y=−21 and +21 mm; only its top lip grows to 42×84 mm.
The assembled top is z=60.4 mm, giving an 8U (56 mm) stack pitch when the
upper feet seat fully; a 2 mm roof remains below the sockets, with 1 mm
nominal headroom above a 50 mm tool on the 3 mm floor.
Print **socket-down, mouth-up** in PETG. Its `support` checkbox defaults to
on and reuses the family's removable breakaway lattices. Remove both lattices
and all attachment nibs before stacking; turn support off only for slicer
supports or a printer-verified unsupported bridge. The approximately
**0.14 mm mouth walls** are a user-accepted experimental print-trial exception,
not proven printable or durable. Check the sliced walls, printed foot fit,
stack strength and neighbouring-cell clearance before loading a stack.
The smooth `.cover` remains unchanged and support-free; the parent scene retains it.
The user accepted the lower floor, six-column layout, matching TPU insert and
8U stacking pitch. Reprint the ASA base and TPU insert together; the smooth
cover remains unchanged and compatible. Actual tool-head packing and the
1 mm nominal headroom still require a physical trial.
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

### Separate printable stacking lips

**Separate stacking lips** is an off-by-default checkbox on the five upright
`wood`, `metal`, `stone`, `allen`, and `hex.bits` stackable covers, the Dremel
stackable cover, and the bin lid. It does not apply to sideways holders.
The [accepted split-print decision](docs/stackable-cover-specification.md)
preserves the clean one-piece socket, stacking pitch, roof, labels and closure.

When enabled, the preview shows two XY-separated bed-seated parts and offers
two child STL download controls: **lid_body** and **stacking_lips**. This is
an exploded **print layout, not an assembled lid**; print the individual STLs.
Python callers can use `create(separate_stacking_lips=True)`; the existing
named-Compound export convention writes `<model>_lid_body.stl` and
`<model>_stacking_lips.stl`. `IS_ASSEMBLY` stays false. Disabling the checkbox
keeps the original one-piece Part and default-on support behavior.

Print both in PETG without built-in socket supports: the body has its flat
roof/glue face on z=0 and its mouth or skirt upward; the lips have their flat
glue face on z=0 and open sockets upward. The support checkbox is ignored in
this mode because no socket roof bridges during either print. Dremel and
multi-cell bin lips are one connected receiver field in one STL, not one
download per socket; the original webs hold their spacing. Inspect the slicer
for those webs and bed adhesion. Split printing does **not** thicken the
experimental ~0.14 mm tool-cover mouth walls or prove their printability.

For assembly, turn the body mouth/skirt-down so its flat roof faces up, keep
the lips socket-up, and dry-align the matching outer contours and rounded
corners. The tool-cover lips overhang their original body by 0.25 mm per side;
centre that overhang. Preserve the chosen half-cell socket arrangement on bin
lids; use the matching upper foot layout to check orientation and full seating
before gluing. Do not rotate an asymmetric lip field independently. Apply a
thin, even PETG-compatible adhesive film to the contacting flat ring/web faces,
keep adhesive out of the sockets, and hold alignment until fully cured. No
pins, rebates or adhesive-gap allowance are added. The ideal flat-on-flat
zero-gap assembly matches the clean original lid; a real adhesive bond line
adds its thickness to the stack height.
The measured planar bed-face area is **not** the bonded contact area: the lip
overhangs, and the Dremel body's retained pillow fillet narrows its flat roof
contact region. Apply adhesive only where the two planar faces actually meet.
CAD connectivity/equivalence proves an ideal joined shape, not bonded strength.

**Physical acceptance remains pending:** adhesive compatibility and cured
strength, printed flatness, thin-wall slicing/durability, neighbouring-cell
clearance and loaded-stack stability need a representative print/glue trial.
Do not load a stack based on CAD equivalence alone. Smooth covers remain the
support-free option requiring no glue.

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
