# WORKZONE wrench storage

A lightweight PETG Gridfinity bin for six WORKZONE double-open wrenches,
standing on their narrow edges in parallel, with either a separate removable
stackable lid or an explicit lidless open/stackable version. Two slotted
transverse racks support each column. The accepted compact default packs all six
into one column in **1×5 cells**; changing
`wrenches_per_column` from 1 to 6 optionally re-groups the same tools, using
connected stepped footprints where shorter columns save occupied cells.

- [Approved specification](docs/wrench-storage-specification.md) — purpose,
  accepted requirements and boundaries.
- [Accepted bin CAD contract](docs/bin-cad-contract.md) — frozen compact anchor,
  CAD proof, review artifacts and the explicit user acceptance signal.
- [Active lid CAD contract](docs/lid-cad-contract.md) — current dependent lid
  scope, technical definitions, proof predicates and human review gate.
- [Lidless CAD contract](docs/lidless-cad-contract.md) — accepted open-tray reuse,
  tall-bin anchor, stacking-rim proof predicates and pending visual acceptance.
- [Evidence and Python interfaces](docs/evidence.md) — A4 photo provenance,
  measured thicknesses, actual aligned contours and handle-support stations.

The user selected **“Accept the 1×5 bin”** on 2026-10-03 and approved proceeding
with its matching lid. The bin geometry is frozen: it remains an open, low-walled
tray with exposed heads accessible when the lid is removed. The compact footprint,
support and retrieval envelopes have CAD evidence in the accepted bin contract;
actual printed tool fit has not been established.
On 2026-10-06 the user confirmed two additional lidless variants: **open**
retains those low walls/racks; **stackable** raises walls above every wrench
and adds a rim locating the next bin. This approval changes neither the accepted
base nor the existing lid. It approves purpose/requirements, not the tall bin's
visual geometry or physical printed fit.
The subsequent **“Match walls and continuous rim”** selection and latest
instruction, **“The new agent said the spec is the same. Implement the wall and
base like the references gridfinity bins at
/home/jonas/git-projects/cad-and-3d/gridfinity-bins”**, authorize replacing the
tall part's inherited low-tray exterior and feet with the actual reference-style
base and one continuous rounded wall from the foot/body transition. This is an
accepted WS-12 delta, not a requirement to preserve old base solids inside the
tall part. Tool poses, rack slots/seats, all grouping choices and connected
stepped footprints remain fixed. Public low `base`/family root/`open` and the
separate lid remain unchanged.

## Printable parts and inspection scenes

| Model | Role |
| --- | --- |
| `wrench_storage` / `wrench_storage.base` | The same printable bin, base-down on `z=0`; the family root remains the bin, not a closed assembly. |
| `wrench_storage.open` | Explicit lidless open tray: reuses the accepted `base` geometry and checks, including low walls, exposed heads and support racks; base-down on `z=0`. |
| `wrench_storage.stackable` | Lidless tall-wall bin with an open mouth and locating rim for the next bin; same tools, support racks, lightweight base and grouping choices; base-down on `z=0`. |
| `wrench_storage.lid` | One-piece printable lid, socket mouths down on `z=0`, cover mouth/skirt upward. `support=True` is the default and adds removable socket supports; `support=False` returns the clean lid in the same print pose. |
| `wrench_storage.preview` | Open inspection scene: actual bin and coloured photo-approximate tool envelopes. Not printable tools or a print layout. |
| `wrench_storage.closed` | Closed inspection scene: the same bin/tools in their canonical pose plus one translucent seated lid, without sacrificial supports. Transparency is for review, not a material requirement. |

Both lidless defaults retain the **1×5-cell** compact grouping. The accepted open
tray measures **41.5×209.5 mm**, with a **14 mm rim / 19.079 mm maximum rack
height**. The tall replacement requires **3.75 mm outer corner radii**,
**1 mm nominal continuous body walls**, and reference feet with **0.8/1.8/2.15 mm**
vertical stages (**4.75 mm total**) and **0.8/1.6/3.75 mm** radius levels.
The lightweight cleaned base follows the occupied outline rather than retaining
the low tray's exterior. The continuous locating rim retains explicitly
documented access/bearing adaptations; it is not claimed to be an exact standard
lip. The replacement measures **41.5×209.5×53 mm**, with **49 mm stacking
pitch** and **5.989 mm tool headroom**. The final gate passes **1356 assertions
with zero failures** across all six groupings. An independently built actual
reference matches all **88 sampled foot/body exterior comparisons**. Earlier
52.65 mm height and the 1023-assertion gate are historical, not replacement proof.
Current STL/GLB/HTML and reference/stacking drawings are recorded in the
[lidless contract](docs/lidless-cad-contract.md).
Human geometry acceptance, printed fit and load capacity remain unverified.

For covered storage, use the **same `wrenches_per_column` value for bin and lid**.
For lidless stacking, use the same grouping for mating bins. All printable
versions default to 6, the accepted compact 1×5 grouping. Only the printable lid has a support
control; the closed scene always represents cleaned use state. Remove the socket
supports and their residual attachment nibs before seating another bin for
stacking. Bin and lid print separately; there is no glue assembly, snap, magnet,
seal, label or other retention hardware.

The lid uses an unretained sliding-fit locating skirt and flat rim landing.
Its technical baseline is a 1 mm body/roof, 1.2 mm skirt with 3 mm engagement
away from local rack passages, and 2.5 mm lower-foot stacking receivers.
Default integration exports measure 41.5×209.5 mm footprint and 40.5 mm print
height. Canonical-use receiver-floor stack datum 49 mm, interior ceiling 48 mm
and socket mouth 51.5 mm are measured from the bin's print-bed datum `z=0`,
not its interior floor at `z=5.4 mm`. Export/view succeeded; the lid's
physical CAD gate and final section inspection are recorded separately in the
active contract, not inferred from those dimensions. **With tools loaded,
lift the lid straight upward**: rack passages are not permission to tilt it
sideways across the racks or tool heads.

### Scoped lid slicing

For the user's **Centauri Carbon 0.4 mm / Jayo PETG / 0.20 mm standard** setup
in **OrcaSlicer 2.4.2**, use **0.21 mm first layer on the lid only**, followed by
**0.20 mm layers**; keep the bin's print settings separate. This phase-adjusted
slice preserves the intended effective 0.20 mm support/roof separation, whereas
the standard 0.20 mm first layer produces an effective 0.40 mm separation
despite the nominal 0.20 mm CAD gap. All 10 weak attachment necks survive in the
phase-adjusted slice; the gap core contains only their extrusion paths and beads.
The audit covers the entire lattice/edge-rail core, **not the unmeasured whole
footprint**.

The regenerated slice estimates **40.15 g and 1 h 20 min 58 s**. Only profile
inheritance was flattened for slicing; the original user profiles were
unchanged. See the [active lid contract](docs/lid-cad-contract.md#scoped-slicing-instructions-and-evidence)
for layer heights and the numerical evidence path. This first-layer adjustment
is scoped to that setup, **not a universal or calibrated printer default**;
necks surviving a slice do not prove physical removal, roof sag or load capacity.

`config.py` and `profiles.py` are the dimensional/evidence inputs. Photo outlines
are approximate and include small shadow fringes; only the supplied maximum
head/handle thicknesses are direct physical measurements. CAD/photo-envelope
proof does not establish printed fit. Lid support release, roof sag, mating fit
and stacking capacity remain printer/profile and printed-coupon dependent.
