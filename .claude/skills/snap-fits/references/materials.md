# Allowable strain, modulus and friction for FDM snap fits

Everything a snap-fit formula needs about the material: the allowable strain
`ε₀`, the secant modulus `E_s`, the friction coefficient `µ`, and the derate for
printing anisotropy.

## Contents

- [Why you have to derive ε₀ yourself](#why-you-have-to-derive-ε₀-yourself)
- [The molder's rules (and which one is authoritative)](#the-molders-rules-and-which-one-is-authoritative)
- [The additive rule](#the-additive-rule)
- [Derived table for real filaments](#derived-table-for-real-filaments)
- [Two published errors to contradict](#two-published-errors-to-contradict)
- [Always use the actual spool's TDS](#always-use-the-actual-spools-tds)
- [Anisotropy is the biggest lever](#anisotropy-is-the-biggest-lever)
- [Do not anneal a snap fit](#do-not-anneal-a-snap-fit)
- [Material ranking for snap arms](#material-ranking-for-snap-arms)
- [Friction coefficient µ](#friction-coefficient-µ)
- [Sources](#sources)

## Why you have to derive ε₀ yourself

Every snap-fit formula is written in terms of a permissible strain `ε₀`, and
every published table of `ε₀` lists injection-moulding resins: PC, ABS, PA,
POM, PBT, PC/ABS. **No molder's table will ever list PLA or PETG** — they are
not moulding grades, and the number would not transfer anyway because a printed
part is anisotropic and a moulded one is not.

So `ε₀` has to be derived from the filament's own datasheet. Two rules do it.

## The molder's rules (and which one is authoritative)

Covestro, *Snap-Fit Joints for Plastics*, p. 11, on the permissible undercut:

> In general, during a single, brief snap-fitting operation, partially
> crystalline materials may be stressed almost to the yield point, amorphous
> ones up to about 70% of the yield strain.
>
> Glass-fiber-reinforced molding compounds do not normally have a distinct
> yield point. The permissible strain for these materials in the case of snap
> joints is about half the elongation at break.

| Class | Examples | `ε₀` as a fraction of yield strain |
| --- | --- | --- |
| Semi-crystalline | PP, PE, PA, POM | ~100% (almost to yield) |
| Amorphous | PC, ABS, PS, PMMA | 70% |
| Glass-reinforced | any GF grade | 50% of *elongation at break* |

And the repeated-use derate, from the caption of Covestro's Table 2 (allowable
short-term strain, single joining operation):

> for frequent separation and rejoining, use about 60% of these values

So `ε₀(repeated) = 0.60 · ε₀(one-time)`. That factor is the single most-skipped
number in snap-fit design, and it is why a lid that survives its first close
cracks on the fifth.

## The additive rule

For printed parts, HP's MJF snap-fit handbook replaces the class rules with one
blanket derate that already absorbs the anisotropy and the porosity:

> Allowable strain (ε) < ⅓ · Material elongation at yield

Same document: minimum cantilever base thickness 1 mm, minimum overhang depth
1 mm, root radius at least half the base thickness, and PA 12 modulus
`E = 1800 MPa`.

**Use the ⅓ rule for anything printed.** It lands, independently, on the same
place as derating a printed part's strength to 30–40% of its moulded datasheet
value — see [Anisotropy](#anisotropy-is-the-biggest-lever) below.

## Derived table for real filaments

Use the **flexural** modulus, not the tensile one: a snap arm is a beam in
bending, and for these polymers the two differ by up to 2×.

| Material | Flexural modulus `E_s` | Elongation at yield | `ε₀` one-time | `ε₀` repeated |
| --- | --- | --- | --- | --- |
| PLA (Prusament) | 3.1 ± 0.1 GPa | 2.9 ± 0.3% | **1.0%** | 0.6% |
| PETG (Prusament) | 1.7 ± 0.1 GPa | 5.1 ± 0.1% | **1.7%** | 1.0% |
| ASA (Prusament) | 2.0 ± 0.1 GPa | 3.4 ± 0.2% | **1.1%** | 0.7% |
| PA12 (HP MJF) | 1.8 GPa (tensile) | ~10% (estimate) | **3.3%** | 2.0% |

Derivation, so you can redo it for any spool:

- one-time `ε₀ = ⅓ × elongation at yield`: 2.9/3 = 0.97 → 1.0%; 5.1/3 = 1.70%;
  3.4/3 = 1.13 → 1.1%; 10/3 = 3.33 → 3.3%.
- repeated `= 0.60 ×` that: 0.58 → 0.6%; 1.02 → 1.0%; 0.68 → 0.7%; 1.98 → 2.0%.

Modulus and elongation are read straight off the Prusament TDS "Horizontal"
column (ISO 178 for flexural modulus, ISO 527-1 for elongation at yield).

> **Caveat on the PA12 row.** HP does not publish an elongation *at yield* for
> 3D HR PA 12 — only elongation at break. The 10% is an engineering estimate,
> not a datasheet value, and it is the one number in this table you should
> replace with a measurement before trusting it. The 1800 MPa is HP's own
> figure but is a *tensile* modulus, so it under-reads the bending stiffness
> slightly.

## Two published errors to contradict

**1. Fictiv's PLA strain table is flatly wrong for FDM.** Its "acceptable
strain" table gives PLA **4–8%**, Nylon 4–15%, ABS 7%. Printed PLA yields at
**2.9 ± 0.3%** (Prusament, ISO 527-1). Designing a snap arm to 6% strain in PLA
does not flex it — it cracks it. The correct figure is 1.0% one-time, 0.6%
repeated, i.e. **4–8× lower** than the published table.

**2. The semi-crystalline / amorphous ordering is published both ways.** Several
secondary guides invert Covestro's rule, allowing amorphous polymers 60–70% of
yield strain and semi-crystalline only 50–60%. **Covestro's own manual is
authoritative**: semi-crystalline ~100%, amorphous 70%, glass-reinforced 50% of
elongation at break. Where a secondary source disagrees with the resin
manufacturer's own design guide, take the manufacturer.

Neither error matters much once you use the ⅓ rule, which is stricter than
either — but you will meet both numbers in search results, so recognise them.

## Always use the actual spool's TDS

"PETG" is not a specification. Two mainstream PETG filaments:

| | Prusament PETG | Bambu PETG Basic |
| --- | --- | --- |
| Tensile (Young's) modulus | 1.5 ± 0.1 GPa | 2.78 ± 0.07 GPa (X-Y) |
| Flexural (bending) modulus | 1.7 ± 0.1 GPa | 1.95 ± 0.05 GPa (X-Y) |

The tensile moduli are **1.85× apart** (2780/1500) for the same nominal
polymer. The flexural moduli — the ones a snap arm actually cares about — are
only 1.15× apart, which is itself the argument for using the flexural number:
it is the more stable of the two across brands as well as the more correct one.
Pull the TDS for the spool you are printing with.

## Anisotropy is the biggest lever

**Print the arm flat in XY so bending stress runs along the extrusions, never
across a layer interface.** Nothing else you can do to a snap fit matters as
much.

CNC Kitchen's printed-hook test, same geometry, two orientations:

| Material | Horizontal (flat) | Vertical (upright) | Vertical / horizontal |
| --- | --- | --- | --- |
| PLA | 73 kg | 40 kg | 55% |
| PETG | 55 kg | 25 kg | 46% |
| ASA | 57 kg | 17 kg | 29% |
| ASA, ~30 °C enclosure | 57 kg | 20 kg | 35% |

Note the ranking inverts with orientation: ASA beats PETG flat (57 vs 55 kg)
and loses badly upright (17 vs 25 kg). An enclosure recovers part of ASA's
layer adhesion but not all of it.

**Datasheet trap.** Prusament's TDS has two columns, "Horizontal" and "Vertical
xz". The `xz` column is a specimen printed on its side and pulled along the
extrusions — it is *not* an upright, across-the-layers specimen, which is why
its numbers are as good as or better than the horizontal ones (PETG elongation
at yield is 5.1% in both). The real Z-direction number lives in a separate row,
**Interlayer Adhesion**: PLA 17 ± 3 MPa, PETG 18 ± 4 MPa, ASA 11 ± 1 MPa,
against tensile yield strengths of 51, 47 and 42 MPa respectively.

Stacking the derates — the ⅓ rule already covers the flat-printed case — the
practical bands are:

- **flat in XY (correct)**: `ε₀` as tabulated above, ~30–40% of the datasheet
  yield strain. The ⅓ rule and the CNC Kitchen ratios agree here independently.
- **loaded across layers (Z)**: 15–20% of datasheet yield strain. Halve `ε₀`
  again, and prefer to redesign the part instead.

## Do not anneal a snap fit

CNC Kitchen annealed PLA hooks at 100 °C for 45 min:

- horizontal hooks: 75 kg → 87 kg, **+16.2%**
- vertical hooks (layer adhesion): 42 kg → 42 kg, **no change at all** —
  "all cracked right between the layers"
- dimensional change **up to 10%**: 50 mm contracting to 45 mm in XY while
  growing 50 → 55 mm in Z

Annealing buys nothing where a snap fit is weakest and destroys every clearance
and interference you dimensioned. Skip it.

## Material ranking for snap arms

Pulling the numbers above into one ranking, for an FDM arm printed flat in XY
(the anisotropy section's "correct" orientation):

| Rank | Material | `ε₀` one-time / repeated | `E_s` (flexural) | Anisotropy ratio (vert/horiz) | Verdict |
| --- | --- | --- | --- | --- | --- |
| 1 | **PETG** | 1.7% / 1.0% | 1.7 GPa (softest) | 46% | Best all-round choice: the highest usable strain of the three FDM filaments, a soft modulus that keeps mating force low for the same deflection, and a mid-pack anisotropy loss. Default recommendation absent a reason to use something else. |
| 2 | ASA | 1.1% / 0.7% | 2.0 GPa | 29% (35% with an enclosure) | UV- and heat-stable, but the worst layer adhesion of the three — an arm that must be loaded across layers loses the most here. Fine printed flat; avoid for a vertical-load arm. |
| 3 | PLA | 1.0% / 0.6% | 3.1 GPa (stiffest) | 55% (best ratio) | Lowest allowable strain and the stiffest modulus, so it both cracks first and demands the most force per degree of deflection. Its anisotropy *ratio* is actually the best of the three, but that is cold comfort at the lowest `ε₀` in the table. Also creeps under sustained interference (see `box-closures`'s friction-lip section) — a poor choice for an arm left deflected for a long time. |

`PA12` (HP MJF) is not in this ranking — it is a powder-bed process, not FDM,
and its near-isotropic parts do not carry the anisotropy penalty this ranking
is built around. Its row in the [derived table](#derived-table-for-real-filaments)
above is for reference if a design is dual-sourced to MJF, not a recommendation
to switch processes for a snap fit.

**When repeated cycling matters more than raw strain capacity, re-rank by the
*repeated* column, not the one-time column** — PETG's advantage widens
(1.0% vs. PLA's 0.6%, ASA's 0.7%) precisely because its ductility, not just its
one-shot ceiling, is doing the work.

## Friction coefficient µ

Covestro Table 3, guide data for plastics **on steel**. For two components of
the same plastic the coefficient is higher; where the factor is known Covestro
prints it in parentheses.

| Material | µ on steel | Like-on-like factor |
| --- | --- | --- |
| PTFE | 0.12–0.22 | — |
| PE rigid | 0.20–0.25 | ×2.0 |
| PP | 0.25–0.30 | ×1.5 |
| POM | 0.20–0.35 | ×1.5 |
| PA | 0.30–0.40 | ×1.5 |
| PBT | 0.35–0.40 | — |
| PS | 0.40–0.50 | ×1.2 |
| PC | 0.45–0.55 | ×1.2 |
| PMMA | 0.50–0.60 | ×1.2 |
| ABS | 0.50–0.65 | ×1.2 |
| PVC | 0.55–0.60 | ×1.0 |

**These numbers are not tight.** BASF's own table gives PC at **0.25–0.40**,
while Covestro's worked example takes PC on PC as 0.50 × 1.2 = **0.6** — nearly
2× apart for the same pair of materials, before you add print texture, layer
ridges, and whatever release agent is on the bed sheet.

**Treat µ as ±50% and never design a knife-edge mating force.** Compute the
mating force at your nominal µ, then again at 0.5× and 1.5× it, and check the
whole band is acceptable. House default for like-on-like FDM plastic:
**µ = 0.5**.

## Sources

- Covestro (ex-Bayer), *Snap-Fit Joints for Plastics — A Design Guide*:
  <https://solutions.covestro.com/-/media/covestro/solution-center/brands/downloads/imported/1556891135.pdf>
  (mirror: <https://fab.cba.mit.edu/classes/S62.12/people/vernelle.noel/Plastic_Snap_fit_design.pdf>)
  — p. 11 permissible strain by polymer class; Table 2 caption (60% repeated);
  Table 3 friction; worked example µ = 0.50 × 1.2 = 0.6.
- BASF, *Snap-Fit Design Manual* — friction table (PC 0.25–0.40), Q factor,
  R/t ≥ 50%. Indexed at
  <https://fab.cba.mit.edu/classes/S62.12/people/vernelle.noel/resources.html>;
  copy at <https://www.scribd.com/document/56495232/BASF-Plastics-Snap-fit-Design-Manual>
- HP, *Snap-fits Design for HP MJF: Union joints design*:
  <https://endeavor3d.com/wp-content/uploads/2024/12/Snap-Fits-Design-for-HP-MJF-Union-Joints-Design.pdf>
  — allowable strain < ⅓ elongation at yield; h ≥ 1 mm; radius ≥ h/2;
  PA 12 E = 1800 MPa.
- Prusament PLA TDS:
  <https://prusament.com/wp-content/uploads/2022/10/PLA_Prusament_TDS_2021_10_EN.pdf>
- Prusament PETG TDS:
  <https://prusament.com/wp-content/uploads/2022/10/PETG_Prusament_TDS_2021_10_EN.pdf>
- Prusament ASA TDS:
  <https://prusament.com/wp-content/uploads/2022/10/ASA_Prusament_TDS_2022_16_EN.pdf>
- Bambu PETG Basic TDS (V3.0):
  <https://store.bblcdn.com/s1/default/cb94589bf7994fdcbfa833badefae9cd/Bambu_PETG_Basic_Technical_Data_Sheet.pdf>
- CNC Kitchen, *Comparing PLA, PETG & ASA — feat. PRUSAMENT*:
  <https://www.cnckitchen.com/blog/comparing-pla-petg-amp-asa-feat-prusament>
- CNC Kitchen, *Better performing 3D prints with annealing, but… Part 1: PLA*:
  <https://www.cnckitchen.com/blog/better-performing-3d-prints-with-annealing-but-part-1-pla>
- Fictiv, *How to Design Snap Fit Components* (the 4–8% PLA table this file
  contradicts): <https://www.fictiv.com/articles/how-to-design-snap-fit-components>
