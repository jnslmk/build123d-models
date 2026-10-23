# Stackable cover — current CAD slice

## References

- Context: `../README.md`, `../box.py`, `../hex/README.md`.
- Specification: [stackable-cover-specification.md](stackable-cover-specification.md), revised SC-1–SC-4.
- Supporting evidence: `models.lib.gridfinity.gridfinity_foot`, `box.cover_height_for`, existing cover geometry and fit constants.

## Current slice

- Name: two-part-only keyed glue interface with self-supporting undersides, accepted 2026-10-23.
- Anchor: the existing accepted stackable PETG lids, not a new base/insert design.
- Public result: exactly `lid_body` and `stacking_lips` print children; no one-piece alternative, `support` or `separate_stacking_lips` switch. Smooth covers remain unchanged.
- In scope: positive keyed location, light self-retention while curing, adhesive relief, named print poses and independent STL downloads. Both supplied poses must avoid unsupported precision mating cantilevers; the previous shallow-rebate joint did not meet that requirement.
- Preserve: foot fit, stack pitch, roof/tool clearance, labels and closure.
- Historical planar-split and shallow-rebate keyed-joint results below do not establish verification of the self-supporting revision.

### Joint design for this slice

The revised joint removes the broad 0.4 mm roof rebate and its unsupported
precision mating ledges. The body retains the original flat socket-floor
split plane as its bed-backed hard seating datum and full roof, apart from
discrete locating sockets and shallow adhesive channels. There is no added
bond-line allowance changing the foot seat or stack height.

The locating sockets are 45° conical recesses, 0.4 mm deep with 0.4 mm mouth
radius, closing continuously as the body prints upward. The lip child carries
tapered sacrificial locating/crush cones, 0.45 mm base radius and 0.3 mm high,
tapering to an apex. For the five upright tool covers and the bin, four cones
locate each receiver, centered 0.8 mm outward from the actual socket-floor
inner wire's straight-side midpoints. A fifth cone keys the lexicographically
first receiver on its +X side at +Y offset `min(5 mm, cell_height / 6)`,
including full/half-cell layouts. Dremel instead places its locating features
on the bed-backed inter-socket web, as detailed in its contract.
The nominal 0.05 mm radial base interference tapers toward entering clearance.
Holding is local crush/friction during cure, not a snap, axial undercut or
load-bearing claim; printed retention effort is unverified.

Adhesive relief is cut into the body's bed plane as open triangular V channels,
0.2 mm wide, 0.1 mm deep and 0.8 mm long. Their 45° sides close without a
horizontal reservoir ceiling. Flat lands remain at the original hard seating
datum. A 1 mm roof retains 0.6 mm under the locating recesses and 0.9 mm under
the channels; the Dremel's 2 mm roof retains 1.6 / 1.9 mm respectively.
The interior roof surface is unchanged. Dimensions are the geometry owner's
implementation values, not measured printed fits.

The body prints flat-socket-floor-down/open-mouth-up at z=0; the lips now
print **socket-mouth-down/joint-up** at z=0. The lip field contains no socket
roof to bridge in this pose, and its tapered cones grow from the joint face.
This replaces the earlier broad glue-lap-down/socket-up lip pose. The
experimental approximately 0.14 mm cover receiver mouths now contact the bed;
their adhesion and sliced continuity require a separate slicer/print trial.

To reconstruct the seated joint, translate the body by `socket_depth` in Z
and undo only the lip child's X preview offset. No lip flip or Z translation
is applied. The original socket-floor datum therefore remains the hard seat,
without a 0.4 mm transferred-lap allowance.

The Dremel stackable cover also replaces the inherited 3 mm exterior pillow
round with a 3 mm, 45° bevel to satisfy the supplied-pose growth requirement.
Its smooth cover retains the pillow round. This stackable-only correction
preserves the interior 2 mm roof, label, snap, socket fit and 8U pitch.

## Applicable specification constraints

| Requirement | Consequence |
| --- | --- |
| SC-1 | Full 4.4 mm foot profile enters a 4.4 mm-deep socket; lip sits at 7U + 4.4 mm and next foot's body seats at 7U. Only stackable lip widens from 41.5 to 42 mm. |
| SC-2 | Original bases and smooth covers retain their envelope and snap joints; the lip mouth's sub-perimeter wall is a user-accepted experimental exception, not proven printable. |
| SC-3 | All seven leaves print only as two named children with self-supporting underside joint geometry in the supplied poses; no public one-piece/support/split control. Smooth covers remain available unchanged. |
| SC-4 | Keyed locating, light cure-time retention and adhesive relief must not rely on unsupported horizontal precision mating ledges. Preserve physical interfaces and the accepted stack pitch. Two bed-seated, XY-separated children download independently. |

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

