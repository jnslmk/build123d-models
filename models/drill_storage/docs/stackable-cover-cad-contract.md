# Stackable cover — current CAD slice

## References

- Context: `../README.md`, `../box.py`, `../hex/README.md`.
- Specification: [stackable-cover-specification.md](stackable-cover-specification.md), revised SC-1–SC-4.
- Supporting evidence: `models.lib.gridfinity.gridfinity_foot`, `box.cover_height_for`, existing cover geometry and fit constants.

## Current slice

- Name: two-part-only keyed glue interface, accepted 2026-10-23.
- Anchor: the existing accepted stackable PETG lids, not a new base/insert design.
- Public result: exactly `lid_body` and `stacking_lips` print children; no one-piece alternative, `support` or `separate_stacking_lips` switch. Smooth covers remain unchanged.
- In scope: positive keyed location, light self-retention while curing, adhesive relief, named print poses and independent STL downloads.
- Preserve: foot fit, stack pitch, roof/tool clearance, labels and closure.
  Current native and browser evidence is recorded below; historical planar-split
  evidence is not used as new-joint proof.

### Joint design for this slice

The geometry owner selected a shallow keyed roof lap, transferring the receiver
wall/web footprint 0.4 mm into the roof to the lip child. The body keeps its
central socket floors on the bed. A 1 mm roof retains 0.6 mm beneath the lap
generally and 0.5 mm beneath adhesive reservoirs; the interior roof is unchanged.
Hard seating lands retain the original socket-floor datum; adhesive relief
sits below the lap rather than adding a bond-line stack-height allowance.

The selected PETG side relief uses `FREE` (0.4 mm diametral); sparse crush ribs
use `PRESS` (−0.10 mm diametral effective fit, 0.05 mm per side interference).
Four rounded sacrificial crush pads per actual rectangular receiver each have
0.45 mm radius and 0.15 mm tapered entering ends. The +X pad is shifted toward
−Y by `min(5 mm, socket-floor Y span / 6)` so a half-cell key pocket cannot
swallow its interference; the other pads remain at their flat midpoints.
Mating lead-ins are 0.15 mm at 45°. Key, pad and reservoir positions derive
from each actual socket-floor inner-wire bounds, including half-cell and
2.5 mm-deep bin sockets. The first socket's +X side carries one 6 mm-long,
1.2 mm-inward asymmetric key at +Y offset `min(5 mm, socket-floor Y span / 6)`.
Radial adhesive vent/reservoir slots use −Y offset
`min(7 mm, socket-floor Y span / 5)`; full 1×1 offsets remain +5/−7 mm.
Slots are 0.8 mm wide and 0.1 mm deep; uncut pocket-floor lands hard-seat.
These implementation values were reported by the geometry owner, not measured
printed fit or retention force. Holding is one-shot crush/friction, not a snap,
axial undercut or load-bearing claim.

The body prints original-central-socket-floor-down/open-mouth-up at z=0;
the lips print glue-lap-down/socket-up at z=0. To reconstruct the seated joint,
translate the body by `socket_depth`; undo the lip child's XY preview offset,
rotate it 180° about X and translate it by `socket_depth + 0.4` in Z.
These integrated transforms and geometry predicates pass the targeted gates;
printed fit and retention force remain separate physical acceptance items.

## Applicable specification constraints

| Requirement | Consequence |
| --- | --- |
| SC-1 | Full 4.4 mm foot profile enters a 4.4 mm-deep socket; lip sits at 7U + 4.4 mm and next foot's body seats at 7U. Only stackable lip widens from 41.5 to 42 mm. |
| SC-2 | Original bases and smooth covers retain their envelope and snap joints; the lip mouth's sub-perimeter wall is a user-accepted experimental exception, not proven printable. |
| SC-3 | All seven leaves print only as two named children; no public one-piece/support/split control. Smooth covers remain available unchanged. |
| SC-4 | Keyed locating, light cure-time retention and adhesive relief; preserve physical interfaces and the accepted stack pitch. Two bed-seated, XY-separated children download independently. |

## Evidence-backed dimensions

