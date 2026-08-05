# Verifying geometry in code

## Contents

- [Why the viewer is not verification](#why-the-viewer-is-not-verification)
- [The instrument: `is_solid_at`](#the-instrument-is_solid_at)
- [The angle instrument: `interior_angle` and `sharp_convex_edges`](#the-angle-instrument-interior_angle-and-sharp_convex_edges)
- [The collector: `Report`](#the-collector-report)
- [The runner: `uv run check`](#the-runner-uv-run-check)
- [Print-pose assertions](#print-pose-assertions)
- [Worked example](#worked-example)
- [Writing good samples](#writing-good-samples)

## Why the viewer is not verification

Ribs inside a bore, a wall gap behind a boss, a blind pocket, a fit clearance
between two parts — none of these appear in an SVG projection or a viewer
screenshot. Neither does a chamfer that silently failed to apply, because the
absence of a 0.8 mm bevel is invisible at projection scale.

So the house rule is: **verify internal geometry in code, not by eye.** Sample the
solid, compare volumes, assert arithmetic. The viewer is for confirming you built
the thing you meant to build; the checks are for confirming it is actually correct.

## The instrument: `is_solid_at`

`models/lib/checks.py` provides the only way to see *into* a solid — ask the kernel
whether a point lies in the material:

```python
from models.lib.checks import Report, is_solid_at
```

`is_solid_at(part, x, y, z) -> bool` wraps OCC's `BRepClass3d_SolidClassifier`:
it constructs the classifier over `part.wrapped`, calls
`.Perform(gp_Pnt(x, y, z), TOL)` with `TOL = 1e-6`, and returns `True` when the
resulting state is `TopAbs_IN` or `TopAbs_ON` (`models/lib/checks.py:29-33`).
`TopAbs_ON` counts as inside, so a sample landing exactly on a face reads solid —
which is why samples are usually offset a few tenths of a millimetre off any
surface rather than placed on it.

Boolean volume is the other useful probe, for interference rather than presence:
`(a & b).volume` is the overlap between two parts. Used throughout
`models/led_psu_enclosure/checks.py` to assert that a seated lid, a shelf or a
component mock does not foul the shell.

## The angle instrument: `interior_angle` and `sharp_convex_edges`

`is_solid_at` answers questions about a point. Two more functions in
`models/lib/checks.py` answer questions about an **edge**:

- `interior_angle(part, edge, faces=None, probe=None) -> float | None` — the
  dihedral angle *through the material* at an edge, in degrees: ~90 for a
  square corner, ~135 for the two edges a 45° chamfer leaves, ~180 for a
  tangent or filleted edge, ~270 for a concave step. `None` means the edge
  could not be classified (a sliver, or not shared by exactly two faces).
- `sharp_convex_edges(part, min_length=2.0, max_interior=120.0, allow=()) ->
  ShapeList[Edge]` — every convex edge at least `min_length` long whose
  interior angle is at most `max_interior`, i.e. sharp enough to want
  breaking. The default `120` reports a raw 90° corner and passes the ~135°
  a 45° chamfer leaves, so a treated part comes back clean. `allow` takes
  `(predicate, reason)` pairs; anything a predicate matches is excluded, and
  the reason is what the caller prints — turning "this edge happens to be
  raw" into "this edge is raw *because*", which is the whole difference
  between this check and the `AGENTS.md` prose it replaces
  (`models/lib/checks.py:82-181`).

Writing `interior_angle` surfaced two traps worth knowing before writing a
similar check yourself, both silent:

- **The intuitive convexity test is wrong, and it is wrong silently.**
  Stepping out along the *sum* of the two adjacent faces' outward normals to
  see whether you leave the solid looks like it should separate convex from
  concave edges. It does not: a convex 90° edge and a concave 90° edge share
  the exact same pair of outward normals. What differs between them is which
  quadrant around the edge holds material, and the summed normal points into
  the one empty quadrant *in both cases at once*. The test that actually
  works probes the `n_b - n_a` quadrant instead, which is empty only when the
  edge is convex (`models/lib/checks.py:90-114`).
- **`Vector.get_angle` returns degrees, and so does the rest of build123d's
  public API** — `Vector.rotate`, `Axis.angle_between`, `Rotation`, extrude's
  `taper`, all of it. The trap is reaching for `math.degrees()` by reflex, as
  if this one call were the radians exception to a radians library. It is
  not, and there is no such exception to fall back on: wrap it anyway and it
  silently double-converts, so every edge clears every threshold and the
  check passes having verified nothing. `interior_angle` takes
  `n_a.get_angle(n_b)` as already degrees, with a comment at the call site so
  it is not re-"fixed."

Both bugs are in the check itself, not the geometry, which is exactly why a
new check needs to be shown failing on broken geometry before it is trusted —
see "When to stop iterating" in `SKILL.md`.

## The collector: `Report`

A bare `assert` stops at the first failure and hides every later one, which turns
one debugging session into five. `Report` (`models/lib/checks.py:36-58`) collects
pass/fail lines instead, so a single run surfaces every problem:

- `r.check(ok, label, detail="")` — record one assertion. `detail` is for the
  measured value, and it is worth filling in: a failure that prints
  `2.31 mm` tells you how far off you are, a bare `FAIL` does not.
- `r.section(title)` — group the lines that follow.
- `r.render()` — the full text, ending in `all checks passed` or
  `N FAILED: <labels>`.
- `r.failures` — the list of failed labels, which is what drives the exit code.

## The runner: `uv run check`

```bash
uv run check led_psu_enclosure
```

`check.py` at the repo root resolves a model name and, crucially, **exits non-zero**
when the assertions fail, so a check is something CI or a pre-commit hook can hold
you to. Discovery order (`check.py:9-17`):

1. `models.<name>` is a package with a `checks` submodule exposing `main()` — the
   convention for a model large enough to earn its own package.
2. `models.<name>` exposes a top-level `check()` — the convention for a single-file
   model. Returning `False` or raising `AssertionError` fails the run.
3. Neither — it says so plainly and exits 0. A model without checks is not
   reported as a failure, because that would train people to ignore the command.

A package's `checks.main()` owns its own exit code. The standard shape:

```python
def run() -> Report:
    r = Report()
    part = create_thing()
    check_something(part, r)
    return r


def main() -> None:
    import sys

    r = run()
    print(r.render())
    sys.exit(1 if r.failures else 0)
```

## Print-pose assertions

`AGENTS.md` requires every part to be returned already sitting in its print pose:
flat on the bed, print direction `+Z`. That makes coordinates in a check
meaningful — a sample at `z = 0.5` is half a millimetre above the bed, in every
model, without having to know how the part was built.

It also makes the pose itself checkable:

```python
r.check(abs(part.bounding_box().min.Z) < 1e-6, "part sits on z=0")
```

Models establish the pose with a rotate-then-reseat, e.g.
`models/led_psu_enclosure/lid.py:112-113`:

```python
flipped = as_part(Rotation(180, 0, 0) * _build_lid_use_pose())
part = as_part(Pos(0, 0, -flipped.bounding_box().min.Z) * flipped)
```

Same pattern in `models/round_snap_box.py:220`,
`models/drill_storage_gridfinity.py:1166` and `models/lens_cap.py:107`. If you add
a feature that hangs below the old minimum, the reseat handles it — but the
assertion is what tells you the reseat is still there.

## Worked example

From `models/led_psu_enclosure/checks.py:30-52`, the shell check. Note that every
line names what it means physically, and that both the solid and the void are
asserted — checking only "the wall is there" would pass on a part machined from a
solid block:

```python
def check_shell(tray: Part, r: Report) -> None:
    """Wall/floor are solid where they should be and void where they shouldn't."""
    r.section("shell")
    mid_z = 50.0
    wall_mid = c.INTERIOR_X / 2 + c.WALL / 2
    # Sample at y=55, clear of the vent recess (which reaches y=+-45).
    r.check(is_solid_at(tray, wall_mid, 55.0, mid_z), "side wall is solid")
    r.check(not is_solid_at(tray, 0, 0, mid_z), "interior is hollow")
    r.check(is_solid_at(tray, 0, 0, -c.FLOOR / 2), "floor is solid")
    r.check(not is_solid_at(tray, 0, 0, -c.FLOOR - 1), "nothing below the floor")
```

The same file shows the two other probe styles worth copying:

- **Marching a ray to measure a thickness** — `_panel_thickness`
  (`models/led_psu_enclosure/checks.py:214-224`) steps along Y in 0.05 mm
  increments counting solid hits, to check a connector's panel never exceeds the
  3 mm the part is rated for.
- **Interference by volume** — `check_interference`
  (`models/led_psu_enclosure/checks.py:173-188`) intersects every component mock
  with the shell and with each other pair, and fails on more than 1 mm³ of overlap.

## Writing good samples

- **Assert the void as well as the solid.** A rib "exists" check that only samples
  material passes on a part with no bore at all.
- **Offset off surfaces.** `TopAbs_ON` reads as inside, so a sample placed exactly
  on a face is ambiguous. Sit a few tenths clear on the side you mean.
- **Say where you sampled and why**, in a comment, when the position is chosen to
  dodge another feature. The enclosure's `y=55` comment above is the model: without
  it, the next person moves the sample onto the vent recess and gets a mystery
  failure.
- **Put the measurement in `detail`.** `f"{t:.2f} mm"` beats a bare pass/fail every
  time you have to debug the check itself.
- **Check derived arithmetic too**, not only sampled points — snap engagement,
  cantilever strain, whether a part fits through the opening it must pass through.
  These need no geometry query and catch design errors before a print does.
