---
name: snap-fits
description: Sizes and verifies a snap-fit joint for a 3D-printed build123d part — picks the family (cantilever arm, annular bead, or torsional bar), sizes the arm or bead against a material's permissible strain, and checks the resulting deflection and mating force. Carries the strain, secant-modulus and friction data and the Covestro cantilever/annular/torsional formulas that box-closures and part-joints reference by name instead of duplicating. Use when adding, sizing or debugging a snap fit, cantilever snap, snap bead, undercut, latch, catch, or hook; when a snap arm cracks, whitens, does not release, or feels too stiff or loose; when picking a lid's bead height or an arm's length, thickness, taper or root fillet; or when checking deflection, strain or mating force against a filament (PLA, PETG, ASA, PA12). Keywords: snap fit, cantilever, cantilever snap, annular snap, bead, undercut, latch, catch, hook, deflection, permissible strain, secant modulus, mating force, snap arm, torsional snap.
---

# Snap fits

A snap fit is a spring, sized to a strain limit, not a shape you eyeball. Pick
the family, size it against the material's permissible strain, check the
force, then check it actually survives the print. This skill carries the
shared math; `box-closures` and `part-joints` point here instead of repeating
it.

## Scope boundary

- **A box lid closing over a rim** → `box-closures` picks the closure (rows 2
  and 3 there use the annular math from this skill). Come here for the bead
  height, go there for the joint layout.
- **A snap feature joining two non-lid parts** (a latch, a clip, a print-in-place
  catch) → `part-joints` for the joint choice, here for the strain math.
- **How much clearance the hook needs to clear the catch** →
  `fdm-fits-and-clearances` for the clearance philosophy; this skill only
  states the specific 0.4 mm hook-catch number it needs.
- **The strain/modulus/friction numbers themselves** → always
  `references/materials.md`, from every family's formulas.

## Pick the family

| Family | Shape | Use it when |
| --- | --- | --- |
| **Cantilever** | A beam, fixed at the root, free at the tip | The default. A hook, a latch, a tab, a single catch — anything that is one arm, not a full loop |
| **Annular** | A continuous bead around a full circle | A round lid, cap, or boss where the retaining feature runs all the way round — see `box-closures` §3 |
| **Torsional** | Two bars twisted about their own axis | Rare; only when geometry forces a twisting joint and a bending arm has no room. See `references/torsional.md`'s FDM caution before choosing this |

**A ring with a slit or gap in it is a cantilever, not an annular joint** —
see `references/annular.md`. If in doubt: is the retaining feature a closed
loop that has to stretch uniformly (annular), or a beam that bends at one
point (cantilever)? Most joints in this repo are cantilever or annular; reach
for torsional only when told to.

Full formulas, taper tables, and worked numbers for each family:
`references/cantilever.md`, `references/annular.md`, `references/torsional.md`.

## Size it

1. **Get the permissible strain `ε` from `references/materials.md`.** Never
   guess a strain or pull one from a moulding-resin table — PLA and PETG are
   not moulding grades and their real allowable strain (derived from the
   filament's own TDS) is far below what most web guides claim. Pick one-time
   or repeated, and derate further if the arm is loaded across layers instead
   of printed flat.
2. **Get the secant modulus `E_s` and friction `µ`** from the same file. Use
   the **flexural** modulus, not tensile — a snap arm is a beam in bending.
3. **Size the geometry** from the matching family reference: cantilever arm
   length/thickness/taper, or annular bead height `h = ε·d/2`.
4. **Compute the mating force `W`** and check it against the family's target
   band (cantilever: 20–50 N, ceiling 50–100 N).
5. **Add the lead-in and return angle**, and decide reopenable vs. captive.
6. **Verify in code** — a 0.3 mm bead or a 1.09-tapered arm is invisible in a
   projection. Assert the derived numbers (bead height, root thickness, `l/h`
   ratio) in a check; see `build123d-geometry-ops` for point-sampling
   technique.
7. **Print a test coupon** before committing a part with a snap you have not
   built before. Strain-to-failure is the one number in this whole skill that
   is worth confirming on your own printer and spool.

## Worked example — `models/round_snap_box.py`, annular family

The box and lid from `box-closures`' house pattern (stepped rabbet + buried
snap bead). Constants read from the file:

