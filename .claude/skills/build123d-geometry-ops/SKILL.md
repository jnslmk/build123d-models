---
name: build123d-geometry-ops
description: Guides build123d edge treatments and in-code geometry verification for this CAD repo. Covers choosing between an OCC edge fillet/chamfer and a boolean chamfer tool, isolating flaky OCC failures so they cannot cascade through a BuildPart, selecting the right edge, and asserting internal geometry by point-sampling the solid. Use when adding or debugging a fillet or chamfer, when an OCC fillet/chamfer raises or silently does nothing, when a lead-in is needed at a hole or bore mouth, when edge selection returns the wrong point (arc_center vs center), when ribs, wall thickness, clearances or print pose need verifying, or when writing a model's checks. Keywords: fillet, chamfer, OCC failure, edge selection, boolean chamfer, lead-in, verify geometry, point sampling, is_solid_at, build123d.
---

# build123d geometry ops

Two operations in this repo fail in ways that waste a whole session if you do not
know them up front: OCC edge `fillet`/`chamfer`, and believing a part is right
because it looked right in the viewer. This skill is the decision procedure for
both.

## The core rule

**OCC edge ops are reliable on vertical edges of an otherwise clean face. Anywhere
the face carries other features — holes, ribs, countersinks, engraved text, a
neighbouring rim — cut a boolean chamfer instead.**

A boolean is a subtraction of a solid tool. It cannot raise, cannot half-apply, and
cannot poison the builder. An OCC edge op can do all three, and does so
non-deterministically on non-trivial geometry (see `references/gotchas.md`).

A chamfer on a horizontal top or bottom edge is the house style anyway (see the
"Edge design for FDM" section of `AGENTS.md`), so the boolean is rarely a
compromise — it is usually the shape you wanted.

## Decide

| Edge | Use |
| --- | --- |
| Vertical corner of a plain prism | `fillet(...)` / `chamfer(...)` directly |
| Top or bottom outer ring of a rounded-rect body | `top_chamfer_tool` / `bottom_chamfer_tool`, subtracted |
| Mouth of a round or hex bore (lead-in) | subtract a `Cone(r, r + ch, ch)` frustum |
| Any edge on a face that also carries holes, ribs, or text | boolean |
| Internal corner under load, on a clean face | `fillet(...)`, wrapped in `chamfer_edge`-style snapshot/restore |

If you are unsure, pick the boolean. The failure mode of an unnecessary boolean is
slightly more code; the failure mode of an unnecessary edge op is a silent cascade
that removes every later chamfer in the same builder.

## Use the helpers that already exist

`models/lib/edges.py`:

- `chamfer_edge(builder, edges, size) -> bool` — the OCC edge op wrapped in
  snapshot/restore. Returns `True` if the chamfer took, `False` (with a printed
  warning) if OCC refused. Use this instead of a bare `try`/`except` **always**;
  a bare except leaves the builder corrupted.
- `top_chamfer_tool(size_x, size_y, corner_r, z_top, ch) -> Part` — a subtractable
  45° chamfer for the top outer edge of a rounded-rect prism. Built as an oversized
  slab minus a lofted keep-frustum.
- `bottom_chamfer_tool(size_x, size_y, corner_r, z_bottom, ch) -> Part` — the same
  for the bottom outer edge (elephant's-foot relief).
- `as_part(shape) -> Part` — narrows a `Location * Shape` result (what
  `Pos(...) * part` and `Rotation(...) * part` return) back to `Part`. Use it
  rather than scattering type ignores.

Subtract a tool with `add(tool, mode=Mode.SUBTRACT)` inside the `BuildPart`. Worked
example: `models/led_psu_enclosure/lid.py:92-105` subtracts both tools in one
builder.

Other patterns in the repo, when the lib helper does not fit:

- Round and hex bore mouths — `models/drill_storage_gridfinity.py:966-991` cuts a
  `Cone` frustum at every mouth, round and hex, and says why in a comment.
- A rounded-square rim where no lib helper is imported —
  `models/drill_storage_gridfinity.py:447` (`_rim_chamfer_tool`).

`models/led_psu_enclosure/util.py` re-exports `as_part`, `chamfer_edge`,
`top_chamfer_tool` and `bottom_chamfer_tool` for back-compatibility; existing
modules in that package import them from `.util`, but new code should import
`models.lib.edges` directly (`models/led_psu_enclosure/util.py:1-6`).

## Workflow

1. **Classify the edge** against the table above. Do this before writing code —
   retrofitting a boolean after an edge op has been threaded through a builder is
   more work than starting with it.
2. **Reach for the existing helper.** Do not re-derive a chamfer tool that
   `models/lib/edges.py` already provides. If you need a new shape of tool, add it
   there rather than privately in a model.
3. **If you do use an edge op**, obey all four rules at once — they are not
   alternatives:
   - one feature per call, never a loop over a list captured earlier;
   - re-query `builder.edges()` on each pass, because every successful op
     invalidates the previous selection;
   - go through `chamfer_edge` (or an equivalent snapshot/restore) so a failure is
     isolated;
   - if the size matters, retry down a decreasing ladder so the feature still gets
     the largest chamfer that fits.
   Details and symptoms: `references/gotchas.md`.
4. **Verify in code.** A chamfer that silently did not apply looks identical to one
   that did in an SVG projection. Point-sample the solid, or compare a volume, or
   check a bounding box. See `references/verification.md`.
5. **Show it.** `uv run show <model>` after every model edit, per `AGENTS.md`. The
   viewer is the last step, not the verification.

## When to stop iterating

Stop when all of these hold. Not before, and — importantly — not after.

- Every edge treatment you intended is present. If you used `chamfer_edge`, its
  return value was `True` for every feature, or you consciously accepted a `False`
  and left a comment saying so. Judge this by the **return value**, not by
  scanning for "warning: chamfer skipped" in the log — a radius ladder
  (`references/gotchas.md` §3) prints that warning on every failing rung even
  when a later rung succeeds, so warnings alone are not the signal. A warning
  with no later success for that same feature is the unfinished part.
- `uv run check <model>` exits zero, if the model has checks. If your change
  touched geometry a check covers, and no check covers the thing you changed, add
  one — that is the point of the runner.
- `uv run ruff check .` and `uv run ty check .` are clean.
- The part is returned in print pose: flat on `z = 0`, print direction `+Z`. Assert
  it rather than eyeballing it (`part.bounding_box().min.Z`).
- `uv run show <model>` has been run so the user can see the change live.

Do **not** keep tuning a chamfer length to coax an OCC edge op into working. Two
failed lengths is the signal to switch to a boolean, not to try a third. The repo's
own record of this: OCC refused to chamfer a lid perimeter at *any* length once 14
countersinks existed on the same face, 5 mm clear of it
(`models/lib/edges.py:11-14`).

## References

- `references/gotchas.md` — the five OCC and edge-selection traps, each with the
  symptom that identifies it and the fix.
- `references/verification.md` — point-sampling the solid with `is_solid_at`, the
  `Report` collector, the `uv run check` runner, and print-pose assertions.
