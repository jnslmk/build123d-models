# Stella CAD contract and re-entry index

> This is the live, compact re-entry source for `led_profiles` Stella work. It
> records the current design slice and points to the canonical geometry rather
> than copying constants or replaying session history.

## Re-entry

1. Read this contract first, then read only the row in the scoped map that
   matches the request.
2. Treat `stella_config.py` and the named geometry module as canonical for
   dimensions and current implementation state.
3. Work one current slice, update this contract when feedback changes it, prove
   its listed predicates, render its review views, and record the user's explicit
   acceptance before opening a dependent slice.

Historical OMP sessions are provenance; this contract is the setup source for a
new iteration.

## Current slice

- **Name:** Side-loadable terminated-cable route.
- **Anchor part:** `stella_core.py`.
- **Purpose and print pose:** A flat, support-free core lets each profile cable
  with its fitted SP16 connector enter through an oblique passage opened at the
  rim.
- **In scope:** The base and offset cores' three cable passages, their lead-ins,
  and the existing arm-tab cable-clearance constraint.
- **Deferred interfaces:** Hub topology, core/arm fastening, keeper geometry,
  and full-assembly placement remain unchanged by this slice.
- **Acceptance:** Pending. The side-opening request is explicit; no explicit
  acceptance of the revised core's shape or service sequence is recorded yet.

## Locked baseline

| Decision | Canonical source | Consequence |
| --- | --- | --- |
| Modular core, arm, and keeper part types | `stella_core.py`, `stella_arm.py`, `stella_keeper.py` | Preserve this topology within the cable-route slice. A one-piece-hub proposal is a separate design decision. |
| Cables enter after termination | `stella_config.CABLE_SLOT_W`; `stella_core.cable_passage_axes()` | Each passage opens tangentially at the rim; the arm notch is the matching cable path. |
| Keyed M5 arm joint carries shear; exposed M4/M5 hardware remains serviceable | `stella_config.py`; `checks.check_stella_parts()` | Cable changes retain the key pockets, bolt access, and structural wall on the passage's opposite side. |
| ASA, support-free print poses, and the hub load basis | `stella_config.py`; `README.md` | Fit, wall, and root-strength changes use the named material and load constants rather than local guesses. |

## Scoped entry map

| Request concerns | Read now | Read only when needed |
| --- | --- | --- |
| Any Stella iteration | This contract; `stella_config.py` | `README.md` for user-facing wording; `docs/design-notes.md` for rationale |
| Core cable mouth or sling slot | `stella_core.py`; `checks.py::check_stella_parts` | `mount_config.py` only if the cable envelope or material changes |
| Arm cable notch, ribs, or tab | `stella_arm.py`; `checks.py::check_stella_parts` | `part-joints` when changing the core/arm joint; `fasteners-and-inserts` when changing M4/M5 geometry |
| Keeper geometry | `stella_keeper.py`; `checks.py::check_stella_parts` | `fasteners-and-inserts` for its bolts or clearances |
| Vertex or double-tetrahedron placement | `assemblies/stella_octangula.py` after the involved part has passed its slice gate | The assembly check is an integration/CI gate, not the interactive edit loop |
| Edge treatment or a new geometry predicate | `build123d-geometry-ops` before the target source/check | `fdm-fits-and-clearances` before changing a fit or cable-slot clearance |

## Current physical proof

- [ ] **Each base and offset core has three clear oblique cable axes** —
  `checks.check_stella_parts()` samples each finished core.
- [ ] **Each cable passage is open to the rim while its opposite side remains
  structural** — the same targeted core gate samples both conditions.
- [ ] **The matching arm notch clears the seated profile cable** — the targeted
  arm gate measures shared volume.
- [ ] **Generic part and fastener invariants remain true** — the existing Stella
  check covers print pose, one-solid construction, M4/M5 access, and core/arm/
  keeper interference.

Run only the affected leaf gate during the edit loop:

```bash
uv run check led_profiles.stella_core
uv run render led_profiles.stella_core --png
```

Run the arm leaf only when the arm changes. Use the full assembly only for an
intentional integration review after the accepted part slices; it is not the
normal loop.

## Visual review and acceptance

- **Views:** Core isometric and top; one local vertex view that shows a seated
  cable entering the rim and the matching arm notch.
- **Human decision requested:** Does the open rim admit the terminated cable
  without compromising the core's useful shape or service sequence?
- **Acceptance signal:** Record the user's exact approval here. `Continue` is
  not acceptance.
- **Next slice after acceptance:** The arm-side cable interface, only if the
  accepted core requires a change beyond its current matching notch.

## Update rule

When feedback changes a pending slice, update its scope, constraints, and
predicates here before more geometry. At the end of an accepted Stella slice,
replace the current-slice section with the next anchor, retain only live locked
decisions and evidence, and attach the specific render or physical-proof command
that justified acceptance. Keep the source map scoped; code remains the source
of truth for dimensions and geometry.
