# LED PSU Enclosure

A weatherproof enclosure for a complete 24 V addressable-LED driver stack: a
Mean Well RSP-320-24, an Athom/IoTorero Ethernet WLED ESP32 controller, a 4-way
blade-fuse block (one fuse per output) and four Weipu SP1712 output connectors.

**Ventable with a thumb.** The RSP-320-24 sheds ~40 W at full load and derates
from 50 °C ambient, so a permanently sealed box is comfortable at light load and
not viable at heavy load. Rather than guess at print time, both end walls carry
an identical port with a **sliding shutter** in it: a louvred panel screwed in
once, and a slotted slider that runs in a channel on its face. Let the slider
down and the port is wide open; push it up half a slot pitch and it is shut. The
louvre slots are cut at 45°, so there is no straight-line path from outside to
inside even wide open.

**And a 24 V fan on the inside when that is not enough.** Convection through
those ports is worth under 2 W of the 40 W — the arithmetic is in
`docs/design-notes.md`, and it is the reason `vent_fan_yoke` exists: a printed
carrier that holds a 40 × 40 × 10 mm 24 V fan *behind* the high port's louvre,
so you get forced through-flow without giving up the labyrinth in front of it.
It runs straight off the PSU's own output terminals. Optional — the box works
without it, and the yoke is four screws.

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
| `tray` | 235 × 132 × 111.5 | ~446 g |
| `lid` | 235 × 132 × 16 | ~213 g |
| `psu_plate` | 216 × 116 × 4 | ~100 g |
| `shelf` | 215 × 115 × 4 | ~89 g |
| `vent_shutter` ×2 | 89.4 × 55.4 × 7.1 | ~14 g ea |
| `vent_slider` ×2 | 59.4 × 37.8 × 4.4 | ~4 g ea |
| `vent_fan_yoke` | 88 × 44 × 7.5 | ~11 g, optional |
| `vent_blank` / `vent_fan` | 89.4 × 55.4 × 15.5 | optional |

**~880 g fitted** (tray, lid, plate, shelf, two shutters, two sliders, yoke).
Outside is **235 × 132 × 111.5 mm**, interior 228 × 125 × 108. The lid **snaps
into the mouth** — no flange, no screws, sides flush with the walls. One
perimeter bead cannot crush the gasket the way 14 screws did: behind the plug
labyrinth the joint is a dust/splash seal, not an IP65 crush.

> **Printer:** everything is ≤ 235 mm across, so this fits the **Centauri
> Carbon** (256 mm) now.

### Where the size comes from

Nothing in the vertical stack is a chosen number — `config.interior_z()` takes
the tallest of three chains and rounds up, so the box is as short as its contents
allow and the trade-offs are visible in code rather than folklore:

| Chain | Height it demands |
|---|---|
| high vent port + internal fan → below the rim band | 105.0 |
| shelf → fuse block (41.7 mm) → 10 mm of finger room | **107.7 ← binds** |
| SP1712 counterbores → below the rim band | 101.5 |

X is not compressible at all: 215 mm of PSU + 5 mm of vent frame + 1.5 mm of
drop clearance at each end *is* the 228 mm interior. Setting `VENT_FAN_SIZE = 30`
re-derives a box ~5 mm shorter at the cost of roughly half the forced airflow.

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
| 4 | M4 × 8 | PSU to plate — **no longer, see below** |
| 2 | M4 × 16 + nyloc | fuse block to shelf |
| 2 | M3 × 16 + nyloc | controller to shelf |
| 4 | M3 × 10 self-tapping | vent shutters (2 per port) |
| 1 | **40 × 40 × 10 mm 24 V fan** (optional) | for `vent_fan_yoke` — runs off the PSU output |
| 4 | M3 × 10 self-tapping (optional) | yoke to the high port's frame |
| 4 | M3 × 16 fan screws (optional) | through the yoke into the fan's own housing |

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

