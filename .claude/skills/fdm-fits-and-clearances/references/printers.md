# Printers this repo targets

Short and factual. Anything not confirmed against a vendor page or a spec sheet is marked
**unverified** rather than guessed at.

## Baseline assumed throughout the skill

Every number in `references/fits.md` assumes:

- **0.4 mm nozzle** — extrusion width ~0.4–0.45 mm, which sets the minimum resolvable
  feature and the 0.8 mm two-perimeter wall floor.
- **0.15–0.2 mm layers.**
- **Calibrated flow.**

**Calibration outranks every number in this skill.** An uncalibrated extrusion multiplier
swamps the entire table: over-extrusion piles material on the inside of a curve and
narrows a hole by 0.1–0.2 mm
([Creative3DP](https://tools.creative3dp.com/tools/hole-tolerance-calculator/)) — the whole
of a snug fit and half of a sliding one. Before changing a clearance in CAD because a part
did not fit, confirm the flow multiplier and the first-layer squish. Chasing a fit through
the model with an unknown flow rate produces a constant that is correct on exactly one
machine on exactly one day.

Both machines below are **enclosed**, which matters twice over:

- it suppresses the differential cooling that drives ABS/ASA shrink and warp, so a
  chamber-printed ASA part comes out closer to nominal and wants a **tighter** clearance
  than the open-frame row in `references/fits.md` (about −0.05 mm);
- it makes ABS, ASA and PC realistic choices here, so the high-shrinkage rows of the
  material tables are live, not theoretical.

## Creality K2 Plus

Enclosed, actively heated chamber, CFS multi-material.

| Spec | Value |
|---|---|
| Build volume | 350 × 350 × 350 mm |
| Chamber | actively heated, up to 60 °C |
| Nozzle | hardened tip, up to 350 °C |
| Bed | up to 120 °C |
| Multi-material | CFS, 4 filaments per unit, up to 4 units (16 colours) |
| Max speed / accel | 600 mm/s, 30 000 mm/s² |

Source: [Creality K2 Plus CFS Combo product page](https://www.creality.com/products/creality-k2-plus-cfs-combo),
corroborated by [MatterHackers](https://www.matterhackers.com/store/l/creality3d-k2-plus-high-speed-multi-color-3d-printer/sk/M4CZ3FYD).

**Networked.** Reachable on the local network — Moonraker on port **7125**, Fluidd on port
**4408**. *Unverified against vendor documentation*; these are the ports observed on this
repo's machine, not a published default. Useful for pushing a test coupon without walking
to the printer.

The heated chamber is the reason the ASA-enclosed row exists in the per-material table. It
is also the machine that makes PC and high-shrink materials worth the shrinkage rows.

## Elegoo Centauri Carbon (ECC)

The other machine in use. Enclosed, single-material.

| Spec | Value |
|---|---|
| Build volume | 256 × 256 × 256 mm |
| Enclosure | fully enclosed (steel chassis, aluminium and glass shell) with an enclosure fan |
| Chamber heating | *unverified* — enclosed and fan-regulated, but no actively heated chamber confirmed |
| Nozzle | 0.4 mm hardened steel (default), up to 320 °C |
| Bed | up to 110 °C |
| Layer height | 0.1–0.4 mm, 0.2 mm recommended |
| Max speed / accel | ≤ 500 mm/s, 20 000 mm/s² |

Sources: [ELEGOO Centauri Carbon introduction (PDF)](https://3dprinteq.dk/wp-content/uploads/ELEGOO-Centauri-Carbon-Intro-EN.pdf),
[3DPros printer database entry](https://3dpros.com/printers/elegoo-centauri-carbon),
[Printago nozzle guide](https://printago.io/guides/elegoo-centauri-carbon-nozzle).

Note that the ECC's recommended 0.2 mm layer is at the top of this skill's 0.15–0.2 mm
baseline, so Z-direction features land on a slightly coarser quantisation than the K2 Plus
at 0.15 mm. On a fit whose critical dimension runs along Z, that is worth a layer of extra
clearance.

## What is *not* established here

- **No per-machine measured fit offsets exist yet.** Nothing in `references/fits.md` has
  been calibrated against either printer specifically; the numbers are the reconciled
  desktop-FDM consensus. The moment a test coupon is printed on one of these machines, its
  measured offset belongs in this file and should override the generic table for that
  machine.
- **No first-layer / elephant's-foot compensation values** are recorded per machine. The
  `−0.1 to −0.2 mm` figure in `references/fits.md` is a generic starting point.
- **Slicer shrinkage compensation state is unknown.** This determines whether ABS/ASA
  should use the `−0.15` material offset or be treated as PETG — see "Where sources
  disagree on ABS" in `references/fits.md`. Check the profile before relying on either.
