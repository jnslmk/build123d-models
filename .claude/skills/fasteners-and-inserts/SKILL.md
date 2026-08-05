---
name: fasteners-and-inserts
description: >-
  Guides the choice and sizing of fasteners in 3D-printed parts: heat-set
  threaded inserts, hex nut traps and captive nuts, self-tapping screws into
  plastic bosses, cut/tapped threads, clearance holes, and printable male and
  female threads. Use when a model needs a screw joint, a boss, an insert
  pocket, a nut trap, a clearance or pilot hole, a tapped hole, or a printed
  thread; when picking M2/M2.5/M3/M4/M5/M6/M8 hardware; when sizing an insert
  pilot hole or boss outside diameter; or when deciding between an insert, a
  captive nut, a self-tapper and a printed thread. Also covers the bd_warehouse
  fastener and thread classes and their traps. Keywords - heat-set insert, heat
  set insert, threaded insert, brass insert, boss, nut trap, captive nut, nut
  pocket, self-tapping, screw, bolt, clearance hole, pilot hole, thread, tap,
  tapped hole, printed thread, IsoThread, AcmeThread, M3, M4, M5.
---

# Fasteners and inserts

How to put a screw joint into an FDM part: pick the joint type, size the hole,
size the boss, and know which of the four options actually earns its cost.
Numbers live in the references; each one carries its source.

## Get the justification right first

The usual pitch for heat-set inserts is "much stronger". That is wrong, and
repeating it leads to inserts in places that did not need them.

Measured on PETG, M3, 4 perimeters, 100% infill:

| Joint                        | Pull-out | Torque-out | Reuse cycles |
| ---------------------------- | -------- | ---------- | ------------ |
| Heat-set insert              | 119 kg   | 3 Nm       | unlimited    |
| Screw straight into plastic  | 118 kg   | 1 Nm       | poor         |
| Nut pocket in the bottom face| 166 kg   | n/a (nut)  | good         |

Source: [CNC Kitchen, Helicoils/inserts/embedded nuts][ck-helicoil]

Read it as three facts:

1. **Pull-out is a wash** between an insert and a screw driven straight into
   plastic - 119 kg vs 118 kg. An insert buys nothing on axial load.
2. **What an insert buys is torque capacity and reuse**: 3 Nm vs 1 Nm, roughly
   3x, plus unlimited assembly cycles. Anything opened repeatedly, or torqued
   by hand with a driver, wants an insert.
3. **A nut pocket in the bottom face beats both on pull-out** (166 kg) and
   costs nothing but geometry - if the part can bridge over the pocket.

So: choose on **torque, reuse and cost**, not on pull-out strength.

## Choosing the joint

| Joint            | Pick it when                                   |
| ---------------- | ---------------------------------------------- |
| Heat-set insert  | Repeated assembly, real torque, blind boss     |
| Hex nut pocket   | Max pull-out, no hardware tooling, can bridge  |
| Self-tapping     | Assemble once or twice, cheap, thick boss      |
| Tapped thread    | One-off, have a tap, PETG/nylon not PLA        |
| Printed thread   | M6+, lids/caps/adjusters, no metal wanted      |

Decision order, first match wins:

1. Will it be opened more than a handful of times, or torqued past ~1 Nm?
   **Heat-set insert.** See [references/heat-set-inserts.md][r-inserts].
2. Is the fastener axis such that a nut can sit in a pocket in the **bottom**
   face (or a side pocket), and can the slicer bridge over it? **Nut pocket** -
   strongest option, zero specialty hardware.
   See [references/alternatives.md][r-alt].
3. Is this a coarse adjuster, a screw-on lid, or a cap where metal is unwanted
   and the diameter is M6 or larger? **Printed thread.**
   See [references/threads.md][r-threads].
4. Assemble-once, low torque, thick boss available? **Self-tapping screw.**
5. Otherwise, and especially **below M5 under load: heat-set insert**. Do not
   print a small load-bearing thread.

The mating (clearance) side is always a plain hole - see the clearance-hole
table in [references/alternatives.md][r-alt].

## Sizing workflow

1. **Pick the thread size** from the load, not the look. M2-M4 covers most
   enclosure work; anything smaller is fragile in plastic.
2. **Look up the hole** in the per-size table in
   [references/heat-set-inserts.md][r-inserts] (inserts) or the pilot / tap /
   clearance tables in [references/alternatives.md][r-alt].
3. **Apply the FDM correction.** Small vertical holes print undersize. For
   inserts the repo default is **4.2 mm for M3**, not the nominal 4.0 mm, and
   **+0.2 mm on every other table row** unless hole compensation is on in the
   slicer. The conflict between the nominal table and the printed measurement
   is documented, not averaged, in the reference.
4. **Size the boss.** Table minimum is a floor, not a target. Aim for **2x the
   insert outside diameter** where space allows; **1.6x is the floor** on a
   load-bearing boss. The 2-3x figure quoted everywhere is an
   injection-moulding rule - the reference explains why it does not transfer.
5. **Set the depth.** Insert length + 2 thread pitches minimum; blind holes get
   insert length **+1 mm** as a relief well for displaced plastic; through
   holes need no extra.
6. **Check the wall.** Keep at least 1x the fastener diameter of material
   around a threaded hole, and respect the per-size minimum wall in the table.
