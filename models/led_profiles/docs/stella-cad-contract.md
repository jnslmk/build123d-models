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
| Accepted functional organic-Y core | Accepted interface in current `cad-contract.md`; `stella/config.py`; `stella/core.py`; `stella/checks.py::check_core` | `stella-analytical-basis.md` for sizing history and explicit non-claims |
| Current mating profile arm / arm-to-core connection | Current `cad-contract.md`; accepted core interface; ADR-0001; ADR-0002 | Previous `stella_arm.py` only as historical evidence; load `part-joints`, `fasteners-and-inserts`, `fdm-fits-and-clearances` and `build123d-geometry-ops` before geometry |
| Previous round core, cable mouth, or sling slot | `stella_config.py`; `stella_core.py`; `checks.py::check_stella_parts` | `mount_config.py` for the existing cable envelope; these are not redesign defaults |
| Previous arm tab, notch, ribs, or saddle | `stella_config.py`; `stella_arm.py`; `checks.py::check_stella_parts` | These are evidence, not redesign geometry; do not inherit the M5 joint, cable notch or ASA assumptions |
| Previous keeper geometry | `stella_keeper.py`; `checks.py::check_stella_parts` | The redesigned keeper remains gated until the mating arm is accepted |
| Edge treatment or a new geometry predicate | `build123d-geometry-ops`, then the target source/check | `fdm-fits-and-clearances` before changing a fit or cable-slot clearance |

## Tight edit loop

The accepted core proof command is:

```bash
uv run check led_profiles.stella.core
```

The complete-arm boundary is authorized while the removable keeper remains
deferred. Its edit loop is:

```bash
uv run check led_profiles.stella.arm
```

Run only the views named by the current contract.

The `stella.*` namespace is the redesign; underscore-named `stella_core`,
`stella_arm`, `stella_keeper`, and the current assembly are the previous
implementation. Keep those separate parts and assembly callers isolated from
the redesign until their dependent slices are accepted. Do not inherit frozen
dimensions, reservations or proof assumptions from the old arm into the new
profile-arm slice. Run the full assembly only for an intentional integration
review after accepted dependent slices, never as the normal part edit loop.

## Contract hygiene

When feedback changes a pending slice, update `cad-contract.md` before more
geometry. When feedback changes an accepted requirement, invoke
`grill-with-docs` and update `stella-specification.md` before the contract. At
acceptance, replace the current slice with the next anchor, retain only live
constraints and evidence, and record the exact approval and proof command. Keep
this index limited to entry paths and loop policy so it does not become a second
source of design state.