| Dimension | Value | Source |
| --- | --- | --- |
| Original 1×1 pad, body and smooth cover | 41.5 mm | `models.lib.gridfinity.PAD`, unchanged |
| Stackable lip envelope | 42 mm, +0.25 mm per side | Gridfinity draft drawing; user-authorized exception at the lip only |
| Foot lower bevel / straight band / upper bevel | 0.7 / 1.8 / 1.9 mm | `models.lib.gridfinity.FOOT_C1`, `FOOT_STRAIGHT`, `FOOT_C3` |
| Full foot seat and added lip height | 4.4 mm | `models.lib.gridfinity.BASE_H`; drawing's 2U = 14 + 4.4 mm |
| PETG socket clearance | `fits.SLIDING`, 0.22 mm diametral | `models.lib.fits` |
| Narrowest nominal lip wall | (42 − 41.5 − 0.22)/2 = 0.14 mm | Full-width foot shoulder and user-accepted thin-lip exception |
| Minimum solid cover ceiling | 1.0 mm | `box.CAP_H` |

## Open technical definitions

| Question | Resolution path | Blocking effect |
| --- | --- | --- |
| Will a 0.14 mm nominal lip wall survive PETG slicing, first-layer spread and repeated stacking? | Inspect slicer toolpath and print a fit/durability coupon with the actual machine | Cannot call this physically printable or load-bearing before testing |
| Will nominally 42 mm lips coexist in adjacent cells without touching? | Print and measure neighbouring holders in the intended grid | No tolerance budget remains inside 42 mm pitch |
| Will the new joint locate, seat and retain gently while curing without disturbing foot fit or stack height? | Inspect the integrated CAD gates, then print/dry-fit/glue a representative lid | CAD and physical acceptance are separate; cured strength and fit remain unverified |

## Service and assembly constraints

1. Print both named child STLs in their supplied poses; dry-fit the keyed joint before using PETG-compatible adhesive.
2. Fully seat the joint, keep adhesive clear of sockets/closure and retain alignment until cured. Light retention is not a substitute for a proven bond. Keep smooth covers as the unchanged no-glue option.

## Required skills

`model-documentation`, `cad-iteration`, `box-closures`, `fdm-fits-and-clearances`, `build123d-geometry-ops`.

## Current joint verification required

- [x] Both named children are valid connected bed-seated print solids, with
  keyed location, light retention and adhesive relief present.
- [x] Independent seated reassembly preserves the accepted foot socket,
  stacking pitch, solid roof/tool clearance, labels and closure.
- [x] Joint location/retention and glue relief are checked directly. Replacing
  the joint with the former planar split fails six predicates; removing only
  crush pads fails the retention predicate while the locating predicates pass.
- [x] Six cover leaf gates and the complete bin integration gate pass, including
  offset half-grid, minimum half-cell, all-half-cell, organized and taller lids.
- [x] The actual incremental build worker exports both child STLs for all seven
  leaves. Explicit per-model `.parts.json` output ownership supplies static web
  downloads without confusing smooth covers with similarly named stackable lids.
- Existing regression suite: 113 tests, one skipped; Ruff and ty pass.
- Actual Chromium/WASM proof: custom 1×1 bin lid built in 20.3 seconds; both
  downloaded child STLs measured 41.5 mm in Y (11,358 body / 52,842 lip
  triangles). Changing lid height to 9 mm hid child downloads during generation
  and completed with 64,236 preview triangles. The actual smooth-cover page
  retained its own STL control and no child controls. Default bin child downloads
  returned HTTP 200 and matched native exports byte-for-byte.

### Current raw edge survey

Counts are body/lips from the final analytic implementation, not a claim that
every edge has a certified dihedral angle. WASM OCC rejected inward wire offsets
even for unkeyed sockets; the final implementation reconstructs analytic
rounded-rectangle profiles from actual floor wire bounds and corner radii.
All seven native gates, STL-pair exports, the 113-test suite and mutation rejection
proofs were repeated, and the real WASM custom build/download scenario passed.

| Leaf | Sharp | Unclassifiable |
| --- | --- | --- |
| wood | 14 / 25 | 0 / 26 |
| metal | 42 / 25 | 0 / 26 |
| stone | 39 / 25 | 0 / 26 |
| allen | 14 / 25 | 0 / 26 |
| hex.bits | 36 / 25 | 0 / 26 |
| Dremel | 62 / 40 | 0 / 24 |
| bin, default | 20 / 1 | 0 / 50 |

Functional square boundaries retain flat glue/seating lands, key and reservoir
edges. Prior exact-edge-identity inspection mapped the upright lip's 26
unclassifiable edges to datum faces; the final audit repeats the same count
with all at z=0.4 mm (within 0.000001 mm). Their eight remaining sharp mouth
edges preserve the experimental thin receiver. Retained engraved glyph edges number 28 metal,
25 stone and 22 BITS. Dremel additionally retains its original closure/text
edges and curved pillow/lap intersections: four unclassifiable corner arcs lie
about 0.00002 mm below the lap datum and were not certified by the planar-face
identity filter. The audit is not advertised as zero-unclassifiable. Bin lap
and receiver-floor boundaries are likewise functional contact geometry.
These explicit exceptions do not establish sliced thin-wall continuity,
printed surface quality, retention force or cured joint strength.

