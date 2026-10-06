# Lidless wrench-storage CAD contract

## Slice, authority and references

The current anchor is **`wrench_storage.stackable`**, a tall lidless six-wrench
bin. Accepted WS-12 now requires its **own reference-style base/feet and one
continuous rounded wall from the foot/body transition**, not an extension of the
frozen low tray. Replace inherited low-tray exterior material inside this part;
preserving every low-tray solid is explicitly not a requirement.

On 2026-10-06, after “Confirm both variants” and “Match walls and continuous rim”,
the user confirmed the purpose and replacement delta with the exact instruction:
**“The new agent said the spec is the same. Implement the wall and base like the references gridfinity bins at /home/jonas/git-projects/cad-and-3d/gridfinity-bins”**.
No renewed purpose/delta approval question is pending. This authorizes
implementation, not acceptance of the resulting geometry.

- [Public purpose](../README.md) and [accepted specification](wrench-storage-specification.md), WS-01–06, WS-08 and WS-10–12.
- [Accepted low-bin contract](bin-cad-contract.md): public `base`, family root and `open` remain frozen. `open` still reuses accepted low-bin `create()`/`check()`.
- [Separate lid contract](lid-cad-contract.md): unchanged.
- [Tool evidence](evidence.md), `config.py`, `layout.py`, `profiles.py`: unchanged tool poses, measured thicknesses and support stations.
- Reference `/home/jonas/git-projects/cad-and-3d/gridfinity-bins/gridfinity_b123.py`: `_make_bin_base_single` lines 221–338; `_make_bin_clean_single` 724–764 and `make_bin_clean` 767–828; body 400–427; lip 430–474. The cleaning/outer trimming is part of the reference geometry, not optional raw-block styling. Independently implement factual dimensions in builder mode; no source copying or runtime import. Source license: CC BY-NC-SA 4.0.

## Dimensional sources and required interfaces

| Interface | Required definition |
| --- | --- |
| Grouping | All six tools in their existing seated poses and rack slots/seats; settings 1–6, default 6 (1×5), connected occupied footprint and absent-cell omissions unchanged. |
| Reference feet | Corner centres 34 mm apart. Radius 0.8 mm at `z=0`, increasing to 1.6 mm at `z=0.8`; straight to `z=2.6`; increasing to 3.75 mm at `z=4.75`. Stage heights 0.8/1.8/2.15 mm, total 4.75 mm; square size `34 + 2r`. This is not the old library's 4.4 mm foot. |
| Reference hollowing | Ultra-light hollow starts at `z=1`, radius approximately 0.3858 mm; rises to 0.6 at `z=1.2142`, straight to `z=3.0142`, increases to 2.75 at `z=5.1642`. Additional upper relief starts at `z=4.75`, radius approximately 2.3358, increasing to 3.75 at `z=6.1642`. Apply their union, not one substituted simplified cavity. |
| Cleaned above-foot structure | Reference raw slab/block reaches `z=5.75`; clip to the continuous occupied outline and hollow it. Do not preserve raw rectangular padding or fill omitted stepped cells. Any necessary internal floor/rack-root accommodation must be measured and recorded explicitly, without hidden external deviations. |
| Continuous body | From `z=4.75`, one rounded occupied-perimeter body: 41.5 mm cell width (0.25 mm grid setback per side), outer convex radius 3.75 mm and nominal wall 1 mm. No old 14 mm tray shoulder, chamfer or 4-to-3.75 mm corner transition survives. |
| Reference lip baseline | Nominal inward width 2.6 mm, underside rise 1.6 mm for 1 mm walls, 0.6 mm landing, 0.7 mm lower bevel, 1.8 mm straight locating band, 1.9 mm upper chamfer, 0.75 mm top trim; radius levels 1.15/1.85/3.75 mm. Reference base/body match is distinct from retained functional rim adaptations. |
| Functional rim | Preserve continuous global front/rear access caps and positive actual foot bearings. Adapt its mating profile to the new reference feet; document final radial/vertical clearances, landing widths, stack datum and tip dimensions. Do not claim an exact standard lip merely because stacking works. |
| Print/service | Builder implementation, PETG, one printable solid base-down at `z=0`, open mouth, no cover or removable support. Same grouping for mating bins; individual straight vertical retrieval. No snap, seal or load-rating claim. |

The unchanged low-bin default is 41.5×209.5 mm, low rim 14 mm, maximum rack
height 19.079 mm and seated tool-envelope top 43.011 mm above the print bed.
These are low-bin evidence, not newly measured replacement dimensions. Fixed
tool poses and rack slot/seat geometry remain requirements even if internal
rack-root joining material needs explicit accommodation.