1. **Bolt the PSU to `psu_plate`** from underneath, M4 × 8, countersunk side down.
   This is a bench job: the bolts only go in from below the plate, and once the
   PSU is on it, the PSU covers every stud position — which is exactly why the
   plate **snaps** to the tray instead of screwing.
2. **Drop the plate+PSU assembly in** over the four snap studs and press
   straight down until all four click. To remove, pull straight up — the 45°
   head ramps release.
3. **Fit the wall parts** — 4 × SP1712 (flat side **up**), the RJ45 coupler and
   the gland. The SP1712 pockets bring the local panel to 2.85 mm, inside the
   3 mm spec limit; the rear nuts tighten from inside.
4. **Wire it** — mains in via the gland to PSU terminals 1/2/3 (L/N/FG); PSU
   +V (7–9) to the fuse block feed; each fused output to one SP1712 pin; −V (4–6)
   common. The controller takes its DC from the PSU and drives the data pins.
5. **Bolt the fuse block and controller to `shelf`**, then drop the shelf onto
   its ledge. It lifts straight back out to reach the PSU terminals and the
   `+V ADJ` trimmer.
6. **Gasket** — press 3 mm silicone cord into the rim groove, cut to length,
   butt the ends with a drop of CA. (Or lay an RTV bead and let it cure against
   an oiled lid.)
7. **Fit the vent shutters** — cord (or RTV bead) in the panel's groove, gasket
   side in, two screws each. Then slide a `vent_slider` in at the **bottom** of
   each panel's channel and push until it clicks past the detent rod. That click
   is the open stop; it is also what stops the slider dropping back out.
8. **Fit the fan, if you are fitting one** — bolt the 40 mm fan to
   `vent_fan_yoke` with four M3 × 16, **blowing outward**, then screw the yoke to
   the four blind pilots inside the high port's frame. Take its 24 V from the PSU
   output terminals. This goes in *after* the shelf; see the note below.
9. **Lid on** — press straight down around the perimeter until the snap bead
   clicks. To open, pry gently at a corner and work along an edge.

### What comes out again, and in what order

The fan assembly reaches inboard past both the shelf's and the PSU plate's edges,
so it constrains disassembly — deliberately, and in the right direction:

- **The shelf still lifts straight out with the fan fitted.** It has a notch in
  its high-port edge exactly for this, because lifting the shelf is how the PSU's
  terminal block and `+V ADJ` trimmer are reached. `check_internal_fan()` sweeps
  the shelf upward through the fan and the yoke to prove it.
- **The PSU plate does not.** Take the yoke out first (four screws). The plate is
  fitted once and left alone, so this is the cheap side of the trade.

## Print settings

- **ASA** (or ABS if it will be shaded — ASA holds up far better in UV). **Not
  PLA**: internal air reaches 55–80 °C at high load without a fan and PLA creeps.
  PETG is a distant third.
- **≥ 4 perimeters, ≥ 5 top/bottom.** Watertightness comes from wall count and
  good layer bonding, not from thickness alone.
- No supports needed anywhere — every overhang is 45° or a bridge by design.
- The tray is a big ABS/ASA part: heated chamber, brim, and don't open the door.
- Optional: a wipe of epoxy or acetone on the *outside* of the tray closes any
  residual layer porosity. Do **not** acetone-smooth the shutter panels — it
  closes the louvre slots and welds the slider into its channel.

## Print a test coupon first

Before committing to a ~10 h tray print, print a small section carrying one
SP1712 cutout with its counterbore, a piece of the rim with the gasket groove
and snap bead — and one `vent_shutter` + `vent_slider` pair, which is a 25 min
print on its own. That proves the connector fit, the panel thickness and the
slider's running fit for the cost of half an hour.

## Thermal guidance

| Load | Roughly | Recommendation |
|---|---|---|
| ≤ 25 % (≤ 80 W) | ~10 W of heat | Both sliders shut. No fan needed. |
| 25–50 % | ~20 W | Both sliders open (≈ 765 mm² a port, ≈ IP54). |
| > 50 % (> 160 W) | 30–40 W | **Fit the fan.** Sliders open. |

