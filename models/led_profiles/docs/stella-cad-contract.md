# Stella re-entry index

> This is the stable, compact entry point for `led_profiles` Stella work.
> The specification owns accepted requirements; the current-slice contract owns
> slice acceptance and proof; geometry modules own dimensions and implemented
> state.

## Start rule

1. Read this index first.
2. Read `../CONTEXT.md` and `stella-specification.md` next. They define the
   physical vocabulary and durable user-accepted requirements.
3. If `cad-contract.md` exists, read it as the current-slice source. If it does
   not, start one from `skill://cad-iteration/references/cad-contract.md` before
   creating geometry for a new design slice.
4. Read only the matching row in the scoped map below. Session histories are
   provenance, not iteration setup.

## Scoped entry map

| Request concerns | Read now | Read only when needed |
| --- | --- | --- |
| Any Stella iteration | This index; `../CONTEXT.md`; `stella-specification.md`; current `cad-contract.md` | `README.md` for public wording; `docs/design-notes.md` for previous-implementation rationale |
| Functional organic-Y core: continuous web-section outline, core-side M3 seats and two-hole textile-cord suspension; electrical cables outside | Current `cad-contract.md`; `stella/config.py`; `stella/core.py`; `stella/checks.py::check_core` | `stella-analytical-basis.md` for historical candidate assumptions and current cord evidence; source may lag the active definition, as recorded in the contract |
| Previous round core, cable mouth, or sling slot | `stella_config.py`; `stella_core.py`; `checks.py::check_stella_parts` | `mount_config.py` for the existing cable envelope; these are not redesign defaults |
| Previous arm tab, notch, ribs, or saddle | `stella_config.py`; `stella_arm.py`; `checks.py::check_stella_parts` | `part-joints` and `fasteners-and-inserts` when that interface is explicitly in scope |
| Previous keeper geometry | `stella_keeper.py`; `checks.py::check_stella_parts` | `fasteners-and-inserts` for its bolts or clearances |
| Previous vertex or double-tetrahedron placement | `assemblies/stella_octangula.py`, only for an explicit previous-assembly task | No redesigned assembly until the dependent slices are accepted; full-assembly proof is an integration/CI gate |
| Edge treatment or a new geometry predicate | `build123d-geometry-ops`, then the target source/check | `fdm-fits-and-clearances` before changing a fit or cable-slot clearance |

## Tight edit loop

For a part-level change, run that leaf's physical gate and render only the views
named by the current contract:

```bash
uv run check led_profiles.stella.core
uv run view led_profiles.stella.core
uv run render led_profiles.stella.core --view top --png
```

The `stella.*` namespace is the redesign; underscore-named `stella_core`,
`stella_arm`, `stella_keeper`, and the current assembly are the previous
implementation. Keep those separate parts and assembly callers isolated from
the redesign until their dependent slices are accepted. Core-side features
belong to the functional core review defined in `cad-contract.md`, not an
implicit later assembly slice. Do not inherit frozen dimensions, reservations
or proof assumptions from the old blank body into new functional-core code.
Run the full assembly only for an intentional integration review after accepted
dependent slices, never as the normal core edit loop.

## Contract hygiene

When feedback changes a pending slice, update `cad-contract.md` before more
geometry. When feedback changes an accepted requirement, invoke
`grill-with-docs` and update `stella-specification.md` before the contract. At
acceptance, replace the current slice with the next anchor, retain only live
constraints and evidence, and record the exact approval and proof command. Keep
this index limited to entry paths and loop policy so it does not become a second
source of design state.
