---
name: snap-fits
description: >-
  Sizes and verifies a snap-fit joint for a 3D-printed build123d part — picks the
  family (cantilever arm, annular bead, or torsional bar), sizes the arm or bead
  against a material's permissible strain, and checks the resulting deflection
  and mating force. Carries the strain, secant-modulus and friction data and the
  Covestro cantilever/annular/torsional formulas that box-closures and
  part-joints reference by name instead of duplicating. Use when adding, sizing
  or debugging a snap fit, cantilever snap, snap bead, undercut, latch, catch, or
  hook; when a snap arm cracks, whitens, does not release, or feels too stiff or
  loose; when picking a lid's bead height or an arm's length, thickness, taper or
  root fillet; or when checking deflection, strain or mating force against a
  filament (PLA, PETG, ASA, PA12). Keywords: snap fit, cantilever, cantilever
  snap, annular snap, bead, undercut, latch, catch, hook, deflection, permissible
  strain, secant modulus, mating force, snap arm, torsional snap. Load BEFORE
  sizing a cantilever arm, snap bead or torsional bar, or before typing a strain
  value — this is the one place the permissible-strain and force formulas live,
  and `box-closures`/`part-joints` reference it by name rather than repeating it.
  TRIGGER: about to compute an arm's length, thickness or taper, a bead height,
  or check deflection, strain or mating force against a filament.
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
CLEARANCE   = 0.25 mm  (radial gap, lip OD to lid bore)
BEAD        = 0.30 mm  (radial protrusion of each interlocking bead)
```

**Derived lip geometry**, from `_dims()`:

```text
lip_wall = BODY_WALL − LID_WALL − CLEARANCE = 2.4 − 1.2 − 0.25 = 0.95 mm
lip_r    = (INNER_DIA/2 + BODY_WALL) − LID_WALL − CLEARANCE = 39.95 mm
lip OD   = 2 · lip_r = 79.9 mm
```

**This is a double-bead joint, and that changes which interference you feed
the formula.** Both members carry a bead (`Torus(..., mode=Mode.ADD)` on the
lip and in the lid bore), so the lid's bead does not ride into a plain bore —
the two beads climb over *each other*. Three separate radial quantities come
out of one bead size, and they answer three different questions:

```text
peak    = 2·BEAD − CLEARANCE = 0.35 mm   beads crossing — MOMENTARY, one stroke
seated  = BEAD − CLEARANCE   = 0.05 mm   at rest — SUSTAINED while the lid is shut
barrier = peak − seated = BEAD = 0.30 mm what a pull-off climbs — the RETENTION
```

**Apply the annular headline formula** (`references/annular.md`), remembering
`y` is diametral, so each radial figure doubles:

```text
ε_momentary = 2·0.35 / 79.9 = 0.88%     ← check against the strain ceiling
ε_sustained = 2·0.05 / 79.9 = 0.13%     ← a creep load, not a snap load
```

**Which ceiling applies is set by load duration, and getting that wrong is the
trap.** `materials.md` derives PETG at 1.7% one-shot and 1.0% repeated, where
the 0.60× repeated derate is Covestro's figure for "frequent separation and
rejoining". A reopened box lid *is* frequent rejoining, so the **momentary
peak** is the number to hold against **1.0%**. 0.88% clears it.

The **sustained** figure is a different question entirely: **neither PETG
number is a creep allowable** — both are short-term snap values. So a
sustained strain wants to be small on principle rather than merely legal, and
0.13% is. This matters more than it looks: a "fix" that trades a momentary
peak for a permanent strain can easily be a worse joint even when the number
goes down.

**Why the barrier is the retention, not the seated interference.** `SNAP =
1.0 mm` holds the two beads far enough apart in Z that they never overlap once
seated, so the seated interference is only 0.05 mm — which looks alarmingly
close to nothing. It is not the retention. To lift the lid, its bead has to
climb back over the box bead, i.e. re-cross the full 0.35 mm peak; the step it
must climb is `barrier = 0.30 mm`, comfortably above FDM print variance.
Judging this joint by its seated interference would condemn a sound design.

**Load sharing is headroom on top of all of it.** `LID_WALL = 1.2 mm` and
`lip_wall = 0.95 mm` are both thin, so the interference splits across two
flexible sides rather than loading one rigid one — the
[load-sharing](references/annular.md#load-sharing-halves-the-strain) effect in
`annular.md`. Real mechanics, but treat it as margin, not as licence to size
up: design to the rigid number, as the figures above do.

**History, because the earlier numbers are still quoted elsewhere.** This box
shipped `CLEARANCE = 0.3` / `BEAD = 0.4` for a long time, which puts the
momentary peak at `2·(0.8 − 0.3) / 79.8 = 1.25%` — over PETG's repeated-use
ceiling, and over PLA's 1.0% one-shot ceiling too. Tightening the clearance to
0.25 mm and the bead to 0.30 mm brought it to 0.88% while *keeping* a 0.30 mm
barrier and the same detent. Two dead ends are worth not repeating: deleting
the lid's bead to cure the strain destroys the detent outright (interference
goes flat across the whole stroke — a friction fit whose strain is now
permanent), and reading `box-closures`' "2 perimeters behind the bead" as
`wall ≥ 0.8 + bead` for these *protruding* beads inflates the wall budget for
no measured gain. **In PLA this joint is still marginal at any of these
numbers — use PETG**, per `AGENTS.md`'s default and the ranking below.

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
