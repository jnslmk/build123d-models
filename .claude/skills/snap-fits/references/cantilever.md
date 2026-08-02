# Cantilever snap-fit arm

The default snap-fit family: a beam fixed at the root, free at the tip, deflected
over an undercut and released. Formulas and the taper-factor table are from
Covestro (ex-Bayer), *Snap-Fit Joints for Plastics — A Design Guide*, the
governing reference for this whole family.

## Contents

- [Symbols](#symbols)
- [The three cross-sections](#the-three-cross-sections)
- [The taper factor is 1.63, not a rounding fluke](#the-taper-factor-is-163-not-a-rounding-fluke)
- [Deflection and mating force](#deflection-and-mating-force)
- [Proportions: L/t and the Q-factor](#proportions-lt-and-the-q-factor)
- [Root fillet](#root-fillet)
- [Minimum sections for FDM](#minimum-sections-for-fdm)
- [Return angle: reopenable vs. captive](#return-angle-reopenable-vs-captive)
- [A 90° return is not automatically permanent](#a-90-return-is-not-automatically-permanent)
- [Assembly limits and force targets](#assembly-limits-and-force-targets)
- [Sizing procedure](#sizing-procedure)
- [Sources](#sources)

## Symbols

| Symbol | Meaning |
| --- | --- |
| `y` | permissible deflection = the undercut the arm rides over |
| `ε` | permissible strain at the root (from `materials.md`) |
| `l` | arm length, root to tip |
| `h` | root thickness (the dimension the beam bends about) |
| `b` | root width |
| `E_s` | **secant** modulus at the working strain, not the initial tangent modulus |
| `P` | force to deflect the arm by `y` |
| `W` | force to push the mating parts together (mating force), or to separate them |
| `µ` | friction coefficient — see `materials.md` |
| `α` | lead-in (entry) angle for `W`, or the return angle for the separating force |

## The three cross-sections

Covestro Table 1 gives permissible deflection for three tapers, all sharing the
same root strain limit but trading material for deflection:

| Section | Formula | Deflection relative to constant |
| --- | --- | --- |
| Constant `h`, constant `b` | `y = 0.67 · ε·l²/h` | 1.00× (baseline) |
| **`h` tapers to `h/2` at the tip** | `y = 1.09 · ε·l²/h` | **1.63×** |
| `b` tapers to `b/4` at the tip | `y = 0.86 · ε·l²/h` | 1.28× |

Thickness taper is the one to reach for. It buys the most extra deflection per
unit of added modelling complexity, and it is a natural fit for a printed arm —
a linear loft from the root cross-section to half its thickness at the tip is
one more sketch, not a new feature.

## The taper factor is 1.63, not a rounding fluke

`1.09 / 0.67 = 1.6269` — call it 1.63. Two other manufacturers' design guides
give the same ratio independently:

| Source | Constant-section coefficient | Tapered coefficient | Ratio |
| --- | --- | --- | --- |
| Covestro | 0.67 | 1.09 | **1.627** |
| BASF | 0.92 | 1.50 | **1.630** |
| Ticona | — | — | **1.636** |

Three independent design guides land within 0.01 of each other. **Tapering the
arm's thickness to half at the tip buys +63% permissible deflection for the
same root strain, for free** — no extra length, no extra width, just a linear
taper the printer already does for nothing.

Covestro states the cost of skipping it plainly: a constant-section arm sized
for the same deflection as an optimally tapered one uses **17% more material**
and, sized for the same *envelope* instead, runs **46% higher root strain**.
Either way the untapered arm is the worse design, not just the simpler one.

## Deflection and mating force

Force to deflect the arm by `y` (rearranged so it takes `ε` directly rather
than `y`, since you size the arm *from* the strain limit):

```text
P = (b·h²/6) · (E_s·ε/l)
```

This is the force felt during assembly *and* during release — it is the arm's
own spring force at the permissible strain, independent of which way the load
runs.

Mating force — what it takes to push the parts together, riding the lead-in
angle `α` and friction `µ`:

```text
W = P · (µ + tan α) / (1 − µ·tan α)
```

The same formula gives the **separation force** if you use the *return*
angle instead of the lead-in angle — see
[Return angle](#return-angle-reopenable-vs-captive) below. A steep return angle
drives `tan α` up and `W` climbs fast; near 90° the denominator `(1 − µ·tan α)`
approaches zero and the formula says the joint cannot be pulled apart by force
on the hook at all — only by bending the arm back manually.

## Proportions: `L/t` and the Q-factor

The formulas above assume a **slender beam**: `l/h > 10:1`. Below that ratio
the arm behaves more like a short deep beam than a slender cantilever, and the
classical formula over-predicts how much it can deflect at a given root
strain. Covestro corrects for this with a factor `Q`, read off a chart keyed to
`l/h`, applied to reduce the predicted deflection.

**Treat `Q = 1` (no correction) as the conservative default.** It is
conservative in the direction that matters: it *under*-predicts how far a
short, stubby arm can safely deflect, so an arm sized this way is a bit more
timid than it needs to be rather than over-strained. If you must push an arm
below `l/h ≈ 10` and need the extra deflection, look up the actual `Q` in
Covestro's chart rather than guessing a number — do not invent a formula for it.

**For FDM, keep `l/h ≥ 5` as an absolute floor and prefer `8–10`.** Below 5 the
arm is short enough that print-scale error (a fillet that came out a little
fat, a wall that printed 0.1 mm thick) is a large fraction of `h`, and the
Q-factor correction plus ordinary FDM tolerance stack against you at once.

## Root fillet

The stress concentration lives at the root, not in the arm's body, so the
root fillet radius is not a cosmetic choice:

- **`R = 0.6·h` is the optimum** most design guides converge on.
- **`R ≥ 0.5·h`** is the standard floor — the arm cannot rely on the classical
  formulas below this without a real stress-concentration factor applied.
- **0.4 mm is the absolute floor** regardless of `h`, since it is close to the
  smallest radius a 0.4 mm nozzle resolves cleanly.

Cut this as a boolean chamfer/fillet tool rather than an OCC edge `fillet()`
where the root sits beside other features (a rib, a wall junction) — see
`build123d-geometry-ops` for why OCC edge ops are the flaky choice there.

## Minimum sections for FDM

These are floors, not targets — the formulas above still govern the actual
size once the floors are cleared:

| Feature | Minimum |
| --- | --- |
| Root thickness `h` | 1.6 mm (4 perimeters at a 0.4 mm nozzle) |
| Arm width `b` | 6 mm — see derivation below |
| Undercut `y` | 1.2 mm, **and** `y ≥ h` (below that the arm is stiffer than its own undercut and won't ride over it without gouging) |

**`b ≥ 6 mm` combines a published floor with this file's own fillet-room
check.** Protolabs Network's snap-fit guide gives a **minimum clip width of
5 mm** directly, alongside "increase the width... to improve strength" as the
preferred lever over changing thickness, since deflection scales with the
*square* of `h` but only linearly with `b` — a small width change is a cheap,
predictable way to tune stiffness without touching the strain formula
([Protolabs Network][pl-snap]). That same source's fillet rule (`R ≥ 0.5·h`)
matches the floor already stated above, which is a useful cross-check on both
numbers.

This file rounds the published 5 mm floor up to **6 mm** for one repo-specific
reason: at the root-thickness floor (`h = 1.6 mm`), two root fillets at
`R = 0.6·h` *per side* already consume `2 × (0.6 × 1.6) = 1.92 mm` across the
width before any flat land is left between them, and 5 mm leaves that land
uncomfortably thin. **Below the root-thickness floor, 5 mm from Protolabs is
the number to use; at or above it, prefer 6 mm** so the fillets and the land
between them both have room.

## Return angle: reopenable vs. captive

The face the hook rides on during *release* sets whether the joint comes apart
by hand or is meant to stay shut:

- **Lead-in (entry) face: 30°.** Shallow enough to self-guide and to keep the
  assembly force low.
- **Return face, reopenable: 40°.** A snap you expect to open again — a lid,
  an access panel. Low enough that `W` in the mating-force formula stays a
  human-scale pull.
- **Return face, captive: 85° plus a land ≥ 0.6 mm.** Not 90° flat — see below
  for why the land matters more than the angle.

## A 90° return is not automatically permanent

A perfectly square return face looks like a permanent lock, and often is not
one. The formula's denominator `(1 − µ·tan α)` blows up near `α = 90°`, which
correctly says a straight *pull* cannot separate the joint — but a square face
gives the mating part nothing to grip *sideways*. A lateral or torsional force
can walk the two faces across each other and rotate the hook clear of the
catch with **no shear failure at all** — nothing breaks, it just slides off at
an angle the pull-apart formula never modelled.

**A land length, not just a steep angle, is what makes a snap permanent.** A
flat ledge of `≥ 0.6 mm` behind the hook face gives the mating part somewhere
to sit square before any lateral force can act on it, or close the hook into a
loop the mating part cannot rotate out of. Angle alone is the wrong lever.

## Assembly limits and force targets

- **Deflection during assembly ≤ `l/8`.** Above this the beam is no longer
  behaving as a small-deflection cantilever and the linear formulas above
  stop applying — the arm is bending, not just flexing.
- **Hook-to-catch clearance: 0.4 mm.** Matches the box-closures snap-bead
  clearance; see `fdm-fits-and-clearances` if the printer needs a different
  number.
- **Mating force target: 20–50 N.** Comfortable for one-handed assembly.
- **50–100 N is the ergonomic ceiling** — above that the joint needs two hands
  or a tool, which is a sign to lower `ε`, shorten the lead-in angle, or add
  length to the arm rather than accept the force.

## Sizing procedure

1. Pick the material's permissible strain `ε` from `materials.md` — one-time or
   repeated, and derated for a printed arm loaded flat vs. across layers.
2. Pick the section: **thickness-tapered to `h/2`** unless there is a reason
   not to (a rib that needs the full root thickness at the tip, say).
3. Choose `l` and `h` together so `l/h` clears the FDM floor of 5 (prefer 8–10),
   then solve `y = 1.09·ε·l²/h` for whichever of `y`, `l`, `h` is free — usually
   `y` is fixed by the undercut you need and you solve for `l` or `h`.
4. Set `b ≥ 6 mm`, root fillet `R = 0.6·h` (floor `0.5·h`, absolute floor
   0.4 mm).
5. Compute `P`, then `W` at the lead-in angle (30°) and check it lands in
   20–50 N. If not, adjust `α`, `ε`, or the arm geometry — not the friction
   number, which you do not control.
6. Decide reopenable (40° return) or captive (85° + land ≥ 0.6 mm land, not
   angle alone).
7. Verify `y ≥ h`, deflection during assembly `≤ l/8`, and print the arm flat
   in XY per `materials.md`'s anisotropy section.

## Sources

- Covestro (ex-Bayer), *Snap-Fit Joints for Plastics — A Design Guide*:
  <https://solutions.covestro.com/-/media/covestro/solution-center/brands/downloads/imported/1556891135.pdf>
  (mirror: <https://fab.cba.mit.edu/classes/S62.12/people/vernelle.noel/Plastic_Snap_fit_design.pdf>)
  — Table 1 (deflection formulas, taper coefficients), Q-factor chart, material
  cost/strain comparison for tapered vs. constant section.
- BASF, *Snap-Fit Design Manual* — tapered/constant coefficients 1.50/0.92.
  Indexed at
  <https://fab.cba.mit.edu/classes/S62.12/people/vernelle.noel/resources.html>;
  copy at <https://www.scribd.com/document/56495232/BASF-Plastics-Snap-fit-Design-Manual>
- Ticona, *Design Guide: Snap-Fit Joints for Plastics* — tapered/constant ratio
  1.636 (via the same secondary literature that cross-checks Covestro and BASF).
- Protolabs Network — [How do you design snap-fit joints for 3D printing?][pl-snap]
  — minimum clip width (5 mm), preference for tuning width over thickness
  (deflection scales with `h²` but only linearly with `b`), minimum base
  thickness (1 mm), and fillet radius `≥ 0.5·h`.

[pl-snap]: https://www.hubs.com/knowledge-base/how-design-snap-fit-joints-3d-printing/
