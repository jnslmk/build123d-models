# LED PSU Enclosure

A weatherproof enclosure for a complete 24 V addressable-LED driver stack: a
Mean Well RSP-320-24, an Athom/IoTorero Ethernet WLED ESP32 controller, a 4-way
blade-fuse block (one fuse per output) and four Weipu SP1712 output connectors.

**Sealed by default, ventable on demand.** The RSP-320-24 sheds ~40 W at full
load and derates from 50 °C ambient, so a permanently sealed box would be fine at
half load and marginal above it. Rather than guess, both end walls carry an
identical port: a blanking plug makes the box sealed, and a louvre or fan
cartridge clicks into the same opening if the PSU runs hot in service.

```bash
uv run show led_psu_enclosure                # closed assembly, contents visible
uv run show led_psu_enclosure.tray           # a single part (.lid .shelf .plate .vent)
uv run export led_psu_enclosure.printable    # <- STLs for the slicer
uv run python -m models.led_psu_enclosure.checks   # geometry assertions
```

**Export `led_psu_enclosure.printable`, not `led_psu_enclosure`.** The plain name
is the *assembled* view and includes the component mocks as children, so
`export.py` will happily write you an STL of a fake power supply.

`create()` is the closed assembly, `create_open()` drops the lid,
`create_print_layout()` spreads the printed parts, `create_mocks_only()` shows
just the contents.

---

## Printed parts

| Part | Size (mm) | ASA |
|---|---|---|
| `tray` | 235 × 144 × 121.5 | ~496 g |
| `lid` | 235 × 135 × 16 | ~218 g |
| `psu_plate` | 216 × 116 × 4 | ~101 g |
| `shelf` | 218 × 118 × 4 | ~92 g |
| `vent_blank` ×2 | 89.4 × 55.4 × 15.5 | ~29 g ea |
| `vent_louvre` / `vent_fan` | 89.4 × 55.4 × 15.5 | optional |

**~1.0 kg total.** Interior is 228 × 128 × 118 mm. The lid **snaps into the
mouth** — no flange, no screws, sides flush with the walls. One perimeter bead
cannot crush the gasket the way 14 screws did: behind the plug labyrinth the
joint is a dust/splash seal, not an IP65 crush.

> **Printer:** everything is ≤ 235 mm across, so this fits the **Centauri
> Carbon** (256 mm) now.

## Bought parts

| Qty | Item | Notes |
|---|---|---|
| 1 | Mean Well RSP-320-24 | 215 × 115 × 30, 4 × M4 bottom on 150 × 50 |
| 1 | Athom / IoTorero Ethernet WLED ESP32 | 102 × 65 × 22, 2 × Ø4 at 110 mm |
| 1 | LXD-4P 4-way blade-fuse block | 86.2 × 53 × 41.7, 2 × Ø5.2 at 76.5 mm |
| 4 | Weipu **SP1712** rear-nut 3-pin socket | + 4 × SP1710 cable plugs |
| 1 | IP68 panel-mount RJ45 coupler | Ø22 panel hole |
| 1 | Cable gland | **see the warning below** |
| ~1 m | 3 mm silicone O-ring cord | butt-joined with CA, or a formed-in-place RTV bead |
| 4 | M3 heat-set inserts (Ø4.2 × 5.8) | PSU plate, in the floor bosses |
| 4 | M4 × 8 | PSU to plate — **no longer, see below** |
| 4 | M3 × 12 | plate to floor |
| 2 | M4 × 16 + nyloc | fuse block to shelf |
| 2 | M3 × 16 + nyloc | controller to shelf |
| 4 | M3 × 10 self-tapping | vent cartridges |
| 1 | 40 × 40 × 10 fan (optional) | only for `vent_fan` |

### ⚠ Check your gland before ordering

An **M12 gland clamps 7.8 mm maximum.** H05VV-F 3G1.5 mains flex is ~9.5 mm OD
and **will not fit**; only 3G0.75 (~6.8 mm) does. 320 W at 230 V is ~1.4 A so
0.75 mm² is fine electrically, but **M16 (5–10 mm clamp) is the safer choice**.
`GLAND_HOLE_D` in `config.py` is a parameter — change it to 16.5 and reprint if
you go that way.

