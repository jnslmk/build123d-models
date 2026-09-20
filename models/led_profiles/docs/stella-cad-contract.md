# Stella re-entry index

> This is the stable, compact entry point for `led_profiles` Stella work.
> The current-slice contract owns user decisions, acceptance, and proof;
> geometry modules own dimensions and implemented state.

## Start rule

1. Read this index first.
2. If `models/led_profiles/docs/cad-contract.md` exists, read it next. It is
   the current-slice source and supersedes older design assumptions.
3. If no current contract exists, start one from
   `skill://cad-iteration/references/cad-contract.md` before creating geometry
   for a new design slice.
4. Read only the matching row in the scoped map below. Session histories are
   provenance, not iteration setup.

## Scoped entry map

| Request concerns | Read now | Read only when needed |
| --- | --- | --- |
| Any Stella iteration | This index; `stella_config.py`; current `cad-contract.md` | `README.md` for user-facing wording; `docs/design-notes.md` for rationale |
| Core body, cable mouth, or sling slot | `stella_core.py`; `checks.py::check_stella_parts` | `mount_config.py` when the cable envelope or material changes |
| Arm tab, notch, ribs, or saddle | `stella_arm.py`; `checks.py::check_stella_parts` | `part-joints` for a core/arm joint change; `fasteners-and-inserts` for M4/M5 geometry |
| Keeper geometry | `stella_keeper.py`; `checks.py::check_stella_parts` | `fasteners-and-inserts` for its bolts or clearances |
| Vertex or double-tetrahedron placement | `assemblies/stella_octangula.py`, after the affected part passes its slice gate | Full-assembly proof is an integration/CI gate |
| Edge treatment or a new geometry predicate | `build123d-geometry-ops`, then the target source/check | `fdm-fits-and-clearances` before changing a fit or cable-slot clearance |

## Tight edit loop

For a part-level change, run that leaf's physical gate and render only the views
named by the current contract:

```bash
uv run check led_profiles.stella_core
uv run render led_profiles.stella_core --png
```

Run the arm leaf when the arm changes. Use the full assembly only for an
intentional integration review after accepted part slices; it is not the normal
interactive loop.

## Contract hygiene

When feedback changes a pending slice, update `cad-contract.md` before more
geometry. At acceptance, replace its current slice with the next anchor, retain
only live locked decisions and evidence, and record the exact approval and proof
command. Keep this index limited to entry paths and loop policy so it does not
become a second source of design state.
