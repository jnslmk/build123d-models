# Drill Storage

Gridfinity drill holders: a bored 1×1 base with a tall labelled cover that snaps
over it, one holder per tool set, all cut from a single engine.

```bash
uv run show drill_storage                    # the engine's demo set
uv run show drill_storage.wood               # 2-10 mm brad-point set + countersink
uv run show drill_storage.metal              # 1-10 mm HSS twist set + hex tap
uv run show drill_storage.hex                # 16-piece 1/4" hex-shank bit set
uv run show drill_storage.assemblies.wood    # the wood set with drills standing in it
uv run show drill_storage.flex               # ASA shell + TPU cartridge, same wood set
uv run export drill_storage.wood             # STLs for the slicer (base + cover)
```

## Layout

| module | what it is |
|---|---|
| `box.py` | **The engine.** Constants, hole packing, rib geometry, wall legends, `create_base` / `create_cover`. Not a model. |
| `sampler.py` | `drill_storage` — three covers and two graduated bases, so the engine is showable without picking a tool set. |
| `wood.py` | `drill_storage.wood` — 2-10 mm brad-point set plus a 10 mm hex-shank countersink. |
| `metal.py` | `drill_storage.metal` — 1-10 mm HSS twist set plus a 10 mm hex tap. |
| `hex.py` | `drill_storage.hex` — 16-piece ¼″ hex-shank bit set, 8 long + 8 short. |
| `assemblies/wood.py` | `drill_storage.assemblies.wood` — a scene, not a print job: every drill standing in its bore under a translucent cover. |
| [`flex/`](flex/README.md) | `drill_storage.flex` — the same wood set as a rigid **ASA shell** plus a compliant **TPU cartridge**. No ribs: TPU is the spring, so the grip is a short land instead. Reuses this engine's foot, collar, snap and cover. |

A holder module supplies a drill list, a cover label and (for a short set) a
cover height. Everything else — where the holes go, how big the ribs are, what
gets engraved on which wall, which way up each part prints — is solved in `box`.
Adding a tool set is a new module of about sixty lines; edit `DRILL_DIAMS` and
the layout re-packs itself.

## How the parts hold together

**Base → cover.** A 41.5 mm body steps down to a 35 mm collar that plugs into
the cover's bore on a 0.4 mm diametral slip fit, and a ramped bead inside the
cover clicks into a rounded groove on the collar. The bead is asymmetric on
purpose: a long gentle lead-in below the tip so the cover slides on
progressively, a shorter steeper face above so it still detents going in.

**Bore → drill.** Bores do not grip on a close-fitting wall. Three compliant
ribs stand into each bore and hold the bit on its plain shank at a measured
diametral interference. A rib is a spring; a tight cylinder is a jam, and it
also has to survive the printer's own error on a 2 mm hole.

## The interference is measured, not calculated

`box.grip_for(d)` is the production law, and it is not a constant: small bores
print their ribs short, so below 5 mm the grip ramps up along a measured table
(`RIB_GRIP_SMALL`) rather than a formula. Every entry in that table came off a
printed coupon.

The coupons are the sibling package, [`models/drill_fit_tester`](../drill_fit_tester/README.md).
Print those before re-cutting a holder — a bar takes twenty minutes and a holder
takes eight hours.

## Printing

PETG, no supports.

- **Base** — bores up, flat on the foot. Every bore mouth carries a 45° lead-in
  chamfer cut as a boolean cone, not an OCC fillet: filleting a ribbed mouth is
  unreliable, and a failed fillet corrupts the builder so every later one fails
  silently too.
- **Cover** — pillow top on the bed, mouth up. `create_cover` already returns it
  that way, so the STL drops straight into the slicer.

Cover heights are quantised: `cover_height_for()` picks the smallest whole
Gridfinity Z unit (7 mm) that still swallows the longest drill standing on the
bore floor, so the assembled holder always sits on a unit boundary.