### ⚠ The PSU's bolt holes take 3 mm of screw, no more

`PSU_BOLT_MAX_DEPTH`. The plate is counterbored so an M4 × 8 lands correctly.
A longer screw will bottom out inside the power supply.

---

## Assembly order

1. **Heat-set the inserts** — 4 × M3 in the floor bosses.
2. **Bolt the PSU to `psu_plate`** from underneath, M4 × 8, countersunk side down.
3. **Drop the plate in** onto the four floor bosses, M3 × 12.
4. **Fit the wall parts** — 4 × SP1712 (flat side **up**), the RJ45 coupler and
   the gland. The SP1712 pockets bring the local panel to 2.85 mm, inside the
   3 mm spec limit; the rear nuts tighten from inside.
5. **Wire it** — mains in via the gland to PSU terminals 1/2/3 (L/N/FG); PSU
   +V (7–9) to the fuse block feed; each fused output to one SP1712 pin; −V (4–6)
   common. The controller takes its DC from the PSU and drives the data pins.
6. **Bolt the fuse block and controller to `shelf`**, then drop the shelf onto
   its ledge. It lifts straight back out to reach the PSU terminals and the
   `+V ADJ` trimmer.
7. **Gasket** — press 3 mm silicone cord into the rim groove, cut to length,
   butt the ends with a drop of CA. (Or lay an RTV bead and let it cure against
   an oiled lid.)
8. **Fit the vent blanks**, gasket side in, click, then two screws each.
9. **Lid on** — press straight down around the perimeter until the snap bead
   clicks. To open, pry gently at a corner and work along an edge.

## Print settings

- **ASA** (or ABS if it will be shaded — ASA holds up far better in UV). **Not
  PLA**: internal air reaches ~55–65 °C at high load and PLA creeps. PETG is a
  distant third.
- **≥ 4 perimeters, ≥ 5 top/bottom.** Watertightness comes from wall count and
  good layer bonding, not from thickness alone.
- No supports needed anywhere — every overhang is 45° or a bridge by design.
- The tray is a big ABS/ASA part: heated chamber, brim, and don't open the door.
- Optional: a wipe of epoxy or acetone on the *outside* of the tray closes any
  residual layer porosity. Do **not** acetone-smooth near the vent latches.

## Print a test coupon first

Before committing to a ~10 h tray print, print a small section carrying one
SP1712 cutout with its counterbore, a piece of the rim with the gasket groove
and snap bead, and one vent latch. That proves the connector fit, the panel thickness and the
snap force for the cost of half an hour.

## Thermal guidance

| Load | Roughly | Recommendation |
|---|---|---|
| ≤ 50 % (≤ 160 W) | ~20 W of heat | Sealed. Both blanks in. |
| 50–75 % | ~30 W | Fit `vent_louvre` in both ports (≈ IP54). |
| > 75 % | ~40 W | `vent_louvre` low + `vent_fan` high. |

The low port is at the terminal end and the high port is over the PSU's top-cover
fan, so a fitted pair gives real cross-flow rather than one hole doing nothing.
The shelf is slotted so the plenum below it stays connected to the high port.

---

## Layout, and why it is shaped this way

See `docs/design-notes.md` for the reasoning and `docs/part-data.md` for the
researched component dimensions with sources. The short version:

The PSU is 215 × 115 in a 228 × 128 interior — it comes within 6.5 mm of every
wall, so **no wall at PSU height can host a connector** (an SP1712 needs 19.7 mm
behind the panel). The whole layout follows from resolving that: the shelf sits
25 mm above the PSU so the top-cover fan has a plenum, the connectors go in the
front wall at shelf height, and everything mounted on the shelf is held 36 mm
back from that wall so the connector bodies have somewhere to be.

## Verifying changes

`checks.py` point-samples the solids rather than trusting a projection — it
verifies the SP1712 panel thickness against the 3 mm spec limit, that the D-flat
is oriented up (so it prints as a bridge), that every insert pocket is blind,
that the gasket groove is continuous, that the lid's snap bead engages the rim
groove without welding, that every internal part fits *through the rim opening*,
and that nothing collides with anything. Run it after any change to `config.py`.