### Final implementation dimensions

The final untrimmed-base implementation uses the following dimensions, with
integration proof recorded below:

- Foot widths at the three radius levels are 35.6/37.2/41.5 mm. The raw slab is `z=4.75..5.75`, clipped to the continuous 3.75 mm corner outline. An independently built outer 1 mm body wall protects the reference hollow relief from breaking through the exterior.
- Full reference seam webs remain at `z=5.75`; there is no internal 0.35 mm trim. A direct measurement against the actual reference's lower 6 mm found zero overlap for every fixed seated tool envelope, disproving the initial assumption that a higher web top would obstruct the tools. Racks reuse `base._rack` against the new unhollowed-feet/outline mask; slots, seats and tool poses remain unchanged.
- Rim mating stages become 0.8/1.8/2.15 mm for the actual new foot. Bottom inset is 2.95 mm, shoulder inset/rise 3.95/2.95 mm, landing 0.6 mm, edge bevel 0.2 mm, top trim 0.75 mm and radial receiver gap 0.11 mm. Global front inset cap remains 1.8 mm and rear tool-envelope caps remain.
- Flat side bearing is 0.8 mm; rear flat width is `min(3.95, rear_cap) - 0.2 - 2.95` (0.35 mm for the default). Actual side/back contact passes in the final all-grouping run. Default pitch is 49 mm and measured top is 53 mm. These rim adaptations preserve access/bearing; they are not an exact reference-lip claim.
- The preserved 1.8 mm global front tool cap overrides the nominal straight receiver inset `2.15 - 0.11 = 2.04 mm`. Consequently the front straight receiver has 0.35 mm radial gap to the actual foot (`20.75 - 1.8 - (17 + 1.6)`), while uncapped straight walls retain 0.11 mm. This is an explicit consequence of the existing access cap, not a uniform-clearance claim; front bearing remains unnecessary.
- Inner rim throat corners retain at least 0.4 mm radius. A 3.95 mm inset exceeds the body's 3.75 mm corner radius; allowing those corners to collapse changes loft topology and creates kinked/sharp surfaces on stepped groupings. The 0.4 mm minimum applies only to the inward rim profiles, not the reference exterior/body corners.
- The front cap remains vertical until the nominal upper-mouth inset reaches 1.8 mm (`z=51.84` for the default), then joins the 45° lead-in. An explicit section at that crossing prevents interpolation from distorting the front chamfer. Targeted default/stepped rim sections and edge surveys pass after these two corrections, with zero untreated sharp or unclassifiable edges.

## Measurable proof predicates

For every grouping 1–6, the centralized tall-bin gate must establish:

- Exactly six tools, unchanged grouping/poses/rack slots/seats, connected occupied cells and void omitted cells; one valid printable solid at `z=0`.
- Actual foot profiles at each radius/stage datum match the reference 4.75 mm foot, including rounded corners; reference hollow stages and upper relief exist with lightweight printable load paths.
- Cleaned outer structure follows the occupied outline below and above the transition. Measure any floor/rack-root accommodations and show they do not change exterior reference dimensions or fixed seat geometry.
- A continuous 1 mm body with 3.75 mm convex corners at lower, middle and upper heights on straight runs, corners and stepped transitions. No inherited low-tray seam or material-retention constraint at 14 mm.
- Supported rack roots, positive rack/tool and wall/tool clearance, walls above all seated tool tops and at least 3 mm headroom at the selected stack pitch.
- Every conservative independently constructed projected-tool XY retrieval prism clears the actual rim with explicit clearance. Discrete lifted poses alone are insufficient.
- The actual matching new foot has positive locating clearance and distributed flat side/back bearing; front bearing is not required. Test corners and stepped transitions, not just nominal XY profile overlap.
- Two actual stacked bins have no unintended intersection; loaded lower tools clear the upper bin; measured bounds agree with full height and stack pitch.
- Continuous rim and global access caps without per-cell receiver scallops or per-lane notches; hollow, roof-free cell centres remain intact.
- Exposed convex edges classified with zero untreated sharp/unclassifiable edges, scoped standard-foot/bed and raw handle-seat exceptions only; no blanket new-body/rim exception.
- A reduced-pitch negative control fails the same headroom predicate.
- Public low `base`/root/`open` and separate lid unchanged; inherited-low-tray retention predicates are retired only for the tall part.

## Current evidence state

The integration owner observed **1356 passed / zero failed assertions** from
`uv run check wrench_storage.stackable` for all six groupings after removal of
the unnecessary internal web trim. The final lower reference webs remain
`z=5.75`. All fixed seated-tool envelopes clear the actual reference's lower
6 mm with **zero overlap**. Actual loaded tool/upper-bin and retrieval overlaps
are also zero. Foot profiles, hollowing, rack load paths, omitted stepped cells,
corner walls, rim bearings and all other predicates above pass.

