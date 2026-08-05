---
name: box-closures
description: >-
  Chooses and sizes the closure for a 3D-printed box, enclosure, or container in
  this build123d repo. Covers ten closure types — friction lip, flush stepped
  rabbet, annular snap bead, screw-on thread, living hinge, sliding dovetail,
  bayonet twist-lock, magnets, screw-down with heat-set inserts, and
  gasket/O-ring seals — giving the clearance, wall budget and print pose each one
  needs, plus the house rules on print orientation and flat-on-flat mating faces.
  Use when designing or fixing a lid, cap or cover, when a lid must close flush,
  when a box rattles, jams, or pops open, when deciding between a snap, a screw,
  a magnet and a twist-lock, or when the joint has to seal. Keywords: lid, cap,
  cover, box, enclosure, closure, flush, rabbet, lip, snap lid, hinge, bayonet,
  twist-lock, dovetail, magnet, gasket, seal, O-ring. Load BEFORE sizing a lid,
  cap or cover's wall thickness — the closure choice fixes the wall budget before
  any geometry is cut, and picking the wall first forecloses the good options.
  TRIGGER: about to write a lid, rim or joint clearance as a literal number;
  choose between a snap bead, screw, magnet, hinge, dovetail, bayonet or gasket;
  or a box design mentions closing, sealing, rattling, jamming, or popping open.
---

# Box closures

How a box closes is a decision, not a detail. Make it before you model the wall
thickness, because the closure sets the wall budget — not the other way round.

Pick from the table, then size it from the matching section below. Do not read the
whole catalogue.

## Decide

| Closure | Key clearance | Wall budget | Print pose | Pros / cons |
| --- | --- | --- | --- | --- |
| **1. Friction lip** | 0.2–0.4 mm diametral (0.1 mm tight) | lip ≥ 1.2 mm, body ≥ 2 mm | both mouth-up | Simplest thing that works · wears loose, PLA creeps |
| **2. Stepped rabbet (flush)** | 0.15–0.25 mm lip OD → lid bore | `body = lip + clear + lid`, lip ≥ 0.8 mm | body mouth-up, lid flipped mouth-up | Only way to a flush exterior · thick body wall, tight tolerance |
| **3. Snap bead** | 0.4 mm hook↔catch (house default) | ≥ 2 perimeters behind the bead (0.4 bead → 1.2 mm lip) | as its host joint | Audible click, no parts · needs strain math, can fatigue |
| **4. Screw-on thread** | 0.40 mm total diametral | 3 perimeters min | axis vertical, always | Repeatable, sealable · slow to model, print-calibration sensitive |
| **5. Living hinge** | none (one part) | 0.4–0.6 mm at the flexure | hinge axis in the bed plane | No fasteners, captive lid · ~25–50 cycles in FDM; TPU/PP only for real use |
| **6. Sliding dovetail** | 0.1–0.15 mm per face (0.2–0.3 mm total) | tongue ≥ 2 perimeters wide | slide axis in XY | No flex, no fatigue · slides out without a stop; ≤ 50–60 mm per dovetail |
| **7. Bayonet / twist-lock** | Ø1.2 notch on Ø0.8 column; 5° entry slack | tab chamfer 45° | lid upside-down, receiver floor-down | Fast quarter-turn, high retention · fiddly to model, needs ≥ 40 mm Ø |
| **8. Magnets** | pocket +0.2–0.3 mm Ø, depth = magnet | ≥ 0.8 mm of wall over a buried magnet (house default) | pocket opens up, or bridged | Effortless, infinite cycles · weak in shear, needs separate alignment |
| **9. Screws + heat-set inserts** | see `fasteners-and-inserts` | boss wall ≥ 1× fastener Ø | flange up | Strongest, gasket-capable, serviceable · most parts and labour |
| **10. Gasket / O-ring** | groove sized for ≤ 30 % static squeeze | 2–3 mm wall, 4 perimeters | groove up-facing | The only real seal · a bought consumable; needs 4 or 9 to compress it |

