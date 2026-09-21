# Stella analytical inputs

Evidence gathered 2026-09-20 for the [Stella specification](stella-specification.md)
and its current [CAD contract](cad-contract.md). This is source-backed input and
illustrative arithmetic, not accepted geometry, a load rating, or physical
validation. The agreed scope is estimates/CAD only.

## Existing hanging pose and separate frames

Primary repository sources: `../assemblies/stella_octangula.py` (`BASE_SIGNS`,
`OFFSET_SIGNS`, `tetra_vertices`, `_vertex_core_frame`, placement loops),
`../stella_config.py` and `../mount_config.py`.

- The current global pose has four upper vertices: two belonging to each
  tetrahedron. Each tetrahedron contains six lamps and its own four vertex cores.
- The six apparent crossings are deliberately separated. There is no structural
  connection between the two tetrahedra in the current model; a crossing must not
  be counted as a load-transfer joint.
- A single safety attached to one tetrahedron would not retain the other if its
  primary path failed. The accepted Round 4 architecture backs up a common
  **metal collector/master link** carrying both primary bridles. It backs up
  the upper connection, not every downstream leg, printed joint or lamp;
  detailed hardware and actual safety-arrest forces are not established.

### Headroom consequence of the 45-degree bridle limit

For the existing 1500 mm lamps, the documented gland setback is about 35 mm and
cap thickness is 15.85 mm. Thus the current mathematical edge length is about
`1500 + 2 × (35 + 15.85) = 1601.7 mm`, with half-cube coordinate
`u = 1601.7 / sqrt(8) = 566.29 mm`.

The base core reference centres remain at their mathematical vertices. Only the
**offset tetrahedron** receives the additional shift `EDGE_OFFSET / 3`, currently
`30.75 / 3 = 10.25 mm` per signed coordinate. The two upper pairs are not coplanar.

| Upper core reference pair | z above assembly origin | Horizontal reach from centreline |
| --- | ---: | ---: |
| Base tetrahedron | 566.29 mm | 800.85 mm |
| Offset tetrahedron | 576.54 mm | 815.35 mm |

At 45 degrees from vertical, required vertical rise equals horizontal reach.
A pickup above the centreline therefore needs approximately **815 mm above the
higher offset-core references**, or **826 mm above the base-core references**.
For discussion, reserve about **0.82 m of bridle rise above the higher cores**;
final sling contact points and hardware still require their own allowance.
These are placement-reference calculations, not a final rigging drawing.

## Static leg-tension sensitivity

The existing source assumes twelve 0.65 kg lamps: 7.8 kg and 76.52 N at
`g = 9.81 m/s²`. It does not provide a weighed complete-assembly mass. The 10 kg
and 12 kg rows below illustrate additional mass allowances; neither is selected.

For a symmetric example, `T = m g / (n cos(theta))`, where `n` is the number of
legs actually carrying the assumed load and theta is measured from vertical.

| Assumed total mass | Four equal legs, 45° | Two loaded legs, 45° | Two loaded legs × existing 5× factor |
| --- | ---: | ---: | ---: |
| 7.8 kg | 27.05 N/leg | 54.11 N/leg | 270.53 N/leg |
| 10 kg | 34.68 N/leg | 69.37 N/leg | 346.84 N/leg |
| 12 kg | 41.62 N/leg | 83.24 N/leg | 416.20 N/leg |

The two-loaded-leg example represents unequal sharing, not a demonstrated load
case. The 5× factor is carried from the old configuration for comparison only;
the revised calculation margins and mass allowance still need to be stated.
The existing 250 N/hub target is not automatically the appropriate leg-tension,
arm-joint or safety-arrest load.

A single bridle leg applies a force of magnitude T at its attachment, with
vertical and horizontal components. That does **not** assign T to each of the
three arm joints: resolve the node and arm geometry separately. Moments require
the actual eccentricity, `M = F × e`; static leg tension alone cannot calculate
arm bending, insert peel, or shock when a slack safety engages.

## Existing connector evidence and proof limits

Source review, not a destructive test of printed parts:

- `stella_arm.py` / `stella_config.py` currently connect the saddle through a
  **20 × 4 mm plate**, two **5 mm-wide ribs**, and a **28 × 20 × 6 mm tab**.
  The tab contains a bolt hole and an edge-open cable notch. Those dimensions
  describe geometry; they do not establish an adequate section.
- `checks.py`'s `check_stella_parts` covers selected fits, fastener access,
  intersections, point samples, and two nominal load calculations:
  `250 / (10 × 5) = 5.00 MPa` for core/bolt bearing and
  `250 / (2 × 8 × 3) = 5.21 MPa` for the two keys. Both compare with an assumed
  10 MPa sustained limit. The arithmetic is not an end-to-end structural
  analysis.
- It does not cover arm bending and deflection, tab peel, layer separation,
  notched net sections, core ligaments, fastener preload, creep, fatigue,
  profile retention, or handling moments.
- Risks to evaluate include bending in the low plate, stress at rib roots,
  tear-out beside cable cuts, and joint rotation as plastic relaxes. A prettier
  render or larger screw is not evidence against breakage.

## Printed ABS: a reference, not a four-week allowable

Primary source: Polymaker's [PolyLite ABS technical data][abs]. It reports
Young's modulus about 2247 MPa in X-Y and 2081 MPa in Z, and Z tensile strength
29.7 MPa. The HTML table duplicates an X-Y tensile-strength label, so it should
not be treated as an unambiguous design specification.

Its specimen recipe is specific: 260 °C nozzle, 90 °C bed, two shells, three
upper/lower layers, 100% infill and fan off; the published page also lists
90 °C environmental temperature for the specimens. Those conditions and the
named filament are not established for the user's prints.

The manufacturer expressly limits the typical values to reference/comparison,
not design specifications. Its HDT and glass-transition values are not creep
limits. This narrow source search found **no four-week sustained-load allowable**
for the actual printed ABS joints. A thermal, layer or creep derating adopted
for the estimate must be labelled an engineering assumption, not a measured
material property or a transferred ASA allowable.

## M3 inserts: Ø4 × 5 mm user inventory

The dimensions are supplied by the user; brand, knurl/taper, dimensional
tolerances and retention data are not. Do not substitute a similarly named
catalogue insert or silently reverse diameter and length.

Primary guidance:

