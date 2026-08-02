# Annular (circumferential) snap-fit joint

A continuous bead running all the way round a circular joint — a lid rim, a
cap skirt, a round hoop over a round boss. The whole ring is the spring: it
has to stretch (hoop strain) to ride over the bead, then spring back into the
undercut. This is `models/round_snap_box.py`'s family, and the one to reach for
whenever the retaining feature is a full circle rather than a single arm.

## Contents

- [Symbols](#symbols)
- [Core formulas](#core-formulas)
- [The headline trap: `y` is diametral, not radial](#the-headline-trap-y-is-diametral-not-radial)
- [Bead height by lid diameter](#bead-height-by-lid-diameter)
- [Load sharing halves the strain](#load-sharing-halves-the-strain)
- [A slit ring is not an annular joint](#a-slit-ring-is-not-an-annular-joint)
- [The remote-bead penalty](#the-remote-bead-penalty)
- [Bead section](#bead-section)
- [Sizing procedure](#sizing-procedure)
- [Worked example](#worked-example)
- [Sources](#sources)

## Symbols

| Symbol | Meaning |
| --- | --- |
| `y` | permissible **diametral** interference — the total amount the ring's diameter must stretch over |
| `d` | nominal diameter of the ring at the bead |
| `ε` | permissible hoop strain (from `materials.md`) |
| `t` | wall thickness of the tube/ring carrying the bead |
| `P` | force to expand the ring over the bead |
| `X` | Covestro's annular-joint geometry factor, a function of the ring's diameter-to-wall ratio |
| `W` | mating (or separating) force at the lead-in (or return) face |
| `µ`, `α` | friction coefficient and lead-in/return angle — same roles as in `cantilever.md` |

## Core formulas

```text
y_pm = ε_pm · d                      permissible diametral interference
ε    = (y / d) · 100%                strain for a given interference
P    = y · d · E_s · X               force to expand the ring over the bead
W    = P · (µ + tan α) / (1 − µ·tan α)   mating / separating force
```

`X` comes off Covestro's chart for the ring's proportions (thin ring vs. thick
hub) — it is not 1, and the chart is the source, not a number to guess. `W`
uses the same friction-and-angle form as the cantilever family; see
`cantilever.md` for the return-angle discussion, which applies here unchanged.

## The headline trap: `y` is diametral, not radial

**`y` in every formula above is the total diametral interference — the
increase in *diameter*, not the height of the bead measured radially.** A bead
that stands proud of the lip by a radial height `h` adds `h` to the radius on
*every* side of the circle simultaneously, so it adds `2h` to the diameter:

```text
y = 2h  ⇒  h_bead = ε_allow · d / 2
```

**Get this backwards and every bead comes out 2× too tall.** A surprising
fraction of "just make the bead 0.5 mm" advice online is exactly this error —
someone read `y = ε·d` as a radial-height formula and used the radial height
where the diametral one belongs. It happens to survive on 40–80 mm PETG lids,
where a strain of even 2ε is still under PETG's ceiling — and fails outright
below about 30 mm, where the same mistake doubles the strain past the material's
limit outright.

## Bead height by lid diameter

`h_bead = ε · d / 2`, tabulated so the formula is never re-derived from
scratch mid-design. **Re-derive any number here before trusting it** — these
are a worked table, not a citation.

At `ε = 1.0%` (PLA, one-shot ceiling from `materials.md`):

| Lid Ø | `h_bead` |
| --- | --- |
| 30 mm | 0.15 mm |
| 40 mm | 0.20 mm |
| 60 mm | 0.30 mm |
| 80 mm | 0.40 mm |
| 100 mm | 0.50 mm |

At `ε = 1.7%` (PETG, one-shot ceiling):

| Lid Ø | `h_bead` |
| --- | --- |
| 30 mm | 0.26 mm |
| 40 mm | 0.34 mm |
| 60 mm | 0.51 mm |
| 80 mm | 0.68 mm |
| 100 mm | 0.85 mm |

**PETG repeated (`ε = 1.0%`, from `materials.md`'s 0.6× derate) lands on the
same numbers as the PLA one-shot column above** — both are the `ε = 1.0%` row
of the same formula, so the table does double duty: read the first table as
"PLA, snap once" or as "PETG, snap it open and shut all day."

## Load sharing halves the strain

Every formula above assumes **one side of the joint is rigid** and all the
strain lands on the other. `round_snap_box.py` and most printed lids violate
that assumption on purpose: the lid wall and the lip wall are both thin, so
both flex, and the interference splits between them.

**With equal flexibility on both sides, the strain each side sees is roughly
half of what the single-rigid-side formula predicts — so the permissible
undercut for a given material effectively doubles.** This is not a documented
number from Covestro (whose formula assumes the rigid case) so much as a
mechanical consequence of two springs sharing a displacement instead of one
spring taking it all; treat it as headroom, not as a number to design against
directly. It is also why a design that looks over-strained by the rigid
formula can survive in practice — see the [worked example](#worked-example).

## A slit ring is not an annular joint

**A ring with a slot or gap cut in it — a segmented collet, a C-clip, a slit
skirt — is not annular** even though it looks circular. Cutting the loop open
removes the hoop-tension load path the annular formulas depend on: the ring no
longer has to stretch uniformly, it flexes locally at the slit like a short,
wide cantilever. **Dimension a slit ring as a cantilever** (`cantilever.md`),
using the arc length either side of the slit as the arm — this is Covestro's
own Fig. 4 treatment. Using the annular formula on a slit ring under-predicts
how far it can safely open, sometimes drastically, because it credits stiffness
the slit removed.

## The remote-bead penalty

The annular formulas assume the bead sits at (or very near) the free end of
the tube it is cut into — `round_snap_box.py`'s bead is a fixed distance below
the rim, not buried deep in the box wall. Move the bead away from the tube's
free end and the wall between the bead and the fixed base resists the hoop
expansion instead of springing with it:

**Beyond `δ ≈ 1.8·√(d·t)` from the tube's free end, the theoretical force to
expand the ring over the bead is 4×; measured values run closer to 3×.** Either
way, a bead buried this far in is a materially stiffer joint than the same bead
near the mouth, and the plain formulas above will under-predict the mating
force badly. **Keep the retaining bead within `δ` of the free edge** — near the
rim, near the mouth, near the end of whatever tube it lives on.

## Bead section

The bead's cross-section, independent of its height, needs the same
print-friendly shape everywhere it appears:

- **30° lead-in ramp** on the entry face, matching the cantilever family's
  lead-in angle.
- **40–45° return ramp** so the joint still releases — a triangular section
  that ramps in *and* back out, not a square shoulder.
- **Both faces ≤ 45° from horizontal**, so the bead is self-supporting in
  either print pose and needs no support material.

## Sizing procedure

1. Fix the ring diameter `d` from the part's other dimensions.
2. Pick `ε` from `materials.md` for the material and use case (one-shot vs.
   repeated; flat-printed vs. loaded across layers).
3. If both sides of the joint flex (thin lid over a thin lip, as opposed to a
   thin ring over a rigid boss), you have headroom above the formula per
   [load sharing](#load-sharing-halves-the-strain) — but design to the rigid
   number first and treat the headroom as margin, not as license to double
   the bead outright.
4. Compute `h_bead = ε·d/2` — **not `ε·d`.**
5. Check `h_bead` against the [table](#bead-height-by-lid-diameter) for the
   same `ε` and diameter as a sanity check.
6. Place the bead within `δ ≈ 1.8·√(d·t)` of the tube's free end.
7. Section the bead 30° lead-in / 40–45° return, both faces ≤ 45°.
8. If the ring has any slit, slot, or gap, stop — [it is a cantilever](#a-slit-ring-is-not-an-annular-joint),
   not this section.

## Worked example

See `models/round_snap_box.py` — worked in full in the skill's `SKILL.md` (the
`INNER_DIA = 78.0`, `BEAD = 0.4` case, hoop strain landing at exactly PLA's
one-shot ceiling).

## Sources

- Covestro (ex-Bayer), *Snap-Fit Joints for Plastics — A Design Guide*:
  <https://solutions.covestro.com/-/media/covestro/solution-center/brands/downloads/imported/1556891135.pdf>
  (mirror: <https://fab.cba.mit.edu/classes/S62.12/people/vernelle.noel/Plastic_Snap_fit_design.pdf>)
  — annular joint section: `y_pm = ε_pm·d`, geometry factor `X` chart, Fig. 4
  (slit-ring-as-cantilever), remote-bead force multiplier and the
  `δ ≈ 1.8√(d·t)` distance.