## Current verification — self-supporting underside revision, 2026-10-23

The geometry owner's completed integration record reports **393 passing CAD
assertions, zero failures**: 26 for each of the five upright cover leaves,
139 for Dremel and 124 for the bin lid and its six relevant layouts. Bin
coverage includes default 1×2, shifted 1.5×1.5, organized 1×1, minimum
0.5×0.5, all-half-cell and 9 mm taller-roof cases. These are geometric
predicates, not physical-print tests.

The new underside gate evaluates print-direction growth on the actual CAD
surfaces; all seven leaves had zero unsupported samples. Representative
measured results supplied by the geometry owner:

| Leaf | Body / lips bed contact (mm²) | Body / lips growth samples | Unsupported | Seated crush overlap / after 0.02 mm withdrawal (mm³) |
| --- | --- | --- | --- | --- |
| wood | 1705.68 / 22.44 | 2537 / 3735 | 0 | 0.030107 / 0.004943 |
| Dremel, corrected bevel/web joint | 2861.49 / 60.38 | 1647 / 3675 | 0 | 0.018064 / 0.002966 |
| bin, default | 3446.35 / 434.92 | Not separately recorded here | 0 | 0.054192 / 0.008897 |

Wood's protected-envelope comparison measured 0.000000 mm³ missing/extra
material. The crush overlap is intentional local retention interference,
not whole-joint collision or measured force. Bed area is neither common
bonded area nor proof of thin-mouth bed adhesion.

- Restoring the actual former broad-rebate geometry in memory made **both**
  body and lip underside predicates fail for wood, Dremel and bin:
  `exports/joint-verification/old-geometry-red.json`.
- All seven leaves exported combined STL/GLB and both named child STLs;
  Dremel was rebuilt after its bevel/web-joint correction. Ruff and ty passed.
  Earlier browser/WASM results below remain historical; they were not repeated
  as part of this revision's recorded verification.
- The final edge audit reports **361 raw sharp edges, zero unclassifiable**.
  Each retained edge has a reason in
  `exports/joint-verification/final-sharp-edges-with-reasons.json`: functional
  flat seating/glue datums, experimental thin socket-mouth bed boundaries
  preserving foot fit, unchanged detent junctions and inherited label edges.
  This is an explicit functional exception record, not a zero-sharp-edge claim.
- Wood, Dremel and bin self-contained HTML views were rebuilt and opened.
  Exact CAD section images `exports/stacking-joint-sections.png` and
  `exports/dremel-stacking-joint-sections.png` were inspected: flat body bed
  faces, sloped recesses, mouth-down walls/webs and growing cones, plus the
  corrected Dremel exterior bevel.

No slicer or printer job was run. Experimental mouth continuity/adhesion,
printed locating/crush fit, glue handling, cured PETG bond strength and loaded
stacking remain physically unaccepted.

## Historical verification — superseded shallow-rebate keyed joint

These results precede the user's self-supporting-underside correction on
2026-10-23. They establish only the earlier 0.4 mm-rebate implementation's
reported CAD/export behavior, not printable mating geometry or verification
of the revised joint. No slicing or physical printing is established here.

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

### Historical shallow-rebate raw edge survey

Counts are body/lips from the superseded analytic shallow-rebate implementation,
not current geometry or a claim that every edge has a certified dihedral angle.
WASM OCC rejected inward wire offsets even for unkeyed sockets; that revision
reconstructed analytic rounded-rectangle profiles from actual floor wire bounds
and corner radii. Its seven native gates, STL-pair exports, 113-test suite,
mutation rejection proofs and real WASM custom build/download scenario passed;
those results do not certify self-supporting undersides.

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
- Current accepted delta: user confirmed two-part-only printing and keyed locating/light retention/glue relief on 2026-10-23, then required self-supporting underside joint geometry without unsupported precision mating cantilevers. Only one-piece stackable alternatives are removed, not smooth covers.
- Earlier targeted gates, bin integration, rejection proofs and build-worker exports are historical evidence for the shallow-rebate joint, not current-revision proof.
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
