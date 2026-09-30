# Gridfinity Dremel tool holder

- **DR-1 — Independent variant:** Add a dedicated 1×2 drill-storage variant without changing the existing holders or general-purpose bin. Source: user confirmation, 2026-09-28.
- **DR-2 — Fit and footprint:** The holder occupies 1×2 Gridfinity cells and stores the accepted inventory's nominal shank diameters upright, with tools up to 50 mm long. Source: user request and confirmation, 2026-09-28; diameter requirement revised by user purpose/specification confirmation and inventory acceptance, 2026-09-30. The earlier uniform 2.5 mm shank requirement is historical and superseded.
- **DR-3 — Reference boundary:** The linked Printables holder is visual inspiration, not a source of required lid or hole geometry. Source: user clarification and confirmation, 2026-09-28.
- **DR-4 — Three-part tool-holder variant:** Replace the one-piece Dremel rack with the existing drill-holder architecture: a rigid guide base, removable TPU gripping cartridge, and a separately printable PETG cover enclosing the longest tool. The cover and cartridge mate to this variant's 1×2 base; existing drill sets are not modified. Source: user request and purpose/decision confirmation, 2026-09-28.
- **DR-5 — Inventory and spares:** Preserve all 55 positions: the 41 owned tools below plus 14 spare positions, allocated to the three larger diameter groups. Source: user confirmed the purpose/specification update, retained 55 positions and delegated extra-diameter selection, 2026-09-30; accepted allocation recorded below. Consequence: re-bore the ASA guide and matching TPU insert for each nominal shank diameter using the existing family compensation and guide/land/relief fit rules.
- **DR-6 — Position order and unchanged interfaces:** Group nominal diameters in ascending order along the existing x-major 5×11 layout at 7 mm pitch, with Y increasing within each X column. Preserve the 1×2 envelope, 50 mm tool-length capacity, guide floor, seat heights, and all cartridge-retention and cover interfaces. Source: user acceptance of the existing-position inventory rebore, 2026-09-30. Consequence: change bore diameters only; do not repack holes or redesign the base, insert, or cover envelopes and interfaces.
- **DR-7 — Separate stackable cover option:** Add `drill_storage.dremel.cover_stackable` in PETG without changing the ASA base, TPU insert, smooth cover or smooth-cover parent scene. Retain the existing cover label and snap; provide two full-depth 4.4 mm foot sockets at Y=±21 mm, a 42×84 mm top lip and a 10U (70 mm) seated stack pitch with assembled top z=74.4 mm. Keep a 2 mm roof below the sockets. A default-on support boolean reuses removable breakaway lattices. Source: user purpose/decision confirmation, 2026-09-30. Consequence: print socket-down, remove both lattices and all attachment nibs before stacking; approximately 0.14 mm mouth walls are an explicitly accepted experimental print-trial exception, not proven printable, durable or tolerant of neighbouring holders.

## Accepted inventory

| Nominal shank diameter (mm) | Owned tools | Spare positions | Total positions |
| --- | ---: | ---: | ---: |
| 1.0 | 1 | 0 | 1 |
| 1.5 | 1 | 0 | 1 |
| 2.0 | 1 | 0 | 1 |
| 2.35 | 6 | 4 | 10 |
| 2.9 | 21 | 4 | 25 |
| 3.1 | 11 | 6 | 17 |
| **Total** | **41** | **14** | **55** |

The spare allocation provides capacity in each of the three larger groups,
with the largest reserve for 3.1 mm shanks. These values are nominal tool
dimensions, not compensated CAD bore diameters.

## Acceptance state

The user accepted the purpose/specification update and the 55-position
inventory/spare rebore on 2026-09-30. Current-slice CAD verification passed;
the [CAD contract](dremel-cad-contract.md) owns that evidence.
The base, insert, cover and scene evidence from 2026-09-28 is historical
acceptance of the earlier uniform-bore design, not proof of this rebore.

The user confirmed the separate stackable-cover purpose and DR-7 decision,
then accepted its visual result on 2026-09-30. Its CAD verification passed;
the [current CAD contract](dremel-cad-contract.md) owns that evidence. This is
not physical acceptance of thin walls, printed socket fit or loaded-stack strength.

The rigid base guides tools and carries their floor; the TPU insert supplies the
grip, as in the other drill-storage holders. Material-specific print calibration
still determines the real-world fit and snap effort.