**Do not expect much from convection alone.** Buoyancy through two open ports
30 mm apart in height moves ~0.05 L/s and carries **under 2 W** of the PSU's 40 —
and the PSU's own top-cover fan does not help, because it recirculates inside the
box rather than pumping through the ports. Opening the sliders on a hot box buys
far less than it looks like it should. The full sums are in
`docs/design-notes.md`; the practical upshot is that above about half load the
24 V fan is the part doing the work, and the sliders are there so you can shut
the box down for winter.

A shut slider is weather-tight, not airtight — it is a lapping plate, not a seal.
For a genuinely sealed port (storage, a very wet site, no load) fit `vent_blank`
instead: same recess, same two screws. Note that a blank and the internal fan
claim the same volume, so the high port takes one or the other.

The low port is at the terminal end and the high port is over the PSU's top-cover
fan, so a fitted pair gives real cross-flow rather than one hole doing nothing.
What matters is that they are at opposite *ends* — the 30 mm height difference
between them is worth almost nothing on its own. The shelf is slotted fore and
aft of the components, and notched at the high port, so the plenum below it stays
connected to the exhaust.

---

## A portable variant was contemplated — it is not this box

Running the lamps off a battery instead of mains was considered twice (USB-C PD,
and a Bosch 12 V tool pack). Neither is built and nothing here depends on them,
but the comparison is written down rather than re-derived:
**[`docs/design-notes.md` §7](docs/design-notes.md#7-the-portable-variant-and-where-24-v-comes-from-without-mains)**
for the argument, [`docs/part-data.md`](docs/part-data.md#portable-power-sources)
for the numbers and sources.

The short version: **USB-C PD 3.1 EPR wins** — its AVS mode hands you 24 V
directly at up to 120 W with *no converter in the box*, where a 12 V tool pack
always needs a boost; a €70 power bank beats every Bosch pack on €/Wh, and the
€22 "3 Ah" clones bench-test at 1.5–2.0 Ah. Ceiling either way is ~140 W (4–5
lamps) and ~100 Wh, so a portable build is an hour of three lamps. Keep a Bosch
foot as a second input if hot-swapping matters — that is the only axis it wins.
And it is a **different model**: without the RSP-320 the box is ~140 × 90 × 60
and needs neither vents nor fan.

## Layout, and why it is shaped this way

See `docs/design-notes.md` for the reasoning and `docs/part-data.md` for the
researched component dimensions with sources. The short version:

The PSU is 215 × 115 in a 228 × 125 interior — it comes within 6.5 mm of the end
walls and 5 mm of the front and back, so **no wall at PSU height can host a
connector** (an SP1712 needs 19.7 mm behind the panel). The whole layout follows
from resolving that: the shelf sits 13 mm above the PSU so the top-cover fan has
a plenum, the connectors go in the front wall above it, and everything mounted on
the shelf is held 36 mm back from that wall so the connector bodies have
somewhere to be.

The tightest part of the box is the high port's end. A 118 mm controller and a
40 mm fan share a 215 mm shelf with an 86 mm fuse block, and the controller's
mounting tab ends up 1 mm from the fan — passing *through* the yoke's own throat
to get there. `docs/design-notes.md` §1a has the depth budget.

## Verifying changes

`checks.py` point-samples the solids rather than trusting a projection — it
verifies the SP1712 panel thickness against the 3 mm spec limit, that the D-flat
is oriented up (so it prints as a bridge), that every insert pocket is blind,
that the gasket groove is continuous, that the lid's snap bead engages the rim
groove without welding, that every internal part fits *through the rim opening
and past the vent frames*, that the shutter's slider really covers every louvre
slot when shut and clears every one when open (and that no straight line runs
through the louvre either way), that the internal fan's yoke clears the
controller and that the shelf still lifts out past it, and that nothing collides
with anything. Run it after any change to `config.py`:

```bash
uv run check led_psu_enclosure
```