**If you are unsure, take 2 + 3.** A stepped rabbet with the snap beads buried inside
the joint is this repo's house pattern: it closes flush, needs no fasteners, and
`models/round_snap_box.py` is a working, printed reference to copy from.

Rows 1–4, 6, 7 are *retention*. Row 10 is *sealing*. They compose: a gasket does
nothing without something in rows 3–9 pressing it.

## Rules that apply to every closure

**Print pose is a hard house rule.** Every part is returned already sitting in the
orientation it lands on the bed in, so the exported STL drops straight into the
slicer. A lid modelled closed-top-up gets flipped so the open mouth faces up, then
re-seated on `z = 0`:

```python
part = Rotation(180, 0, 0) * builder.part
part = Pos(0, 0, -part.bounding_box().min.Z) * part
```

This is a rigid transform — it does not change the part, only how it is laid on the
bed. **Print orientation beats a pretty assembly view.** If you also want the closed
assembly, build a separate `seated()` that places the *use-pose* solid, as
`models/led_psu_enclosure/lid.py:118` does, and keep `create()` returning print pose.

**Mating faces must have the same geometry** — flat-on-flat or chamfer-on-chamfer. A
straight rim landing on a chamfered shoulder touches on a thin line and wobbles. If
one part is wider than the other, chamfer the *wider* part's mating edge.

**Every mouth gets a lead-in.** A chamfer or fillet at the opening of the bore, the
thread, the plug skirt, the magnet pocket. Without it the two parts have to be
perfectly aligned before they will start, and a first-layer elephant's foot on the
male part jams the joint. Cut it as a boolean, not an OCC edge op — see
`build123d-geometry-ops`.

**Every clearance here is a property of your printer, not of the design.** The
numbers below are starting points from published guides; the calibration procedure
and this repo's measured values belong to `fdm-fits-and-clearances`. Print a test
coupon before committing a 6-hour box.

**Verify in code.** A 0.3 mm gap is invisible in an SVG projection and in the viewer.
Point-sample the solid or assert the derived arithmetic — `build123d-geometry-ops`
has the technique, and `models/led_psu_enclosure/checks.py` has examples.

## Sizing workflow

1. **Fix the interior first** — what goes in, plus 0.5 mm clearance all round
   ([Protolabs][pl-enc]). See `references/enclosures.md`.
2. **Pick the row** from the table above.
3. **Spend the wall budget** in that row's column. This is where a closure choice
   becomes a wall thickness, and it is why the order matters.
4. **Derive, do not hard-code.** Put the joint's clearance in one named constant and
   compute both mating radii from it, so the two parts cannot drift apart. The house
   idiom is a `_dims()` helper returning every shared radius
   (`models/round_snap_box.py:130`).
5. **Add the edge treatment**: lead-in at the mouth, 45° chamfer on the exterior
   horizontal rings, fillet the vertical corners.
6. **Assert the joint arithmetic** in a check, then `uv run show <model>`.

## 1. Friction / press-fit lip

An unfeatured lip that holds by interference alone.

- **Clearance** 0.2–0.4 mm diametral between lip OD and lid bore; 0.1 mm if the fit
  should be genuinely tight and still removable ([3DPut tolerances][3dp-tol]).
- **Lip wall** ≥ 3 extrusion widths (1.2 mm at a 0.4 mm nozzle) so the lip is a solid
  extrusion sandwich, not two perimeters with a void. **Body wall** ≥ 2 mm
  ([Protolabs][pl-enc]).
- **Engagement** at least the lip wall × 3, or the lid cocks and binds.
- **Slope the bottom edge of the lip** (45° chamfer where it steps out from the
  body): that face is a downward overhang in the body's print pose, and unsloped it
  prints as a rough droop exactly on the sealing surface.
- **Print pose**: body mouth-up (its natural pose), lid flipped mouth-up.

Honest limitations: the fit wears looser every cycle, and PLA under sustained hoop
stress creeps — a lid left closed for a month can be loose when opened. For anything
opened daily, use PETG/ASA, or go to a snap bead (§3), which holds by geometry
instead of by interference.

