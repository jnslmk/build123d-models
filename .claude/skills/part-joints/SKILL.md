---
name: part-joints
description: Guides choosing and sizing a joint between two 3D-printed parts in this build123d repo — everything that is not a box lid (see box-closures) and not a threaded fastener (see fasteners-and-inserts). Covers dovetails, T-slots, tongue-and-groove, pin-and-socket and dowels, crush ribs, print-in-place knuckle hinges, mortise-and-tenon, cross-dowel barrel nuts, magnet and bearing pockets, telescoping tubes and collars, and ribbed bores for tool grip. Use when two parts must plug, slide, pivot, key, hinge or press together, when picking a clearance for a mating feature, when a printed joint jams or rattles, or when adding a lead-in to a mating mouth. Keywords: joint, dovetail, T-slot, tongue and groove, pin, socket, dowel, hinge, press fit, interference fit, slip fit, telescoping, magnet pocket, bearing pocket, crush rib, ribbed bore, alignment, lead-in, clearance.
---

# Part joints

Two printed parts have to meet somewhere. This skill is the decision procedure for
that meeting: **pick the joint first, then size it.** Picking wrong is expensive —
no clearance number rescues a dovetail that should have been a pin, and a joint
that fights the print direction cannot be tuned into working.

Scope boundary:

- A box and its lid → the `box-closures` skill.
- Screws, heat-set inserts, captive nuts → the `fasteners-and-inserts` skill.
- The general question "how much gap?" and why FDM behaves the way it does →
  the `fdm-fits-and-clearances` skill.
- Everything else that joins two parts → here.

## Three rules that come before any number

### 1. A lead-in on every mating mouth

**A 45° chamfer or a 0.5 mm radius at every mouth a mating part enters.** No
exceptions: pin *and* hole, tenon *and* mortise, tube *and* socket, bearing bore,
magnet pocket, dovetail entry.

It does two things. It self-guides assembly, so a part that is 0.1 mm off-axis
still starts instead of stubbing. And it removes the sharp entry corner that
concentrates hoop stress and splits the socket on the first insertion.