The default is one valid solid, **41.5×209.5×53 mm**, volume
**40800.45085333663 mm³**, stack pitch **49 mm** and headroom **5.989 mm**.
The numerical minimum Z is approximately `-1e-7 mm` (OCC tolerance), consistent
with the `z=0` print datum.

An actual external reference built as 1×5×7 is one valid solid measuring
41.5×209.5×52.65 mm. **88 independent inside/outside exterior comparisons
match** at the foot stages and body heights `z=4.76/7/13.7/14/14.3/30/43`.
This establishes sampled base/body fidelity, not an exact rim-profile match.
An earlier focused negative control rejected `base.create(6)` with
`OLD_LOWER_BODY_AND_FOOT_REJECTED`: both the reference lower-body 3.75 mm radius
predicate and `reference_foot_ok` failed for the old tray. The new predicates
pass for the replacement.

All final edge audits report **zero untreated sharp / zero unclassifiable
edges**. Scoped bed/foot/unmodified 5.75 mm web allowances and bounded raw
handle-seat exceptions are:

| Wrenches per column | Bed/foot/web allowances | Handle-seat exceptions |
| --- | ---: | ---: |
| 6 | 361 | 96 |
| 3 | 652 | 96 |
| 1 | 1912 | 96 |
| 2 | 995 | 96 |
| 4 | 652 | 96 |
| 5 | 652 | 96 |

No new wall/rim blanket edge exemption is used. Ruff and ty pass; all five
existing `tests.test_wrench_layout` tests pass. Dependency inspection scopes
each changed geometry/check module to this one of 106 models.

Current printable/interactive artifacts are
`exports/wrench_storage.stackable.stl`, `.glb` and `.html` (HTML about 4 MiB).
Generated rendered PNG line drawings in `exports/wrench_analysis/` include
`stackable_reference_comparison.png` (reference left, replacement right),
`stackable_reference_section.png` (dimension labels), `stackable_lower_body_detail.png`,
`stackable_loaded_stack_section.png`, `stackable_stepped_iso.png`,
`stackable_iso.png`, `stackable_side.png` and `stackable_top.png`.
These are line drawings, not shaded screenshots.
The final lower-body detail, dimensioned reference section, side-by-side
reference comparison, loaded-stack section and stepped drawing were opened
and inspected. The HTML was handed to the desktop via `gio open`; no shaded browser inspection
is claimed. Owned finite verification jobs finished and their process groups
were confirmed empty.

The final actual-source reference base extracted over `z=0..6 mm`, minus the
replacement, has **0 mm³ lost reference material**; all six original reference
base/tool contact volumes are again zero. The control is saved as
`exports/wrench_analysis/reference_base_material_control.json`. This proves
retention of the actual reference base with required rack additions, not whole
bin identity: the rim remains explicitly adapted.

### Historical evidence only

The earlier rounded-wall extension retaining the low base passed **1023
assertions** across six settings. Its default bounds were
41.5×209.5×52.65 mm, pitch 49 mm and headroom 5.989 mm. It used a 0.25 mm
4-to-3.75 mm corner transition, 3.6 mm side shoulder inset, global front/rear
access caps, 0.11 mm sliding allowance and 0.20 mm bearing bevel. Those are
historical implementation facts, not mandatory final replacement dimensions.
Its JSON/STL/GLB/HTML, drawings, edge counts, layout tests and lint/type outcomes
must not be relabelled as replacement proof. The preceding per-cell receiver
version passed 962 assertions; the unchanged low `open` reuse passed 426 in that
earlier scope. Accepted low-bin evidence remains valid for the unchanged parts.

## Review and acceptance

The current matching STL/GLB/interactive scenes and generated reference
comparisons cover the default, foot/body transition and former 14 mm junction,
rim cross-section, loaded actual two-bin section and a stepped grouping.
Reference base/body match and retained rim adaptations remain distinct:
replacement top 53 mm versus reference 52.65 mm, with the documented access
caps, shoulder/landing sizing and inward-corner treatment. A passing stacking
gate does not make these adaptations an exact standard lip.

**Human geometry acceptance remains pending.** The latest instruction accepts
the purpose/delta, not a finished shape. Printed tool fit, PETG mating fit, tip
durability, stability and load capacity remain unverified.

Required skills: `model-documentation`, `cad-iteration`,
`fdm-fits-and-clearances`, `build123d-geometry-ops`.
