# bd_warehouse: the companion library

`bd_warehouse` is the parts/standards companion to build123d. It supplies real
fastener geometry (screws, nuts, washers, bearings) and standards-compliant
thread classes.

Verification status of everything below is stated per item. Items marked
**unverified** were written from external documentation and have **not** been
run against the installed package - confirm before relying on them. Items
marked **verified** cite a `file:line` in the installed package, checked
directly.

## Contents

- [Installation status in this repo](#installation-status-in-this-repo)
- [build123d has no thread classes](#build123d-has-no-thread-classes)
- [When to use bd_warehouse](#when-to-use-bd_warehouse)
- [When to hand-roll instead](#when-to-hand-roll-instead)
- [Traps](#traps)
- [Sources](#sources)

## Installation status in this repo

**`bd_warehouse` 0.2.0 is now installed.** It was absent when this reference
was first drafted (see below); the five traps in the [Traps](#traps) section
have since been checked against the installed source and are marked
accordingly.

Checked with:

```bash
ls .venv/lib/python3.12/site-packages/ | grep -i bd
# bd_warehouse
# bd_warehouse-0.2.0.dist-info
```

`bd_warehouse.thread` lives at
`.venv/lib/python3.12/site-packages/bd_warehouse/thread.py`. Line numbers
below refer to that file at 0.2.0; re-check them after any upgrade.

## build123d has no thread classes

**Verified.** `IsoThread`, `AcmeThread`, `TrapezoidalThread` and `Thread` do
not exist anywhere in `build123d` 0.10.0 as installed in this repo's `.venv`:

```bash
grep -rn "class IsoThread\|class AcmeThread\|class Thread" \
  .venv/lib/python3.12/site-packages/build123d/
# no matches
```

They live in `bd_warehouse.thread`. If a snippet imports `IsoThread` from
`build123d`, it is wrong and will `ImportError`.

What build123d *does* ship, and what a hand-rolled thread is built from
(**verified**, both present in 0.10.0):

- `build123d.objects_curve.Helix(pitch, height, radius, ...)` - also takes
  `cone_angle`, `lefthand`, `center`, `direction`.
- `build123d.operations_generic.sweep(sections, path, ..., is_frenet=False,
  transition=Transition.TRANSFORMED, ...)`.

## When to use bd_warehouse

- **Modelling real hardware in an assembly or mock-up.** Showing the actual
  screw, nut, washer or bearing in a `Compound` so the assembly view is
  honest about clearances and stack-up heights. This repo already hand-rolls
  hardware for exactly this purpose - see `create_countersink` in
  `models/drill_storage/assemblies/wood.py`, which builds a hex shank, a conical
  head and a pilot tip by hand. That is a candidate for replacement.
- **Fastener-driven holes.** `bd_warehouse.fastener` can generate the
  clearance hole, counterbore and countersink *from the fastener object*, so
  the hole and the fastener cannot drift apart when the size changes. That is
  a real correctness win over two independent constants.
- **Standards-compliant threads that must mate with real hardware** - a
  printed female thread taking a metal bolt, where the profile has to be
  genuinely ISO rather than approximately ISO.

## When to hand-roll instead

**Custom printable thread profiles.** Everything in
[threads.md](threads.md) - a 45 degree custom V, a DIN 405 round profile,
crest and root flats sized to one extrusion width, a deliberately coarse
pitch - is outside what a standards library will give you.

Sweeping a profile along a `Helix` is roughly twenty lines in builder mode:

```python
from build123d import BuildLine, BuildPart, BuildSketch, Helix, Plane, sweep

with BuildPart() as thread:
    with BuildLine() as path:
        Helix(pitch=PITCH, height=HEIGHT, radius=MAJOR_D / 2)
    with BuildSketch(Plane(origin=path.line @ 0, z_dir=path.line % 0)):
        # tooth cross-section: crest flat, flanks at beta, root fillet
        ...
    sweep(path=path.line, is_frenet=True)
```

This keeps full control over crest flat, root flat, root fillet and the
fade-in, and it matches the repo's builder-mode house style. Prefer it for
anything printed.

## Traps

Each of these is a real behaviour that costs an hour if it is not known in
advance. Four are now **verified** against the installed 0.2.0 source; the
fifth (`taper_angle`) was verified but the original claim was scoped to the
wrong classes and is corrected below.

### Zero allowance (verified)

`IsoThread` emits the **basic ISO 68-1 profile with zero allowance**. There is
no `allowance` parameter anywhere in `IsoThread.__init__`
(`thread.py:474-490`); the only related knob is `interference` (default
`0.2`), which is documented in the class docstring as "Amount the thread will
overlap with nut or bolt core. Used to help create valid threaded objects
where the thread must fuse with another object" - a **boolean-fusion overlap
control**, not a manufacturing fit. Two threads generated at the same
`major_diameter` interfere perfectly - they are the same surface. Every bit of
printing clearance is yours to add, using the clearance table in
[threads.md](threads.md). Do not assume the class has "a fit" built in.

### `simple=True` produces a null shape (verified)

`simple=True` does **not** build a simplified or low-poly thread. Confirmed
verbatim in the base `Thread` class:

```python
# thread.py:190-191
super().__init__(part=Solid.make_box(1, 1, 1))
self.wrapped = TopoDS_Shape()
```

and again in `IsoThread.__init__` (`thread.py:513-514`, identical two lines).
It exists as a preview / speed flag for `bd_warehouse.fastener`, where the
fastener body is what you want to see. Adding a `simple=True` thread to a
`BuildPart` contributes nothing, silently, and the resulting part simply has
no thread on it.

### `end_finishes="chamfer"` is roughly 3-4x slower, not ~90x

Measured directly against the installed `IsoThread` (0.2.0), 5-run average,
`major_diameter`/`pitch`/`length` varied to check the ratio holds across
sizes:

| Size            | fade avg | chamfer avg | ratio |
| ---------------- | -------- | ----------- | ----- |
| M6 x 1.0 x 10 mm  | 0.22 s   | 0.82 s      | 3.7x  |
| M10 x 1.5 x 20 mm | 0.30 s   | 0.89 s      | 3.0x  |
| M20 x 2.5 x 40 mm | 0.37 s   | 0.99 s      | 2.7x  |

The direction is real - `"chamfer"` is consistently slower - but it is a
**roughly 3-4x** penalty, not the ~90x originally reported here (that number
came from comparing two absolute timings, 1.64 s vs 0.087 s, taken out of
context; their own ratio is ~19x, and neither figure reproduces against the
installed package). On a part with several threads it is still the difference
between an interactive edit loop and a slow one, so the practical advice is
unchanged:

Default to `end_finishes=("fade", "fade")` and cut any lead-in with a boolean
`Cone`. That is the repo's house style for lead-ins anyway (see the build123d
gotchas in `AGENTS.md`), because OCC edge chamfers are flaky on thread
geometry, and it is faster besides.

### `manufacturing_compensation` is a radius (verified)

Confirmed at `thread.py:1077-1084` (`PlasticBottleThread`): `apex_radius` and
`root_radius` are each offset by `manufacturing_compensation` directly, on the
radius. It is a **radius** offset, not a diametral one: `0.2` there means
**0.4 mm on the diameter**. Halve any number taken from a diametral clearance
table before passing it.

It also exists **only on `PlasticBottleThread`** - it appears nowhere in
`IsoThread`, `TrapezoidalThread` or `AcmeThread` - so for the classes actually
used for hardware, compensation has to be applied by changing the diameter
argument instead.

### `starts` (verified) and `taper_angle` (verified, corrected scope)

- `starts > 1` (multi-start threads) is a parameter on **`TrapezoidalThread`
  only** (`thread.py:602`). `IsoThread` has no `starts` parameter, and
  `AcmeThread` - a `TrapezoidalThread` subclass - does not expose it in its own
  signature either.
- `taper_angle` exists **only on the low-level `Thread` base class**
  (`thread.py:126`) and raises there:

  ```python
  # thread.py:142-143
  if taper_angle is not None:
      raise ValueError("taper_angle is not currently supported")
  ```

  That much of the original claim is real. But **`IsoThread`,
  `TrapezoidalThread` and `AcmeThread` - the classes this reference recommends
  above for real hardware - do not expose `taper_angle` at all.** None of
  their `__init__` signatures accept it (`thread.py:478-489`, `:600-611`, and
  `AcmeThread` inherits `TrapezoidalThread.__init__` unchanged). Calling
  `IsoThread(..., taper_angle=5)` raises `TypeError: unexpected keyword
  argument`, not `ValueError` - a different failure at a different layer.
  Practically: nothing sold as a taper option is available on the high-level
  classes at all; `taper_angle` is only ever a possibility if you drop to the
  base `Thread` class directly, and even there it is unimplemented.

### Two ways a thread silently eats the rest of your part

Both are topological rather than API-level, so they are documented in full in
the `build123d-geometry-ops` skill (`references/gotchas.md` §6 and §7). Know
that they exist before you write the thread:

1. **Cutting the bore mouth's lead-in cone into the thread's first turn makes
   OCC's fuse return the thread alone** — no exception, no warning. Leave one
   full pitch of plain bore between the lead-in and the start of the thread,
   which the printed-thread rule in [threads.md](threads.md) asks for anyway.
2. **The thread classes are `BasePartObject`s with `mode=Mode.ADD`, so
   constructing one inside a `BuildPart` already adds it** — at the origin.
   `add()`-ing it yourself then leaves a stray second copy there, which is
   silently wrong on its own and collapses the entire part via trap 1 if the
   origin is a bore mouth with a lead-in. Construct it outside the builder and
   add it once.

Worked example carrying both: `models/led_profiles/endcap.py`.

## Sources

- Installed-package checks against `build123d` 0.10.0 in this repo's `.venv`
  (see the commands quoted above) - verified locally, no URL.
- [bd_warehouse documentation][bdw-docs]
- [bd_warehouse repository][bdw-repo]

[bdw-docs]: https://bd-warehouse.readthedocs.io/en/latest/
[bdw-repo]: https://github.com/gumyr/bd_warehouse
