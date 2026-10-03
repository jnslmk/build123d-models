# WORKZONE wrench storage

A lightweight PETG Gridfinity bin for six WORKZONE double-open wrenches,
standing on their narrow edges in parallel. Two slotted transverse racks support
each column. The default packs all six into one column; changing
`wrenches_per_column` from 1 to 6 re-groups the same tools, using connected
stepped footprints where shorter columns save occupied cells.

- [Approved specification](docs/wrench-storage-specification.md) — purpose,
  accepted requirements and boundaries.
- [Current bin CAD contract](docs/bin-cad-contract.md) — anchor-only scope,
  physical predicates and the pending human acceptance gate.
- [Evidence and Python interfaces](docs/evidence.md) — A4 photo provenance,
  measured thicknesses, actual aligned contours and handle-support stations.

The bin is the current anchor and is **not yet accepted**. It is an open,
low-walled tray: exposed heads must remain accessible with the cover removed.
A separate removable, stackable lid is an approved eventual requirement, but no
lid, closure or mating-interface geometry is authorized before bin acceptance.
The 3 mm future-cover headroom is an envelope constraint, not a built interface.

`config.py` and `profiles.py` are the dimensional/evidence inputs. Photo outlines
are approximate and include small shadow fringes; only the supplied maximum
head/handle thicknesses are direct physical measurements. The 1×5 default is
supported by envelope arithmetic, not yet by CAD or a printed-fit result.
