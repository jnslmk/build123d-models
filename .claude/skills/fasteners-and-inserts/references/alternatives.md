# Alternatives to heat-set inserts

Hex nut pockets, self-tapping screws, tapped threads, and the plain clearance
holes every one of them needs on the mating side. All dimensions in
millimetres.

## Contents

- [Hex nut pockets (nut traps)](#hex-nut-pockets-nut-traps)
- [Self-tapping screws](#self-tapping-screws)
- [Tapped (cut) threads](#tapped-cut-threads)
- [Clearance holes](#clearance-holes)
- [Wall thickness around a threaded hole](#wall-thickness-around-a-threaded-hole)
- [Sources](#sources)

## Hex nut pockets (nut traps)

The strongest joint available in a printed part - **166 kg pull-out** for an
M3 nut in a pocket in the bottom face, against 119 kg for a heat-set insert
and 118 kg for a screw driven straight in.
Source: [CNC Kitchen, helicoils/inserts/embedded nuts][ck-helicoil]

The load goes straight into the nut's bearing face and then into solid
plastic; nothing relies on plastic threads or on a knurl's grip.

### Nut dimensions

| Thread | AF (nominal) | AF (model) | Thickness | Pocket depth |
| ------ | ------------ | ---------- | --------- | ------------ |
| M3     | 5.5          | 5.6-5.65   | 2.4       | 2.6          |
| M4     | 7.0          | 7.1-7.15   | 3.2       | 3.4          |
| M5     | 8.0          | 8.1-8.15   | 4.0       | 4.2          |
| M6     | 10.0         | 10.1-10.15 | 5.0       | 5.2          |
| M8     | 13.0         | 13.1-13.15 | 6.5       | 6.7          |

Nominal across-flats and thickness are DIN 934 maxima.
Source: [DIN 934 hexagon nuts, basic dimensions][din934]

"AF (model)" adds **+0.10 to +0.15 mm** on across-flats. A hexagon needs less
compensation than a circle: the six flats are straight walls that the nozzle
prints accurately, and only the six corners suffer, so the +0.4-0.5 mm that a
round bore needs would leave a hex nut rattling. Pocket depth is nut thickness
**+0.2 mm** so the nut clears and the screw pulls it up against the seat.

ISO 4032 nuts of the same thread size can be thicker than DIN 934 for M5 and
up. Measure the nut on the bench before committing a pocket depth.

### Nut pocket rules

- **Never chamfer or fillet inside the cavity.** Any edge treatment on the
  hexagon walls changes the effective across-flats and the nut spins under the
  driver. This overrides the repo's usual "lead-in at every mouth" habit - the
  *screw* hole through the far side of the pocket still gets its lead-in, the
  hexagon does not.
- **A bottom-face pocket needs a bridge.** The pocket is a void with a
  ceiling; either design the roof so the slicer can bridge it in one span, or
  leave the pocket open to the bed and accept a visible hole, or plan a
  **slicer pause** and drop the nut in mid-print.
- Side-entry pockets (a slot in from a wall) avoid the bridge entirely and let
  the nut be replaced, at the cost of a slot in the exterior.
- Add a small chamfer at the **entry** to the pocket only where the nut is
  pushed in from outside - on the entry face, not on the hexagon walls.
- A captive nut needs somewhere for the screw tip to go. Run the clearance
  hole past the nut, or add a relief pocket.

## Self-tapping screws

The screw cuts or forms its own thread in a plain pilot hole. Cheap, no
hardware, but it degrades with every cycle - budget one or two assemblies.

- **Pilot diameter = 0.75 to 0.80 x screw major diameter.** For M4:
  **3.2 to 3.6 mm**. This targets **75-80% thread engagement**, which is the
  sweet spot between stripping (too large) and splitting the boss (too small).
- **Boss OD = 2.0 to 2.5 x screw diameter.** Smaller splits; larger just wastes
  material and shrinks unevenly.
- **At least 2 mm of material around the hole**, and high infill locally.
- PETG and nylon tolerate this far better than PLA, which is brittle and
  cracks the boss.

Source: [Production Screws, self-tapping screws for plastic][prodscrews],
[Kingroon, how to screw into 3D printed parts][kingroon]

Screw type matters: a thread-forming screw for plastics (wide pitch, single
lead, e.g. Plastite/Delta PT geometry) is much better behaved in a printed
boss than a sheet-metal self-tapper, which cuts chips that pack the hole.

## Tapped (cut) threads

Cutting a standard metric thread with a tap into printed plastic. Good for a
one-off when a tap is already on the bench.

| Thread | Steel tap drill | Plastic tap drill |
| ------ | --------------- | ----------------- |
| M3     | 2.5             | 2.6-2.7           |
| M4     | 3.3             | 3.4-3.5           |
| M5     | 4.2             | 4.3-4.4           |
| M6     | 5.0             | 5.1-5.2           |

The plastic column is the standard tap drill **+0.1 to 0.2 mm**, which
compensates for the hole printing undersize and for the material relaxing back
after the tap passes. Without the adder the tap loads up and tears the thread
rather than cutting it.

- **PETG taps clean.** It is ductile enough to shear a thread instead of
  chipping.
- **PLA is brittle** - go slow, back the tap out often to clear swarf, and do
  not use a spiral-point tap that wants to push chips forward.
- Chase the thread with the actual screw before assembly; do not use the screw
  itself as the tap.
- A tapped thread in plastic is still a plastic thread: it will not take more
  torque than a self-tapper. If it needs torque, use an insert.

## Clearance holes

ISO 273 metric clearance holes, plus the FDM adder.

| Thread | Close (H12) | Normal (H13) | Loose (H14) | Model (normal) |
| ------ | ----------- | ------------ | ----------- | -------------- |
| M2     | 2.2         | 2.4          | 2.6         | 2.65           |
| M2.5   | 2.7         | 2.9          | 3.1         | 3.15           |
| M3     | 3.2         | 3.4          | 3.6         | 3.65           |
| M4     | 4.3         | 4.5          | 4.8         | 4.75           |
| M5     | 5.3         | 5.5          | 5.8         | 5.75           |
| M6     | 6.4         | 6.6          | 7.0         | 6.85           |
| M8     | 8.4         | 9.0          | 10.0        | 9.25           |

Source: [Albany County Fasteners clearance hole chart (ISO 273)][acf-clear]

"Model (normal)" is the normal-fit column **+0.25 mm** for print shrinkage.
Use it unless the slicer is compensating hole diameter, in which case use the
normal column directly.

Two constraints on the model column:

- It must stay **below the heat-set insert hole diameter** for that thread, or
  tightening jacks the insert out of its boss. M3: 3.65 against 4.2 - fine.
  Do not reach for the loose column plus an adder on an insert joint.
- Counterbores for a socket-head screw: **0.5 to 1.3 mm larger than the head
  diameter**, depth equal to the head thickness.
  Source: [SPIROL][spirol-hole]

Clearance holes **do** get a lead-in chamfer, unlike insert holes and nut
pockets - the screw self-guides and the chamfer relieves elephant's foot on a
bed-facing hole.

## Wall thickness around a threaded hole

Keep at least **1 x the fastener diameter** of material around any threaded
hole, measured from the hole wall to the nearest free surface. M3 -> 3 mm of
material all round. This is on top of, not instead of, the per-size minimum
wall in the heat-set insert table.

Where that cannot be met, move the fastener rather than thinning the wall - a
split boss is a scrapped part, and it usually splits during assembly rather
than in service, which is the expensive time to find out.

## Sources

- [CNC Kitchen - helicoils, threaded inserts and embedded nuts][ck-helicoil]
- [DIN 934 hexagon nuts - basic dimensions][din934]
- [Production Screws - self-tapping screws for plastic][prodscrews]
- [Kingroon - how to screw into 3D printed parts][kingroon]
- [Albany County Fasteners - clearance hole chart (PDF, ISO 273)][acf-clear]
- [SPIROL - how to design the proper hole][spirol-hole]

[ck-helicoil]: https://www.cnckitchen.com/blog/helicoils-threaded-insets-and-embedded-nuts-in-3d-prints-strength-amp-strength-assessment
[din934]: https://andrewsfasteners.uk/standards/din-934-hexagon-nuts-basic-dimensions/
[prodscrews]: https://productionscrews.com/self-tapping-screws-for-plastic/
[kingroon]: https://kingroon.com/blogs/3d-print-101/how-to-screw-into-3d-printed-parts
[acf-clear]: https://www.albanycountyfasteners.com/media/6b/b8/g0/1764944339/clearance-hole-chart.pdf
[spirol-hole]: https://www.spirol.com/resources/white-papers/how-to-design-the-proper-hole-for-heat-ultrasonic-inserts/