7. **Check the mating part.** Its clearance hole must be **larger than the
   screw and smaller than the insert pilot diameter**, or tightening jacks the
   insert straight back out.
8. **Expose every value as a module constant** (`INSERT_HOLE_D`, `BOSS_OD`,
   `NUT_AF`, ...) rather than a literal, per the repo convention for fit
   numbers.

## Repo-specific rules

- **No lead-in chamfer on a heat-set insert hole.** This is a deliberate
  exception to the house rule in `AGENTS.md` ("lead-in at every hole mouth").
  The insert's own chamfer does the guiding, and a printed chamfer removes the
  material the insert needs to melt into.
  Source: [CNC Kitchen, tips and tricks for heat-set inserts][ck-tips].
  Every *other* hole in this list - clearance holes, pilot holes, printed
  thread mouths - still gets its lead-in.
- **Never chamfer or fillet inside a nut pocket.** This is a second, equally
  deliberate exception to the same `AGENTS.md` lead-in rule: an edge treatment
  on the hexagon walls changes the effective across-flats and the nut spins
  under the driver. See [references/alternatives.md][r-alt] for the full
  rule. The screw hole passing through the far side of the pocket still gets
  its lead-in - only the hexagon cavity itself is exempt.
- **Cut lead-ins with a boolean `Cone`, not an edge chamfer.** Insert bosses
  sit next to thin walls, which is exactly where OCC `chamfer` is flaky. See
  the build123d gotchas in `AGENTS.md` and the `build123d-geometry-ops` skill.
- **Print pose decides which face gets the nut pocket.** A bottom-face pocket
  is the strongest joint available, but "bottom" means bottom *in the print
  pose the model already sits in* - the part is returned print-ready, so the
  pocket must bridge, or the model must carry a slicer-pause note.
- **4-6 perimeters under a structural insert**, and solid infill locally.
  A structural boss is a perimeter structure, not an infill structure.
- **Verify boss geometry in code**, not in the viewer. Point-sample with
  `BRepClass3d_SolidClassifier` to confirm the boss wall is solid and the
  pocket depth is what the constant says.
- **A fastener is not designed until head AND driver access is asserted** —
  "the hole is the right size" and "the fastener fits" are different
  questions, and only the second one means the part can be assembled. The
  usual check, `BOLT_CLEAR_D < INSERT_D` ("the bolt cannot jack the insert
  out"), is true and useless on its own: `models/led_profiles`'s strap had its
  bolt axis sitting exactly on the arch's own flank, an M4 socket head fouled
  that flank by 2.6 mm, and the strap could not be bolted down at all — while
  `BOLT_CLEAR_D < INSERT_D` passed, right next to the failure, in
  `models/led_profiles/checks.py:761-767`. Assert clearance for the head *and*
  the driver with `models.lib.checks.fastener_clearance(part, at, head_d,
  head_h, direction=None, driver_d=None, driver_len=0.0)`, which places a
  cylinder (plus a driver-sized cylinder above it, if given) where the
  fastener has to sit and returns the mm³ of the part's own material fouling
  it — non-zero means it cannot be installed. `check_bolt_clears_arch`
  (`models/led_profiles/checks.py:877-915`) predates this helper and
  hand-rolls the same head-slug-intersected-with-the-part technique; reach for
  `fastener_clearance` in new checks instead of re-deriving it.

## Quick numbers

The three sizes this repo actually uses. Full tables, sources and the
alternatives are in the references.

| Size | Insert hole | Boss OD (2x) | Nut AF (model) | Clearance |
| ---- | ----------- | ------------ | -------------- | --------- |
| M3   | 4.2 mm      | 9.2 mm       | 5.6-5.65 mm    | 3.65 mm   |
| M4   | 5.5 mm      | 12.0 mm      | 7.1-7.15 mm    | 4.75 mm   |
| M5   | 6.6 mm      | 14.2 mm      | 8.1-8.15 mm    | 5.75 mm   |

Insert hole = table value + the FDM correction; boss OD = 2x insert OD; nut AF
= nominal across-flats + 0.10-0.15 mm; clearance = ISO normal + 0.25 mm. Each
column is derived in the reference that owns it.

## References

- [references/heat-set-inserts.md][r-inserts] - per-size dimension table, the
  two source conflicts (M3 hole size, boss diameter rule), geometry and
  installation rules, and the strength data.
- [references/alternatives.md][r-alt] - hex nut pockets, self-tapping screws,
  tapped threads, clearance holes.
- [references/threads.md][r-threads] - printable threads: overhang maths,
  clearance placement, minimum sizes, modelling rules.
- [references/bd-warehouse.md][r-bdw] - the companion library: when to use it,
  when to hand-roll, and its traps.

[ck-helicoil]: https://www.cnckitchen.com/blog/helicoils-threaded-insets-and-embedded-nuts-in-3d-prints-strength-amp-strength-assessment
[ck-tips]: https://www.cnckitchen.com/blog/tipps-amp-tricks-fr-gewindeeinstze-im-3d-druck-3awey
[r-inserts]: references/heat-set-inserts.md
[r-alt]: references/alternatives.md
[r-threads]: references/threads.md
[r-bdw]: references/bd-warehouse.md
