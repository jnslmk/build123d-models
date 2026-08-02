# Heat-set inserts

Brass inserts melted into a printed boss with a temperature-controlled iron.
Everything below is in millimetres unless stated otherwise.

## Contents

- [Per-size dimension table](#per-size-dimension-table)
- [Conflict 1: the M3 hole is not 4.0 mm](#conflict-1-the-m3-hole-is-not-40-mm)
- [Conflict 2: boss diameter, 2-3x or 1.4x](#conflict-2-boss-diameter-2-3x-or-14x)
- [Hole geometry rules](#hole-geometry-rules)
- [The mating part](#the-mating-part)
- [Filled materials](#filled-materials)
- [Installation](#installation)
- [Strength data](#strength-data)
- [Modelling checklist](#modelling-checklist)
- [Sources](#sources)

## Per-size dimension table

| Thread | Hole | Insert OD | Insert len | Boss OD min | Wall min |
| ------ | ---- | --------- | ---------- | ----------- | -------- |
| M2     | 3.2  | 3.5       | 3-5        | 5.0         | 0.75     |
| M2.5   | 3.7  | 4.0       | 3.5-6      | 5.5         | 0.75     |
| M3     | 4.0  | 4.6       | 4-6        | 6.5         | 0.95     |
| M4     | 5.3  | 6.0       | 5-8        | 8.5         | 1.25     |
| M5     | 6.4  | 7.1       | 6-10       | 10.0        | 1.45     |
| M6     | 7.6  | 8.4       | 8-12       | 11.5        | 1.55     |
| M8     | 10.2 | 11.1      | 10-16      | 15.0        | 1.95     |

Source: [Albany County Fasteners, heat-set insert specifications][acf-specs]

"Hole" is the **nominal** hole diameter - it is what the insert vendor wants
to see in the finished part, not what to draw in CAD. See the next section.
"Wall min" is the minimum wall the vendor quotes to stop the boss splitting;
"Boss OD min" is a floor, not a target.

Insert lengths are ranges because vendors stock several lengths per thread.
Measure the insert actually on the bench before setting a boss depth - insert
outside diameter varies between brands even at the same thread size.

## Conflict 1: the M3 hole is not 4.0 mm

Two sources disagree, and they disagree for a reason worth understanding.

| Source                       | M3 hole | Basis                    |
| ---------------------------- | ------- | ------------------------ |
| Vendor table (above)         | 4.0     | Nominal finished hole    |
| CNC Kitchen, printed, horiz. | 4.1 fits, 4.25 rec. | Measured on prints |
| CNC Kitchen, printed, 45 deg | 4.1     | Measured on prints       |
| CNC Kitchen, printed, vert.  | 4.2     | Measured on prints       |

Sources: [Albany County Fasteners][acf-specs],
[CNC Kitchen tips and tricks][ck-tips]

CNC Kitchen's method was to print a ladder of diameters, melt an insert into
each from smallest up, and inspect the back face for burring - the point where
material stops being pushed out the far side. Horizontally, inserts start
fitting at 4.1 mm and the burr is gone by 4.3 mm, so the recommendation is
**4.25 mm**; vertically, both happen at 4.2 mm.

The gap between 4.0 and 4.1-4.25 is not a measurement error. It is the FDM
hole-undersize effect: the nozzle drags the inner perimeter inward, so a hole
modelled at 4.0 mm comes off the printer smaller than 4.0 mm. The vendor
number describes the *hole you end up with*; the CAD number has to be bigger.

Do not average the two. Take the position:

- **Default to 4.2 mm for M3** (vertical hole, the common case in this repo -
  bosses print axis-up).
- **Add +0.2 mm to every other row** in the table above if the slicer is not
  compensating hole shrinkage.
- If hole compensation *is* on (Orca/Prusa "hole compensation" / "X-Y hole
  compensation"), use the table value as-is and verify on a test coupon.
- A horizontal hole on a vertical wall prints its top edge slightly small
  because the bridged material sags. Either model horizontal holes ~0.05 mm
  larger than vertical ones, or fix it in cooling/bridging settings.

## Conflict 2: boss diameter, 2-3x or 1.4x

SPIROL's white paper says the optimum boss diameter (or wall thickness) is
**2 to 3 times the insert diameter**.
Source: [SPIROL, how to design the proper hole][spirol-hole]

The vendor table above gives, for M3, an insert OD of 4.6 and a boss OD
minimum of 6.5 - a ratio of **1.4x**. Maker-community tables cluster around
the same place.

Both are right about different things. SPIROL is writing for injection
moulding, where the boss is dense, isotropic, and the hole is formed by a core
pin rather than by extruded perimeters. An FDM boss is a stack of perimeters
with a weak Z bond, so:

- **Safe default: 2x the insert OD where space allows.**
- **1.6x is the floor on a load-bearing boss.**
- Below that, treat the vendor minimum as an absolute limit and expect the
  boss to split if the insert goes in hot or crooked.
- Extra boss diameter is nearly free in print time and buys real margin -
  spend it before spending on a longer insert.

## Hole geometry rules

- **The hole must be straight, not tapered.** For a straight insert the taper
  must not exceed **1 degree included angle**. (A hole deliberately designed
  tapered for a tapered insert uses 8 degrees included - not what a printed
  boss should be doing.)
  Source: [SPIROL][spirol-hole]
- **Minimum depth = insert length + 2 thread pitches.**
  Source: [SPIROL][spirol-hole]
- **Blind holes: insert length + 1 mm.** The extra millimetre is a relief well
  for the plastic the insert displaces on the way in; without it the displaced
  material bottoms out and the insert stands proud.
  **Through holes need no extra depth.**
  Source: [CNC Kitchen][ck-tips]
- **No lead-in chamfer.** "Normally, no chamfer is required at the hole edge."
  Source: [CNC Kitchen][ck-tips]

  This is a **deliberate exception** to the repo's standing rule in
  `AGENTS.md` that every hole mouth gets a lead-in. The insert's own external
  chamfer self-guides, and a printed chamfer deletes exactly the material the
  insert should be melting into and re-flowing around. Leave the mouth square.
- **Installed insert sits flush**, with **maximum protrusion 0.13 mm**
  (0.005 in) above the surface.
  Source: [SPIROL][spirol-hole]
- **4-6 perimeters under a structural insert**, plus solid infill in the boss.
  The load path is the perimeter stack, not the infill.

## The mating part

The clearance hole in the part being bolted down must be:

- **larger than the screw** (obviously), and
- **smaller than the insert pilot diameter.**

If the clearance hole is bigger than the insert's hole, tightening pulls the
insert up into the clearance hole and jacks it straight out of the boss. This
is the single most common insert failure that is not an installation error.

For M3: clearance 3.4-3.65 mm against an insert hole of 4.2 mm - fine. Do not
open that clearance hole out to 4 mm "so it lines up easier".

## Filled materials

Glass- and mineral-filled filaments flow less and shrink differently:

| Filler content | Hole adder      |
| -------------- | --------------- |
| >= 15%         | +0.08 mm        |
| >= 35%         | +0.15 mm        |
| in between     | interpolate     |

Source: [SPIROL][spirol-hole]

This stacks on top of the FDM correction in the first conflict section.

## Installation

- **Iron temperature = print temperature + 10-20 degrees C.** In practice:
  PLA ~225 C, PETG ~245 C, ABS ~265 C.
  Source: [CNC Kitchen][ck-tips]
- Vendor figures in Fahrenheit, for cross-checking: PLA 350-400 F,
  ABS 400-450 F, PETG 425-475 F, nylon 450-500 F, polycarbonate 475-525 F,
  acetal 425-475 F. Insertion 2-4 s, cool 30-60 s.
  Source: [Albany County Fasteners][acf-specs]
- **Melt to about 90% of depth with the iron, then seat the last 10% with a
  flat tool** (the cold face of a square block). Hold until the plastic
  solidifies before letting go. This is what produces a flush, square top face
  instead of a tilted one.
  Source: [CNC Kitchen][ck-tips]
- Hold the iron perpendicular. If the insert sinks too far, the plastic is too
  hot; if it will not go, too cold.
  Source: [Albany County Fasteners][acf-specs]

## Strength data

Two independent CNC Kitchen tests, both worth knowing because they answer
different questions.

**Test 1 - insert brand and hole size** (Prusament PLA, 0.15 mm layers,
100% infill, Prusa i3 MK2.5):

| Sample                        | Hole | Pull-out |
| ----------------------------- | ---- | -------- |
| ruthex insert                 | 4.0  | 181 kg   |
| Cheap eBay insert             | 4.1  | 157 kg   |
| Injection-moulding-style      | 4.5  | 39 kg    |
| Screw driven direct into hole | 2.7  | 142 kg   |

Torque-out: **all insert types 3-4 Nm** and the bolt heads sheared before the
inserts moved; **direct screws failed at ~1 Nm**, in the plastic.

Source: [CNC Kitchen, cheap vs expensive inserts][ck-cheap]

The 39 kg row is the important one: an insert designed for injection moulding,
in a hole sized by the moulding rule, is **4.6x weaker than no insert at all**.
Insert knurl geometry has to suit melt-in installation.

**Test 2 - joint type** (PETG, M3, 4 perimeters, 100% infill):

| Joint                         | Pull-out |
| ----------------------------- | -------- |
| Nut pocket in the bottom face | 166 kg   |
| Heat-set insert               | 119 kg   |
| Screw straight into plastic   | 118 kg   |

Source: [CNC Kitchen, helicoils/inserts/embedded nuts][ck-helicoil]

Together: inserts do not win on pull-out. They win on **torque (3x) and reuse**,
and they lose outright to a bottom-face nut pocket on pull-out. Different
material and print settings between the two tests explain the 181 vs 119
figures - compare rows within a test, never across.

## Modelling checklist

- [ ] Hole diameter = table value + FDM correction (M3 -> 4.2), as a constant.
- [ ] Hole straight, no draft, **no lead-in chamfer**.
- [ ] Blind depth = insert length + 1 mm; at least insert length + 2 pitches.
- [ ] Boss OD = 2x insert OD, never below 1.6x on a loaded boss.
- [ ] Wall around the boss >= the per-size minimum and >= 1x fastener diameter.
- [ ] Mating clearance hole < insert hole diameter.
- [ ] Boss reaches the print bed or sits on solid material - not on infill.
- [ ] Point-sample the solid to confirm boss wall and hole depth in code.

## Sources

- [Albany County Fasteners - heat-set insert specifications (PDF)][acf-specs]
- [SPIROL - how to design the proper hole for heat/ultrasonic
  inserts][spirol-hole]
- [CNC Kitchen - tips and tricks for heat-set inserts][ck-tips]
- [CNC Kitchen - threaded inserts, cheap vs expensive][ck-cheap]
- [CNC Kitchen - helicoils, threaded inserts and embedded nuts][ck-helicoil]

[acf-specs]: https://www.albanycountyfasteners.com/media/64/3d/5a/1764619189/heat-set-insert-specs.pdf
[spirol-hole]: https://www.spirol.com/resources/white-papers/how-to-design-the-proper-hole-for-heat-ultrasonic-inserts/
[ck-tips]: https://www.cnckitchen.com/blog/tipps-amp-tricks-fr-gewindeeinstze-im-3d-druck-3awey
[ck-cheap]: https://www.cnckitchen.com/blog/threaded-inserts-for-3d-prints-cheap-vs-expensive
[ck-helicoil]: https://www.cnckitchen.com/blog/helicoils-threaded-insets-and-embedded-nuts-in-3d-prints-strength-amp-strength-assessment