```text
INNER_DIA   = 78.0 mm
BODY_WALL   = 2.4 mm
LID_WALL    = 1.2 mm
CLEARANCE   = 0.3 mm
BEAD        = 0.4 mm   (radial protrusion of each interlocking bead)
```

**Derived lip geometry**, from `_dims()`:

```text
lip_wall = BODY_WALL − LID_WALL − CLEARANCE = 2.4 − 1.2 − 0.3 = 0.9 mm
lip_r    = (INNER_DIA/2 + BODY_WALL) − LID_WALL − CLEARANCE = 39.9 mm
lip OD   = 2 · lip_r = 79.8 mm
```

**Apply the annular headline formula** (`references/annular.md`) to the
bead: a radial bead height of `BEAD = 0.4 mm` is a **diametral** interference
of `y = 2·BEAD = 0.8 mm` riding over the Ø79.8 mm lip:

```text
ε = y / d = 0.8 / 79.8 = 1.0%
```

**That number lands exactly on PLA's one-shot strain ceiling** (1.0%, from
`materials.md`) — and **over** PLA's repeated-use limit (0.6%). In PETG
(one-shot ceiling 1.7%, repeated 1.0%) the same joint sits comfortably inside
both limits.

Why it likely survives in PLA anyway: `LID_WALL = 1.2 mm` and `lip_wall =
0.9 mm` are both thin, so the interference splits across two flexible sides
instead of loading one rigid one — the [load-sharing](references/annular.md#load-sharing-halves-the-strain)
effect in `annular.md`, which is real mechanics but not something this repo
measured or designed to. Read this as a worked example of the formula and its
headroom, not as a defect report: the box was not sized wrong, it was sized
without this margin being made explicit, and PETG removes the question
entirely.

**The margin runs the other way too, and is worth stating alongside the
favourable one.** The 1.0% figure above treats the box's external bead as the
only interference feature, riding into a plain bore. It is not: the lid cuts
its *own* internal bead into its bore (a second `Torus`, same `BEAD = 0.4 mm`
radial), so the joint is a double-bead interlock, not a single bead against a
flat wall. Accounting for both beads crossing each other — the box bead's
outer radius against the lid bead's inner radius — gives a peak diametral
interference nearer **1.0 mm** than 0.8 mm, i.e. hoop strain closer to
**≈1.25%**, which is *above* PLA's one-shot ceiling rather than exactly on it.
The two margins (load-sharing pulling the effective strain down, the
double-bead geometry pulling the peak strain up) both apply to the same joint
and neither was designed to; treat the honest range for this specific box as
**1.0–1.25% in PLA**, straddling the one-shot ceiling either way, and use PETG
if the joint needs to be snapped more than once.

## Related skills

- `box-closures` — chooses the closure (rabbet, snap bead, thread…) that this
  skill's annular math sizes the bead for.
- `part-joints` — chooses the joint (dovetail, pin, hinge…) for anything that
  is not a box lid; a cantilever latch there sizes from this skill.
- `fdm-fits-and-clearances` — the clearance philosophy behind the 0.4 mm
  hook-to-catch number used throughout.
- `build123d-geometry-ops` — booleans over OCC edge ops for root fillets and
  bead sections, and point-sampling to verify a joint you cannot see.

## References

- `references/cantilever.md` — deflection formulas for all three cross-sections,
  the 1.63× taper factor, root fillet, proportions, return-angle and force
  rules, sizing procedure.
- `references/annular.md` — `y = ε·d` and the `y`-is-diametral trap, bead
  height table, load sharing, slit rings, the remote-bead penalty.
- `references/torsional.md` — the twist-angle formulas and why this is the
  least FDM-friendly family.
- `references/materials.md` — permissible strain, secant modulus, friction,
  and the anisotropy/annealing derates every family's formula needs.
