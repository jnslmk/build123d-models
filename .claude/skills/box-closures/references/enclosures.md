# Enclosure numbers around the closure

The closure sits inside a box, and the box has its own minimums. These are the
general figures; the closure joint itself is in `SKILL.md`.

## The baseline numbers

All from the Protolabs Network enclosure design guide
(<https://www.hubs.com/knowledge-base/enclosure-design-3d-printing-step-step-guide/>):

| Feature | Number |
| --- | --- |
| Minimum wall thickness | **2 mm** for all enclosure walls |
| Clearance around internal components | **0.5 mm** all round, for distortion, shrinkage and printer tolerance |
| Port / plug cut-outs | **2 mm total, 1 mm per side** |
| Ribs and gussets | **75–80 % of the wall thickness** |
| Wall around a threaded hole or boss | **≥ 1× the fastener diameter** (M5 → 5 mm of wall around the hole) |
| Locating lugs | **≥ 5 mm wide** |
| Screw clearance holes | fastener Ø **+ 0.25 mm** |
| Self-tapping holes | fastener Ø **− 0.25 mm** |

Two of these interact with the closure directly:

- **The 0.5 mm component clearance is not the closure clearance.** It is slack around
  a bought part. Joint clearances are 0.15–0.4 mm and get calibrated — see
  `fdm-fits-and-clearances`.
- **Ribs at 75–80 % of wall** matter because a rib meeting a lid-seat shoulder is a
  thick junction that will sink. Keep ribs clear of the sealing face.

## Where this repo goes thicker, and why

`models/led_psu_enclosure/config.py` runs `WALL = FLOOR = 3.5` rather than 2 mm,
commented as "4 perimeters at a 0.4 mm nozzle -> watertight-capable". That is the
rule from Prusa's watertight guide — for water-tightness you raise the *perimeter
count*, not the infill
(<https://blog.prusa3d.com/watertight-3d-printing-part-2_53638/>). 2 mm is the floor
for a dry box; a sealed one wants the wall that buys you four perimeters.

Its other whole-box constants, for reference:

| Constant | Value | Role |
| --- | --- | --- |
| `CORNER_R` | 6.0 mm | vertical corner fillet — fillets suit vertical edges |
| `RING_CHAMFER` | 0.8 mm | 45° chamfer on exterior horizontal rings |
| `LEAD_IN` | 0.6 mm | chamfer at bore mouths |
| `INNER_FILLET` | 3.0 mm | wall-to-floor internal fillet, crack relief |

Edge treatment is not decoration here: the bottom-ring chamfer doubles as
elephant's-foot relief, and the internal wall-to-floor fillet is the crack-initiation
fix. The full rationale is the "Edge design for FDM" section of `AGENTS.md`.

## The trap: the mouth is narrower than the interior

Any closure that thickens the wall near the rim — a rabbet lip, a gasket land, a snap
groove band — **shrinks the opening**. A part that fits the interior can then be
impossible to get in.

`config.py` makes this explicit rather than leaving it to be discovered after a
14-hour print:

```python
RIM_WALL = 7.0    # wall thickness over the top band (grows inward)
RIM_BAND_H = 15.0 # height of that thickened band

def installable_x() -> float:
    """Clear opening at the rim -- the real limit on anything fitted inside."""
    return INTERIOR_X - 2 * (RIM_WALL - WALL)
```

With `INTERIOR_X = 228` and `WALL = 3.5`, the real opening is 221 mm, not 228. Every
internal part — shelf, PSU plate — is sized against `installable_*()`, not against
`INTERIOR_*`, and the shelf takes a further `SHELF_DROP_CLEAR = 1.5` mm per side to
drop through.

Do the same in any box whose rim thickens: expose the clear opening as a derived
function, size internals from it, and assert it in a check.

## Sequence

1. Measure the contents. Add 0.5 mm all round.
2. Choose the closure (`SKILL.md` decision table) — it sets the wall budget.
3. Set the wall: 2 mm minimum, more if sealed or load-bearing.
4. Check the *clear opening* after the closure thickens the rim, not the interior.
5. Cut ports at +1 mm per side; keep them clear of the sealing face and the corner
   fillets.
6. Edge treatment: chamfer horizontal rings, fillet vertical corners, fillet the
   wall-to-floor internal corner.