- [SPIROL's insert design guide][spirol] identifies M3 coarse pitch as 0.5 mm.
  Its general heat/ultrasonic depth rule, insert length plus two pitches,
  gives **6 mm minimum host-hole depth** for a 5 mm insert. This is not screw
  length; engagement, joint stack and tip clearance still need separate checks.
- SPIROL's general boss starting range is 2–3 times insert OD: 8–12 mm for this
  inventory envelope. This is general insert-host guidance, not verified FDM
  ABS capacity. The repository's fastener skill additionally requires sufficient
  radial material and a solid load path; a small free-standing boss is not made
  structural merely by meeting an OD ratio.
- [Markforged's insert guidance][markforged] gives a surrounding/below-material
  rule of thumb for its example and stresses cavity design. Its specific cavity
  dimensions are for a different insert, not a pilot recipe for this inventory.
- [AndyMark's M3 example][andymark] has a different OD/length, while [ruthex's
  compact M3 variant][ruthex] uses another dimensional combination. “M3” alone
  does not specify the external geometry or installation hole.

**No exact pilot diameter is established by these sources for the unidentified
Ø4 × 5 mm insert.** In particular, the generic repository Ø4.2 mm M3 pilot is
for a larger insert envelope and must not be copied. The pilot, mating clearance
hole and insert-face bearing area must be coordinated to avoid jacking the
insert out. If an estimated pilot is adopted later, record it as an adjustable,
unverified installation assumption rather than a manufacturer's specification.

The selected two-M3, broad-seat arrangement is not a capacity result. Its boss
roots, load sharing, prying, head bearing, preload
retention and four-week creep still need explicit analytical treatment; merely
counting two screws does not settle those questions.

## Organic-Y core sizing calculation — 2026-09-20

This historical section records **engineering assumptions for the rejected first
body review**. It does not establish properties of the user's printed ABS.
`../stella/config.py` now describes the functional core below, not this blank.

**Provenance:** The calculation below describes the previous, uncut 46 mm blank
body. It is retained as rejected-candidate history, not a minimum section,
height requirement or proof of the functional core. The historical reservations
and screening result do not transfer to the replacement geometry.

### Forces and moments

Allow 12 kg for the complete frame, including lamps, printed parts, wiring and
hardware, provisionally split into two 6 kg tetrahedra. The actual mass remains
unweighed. For unequal sharing, screen one load-carrying primary line per
tetrahedron at the accepted 45° limit:

`T_static = 12 × 9.81 / (2 cos 45°) = 83.24 N`.

A deliberately selected 5× static calculation factor gives `T_screen = 416.20 N`.
This is not the old 250 N hub target, a dynamic model, or proof that one line
stabilizes a tetrahedron. The unequally loaded pose and its rigid-frame moments
are not solved here.

Do not assign that line tension independently to each arm. For an ideal
pin-jointed tetrahedral vertex, the three unit member directions have pairwise
dot product 1/2. In core coordinates one consistent set is
`d_i = (cos(theta_i)/sqrt(3), sin(theta_i)/sqrt(3), sqrt(2/3))`,
with `theta_i` separated by 120°. Inverting that three-member equilibrium gives
rows of norm `sqrt(3/2)`, so for any node-force direction:

`|N_i| <= sqrt(3/2) × |R| = 509.74 N`.

This bounds the ideal member forces, not preload, insert extraction or the
unknown stiffness distribution in a rigid frame. Use the entire bound as
normal force in a conservative preliminary root-section estimate.

Reserve a 32 mm maximum force eccentricity from the screened root section to
the future seat resultant. Add a separate, assumed 10 N transverse handling
force at the midpoint of a 1500 mm lamp, with its own 2× factor:

`M_screen = 509.74 × 32 + 2 × 10 × 750 = 31,311.76 N·mm`.

The full lever and adverse sum are intentional rather than an assumed equal
split between lamp ends. The use assumptions remain designated lifting points,
dismantled transport, and an independently supported structure during service.
The 10 N allowance is not an impact, snag, person, or safety-arrest case.

### ABS and print orientation

Choose the broad web flat on the bed, branches in XY, with the raised buttress
in +Z. This keeps continuous XY material across all three roots and avoids
building any branch as an upright tower. Out-of-plane forces still load layer
interfaces: a flat print does not remove anisotropy.

For this estimate assume 0.2 mm layers, at least six perimeters, and solid
structural regions, with the local printed part at **no more than 40 °C** for
the accepted 28-day duration. Neither the actual local temperature near the
lamps nor the printer's material properties has been measured.

Use the referenced 29.7 MPa Z tensile value rather than a stronger XY value:

`sigma_screen = 29.7 × 0.75 × 0.60 × 0.40 = 5.346 MPa`.

The factors respectively represent assumed process/print variability,
temperature and duration reductions. They are not manufacturer-supplied
deratings, a measured four-week creep curve, or a permissible working stress.
In particular, 28 days and 40 °C cannot be inferred from the cited short-term
tensile specimen. If the real temperature, mass, print basis or use exceeds
these assumptions, this screening comparison no longer applies.

### Inscribed root section and reservations

The 46 mm-deep body must contain a 40 × 44 mm rectangular section at `r=20 mm`,
between `z=1..45`, on every branch. For that conservative inscribed section:

| Quantity | Value |
| --- | ---: |
| Area `A = b h` | 1760 mm² |
| Out-of-plane bending modulus `Zx = b h² / 6` | 12,906.67 mm³ |
| In-plane bending modulus `Zz = h b² / 6` | 11,733.33 mm³ |
| Combined-axis bound `Z_eff = 1/sqrt(1/Zx² + 1/Zz²)` | 8681.96 mm³ |

`M/min(Zx,Zz)` alone would not bound simultaneous bending about both axes.
Cauchy–Schwarz gives
`|Mx|/Zx + |Mz|/Zz <= |M| sqrt(1/Zx² + 1/Zz²)`.
Applying a further assumed 1.25 local concentration factor:

`sigma_est = 1.25 × (509.74 / 1760 + 31,311.76 / 8681.96) = 4.870 MPa`.

The ratio to the assumed screening threshold is only **1.10**. The static and
handling calculation factors are already inside that number; this ratio is
not an additional rated safety factor.

CAD must independently prove that the calculated section and its continuous
material path exist. Each future seat receives a solid 28 × 20 × 8 mm
reservation (`r=22..42`, `z=1..9`), not a finished interface. The central
Ø48 × 44 mm solid reserve can surround a possible 26 × 12 mm sling-opening
envelope: its corner radius is 14.32 mm, leaving 9.68 mm to the guaranteed
24 mm-radius material envelope. There is no sling opening in this slice;
rounded contact, actual webbing and the remaining net sections require their
own sizing and proof after a real opening is proposed.

The valley space reserves external side access for the nominal Ø6.7 mm cable
(6.95 mm with ABS FREE allowance). The 26.8 mm bend radius, Ø21 × 45 mm
connector, coupling and hand/tool access are **not** proven by the bare core.
No holes, pilots, keys, shoulders or downstream solids are implemented here.

### What this calculation does not establish

No resolved frame stiffness, torsion/shear interaction, sling bearing or
ligament stress after cutting, insert retention, preload relaxation, profile
retention, thermal expansion, fatigue, creep deformation, shock or safety
engagement is calculated. No CAD check turns these assumed material reductions
into physical evidence. The result is a dimensioned core for human review,
not an overhead-rated component or a no-breakage prediction.

## Functional-core screen — 2026-09-20

This is historical evidence for the preceding featured candidate, not proof for
the later two-hole/web-outline amendment. The current [contract](cad-contract.md)
owns the active definition and acceptance gate. Source still implements the
**138.603 × 127 × 22 mm** candidate: **6 mm web**, localized buttresses, three
keyed seats at **z=18 mm**, six **Ø3.7 × 6 mm blind insert pilots**, three
edge-open cable passages and a **24.25 × 10.25 mm sling throat with R3 mouths**.
No old dimension was used as a minimum for that candidate.

### Load and material assumptions

Retain a stated, unweighed 12 kg complete-frame allowance, split into two
6 kg tetrahedra, and consider one loaded line per frame at 45°:
`T_static = 83.240 N`. Ideal axial-member equilibrium gives
`N_member <= sqrt(3/2) T = 101.948 N`, with radial component **58.860 N**
and normal-to-core component **83.240 N**. These are not three independent
full-magnitude loads. Rigid-frame stiffness and load redistribution are unsolved.

Separate duration from a brief handling event:

- **Sustained:** 1.5 times the above static forces, compared with
  `29.7 × 0.75 × 0.60 × 0.40 = 5.346 MPa`.
- **Short event:** 5 times static forces plus one arbitrary bending-moment
  vector of magnitude **7500 N·mm**, compared with
  `29.7 × 0.75 × 0.60 = 13.365 MPa`.
- The 7500 N·mm envelope is `2 × 10 N × 1500 mm / 4`, the full
  simply-supported span bending envelope allocated to one joint under a
  midpoint handling force. Both lamp ends must be supported; an unsupported
  cantilever, a snag, impact and safety engagement are not included.
- Use **1.5** as an assumed local stress multiplier. It is not a solved notch
  field. All process, temperature and duration factors are engineering
  assumptions, not a manufacturer's four-week allowable.

Print web-down in ABS, 0.2 mm layers, at least six perimeters and solid
structural regions. Assume the actual part stays below 40 °C for at most
28 days. The short-event comparison deliberately does not apply a four-week
creep reduction to a momentary handling load; this is a changed *analysis
model*, not an assertion of better ABS properties.

### Actual cut sections, not rectangular blank reservations

`check_core` sections the finished B-rep at eight branch stations (including
both insert axes, the inner seat edge and outer seat region), on **all three
branches**, plus two orthogonal central cuts. OCC surface properties integrate
area, centroid and the full centroidal inertia tensor with holes retained.
This is a bounded section screen, not a global stress/FEA solution.

In each branch frame the radial load is axial to the section; its vertical
offset and the normal load's actual radial lever bound bending. The inverse
2×2 inertia tensor includes the product of inertia. Bounding-box corners
bound linear stress over the whole cut; Cauchy–Schwarz applies the single
handling vector, not a full handling moment independently on each axis.
Combine the resulting normal bound with `1.5 V/A` shear using a von-Mises
comparison, then apply the local multiplier. This rectangular-beam shear
approximation is not a resolved shear-flow or torsion analysis.

The initial functional trial with 16 mm seat floors failed the outer-seat
short-event screen: **14.014 > 13.365 MPa**. Raising the floor to **18 mm**
retained the same 22 mm overall depth and 6 mm web, rather than increasing the
entire blank. In the final candidate:

| Screen | Measured estimate | Assumed threshold |
| --- | ---: | ---: |
| Worst branch sustained, r=16 mm | 2.445 MPa | 5.346 MPa |
| Worst branch short event, r=63 mm | 12.294 MPa | 13.365 MPa |
| Entire sling load on one proved 8 × 16 mm ligament, sustained | 3.802 MPa | 5.346 MPa |
| Same ligament, short event | 12.672 MPa | 13.365 MPa |

At the outer-seat controlling section, **A=839.798 mm²**,
**Itt=27221.478 mm⁴**, **Izz=141205.685 mm⁴**, and **z̄=9.558 mm**.
These are actual post-cut values, not the 46 mm blank's inscribed section.
The narrow remaining ratios are screening results, not rated safety factors.

### Joint, sling and service limits

The M3 × 12 / 7.5 mm future arm / 0.5 mm washer stack gives **4 mm
engagement**, with 1 mm unused insert length and 2 mm to the blind-well
bottom. The source-backed head envelope is ISO 4762 Ø5.5 × 3 mm
([table](https://www.aramfix.com/content/files/i762caill/datasheet%20iso%204762.pdf));
the ISO 7089 M3 washer is Ø7 × 0.5 mm
([supplier](https://maedlernorthamerica.com/partshop/washer-din-en-iso-7089-din-125-a-for-m3-32x70x05mm-material-steel-zinc-plated-pn-65315300/)).
The user's unidentified Ø4 insert still has no validated pilot recipe.

With an illustrative 80 N preload, the force/couple calculation demands
approximately **161 N sustained / 766 N short-event retention per insert**.
This is **demand only**. Host containment, screw reach and iron/driver clearance
do not establish pull-out, torque-out, prying resistance, head-bearing capacity
or preload retention. The shoulders are the intended shear path, not the screws.

The selected CT LOOPER PA's published 16 mm width is evidence; 2 mm webbing
thickness, its folded-bight geometry and the core contact suitability are
assumptions. The gate proves that the doubled unsewn bight fits through the
rounded throat and that an 8 mm closed material band remains beyond its
widened mouths. It does not certify the sling/core combination or model
the metal pickup. Keep sewn overlap out of the throat.

Cable proof is a **continuous side-loading swept envelope**, not three air
points. A connected R26.8 upper bend and external connector/grip/unplugging
envelopes clear the bare core. Exact SP16 variant dimensions, SP17 compatibility,
the matching arm, thermal motion, complete extraction, cable retention and
assembled rigging remain outside this core-only result.

The leaf command and deliberate-defect evidence are recorded in the contract.
No result here qualifies suspended use, actual ABS creep capacity or a
no-breakage prediction.

## Two-hole textile-cord attachment — definition evidence

Round 1's “as recommended” accepts knot-compatible textile cord instead of a
sewn-webbing sling; Round 2's “A” selects the separate closed attachment loop.
The cord below remains a provisional engineering selection, not a qualified
attachment; the [contract](cad-contract.md) owns sizing and implementation status.

### Cord candidate

**Petzl CORD / CORDELETTE 6MM, reference R046AA00**: nominal **6 mm nylon**,
**24 g/m**, catalogue **10 kN tensile strength**. The
[manufacturer product page](https://www.petzl.com/INT/en/Sport/Ropes/Cords)
identifies low-stretch accessory cord, CE EN 564/UIAA, and explicitly names
6 mm for a Prusik-type self-locking knot. Its reference table describes a
120 m roll; this is product identification, not a required purchase quantity.

The 10 kN figure is the cord's catalogue strength, **not a working load or a
rating of a knot, printed core, attachment loop or suspended lamp**. The
catalogue describes uses from mountaineering to home projects, while the
[CORD technical notice](https://www.petzl.com/sfc/servlet.shepherd/version/download/068Tx000002rwKuIAI)
defines its PPE climbing/mountaineering field and prohibits use outside the
product's intended limits. Neither source approves this printed lamp attachment.

### Knot and contact evidence

The CORD notice states: “A knot can reduce the cord's initial strength by half.
Use the double fisherman's knot to make a Prusik loop.” This establishes a
manufacturer-documented joining method for a CORD Prusik loop, not tested
capacity or approval for the proposed lamp loop. Do not turn the warning into
an assumed 5 kN residual strength for this assembly.

The notice requires sheath/core inspection before and after use and warns
against damaging sharp edges; wet or icy cord is less abrasion-resistant.
It supplies no numerical minimum edge/contact radius, CORD-specific tail
length, lamp-loop strength or sustained working load. These gaps remain
engineering/compatibility limits, not permission to invent manufacturer data.
Knot rules for other cord families or rappel-rope tests do not transfer.

### Attachment topology — selection basis

Round 2's **“A”** selects the closed-loop architecture now owned by
`STELLA-SUSPENSION-02` in the [specification](stella-specification.md).
The double fisherman's joining method discussed above is the implementation
starting point, not a manufacturer-approved lamp termination.

This is application-specific engineering judgment: it avoids relying on a
stopper knot being too large to pull through a hole and provides one removable,
inspectable cord member. It does **not** establish equal sharing between the
two contacts, redundancy, abrasion life or capacity. The later definition/
sizing must keep the knot away from contact and account for possible movement.

The rejected alternative was direct primary-line attachment with stopper
terminations at the holes. That would require separate treatment of each knot's
seating, possible slippage/pull-through, contact and access; no CORD-specific
instruction for that two-stopper arrangement was found.

## Implemented two-hole functional-core screen — 2026-09-21

This section records the implemented review candidate for
`led_profiles.stella.core`. It supersedes the preceding candidate as current
implementation evidence but does not erase that candidate's history. Geometry
acceptance remains pending.

### Geometry and hardware state

- Overall envelope: **138.603 × 127 × 20 mm**, flat on `z=0`, printed +Z.
- The prior smooth web outline now runs through the complete structural height.
  Only the three functional seat recesses and 0.6 mm top/bed perimeter
  treatments interrupt it; there is no inset buttress, perimeter ledge or
  electrical-cable notch.
- Three keyed seats are **28.25 × 28.25 × 3 mm** with R2.625 corners and a
  0.8 mm entry. Their six insert axes remain at r=41 and r=59 mm.
- The user's unidentified M3, Ø4 × 5 mm inserts use an estimated **Ø3.7 ×
  6 mm** straight blind pilot. The pocket bottom is at z=11 mm. The gate proves
  a 3 mm minimum floor witness, 3 mm radial host outside the installed Ø4
  envelope, and posed iron/fastener/driver clearance. It does not validate the
  pilot, insert retention or preload.
- The suspension route uses two **Ø8 mm** holes on **22 mm centres** for the
  provisional nominal-6 mm cord. The extra 2 mm is a functional movement and
  handling allowance, not a named rigid-part fit or manufacturer minimum.
  Each mouth has actual **R2** toroidal contact. Remaining material is 14 mm
  through the straight throat, 10 mm between rounded mouths, at least 8 mm
  around the pair, and 16 mm high between the contact bands.
  With the structurally preferred flat +Z pose, the lower R2 toroidal mouths
  exceed 45° near the bed. They require local removable support and
  post-print smoothing/inspection before cord contact; support-free printing
  is not claimed.
- The electrical cable remains external. The core-only gate proves solid
  former-notch valleys and open side corridors beginning at r=45 mm for the
  assumed sleeved Ø7.7 cable, r=50 mm for the coupled Ø21 connector envelope,
  and r=60 mm for the Ø40 hand/unplug envelope. Arms and the complete route
  remain deferred.

### Why the 12 mm target became 20 mm

The hardware stack can be packed into the target exactly:

`6 mm insert well + 3 mm retained floor + 3 mm keyed seat = 12 mm`.

That is accommodation, not strength. Building the same finished geometry at
12 mm and sectioning the actual B-rep rejects it:

| 12 mm trial | Result | Assumed threshold |
| --- | ---: | ---: |
| Outer-seat r=63 mm, sustained | 5.706 MPa | 5.346 MPa |
| Outer-seat r=63 mm, short event | 36.507 MPa | 13.365 MPa |
| One 8 mm outer suspension ligament, short event | 25.344 MPa | 13.365 MPa |
| 10 mm mouth bridge, short event | 20.275 MPa | 13.365 MPa |

A 19 mm trial still gives **13.748 MPa** at each r=63 mm outer-seat
short-event section and **13.517 MPa** for one outer suspension ligament,
both above 13.365 MPa. The implemented 20 mm result is the first whole-
millimetre candidate that clears all retained screens:

| 20 mm implementation | Measured estimate | Assumed threshold |
| --- | ---: | ---: |
| Worst branch sustained, r=63 mm | 2.101 MPa | 5.346 MPa |
| Worst branch short event, r=63 mm | 12.402 MPa | 13.365 MPa |
| One 8 × 16 mm outer suspension ligament, sustained | 3.802 MPa | 5.346 MPa |
| Same outer ligament, short event | 12.672 MPa | 13.365 MPa |
| 10 × 16 mm mouth bridge, sustained | 3.041 MPa | 5.346 MPa |
| Same mouth bridge, short event | 10.137 MPa | 13.365 MPa |

The +8 mm departure is therefore driven by actual post-cut branch and
suspension sections, not by inheriting the 22 mm candidate or rejected 46 mm
blank. The narrow numerical margins are screening results, not rated safety
factors.

### Assumptions, proof and limits

The load basis remains explicitly provisional: 12 kg unweighed complete-frame
allowance, one loaded primary line per structurally separate frame at 45°,
ideal member equilibrium, 1.5× sustained and 5× short-event factors, one
7500 N·mm handling-moment vector, 1.5 local multiplier, and the documented
5.346/13.365 MPa assumed ABS comparisons. Print assumptions remain 0.2 mm
layers, at least six perimeters, solid structural regions, no more than 40 °C,
and indoor use for at most 28 days.

`uv run check led_profiles.stella.core`, `uv run ruff check .` and
`uv run ty check .` pass the integrated implementation. Focused deliberate
defects prove that the revised predicates reject a reintroduced valley notch,
a blocked suspension bore and a floor reduced below 3 mm. A 12 mm geometry is
rejected by 31 section predicates; 19 mm is rejected by the four controlling
cases above.

No CAD result supplies a Petzl contact-radius or tail-length minimum, validates
the double fisherman's knot for this lamp, proves equal contact sharing or
movement/abrasion life, or turns the cord's catalogue strength into attachment
capacity. No insert pull-out, torque-out, preload retention, printed-ABS creep,
resolved frame stiffness, fatigue, impact, snag, safety-arrest or professional
qualification is established. The exact connector variant, arms, cable route,
primary-line coupling and service sequence remain deferred.

Fresh visual evidence is
`exports/led_profiles.stella.core_loop-review.html` plus the review-sheet and
individual isometric, top, side, insert-floor-section and
suspension-bridge-section PNGs with the same filename stem. These show shape;
the checks above own hidden-geometry proof.

[abs]: https://wiki.polymaker.com/polymaker-products/more-about-our-products/documents/technical-data-sheets/abs-asa/polylite-tm-abs
[spirol]: https://www.spirol.com/assets/files/ins-threaded-inserts-design-guide-us.pdf
[markforged]: https://markforged.com/resources/blog/heat-set-inserts
[andymark]: https://andymark.com/products/m3-heat-set-threaded-insert
[ruthex]: https://www.ruthex.de/en/products/ruthex-gewindeeinsatz-m3-100-stuck-made-for-voron-rx-m3x5x4-messing-gewindebuchsen-fur-3d-druck
