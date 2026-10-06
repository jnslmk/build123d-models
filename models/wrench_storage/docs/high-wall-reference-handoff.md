# Handoff: reference base and continuous tall wrench-bin body

## Executed intent and authority

Implement **`wrench_storage.stackable` only** with its own actual reference-style
base/feet and continuous rounded occupied-perimeter wall from the foot/body
transition. This replaces the inherited accepted-low-tray exterior; it is not
merely an upward extension of that tray.

The family purpose remains compact PETG storage of the same six WORKZONE
wrenches upright on their narrow edges, with a tall lidless bin locating an
identical bin above. After the assistant acknowledged only a partial reference
match, the user's latest confirmed instruction was:

> The new agent said the spec is the same. Implement the wall and base like the references gridfinity bins at /home/jonas/git-projects/cad-and-3d/gridfinity-bins

This confirms the WS-12 purpose and decision delta. **Do not re-ask approval or
assert that preserving the old base is required because the specification is
unchanged.** Public low `base`, family root, `open` and separate lid remain
frozen; that does not freeze their solids inside the tall replacement. Finished
tall-bin geometry acceptance is still pending.

## Sources and current slice

Read the family README, accepted specification and active lidless contract.
The latter owns current measurable predicates, final implementation dimensions
and observed evidence. Read the accepted low-bin contract only for unchanged
public-part boundaries, and evidence/configuration/layout/profiles for fixed
tool poses, rack slots/seats and grouping. Use builder mode and the applicable
model-documentation, CAD-iteration, geometry-ops and PETG clearance skills.

Reference:
`/home/jonas/git-projects/cad-and-3d/gridfinity-bins/gridfinity_b123.py`:

- `_make_bin_base_single` 221–338: foot corner centres 34 mm apart; radius 0.8 at `z=0` to 1.6 at `z=0.8`, straight to `z=2.6`, then to 3.75 at `z=4.75`. Vertical stages 0.8/1.8/2.15 mm, **4.75 mm total**, not the old 4.4 mm foot.
- Ultra-light hollow: `z=1`, radius approximately 0.3858, to 0.6 at 1.2142; straight to 3.0142; to 2.75 at 5.1642. Union additional upper relief from `z=4.75`, radius approximately 2.3358, to 3.75 at 6.1642.
- `_make_bin_clean_single` 724–764 and `make_bin_clean` 767–828: actual cleaned exterior matters. Clip raw above-foot slab/block (up to `z=5.75`) to the occupied outline and hollow it; do not retain rectangular padding over omitted cells.
- Body 400–427: continuous rounded tube from `z=4.75`, nominal 1 mm wall, 41.5 mm cell width, 3.75 mm convex radius.
- Lip 430–474: 2.6 mm nominal inward width, 1.6 mm underside rise, 0.6 mm landing, 0.7/1.8/1.9 mm upper stages, radius levels 1.15/1.85/3.75 mm and 0.75 mm top trim.

Independently implement dimensional facts; no copied source or cross-repository
runtime import. Reference license is CC BY-NC-SA 4.0. Adapt the continuous
outline to connected stepped footprints without changing occupied cells.

## Completed replacement

The dedicated tall builder replaces `base.create()`-plus-extension: no old
14 mm tray seam, low-wall chamfer or 4-to-3.75 mm exterior transition remains.
It reuses fixed rack slots/seats and all six tool poses/groupings with the
reference hollow feet and continuous body. Full reference internal webs remain
at `z=5.75`: actual lower-reference/tool comparisons established that no 0.35 mm
web trim was necessary. Public low parts and lid remain unchanged.

The new-foot rim retains global front/rear access caps and positive actual
bearings. Final dimensions and the 0.4 mm minimum inner-throat radius /
51.84 mm front-cap crossing corrections are recorded in the active contract.
They are explicit functional rim adaptations, not an exact standard-lip claim.
Obsolete tall-part low-tray-retention predicates are replaced by actual reference
foot/hollow/body, supported rack and preserved seat checks.

## Evidence and completion

The previous **1023-assertion** gate and 52.65 mm top belong to the historical
partial implementation. Final untrimmed-base integration passes **1356
assertions / zero failures** across settings 1–6. Measured default bounds are
41.5×209.5×53 mm, pitch 49 mm and headroom 5.989 mm. Actual stacked solids,
loaded tools and full retrieval envelopes pass, with zero unintended overlap.
All final edge audits have zero untreated sharp/unclassifiable edges. Ruff, ty
and the five existing layout tests pass.

An independently built actual 1×5×7 source reference matches all **88 exterior
inside/outside comparisons** at foot stages and body heights. The final source
reference base over `z=0..6 mm`, minus the replacement, loses **0 mm³ reference
material**; all six reference-base/tool contact volumes are zero. This proves
actual reference base retention with required rack additions, not whole-bin
identity: the access-adapted rim and 53 versus 52.65 mm top remain explicit.
The old tray fails the reference foot/lower-body negative control.

See the [active lidless contract](lidless-cad-contract.md) for final dimensions,
edge allowances, detailed observed proof and artifact paths. Current STL/GLB/HTML
are exported. Final lower-body detail, dimensioned-reference section, side-by-side
comparison, loaded-stack section and stepped view were inspected. These are line
drawings, not shaded browser screenshots. HTML was handed to the desktop through
`gio open`; owned finite CAD process groups were confirmed empty.

Implementation and technical verification are complete. Human acceptance of this
named tall-base/body slice, printed fit, tip durability and load capacity remain
pending. No new model, cover, dependency or hardware is authorized.
