# Modular 24 V Addressable COB Lamp System

Daisy-chainable linear lamps built on 1.5 m aluminium T8 profile, driven by a
24 V addressable COB strip, each lamp containing an ESP32 Mini + power
distribution on an internal PCB. Industrial-style field wiring: standardized
cable, standardized connectors, no custom cabling.

This document is the system specification. CAD models for the printed parts
(endcaps, PCB mount, mounting hardware) land in this package as they are
designed.

## Goals

- Modular daisy-chainable linear lamps
- Native 24 V operation
- Optional USB-C PD standalone power
- WLED compatible
- Robust industrial-style wiring
- Easy field assembly and repair

## Lamp

### Mechanical

- 1.5 m aluminium T8 profile
- COB diffuser
- 3D printed endcaps
- Internal PCB for ESP32 + power distribution
- Input and output pigtails

### Profile

The extrusion, measured and reconstructed in `config.py` / `profile.py`. It is a
stadium in section — two R13 half-circles joined by 4 mm straight flanks — not a
circle and not an ellipse.

| Dimension | Value | |
|---|---|---|
| Outer width × height | 26 × 30 mm | measured |
| Wall thickness | 0.5 mm | measured |
| Rim (aluminium stops, diffuser seats) | z = 16.8 | dialled |
| Shallow recess | 19 mm wide × 1.4 mm deep | dialled |
| Strip slot | 10 mm wide × 1.3 mm deep | measured |
| Strip floor / cavity ceiling | z = 14.1 / z = 13.1 | dialled |
| Endcap screw ports | 22 mm apart, 2 mm self-tappers, z = 14.7 | measured / dialled |
| Diffuser | 26 mm outside, 25 mm inside, 1.0 mm at the crown | measured |
| Length | 1500 mm | |

The rim sits just below the top arc's centre, inside the straight band where the
section is at its full 26 mm — which is why the diffuser measures 26 mm across
and reads as an unbroken continuation of the outline. Its inner face is a
separate circle rather than an offset of the outer one, so it is thinner at the
rim than at the crown, as the real part measures.

The LED channel is genuinely shallow — two steps totalling 2.7 mm. Nearly all
of the tube is cavity: **~12.6 mm deep and ~25 mm wide below the strip floor**
for the 1.5 mm² bus and the ESP32 PCB. The screw bosses straddle the shelf,
hanging down into that cavity, which is what an endcap grabs.

Those are the numbers the endcap gets designed against.

```bash
uv run show led_profiles                  # the full 1.5 m stick
uv run check led_profiles                 # hold the section to its measurements
```

Values marked *assumed* in `config.py` are reconstructions the calipers did not
pin down — check them before a printed part depends on one.

### Endcap

`endcap.py`. One design at both ends, since both carry a pigtail. Screws to the
two ports with M2 × 12 pan-head self-tappers; the M12 × 1.5 gland thread is
printed directly into the cap.

Two facts about the extrusion dictate the design:

- **The gland only just fits.** An M12 gland needs a ~12.3 mm bore and the
  largest circle that fits in the wiring cavity is 12.6 mm. The bore is placed,
  not centred — pushed up to z = 9.0 so it keeps 3.45 mm of plastic to the
  outside while its axis still opens into the cavity. A gland locknut is not an
  option at all (17 mm across, 12.6 mm of cavity), hence the printed thread.
- **The ports sit 2 mm from the outer surface.** A recessed M2 head needs 4.6 mm
  and would break out through the side. So the cap is a **0.6 mm proud collar**
  rather than flush, and the screw heads sit on the face.

| | |
|---|---|
| Collar | 27.2 × 31.2 mm, 0.8 chamfer |
| Flange thickness | 12 mm |
| Register lip | 6 mm deep, 1.2 wall, SLIDING fit in the cavity |
| Gland | M12 × 1.5 printed female, 10.5 mm of thread on a 1.5 mm collar |
| Screws | 2 × M2 × 12 pan-head, 22 mm apart |

Prints outer-face-down: largest possible first layer, thread axis vertical, no
overhangs. Layer height ≤ 0.25 mm (pitch / 6) or the thread staircases.

### Mounting, standing and corners

See `docs/design-notes.md` for the reasoning. The short version:

