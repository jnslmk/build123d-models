# Drill Storage

Gridfinity drill holders, one per tool set. Each is three printed parts in three
filaments: a rigid **ASA shell** that guides, a compliant **TPU cartridge** that
grips, and a tall labelled **PETG cover** that snaps over the collar.

```bash
uv run show drill_storage               # the family: three shells, three covers
uv run show drill_storage.wood          # 2-10 mm brad-point set + countersink
uv run show drill_storage.metal         # 1-10 mm HSS twist + tap + step drill
uv run show drill_storage.stone         # 3-10 mm carbide masonry set
uv run show drill_storage.hex           # 16-piece 1/4" hex-shank bit set
uv run export drill_storage.wood.shell  # STL + STEP for the slicer
uv run check drill_storage.wood         # geometry assertions for one set
```

## Layout

| module | what it is |
|---|---|
| `box.py` | **The engine.** Gridfinity constants, hole packing, wall legends, `create_cover`, and the one-material `create_base`. Not a model. |
| `config.py` | Every clearance, shared by all three sets: the guide fit, the land fit, the relief, the snap. No geometry. |
| `sets.py` | **The three sets**, side by side: sizes, lengths, cover label, shank allowance. The only thing a variant decides. |
| `freepack.py` | The layout solver for the one set `pack_rows` cannot lay out in rows. Run by hand; its answer is frozen in `sets.py`. |
| `shell.py` / `insert.py` / `cover.py` | The three parts, set-agnostic. Hand them a `DrillSet`. |
| `assembly.py` / `sampler.py` | The scenes: one set assembled, and all three side by side. |
| `tools.py` | Display models of the bits themselves, for those scenes. Not printed. |
| [`wood/`](wood/README.md) [`metal/`](metal/README.md) [`stone/`](stone/README.md) | One package per set: the assembled scene, plus `shell`, `insert` and `cover` as their own downloadable models. Four modules of naming each. |
| [`hex/`](hex/README.md) | `drill_storage.hex` — the two-material 16-piece ¼″ driver-bit set: rigid base + TPU insert + translucent cover. Both boxes: the ALLEN 1x1 keeps 8 sockets, the BITS 2x2 spreads 16 across a 4x4 grid. |

Adding a fourth set is a `DrillSet` in `sets.py` and a package copied from
`wood/`. Nothing in the geometry has to know about it.

## How the parts hold together

**Shell → cover.** A 41.5 mm body steps down to a 39.2 mm collar that plugs into
the cover's bore on a 0.4 mm diametral slip fit, and a ramped bead inside the
cover clicks into a rounded groove on the collar. The bead is asymmetric on
purpose: a long gentle lead-in below the tip so the cover slides on
progressively, a shorter steeper face above so it still detents going in.

**Shell → cartridge.** The cartridge drops into a 6.8 mm cavity at the top of the
shell and clicks in on its own bead — outward, on the TPU, so seating it costs a
squeeze rather than deflecting an ASA wall. A key rib on the +X face means it
only goes in one way round, which is what makes the shell's engraved legend true.

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
for a shell.

## Printing

No supports anywhere. Every part comes off `create()` in its print pose.

- **Shell — ASA**, foot down, cavity up. 36 mm tall. ASA wants an enclosure; a
  42 mm footprint is not fussy, but a draught will still lift the foot's corners.
- **Cartridge — TPU**, top face down, bores down. 8 mm tall, every bore a through
  hole, so nothing to bridge and nothing to drain. Keep the perimeter count up:
  the grip land *is* a perimeter, and its diameter is the whole fit.
- **Cover — PETG**, pillow top on the bed, mouth up.

Cover heights are quantised: `cover_height_for()` picks the smallest whole
Gridfinity Z unit (7 mm) that still swallows the longest tool standing on the
shell floor, so the assembled holder always sits on a unit boundary — 19U for
wood, 23U for metal and stone. **The covers are interchangeable**, because
every shell keeps the same seat height; a taller one simply leaves more air.

## Assembly

1. Drop the cartridge into the shell, **key rib on the +X face** lined up with
   the slot in the cavity wall. It only goes one way.
2. Push until the retention bead clicks into the groove near the top. It takes a
   squeeze; TPU compresses 0.44 mm of engagement without complaint.
3. Bits go in **shank first**, pass through the collar, and bottom out on the
   shell's ASA floor 23.2 mm below — soft plastic creeps under a point load.

To swap sets, pinch the 1.2 mm of cartridge standing proud of the shell rim and
pull. Note that the guide bores live in the shell, so a genuinely different set
needs both halves reprinted; the cartridge alone only re-does the grip.
