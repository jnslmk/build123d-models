# Torsional snap-fit joint

Two bars twisted about their own axis instead of bent (cantilever) or
stretched around a hoop (annular). Rare in printed parts — included for
completeness and because Covestro treats it as a third first-class family —
but read the FDM caution below before reaching for it.

## Symbols and formulas

`y₁`, `y₂` are the deflections at the ends of the two arms of length `l₁`,
`l₂`; `φ` is the twist angle:

```text
sin φ = y₁/l₁ = y₂/l₂
```

For a circular cross-section bar of radius `r`, permissible twist angle from
the permissible shear strain `γ_pm`:

```text
φ_pm = (180/π) · (γ_pm · l / r)          [degrees]
γ_pm ≈ (1 + ν) · ε_pm ≈ 1.35 · ε_pm       (ν ≈ 0.35 for these polymers)
```

Torque balance between the two arms (doubled if two bars share the load):

```text
P₁·l₁ = P₂·l₂ = G · I_p · γ / r          (×2 for two bars)
G   = E_s / (2·(1 + ν))                   shear modulus from the secant modulus
I_p = π·r⁴/2                              polar moment, circular section
```

`E_s` and `ε_pm` come from `materials.md`, same as the other two families.
Covestro §C, pp. 18–19 works a full example with two arms of unequal length
sharing one twist.

## FDM caution

**This is the least FDM-friendly of the three families.** A torsion bar is
loaded in shear across its own axis. Print it the natural way — bar axis
horizontal, flat on the bed — and that shear runs partly *across* layer
interfaces, which is the weakest load direction on any FDM part (see
`materials.md`'s anisotropy section: interlayer adhesion is a fraction of
in-plane strength for every filament tested). There is no orientation that
puts a round bar's torsional shear entirely in-plane the way a flat cantilever
arm can be printed flat in XY.

**Prefer a cantilever or a U-shaped arm wherever the design has the freedom
to choose.** Reach for torsional only when the geometry genuinely forces a
twisting bar — a case where the part being joined dictates the axis and there
is no room for a bending arm instead.

## Sources

- Covestro (ex-Bayer), *Snap-Fit Joints for Plastics — A Design Guide*, §C
  (pp. 18–19): <https://solutions.covestro.com/-/media/covestro/solution-center/brands/downloads/imported/1556891135.pdf>
  (mirror: <https://fab.cba.mit.edu/classes/S62.12/people/vernelle.noel/Plastic_Snap_fit_design.pdf>)
