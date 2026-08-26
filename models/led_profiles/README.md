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
stadium in section — two R13.05 half-circles joined by 4.4 mm straight flanks —
not a circle and not an ellipse.

| Dimension | Value | |
|---|---|---|
| Outer width × height | 26.1 × 30.5 mm | drawn, width corrected against hardware |
| Wall thickness | 0.5 mm | measured |
| Rim (aluminium stops, diffuser seats) | z = 16.8 | dialled |
| Shallow recess | 19 mm wide × 1.4 mm deep | dialled |
| Strip slot | 10 mm wide × 1.3 mm deep | measured |
| Strip floor / cavity ceiling | z = 14.1 / z = 13.1 | dialled |
| Endcap screw ports | 22 mm apart, 2 mm self-tappers, z = 14.7 | measured / dialled |
| Diffuser | 26.1 mm outside, 25 mm inside, 1.0 mm at the crown | measured |
| Length | 1500 mm | |

The outline comes off a 1:1 pencil tracing of the extrusion, the diffuser and
the assembled tube on 5 mm graph paper — `docs/assets/profile-dimensions.jpg`,
read back against the grid. That sheet measures 26.30 × 30.72 at the pencil's
centreline; a traced outline runs wide by about half a pencil per side, and the
printed endcap measured **0.55 mm too wide per side** at a 0.6 mm collar, which
puts the tube at 26.1. Scaling the sheet's own aspect ratio onto that gives
30.5. `config.py` lists the three things the sheet says that this package
deliberately does not follow.

The rim sits just below the top arc's centre, inside the straight band where the
section is at its full 26.1 mm — which is why the diffuser measures the same
across and reads as an unbroken continuation of the outline. Its inner face is a
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
two ports with M2 self-tappers; the M12 × 1.5 gland thread is printed directly
into the cap.

The cap is a **flange** flush with the tube, a 20 mm **plug** that goes down the
wiring cavity behind it, and a **strap slot** through the flange under the bore.

- **The strap slot is what sizes the flange.** A 12 mm velcro strap threads
  through the cap and goes round a rigging bar, and it runs *perpendicular to
  the profile* — round the cap's cross-section, not along the tube. So the
  strap's width lies along the tube and the flange has to hold all 12 mm of it.
  `CAP_T` is derived, `STRAP_SLOT_W + 2 × STRAP_WALL` = 15.85; it was 8.0, and
  before that 12.
- **The gland no longer sizes the flange, and no longer reaches all of it.** A
  stock M12 gland carries ~8 mm of male thread and then seals on its flange
  against the cap's *face* — which has not moved, so the gland still seats. The
  thread is cut over the outer 8 mm only and the rest is plain bore.
- **The plug is a shell, not a solid.** A 2.4 mm wall following the cavity's
  lower arc, open along the top — a channel rather than a plug. It used to be a
  solid half-disc, which put 6.99 mm of plastic across the bottom of a cavity
  whose whole job is to carry wiring; the relief pocket never reached down
  there, because its floor is a clearance off the strap slot in the *flange*.
  The section still takes the rocking moment off the two screws — a deep curved
  channel carries it in the layer plane, with the material where the moment is —
  and the gland's axis now runs through the hollow rather than through metal.
- **The gland is on the cap's own centre.** Symmetric, and it costs something —
  the cavity ceiling is below the bore, so a cable cannot be fed from this gland
  into the tube's wiring cavity. `check_gland` measures the opening rather than
  asserting a route that is not there.
- **The screw heads are sunk, and they break out.** Each 3.8 mm head rides
  down a Ø4.85 access bore and seats 4 mm below the face. A flush cap has less
  room outboard of the port than half a head, so the hole cuts ~0.35 mm out
  through each flank — deliberate, and bounded by `check_screw_pockets`.

| | |
|---|---|
| Flange | 26.1 × 30.5 mm, flush with the tube, 0.8 bed chamfer |
| Flange thickness | 15.85 mm, derived from the strap slot |
| Strap slot | 12.25 × 1.5 mm obround, through the flanks, 0.5 fillet at each mouth |
| Strap | 12 × 1 mm velcro, perpendicular to the profile |
| Plug | 16 mm deep, 2.4 mm shell on the cavity's arc, SLIDING fit |
| Gland | M12 × 1.5 printed female, 6.5 mm of thread on a 1.5 mm collar |
| Screws | 2 × M2 × 16 countersunk, 22 mm apart, heads sunk 4 mm down a Ø4.85 access bore |