Nothing wraps the tube. The stadium is at its full 26 mm from z = 13 to z = 17,
so a **cradle** that stops at the rim (z = 16.8) has no undercut at all — the
tube drops in sideways, the diffuser is never shadowed and never trapped, and a
closed polygon can be taken apart. Every foot carries its cradle integrally; the
only wrapping part is a shared 18 mm **strap**, two per station. No mount takes
its load through the endcap, because two M2 self-tappers are the only thing
holding that on.

Corners stay coplanar, which costs ~126 mm of unlit tube per vertex — set by the
two glands pointing at each other, not by the cable, because the jumper loop
lives behind the form plane inside the corner's web. The stand is a light
folding tripod after the Astera AX1‑STD; **~85 g of push at the top topples it**,
which is what that class of stand is. `docs/design-notes.md` §4 has the sum.

**This family prints in ASA, not PETG** — UV outdoors, and HDT against a tube
that runs 40–60 °C. That changes the fits: `fits.SNUG` in ASA is −0.05 mm, an
interference fit, so the cradle uses `for_material(SLIDING, "asa")` = 0.07.
Outdoor handling is *drain, not seal* — no gaskets, no IP claim, A2 stainless
throughout, and a drain out of every upward-facing pocket **except the
corner's**, whose channel and troughs are undrained and hold water: mount a
corner somewhere sheltered. §5 has the depths.

| part | size | hardware |
|---|---|---|
| `strap` | 58 × 18 × 20 mm | 2 × M4 × 16 socket cap |
| `cradle` | 60 × 58 × 21 mm | 4 × M4 heat-set inserts |
| `corner 60°` | 172 × 141 × 29 mm | 8 × M4 inserts, 4 straps |
| `stand hub` | 90 × 90 × 156 mm | 3 × M6 pivots, 6 × M4 inserts |
| `eye foot` | 60 × 58 × 21 mm | 2 × M6 eye bolts + nyloc |
| `wall foot` | 60 × 58 × 21 mm | 2 × M5 into the wall |

The bolt circle is `BOSS_U` = 22.1 mm off the tube axis, which is not a round
number because it is derived: the strap's own arch is 19.5 mm at its widest, and
the head has to seat clear of that flank. See `docs/design-notes.md` §"The bolt
circle is derived, not chosen" — 19.5 was the number, and it did not work.

Bought for the stand: three flat bars, 20 × 3 × 250 mm, Ø6.5 hole 12 mm from one
end — stainless or galvanised, not plain mild steel if it lives outdoors.

```bash
uv run show led_profiles.corner         # one part; also .strap .stand .feet
uv run export led_profiles.corner       # its STL for the slicer
```