## Historical verification — superseded support and planar-split implementations

All results in this section predate the 2026-10-23 keyed joint. They are retained
as baseline evidence only, not a claim that current geometry or exports passed.

- [x] Full foot seats to the socket floor without overlap, and the assembled stack pitch equals a whole 7 mm multiple — all five targeted cover gates passed; physical fit still pending.
- [x] Solid cap and tool-tip clearance remain under the full-depth socket — all five targeted cover gates passed.
- [x] Default support bridges the deeper socket floor in print pose and exposes the seat when removed — geometry gates passed; physical breakaway and unsupported bridge remain unverified.
- [x] Only stackable lip reaches 42 mm; original body retains 41.5 mm and snap interface — targeted gates passed.
- [x] Split children are valid connected solids on z=0; lips point socket-up and retain the complete 4.4 mm height, with substantial planar bed-adhesion faces — all five split gates passed. Bed area is not measured common glue-contact area.
- [x] Independent reassembly retains clean one-piece labels, closure and socket, with no overlapping material and a connected no-gap assembly — all five split gates passed at 0.01 mm³ Boolean tolerance.
- [x] Integration create/export smoke succeeded for all seven confirmed leaves: each yields two named valid connected children and independent STLs on z=0, including three bin parameter variations. Independent review passed; its bed-area wording nit was corrected.
- Shared split-gate red proof on representative bin specimens: reversing the lips to socket-down produced 94.108221 mm³ missing material and failed equivalence; lifting the body 0.3 mm failed pose/bed, equivalence and connectivity; lowering it 0.3 mm failed direct body/lips overlap at 223.432254 mm³. All five positive family gates, Dremel and the full bin gate passed. Ruff and ty passed.

## Historical visual review

- Views: stackable-cover isometric, socket-down projection, side section revealing the entire 4.4 mm foot/lip engagement, and neighbouring-holder view for the 42 mm lip.
- Human review: thin lip, full foot seat, support removal access and unchanged original cover/base silhouettes.
- Prior 2.5 mm-seat artifacts (`exports/drill_storage.wood.cover_stackable.html` and `_bottom.png`) are superseded; regenerate views after physical gates.
- Integration browser proof: actual Chromium live-generation and repeated cache-hit child-STL downloads passed. This is export/UI evidence, not slicing or physical glue acceptance.

## Acceptance gate

- Human confirmation: draft-spec thin 42 mm lip accepted as an experiment, despite the ~0.14 mm nominal wall and lost neighbouring-cell tolerance.
- Current accepted delta: user confirmed two-part-only printing and keyed locating/light retention/glue relief on 2026-10-23; only one-piece stackable alternatives are removed, not smooth covers.
- Current CAD/export verification: targeted gates, complete bin integration,
  old-joint/pad-removal rejection proof and seven build-worker STL-pair exports
  passed on 2026-10-23; physical acceptance remains separate.
- Physical acceptance: pending printed dry fit, retention effort, joint seating/relief, PETG adhesive compatibility and cured strength, loaded stack and adjacent-cell trials.
- Any base/insert, foot or closure redesign is outside this slice.

## Historical planar split edge survey

Integration `sharp_convex_edges` audit; counts are body / lips. Every child
had zero unclassifiable edges. Allowed boundaries were matched by exact edge
identity from planar bed faces, not a loose positional exception.

| Leaf | Raw sharp | Allowed planar bed/interface boundary | Retained original sharp |
| --- | --- | --- | --- |
| wood | 8 / 24 | 8 / 16 | 0 / 8 |
| metal | 36 / 24 | 8 / 16 | 28 / 8 |
| stone | 33 / 24 | 8 / 16 | 25 / 8 |
| allen | 8 / 24 | 8 / 16 | 0 / 8 |
| hex.bits | 30 / 24 | 8 / 16 | 22 / 8 |

Planar bed/interface boundaries intentionally remain square to preserve the
approved planar split. Retained body edges are the original engraved glyph
mouths (metal 28, stone 25, BITS 22). The eight retained lip edges on each
tool cover preserve the accepted experimental ~0.14 mm receiver-mouth profile;
chamfering them would alter it. No edge retuning was made. Bed-face area and
edge exceptions do not prove common bonded area or adhesive strength.