`models/lens_cap.py` is the minimal example: Ø51 bore, 1.2 mm wall, 6 mm tall,
0.6 mm chamfer on the closed face. It returns *closed-top-up*, i.e. mouth on the bed
— which is the wrong way round for this rule and worth flagging rather than copying:
that pose bridges the full Ø51 solid top disc across the open tube on its way up,
well past ordinary unsupported-bridge distances, while the mouth-up pose needed by
the print-pose rule would land that disc flat on the bed (fully supported) and leave
only an open ring facing up, which bridges nothing. A lip carrying any internal
feature has the same asymmetry and must be mouth-up regardless.

## 2. Stepped rabbet (flush) — the house pattern

Recess the top of the box wall inward to a thin lip and let the lid drop *over* that
lip, so the lid's outer face is coplanar with the body. No lip stands proud.

The wall budget is asymmetric — thick body, thin lid:

```text
body_wall = lip_wall + clearance + lid_wall
lip_wall  >= 0.8 mm      (2 perimeters at a 0.4 mm nozzle)
clearance  = 0.15-0.25 mm between lip OD and lid bore
```

- The lid mouth seats **flat-on-flat** on the shoulder ring the recess creates. Do
  not chamfer that shoulder.
- **Snap beads live inside the joint** (§3), so retention never breaks the flush
  exterior.
- Lead-in on the lip's outer top edge and on the lid mouth's inner edge, so the two
  funnel together.