The screws are M2 × 16 countersunk (DIN 965). A 90° taper head is 45° per side,
so the seat is a cone that is self-supporting the whole way down — there is no
flat pocket floor to print out over, which is what the old pan-head counterbore
left as a 1.075 mm ring of unsupported ceiling. A 16 seated flush would leave
0.68 mm of thread in the port, so each hole opens as a Ø4.85 access bore — the
seat cone's own rim, no ledge — sunk 4 mm, exactly what the screw lost against
the old M2 × 20: the head lands 4 mm below the face and `screw_reach()` stays
at 4.7 mm of thread in the aluminium, 2.3 × the thread diameter and past the
2 × d floor a self-tapper wants there for a firm hold. The profile's port is a
continuous channel down the whole extrusion, not a blind hole, so the reach is
bounded by the screw, never by the aluminium.

Prints outer-face-down: largest possible first layer, thread axis vertical, no
overhangs. The strap slot suits that pose — a tall letterbox through a vertical
wall, whose only unsupported run is a 1.5 mm ceiling. Layer height ≤ 0.25 mm
(pitch / 6) or the thread staircases.

**Parametric on the website**, over the four numbers that are choices rather
than measurements of the extrusion: the printed thread's clearance on the gland
(the thing to tune when a real gland binds or wobbles), the strap's width and
thickness, and the plug's depth. The derivations above run for the sliders
exactly as for the defaults — the flange follows the strap, and the screw heads
sink deeper as it grows so `screw_reach()` holds. See `endcap.PARAMS` and the
`Endcap` spec for the ranges and why they end where they do.

### Wired endcap

`endcap_wired.py`. The standard cap's gland is a fitting, not a cable route —
only a 5.5 mm slot of its bore looks into the wiring cavity, against a 6.7 mm
cable. This variant buys the route with length: the flange grows by 10 mm (the
plug is unchanged, so all of it is protrusion past the aluminium), and
everything above the strap block is opened into one chamber whose bottom half
is the wiring cavity's own cross-section, walls flush with the plug's channel
all the way to the tip. A cable through the gland exits the thread into 10 mm
of turning room — exactly what the cap grew — and runs into the tube with
nothing narrower than the bore anywhere on the way.

- **Same screws, same reach.** The M2 × 16 screws keep their length, so the
  access bore gains exactly the 10 mm the flange grew, on top of the standard
  cap's own 4 mm: the head lands 14 mm below the face, riding in on the
  driver's tip, and `screw_reach()` is asserted *identical* to the standard
  cap's.
- **Same strap slot.** The cap's outer 15.85 mm is the standard cap's flange
  verbatim — same slot, same mouths, same fillets — so it straps to a rigging
  bar like every other end. The slot cannot cross the chamber (it would dump
  the strap into the cable run), so the chamber floor sits a `STRAP_WALL`
  above its roof, which is what pins the floor at z = 15.85.

| | |
|---|---|
| Flange thickness | 25.85 mm — the standard cap's 15.85 + 10 |
| Strap slot | the standard cap's, verbatim, in the outer 15.85 mm |
| Chamber | plug-channel section carried through the flange, floor at z = 15.85 |
| Chamber shell | 2.225 mm, plus a `POCKET_CLEAR` column round each screw hole |
| Screws | same M2 × 16 DIN 965, down a Ø4.85 × 14 mm access bore |

### Mounting, standing and corners

See `docs/design-notes.md` for the reasoning. The short version:

Nothing wraps the tube. The stadium is at its full 26.1 mm from z = 13.05 to
z = 17.45, so a **cradle** that stops at the rim (z = 16.8) has no undercut — the
tube drops in sideways, the diffuser is never shadowed and never trapped, and a
closed polygon can be taken apart. Every foot carries its cradle integrally; the
only wrapping part is a shared 18 mm **strap**, two per station. No mount takes
its load through the endcap, because two M2 self-tappers are the only thing
holding that on.

Corners stay coplanar, which costs ~94 mm of unlit tube per vertex — set by the
two glands pointing at each other, not by the cable, because the jumper loop
lives behind the form plane inside the corner's web. The stand is a light
folding tripod after the Astera AX1‑STD, and it is now **entirely printed** bar
three M6 pivots: **~61 g of push at the top topples it**, which is what that
class of stand is, and about a third worse than the bought-steel-bar version it
replaced. `docs/design-notes.md` §4 has the sum and §11 the trade.

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
| `corner 60°` | 156 × 127 × 29 mm | 8 × M4 inserts, 4 straps |
| `stand` (post) | 78 × 71 × 225 mm | 3 × M6 × 30 + nyloc |
| `stand.leg` ×3 | 238 × 26 × 13 mm | — |
| `stand.keeper` ×2 | 53 × 30 × 38 mm | — |
| `eye foot` | 60 × 58 × 21 mm | 2 × M6 eye bolts + nyloc |
| `wall foot` | 60 × 58 × 21 mm | 2 × M5 into the wall |

