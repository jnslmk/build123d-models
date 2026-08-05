# drill_storage.flex — ASA shell + TPU cartridge

A two-material version of the Gridfinity drill holder. Same 1×1 footprint, same
collar, same cover as [`drill_storage.wood`](../wood.py) — split into a rigid
half and a compliant half:

| Part | Model | Material | Job |
| --- | --- | --- | --- |
| Shell | `drill_storage.flex.shell` | ASA | Gridfinity foot, collar, cover snap groove, engraved legend, **and the guide bores** (free fit, 24.8 mm). Keeps drills straight. |
| Collar | `drill_storage.flex.insert` | TPU | A short 12.4 mm collar at the top. Grips, on a 3.5 mm land. Nothing else. |
| Cover | `drill_storage.wood` | ASA / PETG | Unchanged — see below. |

`uv run show drill_storage.flex` shows all three assembled with the drill set in
place.

## What it fits

The `drill_storage.wood` set: eleven brad-point drills, 2 – 10 mm
(2, 2.5, 3, 3.5, 4, 5, 6, 7, 8, 9, 10), plus a 10 mm countersink on a 6.3 mm hex
shank. Edit `DRILL_DIAMS` in `../wood.py` and the layout re-packs itself for both
halves at once — they share one call to `layout_bores`, so they cannot disagree
about where a hole is.

**An already-printed wood cover fits this shell.** The shell keeps `BORE_FLOOR_Z`
and `FOOT_TOP` exactly where the PETG base has them, so `cover_height_for` still
returns 109 mm (19U assembled). `checks.py` asserts this rather than trusting it.

## Why there are no ribs

The PETG base grips each drill on three compliant beads, and
[`box.py`](../box.py) lines 187–286 record the two printed generations it took to
get there. TPU makes that machinery pointless — the material is the spring.

What does *not* follow is a plain deep interference bore. Retention is friction ×
contact area, and TPU on steel runs μ ≈ 0.5–0.9. A full-circle interference bore
over the old 14 mm rib zone reaches tens of kgf at any interference big enough to
model; the interference that would give a pleasant ~1 kgf is about 0.01 mm
diametral, finer than FDM can hold. Where PETG had no number loose enough, TPU
has no printable number tight enough.

So the bores are plain and round, and the **contact** is what got shortened: a
3.5 mm grip land, with everything else relieved. Three ribs over 14 mm and one
full circle over 3.5 mm have comparable contact area.

Guiding and gripping then split cleanly by material. The ASA below is bored
**loose** (`GUIDE_FIT`, +0.25) over 24.8 mm and holds the drill upright; the TPU
collar above is cut **tight** (`LAND_FIT`, -0.10) over 3.5 mm and holds it in
place. `checks.py` asserts that ordering, because a guide that gripped or a land
that cleared would each defeat the split silently. Full argument, with the
numbers, in [`config.py`](config.py) and [`docs/design-notes.md`](docs/design-notes.md).

## ⚠ The grip is not calibrated yet

`LAND_FIT` and `HEX_LAND_FIT` are **modelled nominal** — the argument being that
FDM's own 0.1–0.3 mm hole undersize supplies the interference. That is a starting
point, not a measurement. `models/lib/fits.py` models rigid-plastic *clearance*
fits and says nothing about an elastomer squeezing a steel shank.

Before committing a whole cartridge:

```bash
uv run export drill_fit_tester.land     # five bars: -0.10 .. +0.30
```

Print it **in TPU**, judge which bar holds a drill against a shake but releases to
a straight pull, set `LAND_FIT` accordingly, and write the judgement down in
`docs/design-notes.md`. `RIB_GRIP` took three rounds of exactly this, and both
holder generations printed before it were wrong.

## Printing

Both parts come off `create()` already in print pose. No supports anywhere.

**Shell — ASA**, foot down, cavity up.
ASA wants an enclosure; a 42 mm footprint is not fussy, but a draught will still
lift the foot's corners. ~20 cm³.

**Collar — TPU**, flat bottom down, bores up. ~11 cm³ and 12.4 mm tall. Every bore
is a through hole, so there is nothing to bridge and nothing to drain. Keep the
perimeter count up: the grip land is a perimeter, and its diameter is the whole
fit.

## Assembly

1. Drop the cartridge into the shell, **key rib on the +X face** lined up with the
   slot in the cavity wall. It only goes one way — that is the rib's job, because
   the shell's engraved legend is only true in one orientation.
2. Push it down until the retention bead clicks into the groove near the top.
   It takes a squeeze; TPU compresses 0.44 mm of engagement without complaint.
3. Drills go in shank first, pass clean through the collar, and bottom out on the
   shell's **ASA** floor 24.8 mm below — soft plastic creeps under a point load.

To swap sets, pinch the 1.2 mm of collar standing proud of the shell rim and pull.
The bead is a rounded pocket designed to release. Note that the *guide* bores live
in the shell, so a genuinely different drill set needs both halves reprinted — the
collar alone only re-does the grip.

**Check the small drills first.** The land sits at world z 30.8–34.3. On the
brad-point lengths this set assumes, every size grips plain shank with ≥ 2.7 mm to
spare; on DIN 338 jobber lengths the 2, 2.5 and 3 mm bits would be gripped partly
on their *flutes*, whose hardened spurs broach a grip feature away permanently.
The table and what to do about it are in `docs/design-notes.md`.

## Why the bores are packed tighter than the PETG base's

The shell wall costs bore space twice over — the PETG base packs into 34.8 mm,
this one into 32.1. That is the price of the split, and it is why `SHELL_WALL` is
1.6 mm and not 2.0: at 2.0 the packer runs out of vertical room and silently
compresses the rows until the 6 mm and 9 mm bores are 0.59 mm apart, thinner than
a printable wall, in the softest material in the model.

`pack_rows` only warns about *horizontal* overpacking, so nothing complains about
that — which is exactly why `checks.py` measures every bore pair itself.

## Checks

```bash
uv run check drill_storage.flex
```

Point-samples the solid rather than eyeballing a projection: the land radius and
the relief radius on every bore, both grooves' remaining wall, every bore-to-bore
gap, the key, the bead engagement, and the cover-height identity. It also runs
the sharp-edge audit — the cartridge passes with **no exceptions at all**, and the
shell's three are named in `check_sharp_edges` with their reasons.