- Chamfer the exterior rings: the box bottom (elephant's-foot relief) and the lid
  top, which becomes the bed face once the lid is flipped.

Worked example — `models/round_snap_box.py`, constants verified against the file:

| Constant | Value | Note |
| --- | --- | --- |
| `INNER_DIA` / `INNER_HEIGHT` | 78.0 / 20.0 mm | the two numbers a user actually sets |
| `BODY_WALL` | 2.4 mm | thick: carries lip + clearance + lid |
| `LID_WALL` | 1.2 mm | thin: nests into the recess |
| `CLEARANCE` | 0.3 mm | radial gap, lip to lid bore |
| *derived* `lip_wall` | **0.9 mm** | `2.4 − 1.2 − 0.3`, above the 0.8 floor |
| `LIP_H` | 8.0 mm | recess height = lid engagement depth |
| `BEAD` | 0.4 mm | radial protrusion of both interlocking beads |
| `BEAD_DROP` / `SNAP` | 3.0 / 1.0 mm | bead centre below the rim; seated interference |
| `RING_CHAMFER` / `LEAD_IN` | 0.8 / 0.4 mm | exterior rings; joint mouths |

That 0.3 mm clearance is one step looser than the 0.15–0.25 mm this section
recommends — it is what the printed part uses, and it is the number to beat if you
want a tighter box. Whatever you choose, assert `body_wall − lid_wall − clearance
≥ 0.8` in a check; the flush geometry silently produces a 0.4 mm lip if someone
raises `LID_WALL` in the parametric UI.

## 3. Snap-fit lid (annular bead)

A continuous bead on one face of the joint dropping into a groove — or a matching
bead — on the other. The hoop has to stretch over the bead, so the whole ring is the
spring.

- **Bead height** `h = ε · d / 2`, where `ε` is the permissible strain for the
  material and `d` the ring diameter. **The strain table and the derivation live in
  `snap-fits`** — go there before choosing `h`. Do not guess a strain.
- **0.4 mm clearance** between hook and catch once seated is this repo's house
  default, not a published figure — Formlabs' own position is "there is no perfect
  clearance for any assembly," and the one clearance number on that page (0.4 mm) is
  for PCB-to-enclosure fit, where it recommends **1.5–2.0 mm for FDM** instead
  ([Formlabs][fl-snap]). Get the material-specific tolerance from `snap-fits` before
  trusting 0.4 mm on anything but PLA on a well-tuned printer.
- Leave **≥ 2 perimeters of material behind the bead**: a 0.4 mm bead wants a
  1.2 mm lip. If the rabbet lip is thinner than that, **cut the bead into the lid
  bore instead** — it is the thicker side of most flush joints.
- **Bead faces ≤ 45°** so the bead is self-supporting in either print pose. A
  triangular section ramps in *and* back out, so the lid also releases; a
  square-backed bead is a one-way lock.
- Ring stiffness scales badly. `models/round_snap_box.py` snaps a 0.4 mm bead over a
  Ø79.8 lip; `models/led_psu_enclosure` uses a 0.6 mm bead with only **0.3 mm net
  engagement** (`SNAP_BEAD 0.6 − LID_PLUG_CLEAR 0.3`) because its 221 × 121 mm
  rectangular ring is far stiffer than the small round hoop and anything deeper would
  need a pry tool.

## 4. Threaded screw-on

- **0.40 mm total diametral clearance** between male and female threads is the
  documented working default ([DrLex][drlex]). Tighten toward 0.30 mm on a
  well-calibrated machine, loosen toward 0.50 mm for PETG — that band is tuning, not
  a published figure.
- **3 perimeters minimum** in the threaded wall ([DrLex][drlex]); a thread cut
  through two perimeters is cut through nothing but the skin.
- **Pitch 3–4 mm and at least 2 full turns.** Coarse pitch is what makes a printed
  thread work: a fine pitch puts the flank inside one layer.
- **Layer height ≤ pitch / 6.** DrLex's equivalent: 0.1 mm for fine threads, 0.15 mm
  for coarser, 0.2 mm only for big lids ([DrLex][drlex]).
- **Axis vertical, always** — the thread must spiral up the layer stack. A thread on
  a horizontal axis is a staircase.
- Chamfer the leading edge of the male thread and the mouth of the female, which also
  removes the paper-thin start of the helix ([Snapmaker][snapmaker]).
- **Thread profile** (trapezoidal vs. V, and whether to use a real fastener instead)
  → `fasteners-and-inserts`.

## 5. Living hinge

A thinned web that flexes, printed as part of both halves.

- **0.4–0.6 mm thick** for FDM, minimum two layers ([Protolabs][pl-hinge]).
- The failure modes at the edges of that band and the length rule below are this
  skill's own engineering derivation, not in the source: below ~0.3 mm the hinge
  tears on the first cycles; above ~0.8 mm it will not flex, because outer-fibre
  bending strain rises with thickness for a given bend radius.
- **Length 8–12× the thickness, and ≥ 5 mm** (same derivation) — a short hinge
  concentrates all the bend strain in one place.
- The hinge **width is built up in Z**, so the flexure is continuous extrusions
  rather than a layer bond loaded in tension. Orient the part accordingly.

**Be honest about this one.** Protolabs measured an FDM living hinge failing at
**25 cycles**, and SLS PA12 hinges at **30–50 cycles**; they describe printed living
hinges as suitable for "prototyping or proof-of-concept models that only require a
few cycles" ([Protolabs][pl-hinge]). A printed living hinge in PLA or PA12 is not a
closure for a box that gets opened. It is genuinely viable only in TPU or PP, or as
the flexible section of a multi-material print. If the box will be opened more than a
few dozen times, choose another row.

## 6. Sliding dovetail

A tapered tongue on the lid running in a matching socket; the taper stops it lifting.

- **0.1–0.15 mm per mating face (0.2–0.3 mm total)** as the starting point
  ([3DPut][3dp-dovetail]). If the lid binds, the same source's tuning advice is to
  raise it **in 0.05 mm steps** and check the slicer's extrusion multiplier before
  blaming the model. Treat 0.1–0.4 mm per face as the realistic band once you are
  tuning for a specific printer and material — that wider range is not itself in the
  source, it is the same machine-dependent drift you would expect from any printed
  clearance (see `fdm-fits-and-clearances`).
- **Keep a single dovetail under 50–60 mm wide**; wider is prone to printing defects
  and reduced strength. Use several parallel dovetails on a big lid
  ([3DPut][3dp-dovetail]).
- **Slide axis in XY.** Both parts print flat and the sliding faces are vertical
  walls, which is the one place FDM holds dimension well.
- **It will slide back out.** A dovetail is pure retention in one axis only, so add a
  stop: a friction tab snapping into a recess at full insertion, an embedded magnet
  pair (§8), or a latch ([3DPut][3dp-dovetail]).
- No flexing element means no fatigue and no creep — this is the closure that does
  not wear out.

## 7. Bayonet / twist-lock

Tabs on the lid enter axial slots in the receiver, then twist into a circumferential
channel and click into a detent.

Numbers from the SnapLock parametric spec, tested on **40–100 mm** containers with
**3–6 tabs** ([SnapLock][snaplock]):

- **Snap notch Ø1.2 mm against a Ø0.8 mm column.** The notch is on the tab, the
  column on the receiver.
- **20° twist to engage, with 5° entry clearance** — 25° of entry travel before it
  locks at 20°.
- **Column protrusion 0.3–0.5 mm, with a tip fillet.** This is the whole trick:
  anything deeper "creates a permanent lock" — you get a container you cannot open.
- **45° chamfer on the tabs**, self-supporting when the lid prints upside-down.
- **Print pose**: lid upside-down with the tabs facing up; receiver right-side-up,
  floor on the plate, so the slot walls and columns print cleanly.

High retention for a quarter-turn action, and nothing is loaded continuously, so it
does not creep. The cost is modelling complexity and a diameter floor — below ~40 mm
the tabs have no arc to work with.

## 8. Magnet-retained

- **Pocket Ø = magnet Ø + 0.2–0.3 mm, depth = magnet thickness exactly**, for a firm
  press fit with no glue; keep the pocket **at least 1–2 mm from any external wall or
  edge** ([Rapid Elevation][magnets]). For a looser fit that still needs glue, the
  same source's fallback is simpler than a fixed range: **"if your magnets are too
  tight, add 0.2 mm to some or all dimensions"** and reprint — treat it as one step at
  a time, not a single target number.
- **≥ 0.8 mm of wall over a buried magnet** (2 perimeters) is this repo's house
  default, not a sourced figure. The nearest published number is Rapid Elevation's
  rule for its print-pause insertion technique — **at least 2–3 solid layers below
  the cavity** before pausing, i.e. ~0.4–0.6 mm at a typical 0.2 mm layer height —
  which is thinner than the house default because it assumes the print resumes
  cleanly over the magnet rather than the pocket being fully enclosed and dropped in
  after ([Rapid Elevation][magnets]). Holding force falls off fast with distance, so
  do not go thicker than you must either way.
- **The pocket must open upward, or be bridged.** A pocket in a downward face is an
  unsupported hole. If the magnet is buried, either pause the print and drop it in,
  or design the pocket to open up and cap it with a printed disc.
- Check the polarity convention before you commit — one flipped magnet in an
  assembled lid is unrecoverable.

Effortless to open, effectively infinite cycles, and no creep. But magnets are weak
in shear: the lid slides sideways off the box unless the joint also has a lip, a
rabbet (§2), or locating pins. Magnets are a *retention* mechanism to add to a
locating feature, not a closure on their own.

## 9. Screw-down with heat-set inserts

Threaded brass inserts melted into printed bosses; the lid bolts down.

- **Sizing — insert Ø, boss ID, boss OD, depth, screw length — is in
  `fasteners-and-inserts`.** Do not guess boss diameters here.
- Wall around a threaded hole ≥ 1× the fastener diameter ([Protolabs][pl-enc]); see
  `references/enclosures.md`.
- This is the strongest closure, the only one that reliably compresses a gasket to
  its design squeeze around a long perimeter, and fully serviceable — inserts survive
  many more cycles than printed threads.
- The cost is honest: the most parts, the most assembly labour, a heat-set tool, and
  screw heads on the exterior unless you counterbore.

`models/led_psu_enclosure/lid.py:8-12` records the trade-off it made going the other
way: fourteen screws could crush a 3 mm cord to design compression over a ~700 mm
perimeter, and one perimeter snap bead cannot.

## 10. Gasket / O-ring seal

A bought elastomer cord or O-ring in a printed groove, compressed by rows 3–9.

- **Compress a static seal by no more than 30 %** of its cross-section — the
  source's hard ceiling is a 5–30 % squeeze band across every gland series it
  publishes, with "static seals typically use about 15–30 % squeeze, and dynamic
  seals use less" ([Global O-Ring][goring]).
- **Stretch the O-ring ID by at most ~5 %** over the groove it sits on
  ([Global O-Ring][goring]).
- **Wall 2–3 mm with 4 perimeters**; increase perimeters rather than infill for
  water-tightness, and add 60 % infill if the box will see pressure
  ([Prusa][prusa-wt]).
- **The groove must face up** so it prints as a clean pocket, not a bridged void.
- **Do not print the gasket.** Prusa tested printed gaskets and none held water, even
  screwed between two parts — use a bought silicone cord or O-ring, and grease it
  ([Prusa][prusa-wt]).
- Prusa's own verdict is that no exact number can be given for a given box:
  prototype the groove ([Prusa][prusa-wt]).

In-repo example — `models/led_psu_enclosure/gasket.py` with `config.py`: a 3.0 mm
silicone cord (`GASKET_CORD`) in a groove 3.8 mm wide (`GASKET_GROOVE_W`) and 2.3 mm
deep (`GASKET_GROOVE_D`), i.e. ~23 % compression, comfortably inside the 30 % static
ceiling. The extra groove width is where the squeezed cord goes: the model draws it as
an area-conserving ellipse. The groove is centred on the rim ring at
`GASKET_INSET = RIM_WALL / 2`, and `README.md` states plainly that a single snap bead
is a dust/splash seal, not an IP65 crush.

## Related skills

- `snap-fits` — cantilever and annular snap geometry, the strain table, `h = ε·d/2`.
- `fdm-fits-and-clearances` — how to calibrate every clearance above for your printer
  and material.
- `fasteners-and-inserts` — heat-set inserts, screw bosses, thread profiles.
- `build123d-geometry-ops` — chamfers and lead-ins that do not silently fail, and
  point-sampling to verify a joint you cannot see.

## References

- `references/enclosures.md` — the general enclosure numbers a closure sits inside:
  wall, internal clearance, port cut-outs, ribs, bosses.

## Sources

[3dp-dovetail]: https://3dput.com/sliding-dovetail-lid-for-3d-printed-box-fusion-360-tutorial/
[3dp-tol]: https://3dput.com/complete-guide-to-3d-printing-tolerances-and-fit-getting-perfect-clearance-for-moving-parts/
[drlex]: https://github.com/DrLex0/print3d-customizable-screw-cap
[fl-snap]: https://formlabs.com/blog/designing-3d-printed-snap-fit-enclosures/
[goring]: https://www.globaloring.com/o-ring-groove-design/
[magnets]: https://rapidelevation.com/article-07-magnets-in-prints.html
[pl-enc]: https://www.hubs.com/knowledge-base/enclosure-design-3d-printing-step-step-guide/
[pl-hinge]: https://www.hubs.com/knowledge-base/how-design-living-hinges-3d-printing/
[prusa-wt]: https://blog.prusa3d.com/watertight-3d-printing-part-2_53638/
[snaplock]: https://github.com/flight505/SnapLock
[snapmaker]: https://www.snapmaker.com/blog/3d-printing-threads/

- Protolabs Network — [enclosure design guide][pl-enc], [living hinges][pl-hinge]
- Formlabs — [snap-fit enclosures][fl-snap],
  [interlocking joints](https://formlabs.com/blog/how-to-3d-print-interlocking-joints/)
- [SnapLock][snaplock] — bayonet parameter spec
- [DrLex customizable screw cap][drlex] — printed thread clearance
- [3DPut][3dp-dovetail] — sliding dovetail; [tolerances and fit][3dp-tol]
- [Prusa — watertight printing, part 2][prusa-wt]
- [Global O-Ring — groove design][goring]
- Magnet pockets — [Rapid Elevation][magnets]
- [Snapmaker — printing threads][snapmaker]