The bolt circle is `BOSS_U` = 22.1 mm off the tube axis, which is not a round
number because it is derived: the strap's own arch is 19.5 mm at its widest, and
the head has to seat clear of that flank. See `docs/design-notes.md` §"The bolt
circle is derived, not chosen" — 19.5 was the number, and it did not work.

Bought for the stand: **three M6 × 30 socket caps and three M6 nylocs**, and
nothing else. The legs used to be bought flat bar and are now printed, which is
what took the hardware list down to six pieces and the tip force with it.

The stand is the one mount in the family that **captures rather than clips**,
and the reason is worth stating because a clip is the obvious thing to reach
for. The assembled tube's width rises monotonically to its straight band and is
constant across it, so no lip hooks it from any direction that stays off the
diffuser — §1's conclusion, arrived at from the other side, and
`checks.check_stand_no_undercut` holds it as a test. So the post is a vertical
cradle, and two **keepers** drop into sockets to close its mouth: pegs in holes,
not a snap, because design-notes §3's abuse case puts 96 N of forward pull on
the lower one and a snap on this geometry is worth about 30 N. Fitting a lamp
is two motions — drop it in, drop the keepers in — and no tools at all.

```bash
uv run show led_profiles.corner         # one part; also .strap .stand .feet
uv run show led_profiles.stand.leg      # and .stand.keeper
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
| `assemblies.standing` | 1 lamp vertical on the tripod stand, three printed legs deployed on the floor, both keepers seated, lower endcap on the seat |
| `assemblies.suspended` | 1 lamp hung from two eye feet at the Bessel points — 0.2203 × length from each end, the two-point support that levels a simply-supported beam's own sag — plus the four straps that secure the feet (two per foot) |

```bash
uv run show led_profiles.assemblies.triangle    # 3 lamps, 3 corners, 12 straps
uv run show led_profiles.assemblies.standing    # upright in the tripod hub
uv run show led_profiles.assemblies.suspended   # hung from two eye feet
```

All three take a lamp `length` (the site exposes it as a slider) and are
re-exported from the package, so `from models.led_profiles import
create_standing` still works.

The triangle's 94 mm of unlit tube per vertex (noted above) is the visible
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

Measured off the fitting in hand, because two of these numbers set the size of
every corner in the family (`docs/design-notes.md` §2 and §8):

| | |
|---|---|
| Body hex (against the cap's face) | 16.2 mm across flats, 4.4 mm long |
| Compression nut | 16.1 mm across flats, 14.4 mm long (10 mm of it hex) |
| Nut's outer end | a round-over, not a taper — R4.4, ending Ø7.3 on the cable |
| Envelope, across corners (`GLAND_ENV_D`) | **18.71 mm** |
| Protrusion past the cap face (`GLAND_PROUD`) | **18.8 mm** |

They live in `mount_config.py`; `gland.py` draws the fitting from them, so every
assembly view shows the real thing rather than a reserved hole. Both used to be
assumed at 24 and 30 mm, which cost 32 mm of dark tube at every vertex.

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

> **The boost is only needed on a PD 3.0 source.** PD 3.1 EPR's *Adjustable
> Voltage Supply* covers 15–48 V in 100 mV steps, so a trigger set to 24.0 V
> feeds the bus directly at up to 5 A (120 W) with no converter at all; the
> fallback on a fixed-PDO EPR source is 28 V and a *buck*, which is the easy
> direction. Worth designing the PCB so the converter can be depopulated.
> Full comparison, including against 12 V tool packs, in
> [`led_psu_enclosure/docs/design-notes.md` §7](../led_psu_enclosure/docs/design-notes.md#7-the-portable-variant-and-where-24-v-comes-from-without-mains).

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
- [ ] Folding tripod stand — post, three printed swinging legs, two keepers.
      Geometry, fits and load path done and checked. **The edge treatment is not
      finished**: `check_stand_edges` fails and is skipped behind
      `checks.SKIP_STAND_EDGES`, so the printed rims are sharper than the rest
      of this family. Nothing else in the stand's checks fails.
      The cable problem §10 opened is **closed by deletion**: the seat is
      `gland.free_length()` above the floor and the bore under it is open, so
      nothing stands in line with the gland at all.
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