Each printed part is its own model — `.endcap`, `.strap`, `.corner`, `.stand`,
`.feet` — so the slicer gets them one at a time. `create_print_layout()` still
spreads the whole set into one row, each in its print pose, for anyone who wants
them in a single file (it is also the only way to reach the wall foot, which
shares `feet`'s CLI target with the eye foot).

### Assemblies

The `assemblies/` package puts the mounting family to use: one or three lamps
seated in the mounts above, each placed with that part's own `seated()`
transform (`feet.seated`, `strap.seated`, `stand.seated`/`seated_legs`,
`corner.seated`) rather than a re-derived one. The only new geometry is the
triangle's vertex layout (`triangle_vertices`) and the stand's tube-to-vertical
rotation.

One module per scene, so each is a model in its own right — showable,
exportable, and on the generated website alongside the parts:

| module | shows |
|---|---|
| `assemblies.triangle` | 3 lamps + 3 corners closed into a flat loop, straps at all 12 cradle stations — the corner-and-strap half of the family; no stand hub or feet in this view |
| `assemblies.standing` | 1 lamp vertical in the tripod hub, legs deployed, straps at all 3 stand stations, lower endcap on the seat |
| `assemblies.suspended` | 1 lamp hung from two eye feet at the Bessel points — 0.2203 × length from each end, the two-point support that levels a simply-supported beam's own sag — plus the four straps that secure the feet (two per foot) |

```bash
uv run show led_profiles.assemblies.triangle    # 3 lamps, 3 corners, 12 straps
uv run show led_profiles.assemblies.standing    # upright in the tripod hub
uv run show led_profiles.assemblies.suspended   # hung from two eye feet
```

All three take a lamp `length` (the site exposes it as a slider) and are
re-exported from the package, so `from models.led_profiles import
create_standing` still works.

The triangle's 126 mm of unlit tube per vertex (noted above) is the visible
consequence of staying coplanar — `docs/design-notes.md` §2 has the
derivation. The tripod is studio-class, not load-bearing: ~0.85 N of push at
the top topples it (`docs/design-notes.md` §4).

### LED Strip

Current target:

- 24 V COB
- WS2811 Dual IC
- 960 LED/m RGBCCT
- 24 V constant-voltage architecture

Future compatible with newer 24 V pixel COB strips.

## Internal Wiring

Inside every lamp:

```
Incoming cable
        │
────────┴──────── 1.5 mm² +24V bus
────────┬──────── 1.5 mm² GND bus
        │
        └── short branch to LED strip
```

Power is passed through every lamp. The strip is only connected as a local
branch.

Advantages:

- minimal voltage drop
- easy servicing
- little current through strip solder joints

## Daisy Chaining

- 4–6 lamps without power injection
- Up to 8 lamps with midpoint injection

Data always continues through all lamps.

## Cabling

External cable: **LAPP ÖLFLEX CLASSIC 110 BK**

- 3×1.5 mm²
- Black
- 6.7 mm OD

Chosen because: industrial quality, low voltage drop, easy sourcing,
inexpensive (~€1.60/m).

## Connectors

Current choice: **SP16 or SP17, 3 pin**

- inline connectors on lamp pigtails
- panel connectors on controller

Chosen because: significantly higher current than BTF connectors, supports
larger cable, industrial quality, affordable.

## Pigtails

Each lamp:

```
SP16
 │
100–150 mm cable
 │
Cable gland
 │
Internal bus
```

Benefits: easier installation, less stress on enclosure, easy replacement.

## Cable Glands

Current choice: **M12, 3–7 mm range** — suitable for the 6.7 mm LAPP cable.
Provides IP sealing and strain relief.

## Controller

Ethernet ESP32 controller, current target:

- 4 outputs
- Ethernet
- WLED

Each output gets its own connector and its own fuse.

## Fusing

Recommended: **Mini ATM automotive blade fuses**.

Architecture:

```
Main fuse
   ↓
Power bus
   ↓
Output fuse
   ↓
Connector
```

One fuse per output.

## USB-C Power

The controller includes:

```
USB-C panel connector
   ↓
PD trigger
   ↓
20→24 V boost
   ↓
24 V bus
```

Allows powering: standalone lamp, controller, demonstration setups.

### USB-C Hardware

Preferred architecture (both modules replaceable):

```
USB-C panel extension
   ↓
PD trigger module
   ↓
Boost converter
   ↓
24 V rail
```

Boost converter current recommendation: **XL6019** — inexpensive, sufficient
for ~30 W lamp, proven, readily available. A future PCB revision may integrate
a newer synchronous converter.

## Power Topology

- Native voltage: **24 V**
- USB-C is only an optional input
- All lamps are fundamentally 24 V devices

## Internal Electronics

Each lamp contains:

- ESP32 Mini
- power distribution
- LED output
- optional USB-C power hardware

Only external connections required: **24 V, GND, DATA**.

## System Philosophy

- Modular
- Repairable
- Industrial components
- Consumer-friendly assembly
- Minimal custom cabling
- Standardized connectors
- Standardized cable
- Expandable without redesign

## Status

- [ ] System specification (this document)
- [x] Profile assembly (extrusion + diffuser + strip, the datum for everything else)
- [x] Endcap (screws to the ports, printed M12 gland thread) — see below
- [x] Mounting family designed — `docs/design-notes.md`
- [x] Strap + cradle (the shared interface)
- [x] Corner connector, parametric angle
- [x] Folding tripod stand hub — **clears the gland, not the cable**; the well
      leaves 2 mm in line with the gland's nose against a 26.8 mm bend radius,
      so the cable has nowhere to turn. `checks.check_stand_gland_cable` fails
      on it and `docs/design-notes.md` §10 lists the ways out.
- [x] Suspension eye and wall feet
- [ ] PCB mount inside the endcap
- [ ] PCB (ESP32 Mini + power distribution + LED output)
- [ ] Mounting hardware
- [ ] Controller panel layout (4× SP16/17, fuse holders, USB-C, Ethernet)

Parts are added to `models/led_profiles/` and registered in this package's
`__init__.py` as they are designed:

```bash
uv run show led_profiles                # once a create() exists
uv run export led_profiles              # STL + STEP
```