This is the same rule `AGENTS.md` already states for tool holes ("always add a
lead-in at every hole mouth"), generalised: *every* mating feature is a hole
mouth. The repo's default is `BORE_MOUTH_CHAMFER = 0.8`
(`models/drill_storage_gridfinity.py:107`), cut as a boolean cone rather than an
OCC chamfer — see the `build123d-geometry-ops` skill for why.

### 2. Mating faces must have the same geometry

Flat-on-flat, or chamfer-on-chamfer. **A straight rim landing on a chamfered
shoulder touches on a thin line and wobbles**, because the only contact is where
the rim's inner corner grazes the bevel. It feels loose no matter what clearance
you pick, and the fix is never a clearance change.

The corollary catches people out: when one part is slightly *wider* than the
other — a 42 mm cover over a 41.5 mm Gridfinity body — **chamfer the wider part's
mating edge** so it clears the narrower part's edge and seats flush instead of
overhanging it. The repo does exactly this: the base's body top is left a
deliberately flat shoulder and the *cover* carries `COVER_SEAT_CH = 0.4`
(`models/drill_storage_gridfinity.py:104`, applied at `:1118`), with the reason
written into the comment at `:1054-1056`.

### 3. Lead-ins and compliant features beat tight tolerances

Design the joint to **tolerate** error, not to demand precision. FDM's run-to-run
variation on a small feature is comparable to the whole usable window between
"rattles" and "jams", so a joint whose only mechanism is a well-chosen diameter is
a joint that works on the print you calibrated on and nowhere else.

Compliance is the fix. A crush rib, a ribbed bore, a cantilever bead, a slotted
boss — anything that can *deflect* — converts a position-controlled fit into a
force-controlled one, and one number then covers a range of sizes. Crush ribs are
"far easier (and more forgiving) than trying to get the entire mating surface
exactly right"
([Hackaday](https://hackaday.com/2020/10/15/adding-crush-ribs-to-3d-printed-parts-for-a-better-press-fit/)).

This repo learned it the hard way and wrote the post-mortem down: two printed
generations of scaled ribs both failed, in opposite directions, because the ribs
were bumps welded to the wall rather than springs
(`models/drill_storage_gridfinity.py:183-214`). The fix was geometric, not
numeric. Read that comment before designing any interference feature here.

## Choose the joint

| You need | Use | First clearance to try |
| --- | --- | --- |
| Two flat panels keyed edge-to-edge, no fastener | Dovetail | 0.25 mm per face |
| A part that slides along a rail and stays captive | T-slot / tongue-and-groove | 0.2–0.5 mm per side |
| Alignment only, load carried elsewhere | Pin-and-socket / dowel | 0.1–0.2 mm |
| Free rotation about a separate pin | Pin-and-socket | 0.3–0.4 mm |
| A permanent, load-bearing shaft joint | Crush ribs (**not** a plain press fit) | ribs 0.2 mm proud |
| A hinge that comes off the bed working | Print-in-place knuckle | 0.3 mm around pin |
| A rigid, glued or friction structural corner | Mortise-and-tenon | 0.2–0.3 mm |
| A disassemblable right-angle joint with a bolt | Cross-dowel / barrel nut | bore = nut OD + 0.2–0.3 mm |
| A no-fastener closure or a repeatable index | Magnet pocket | Ø +0.2–0.3 mm |
| A rolling pivot | Bearing pocket | OD −0.05…0.10 mm per side |
| One tube entering another | Telescoping slip fit | +0.4 mm diametral |
| A round tool held with an even grip | Ribbed bore | see `references/bores-and-ribs.md` |

Full table with ranges, taper angles, failure modes and a source URL per number:
**`references/joints.md`**.

### Cross-cutting selection notes

- **Print direction decides more than clearance.** A T-slot's slide axis wants to
  lie in XY, not up Z, or the rail delaminates along the layer boundary under
  side load. A pin loaded in bending wants its axis in XY for the same reason;
  a pin that must be *round* wants its axis in Z. When those conflict, split the
  part in two and use a separate dowel.
- **A post is not a beam.** Keep a printed post shorter than 5× its diameter or
  it shears along the layer lines. Under 5 mm Ø, a printed pin is unreliable at
  all — model a hole and use an off-the-shelf pin
  ([Protolabs Network](https://www.hubs.com/knowledge-base/how-design-parts-fdm-3d-printing/)).
- **One big joint beats many small ones** (author's reasoning, not a sourced
  claim). A key joint spread across several mating pairs stacks each pair's
  tolerance and jams; a single dovetail carries the same load with one
  tolerance.
- **Prefer compliance wherever a load path allows it.** If two joints will both
  work, take the one with a spring in it.

## Then size it

Order of operations, once the joint type is chosen:

1. **Start from `references/joints.md`** for that joint's per-face clearance.
2. **Adjust for size.** Add roughly +0.05 mm per 100 mm of part dimension for
   thermal contraction. Features under 20 mm² of mating area tolerate the tight
   end of a range (0.2 mm) where large ones need the loose end (0.4 mm)
   ([Formlabs](https://formlabs.com/blog/how-to-3d-print-interlocking-joints/)).
3. **Adjust for material and process.** Per-material numbers, hole-shrink
   compensation and the underlying reasoning live in the
   `fdm-fits-and-clearances` skill — do not re-derive them here.
4. **Add the lead-in** (rule 1) and check the mating faces match (rule 2).
5. **Expose the clearance as a named constant with a comment**, never a magic
   number inline. Every fit in this repo that survived contact with a printer did
   so because someone could find and change one constant.
6. **Print a coupon before committing a whole part.** The repo's grip law was set
   by printed sweep bars, twice revised, and the comment trail at
   `models/drill_storage_gridfinity.py:183-274` is the record of why guessing did
   not work.

## Minimums and hard limits

Below these, redesign rather than tune. Sources disagree by roughly a factor of
two, so the conservative column is what to build to on a 0.4 mm nozzle.

| Feature | Absolute floor | Build to |
| --- | --- | --- |
| Hole Ø, axis vertical (Z) | 1.0 mm | 2.0 mm |
| Hole Ø, axis horizontal (XY) | 1.5 mm | 2.0 mm |
| Post / pin Ø | 1.6 mm (4× extrusion width) | 3.0 mm |
| Post height | — | < 5× its diameter |
| Wall left after a chamfer | 0.4 mm | 0.8 mm (2 perimeters) |
| Gap between neighbouring bores | 0.8 mm | 1.2 mm |

Floors from
[Protolabs Network](https://www.hubs.com/knowledge-base/how-design-parts-fdm-3d-printing/);
the ø1.8 mm pin / ø2 mm hole / 0.9 mm wall column from
[Hydra Research](https://www.hydraresearch3d.com/design-rules). A gap under about
0.3 mm does not slice as a wall at all — it simply merges.

## Worked joints already in this repo

Read the real thing before inventing a new one.

- **Telescoping collar with a snap detent** —
  `models/drill_storage_gridfinity.py`. A `COLLAR_W` collar plugs into the
  cover's `INNER_W` bore at `SLIP = 0.4` diametral (`:90`, `:100`), and an
  asymmetric ramped bead (`_snap_bead_ring`, `:416`) clicks into a rounded groove
  (`_snap_ring`, `:401`). The bead's long insertion ramp and short retention face
  are rule 3 in miniature — the earlier symmetric half-round bump fought the user
  going on (`:81-89`).
- **Telescoping tube into a shroud** — `models/wall_bar_lamp.py:36-37`.
  `SHROUD_BORE_DIAMETER = TUBE_OUTER_DIAMETER + 0.4` over a 40 mm tube: a clean
  +0.4 mm diametral slip fit, matching the table above.
- **Hex socket slip fit** — `models/drill_storage_hex.py:51-53`.
  `HEX_CLEARANCE = 0.15` across the flats on a 6.35 mm 1/4" shank, with the
  comment explaining that the fit lives *entirely* in that number because a hex
  socket has no ribs to take up slack. The round bores next door do have ribs,
  and that is precisely why they need no such precision.
- **Ribbed bore for tool grip** — `create_base(ribbed=True)` and `cut_holes` in
  `models/drill_storage_gridfinity.py:830`. The repo's compliant-rib
  implementation, generalised in `references/bores-and-ribs.md`.

## Verify, do not eyeball

An SVG projection cannot show you a 0.2 mm gap or a rib that failed to form.
Point-sample the solid instead — `is_solid_at`-style checks with
`BRepClass3d_SolidClassifier` — and assert the mating clearance, the rib contact
radius and the wall left beside the joint. Procedure in the
`build123d-geometry-ops` skill.

## References

- `references/joints.md` — the full per-joint clearance table, taper angles,
  failure modes, scaling rule and minimums, one source URL per number.
- `references/bores-and-ribs.md` — bore sizing, ribbed bores, and bore-to-bore
  spacing, with this repo's measured constants.

## Sources

- [Formlabs — How to 3D print interlocking parts and assemblies](https://formlabs.com/blog/how-to-3d-print-interlocking-joints/)
- [Protolabs Network — How to design parts for FDM 3D printing](https://www.hubs.com/knowledge-base/how-design-parts-fdm-3d-printing/)
- [Hydra Research — Design rules and best practices for FFF](https://www.hydraresearch3d.com/design-rules)
- [Markforged — Composites design guide](https://support.markforged.com/portal/s/article/Composites-Design-Guide-1)
- [Markforged — 3D printed joinery: simplifying assembly](https://markforged.com/resources/blog/joinery-onyx)
- [Creative3DP — Press-fit tolerances for 3D printing](https://tools.creative3dp.com/blog/press-fit-tolerances-3d-printing/)
- [AON3D — Engineering fits: how to design for 3D printed assemblies](https://www.aon3d.com/applications/engineering-fits-how-to-design-for-3d-printed-assemblies/)
- [UAVMODEL — Print-in-place mechanism design: clearance tolerances, hinge geometry and joint guidelines](https://blog.uavmodel.com/3d-printer-print-in-place-mechanism-design-clearance-tolerances-hinge-geometry-and-joint-guidelines-2026/)
- [Hackaday — Adding crush ribs to 3D printed parts for a better press fit](https://hackaday.com/2020/10/15/adding-crush-ribs-to-3d-printed-parts-for-a-better-press-fit/)
