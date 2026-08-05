# Hole feature detection

`mesh_zones.py` tracks every hole up the axis it scans and classifies it,
adapting the idea from [pzfreo/build123d-mcp](https://github.com/pzfreo/build123d-mcp)
of reading bolt features (holes, counterbores, countersinks) as named things
rather than raw geometry. Their detector reads a build123d part's own BREP
topology; this one reads an STL, which has none, so it reads the same
slice stack `scan_axis()` already produces instead.

## How it works

A hole is a shapely *interior ring* of a slice polygon. `detect_hole_features()`
slices one axis end to end at an even step (`--feature-step`, default 0.3 mm --
independent of `--fine`, which only refines near *zone* transitions and would
sample straight through a counterbore shoulder or a countersink taper without
ever landing inside it) and, for each slice, records every interior ring's
centre, area-equivalent radius, and **two** circularity measures:

- `circularity` -- the classic isoperimetric figure, `4*pi*area/perimeter**2`,
  1.0 for a perfect circle. **Not used as the "is this round" gate** -- see
  the next bullet for why.
- `radius_uniformity` -- the nearest ring vertex's distance from the ring's
  own centroid, divided by the farthest one's. This *is* the gate
  (`RADIUS_UNIFORMITY_MIN`, 0.95).

`circularity` looked like the obvious filter and was tried first, but it is
weak against exactly the shape that matters most in this repo: a bolt-hole
circle with one chord flattened for a D-flat connector cutout (see
`models/led_psu_enclosure/penetrations.py:90-101`, a real Ø17 SP1712 cutout
with a 15.6 mm flat). Flattening one chord removes very little area and very
little perimeter, so `circularity` barely moves -- measured at **0.987** on
that exact cutout, comfortably above any circularity threshold that would
still accept a real bolt hole's tessellation noise. `radius_uniformity`
reads the same shape differently: the flat pulls the near vertices sharply
toward the centroid while the untouched arc stays at the true radius, so the
ratio drops hard where the isoperimetric figure barely notices. Measured on
the same cutout (`led_psu_enclosure.tray`, exported and run directly through
`detect_hole_features`, not assumed): the thread's own samples range from
0.849 (mid-flat) to a mean of **0.929** across the whole thread, both below
`RADIUS_UNIFORMITY_MIN`. A true circle's tessellation noise sits at
0.9996-0.9999 (measured on `door_latch`, `led_profiles.stand`,
`led_profiles.feet`, `led_psu_enclosure.plate` -- see the table below), and an
outright non-circular slot/rectangle sits at 0.45-0.60. The margin on both
sides of 0.95 is wide, so the cutoff is not reverse-engineered to pass one
part -- it sits in a gap nothing measured so far comes close to from either
direction. `circularity` is still computed and reported on every feature (it
is a cheap, informative number -- it just isn't the gate).

Each ring is then chained to the nearest ring in the next slice (within
`CENTER_MATCH_TOL`) into a **thread**: one physical hole's radius-vs-height
curve from face to face. The thread ends the moment nothing matches -- that is
what a blind hole's floor looks like.

A thread's samples collapse into piecewise **runs**, each either:

- **flat** -- radius stable for at least `MIN_FLAT_SAMPLES` (default 3)
  consecutive samples, net change within tolerance. A plain bore or a
  counterbore's shoulder.
- **taper** -- too short to judge, or drifting past tolerance. A countersink
  or a printed lead-in cone. Adjacent taper runs are bridged into one, since a
  short lead-in sampled at 1-2 points otherwise fragments into several.

## The five feature kinds

| Kind | Rule | build123d recipe |
|---|---|---|
| `through_hole` | one flat run, no taper, thread reaches both axis ends | `Circle(r)`, `extrude(..., mode=Mode.SUBTRACT)` clean through |
| `blind_hole` | one flat run, no taper, thread does not reach both ends | `Circle(r)` subtracted for a partial depth |
| `counterbore` | **2+ flat runs** (a step between two plateaus) | two `Cylinder(r, depth)` subtracts on the same centre |
| `countersink` | **no flat run at all** -- the whole thread is taper | a `Cone(...)` subtract at the mouth |
| `irregular_void` | mean `radius_uniformity` below `RADIUS_UNIFORMITY_MIN` (0.95) | not a bolt hole -- a slot, D-flat, or vent; reported, not classified |

A taper riding *alongside* a through/blind/counterbore classification (a mouth
lead-in) is folded into that feature's `chamfer` field rather than reported as
its own top-level `countersink` -- see "Known limitations" for what that field
does and does not capture.

### Hole patterns

`_detect_patterns()` groups `through_hole`/`blind_hole`/`counterbore` features
of matching `nominal_radius` (the narrowest flat run -- the bolt's own
clearance size, not a counterbore's head recess) and checks whether their
centres form a **grid** (distinct X's x distinct Y's == count), a **radial**
ring (equal distance and equal angular spacing from a common centroid), or a
**linear** row (colinear, equal spacing) -- in that order. No match, no
`hole_pattern` entry; the individual features stand on their own rather than
being merged on a guess.

Centres are compared in the slice's own local 2D basis (see
`mesh_analyze.slice_polygons`), not necessarily world X/Y/Z -- fine for
spacing and angle, which are rotation-invariant, but do not read them as world
coordinates.

## Measured circularity vs radius_uniformity

The numbers behind `RADIUS_UNIFORMITY_MIN` = 0.95, all measured by exporting
the model and running `detect_hole_features` directly, not estimated:

| Ring | circularity | radius_uniformity | Classified |
|---|---|---|---|
| `door_latch` pivot hole (true circle, r=1.75) | 0.9999 | 0.9997 | `through_hole` (correct) |
| `led_profiles.feet` eye-bolt hole (true circle, r=3.30) | 1.0000 | 0.9999 | `counterbore` (correct) |
| `led_profiles.stand` pivot hole (true circle, r=3.30) | 0.9997 | 0.9997 | `counterbore` (correct) |
| `led_psu_enclosure.plate` stud hole (true circle, r=3.51) | 1.0000 | 1.0000 | `counterbore` (correct) |
| `led_psu_enclosure.tray` SP1712 D-flat cutout (Ø17, 15.6 mm flat) | 0.987 | 0.929 (thread mean), 0.849 (worst single slice) | `irregular_void` (correct -- see below) |
| `led_psu_enclosure.plate` air/lightening slot (rectangle) | ~0.03-0.45 | 0.45-0.60 | `irregular_void` (correct) |

The SP1712 row is the one this section used to get wrong: circularity (0.987)
sits well inside "looks like a hole" range, while radius_uniformity (0.929)
sits well inside "reject" range. Both measures agree on every other row here,
which is exactly why circularity looked adequate until a real D-flat part was
actually exported and measured instead of assumed.

## Known limitations (measured, not assumed)

Verified against real models in this repo (`door_latch`, `led_profiles.stand`,
`led_profiles.feet`, `led_psu_enclosure.plate`, `led_psu_enclosure.tray` --
see the task's implementer report for the full table):

- **A counterbore misclassifies as a countersink when `--feature-step` is too
  coarse relative to the run's own length.** `MIN_FLAT_SAMPLES` requires at
  least 3 samples inside a plateau to call it "flat"; a shoulder-to-shoulder
  run shorter than `3 * feature_step` never earns that, and the whole thread
  falls through to "no flat run -> countersink". Measured: capping
  `led_profiles.stand` to 50 slices (step 3.12 mm against a ~5.7 mm run)
  turned its correctly-detected counterbore into a countersink. The default
  step (0.3 mm) does not hit this on any part measured so far, but a much
  larger model hitting `--feature-max-slices`'s cap will.
- **The `chamfer` note on a feature reports only the single longest taper
  run**, even when a counterbore has two (a lead-in at the bed mouth and
  another at the shoulder, as `led_profiles.feet`'s eye-bolt holes do). Both
  tapers are still visible in the feature's own `runs` list -- nothing is
  dropped from the JSON, only the one-line human-readable summary picks a
  representative.
- **A 2-member pattern's `layout` label (`linear` vs `radial`) is arbitrary.**
  Two points on a line trivially satisfy both the colinear-equal-spacing check
  and the equal-radius/equal-angle check (a straight line is a special case of
  a circle through 2 points), and `radial` is checked first. A 3+ member
  pattern (like `led_profiles.stand`'s three M6 pivots) is unambiguous.
- **Pattern grouping is pairwise-greedy on radius, not transitive-safe.** Fine
  for the handful of holes one part actually has; would over-merge a long
  chain of holes with slowly drifting radii.
- **Not tested against a pure/dominant countersink** (a flat-head screw seat
  with no straight-wall clearance section at all) -- none of the parts
  exported so far in this repo has one.
- `led_psu_enclosure`'s SP1712 connector row **was** exported and measured
  (`led_psu_enclosure.tray`, see the table above): the D-flat cutout itself is
  correctly rejected as `irregular_void` by `radius_uniformity`. It was
  *not*, however, seen as a round counterbore pocket behind it, or as a
  linear `hole_pattern` of 4 -- the front wall's Y-axis scan tracked the
  cutout as a single `blind_hole`-shaped thread whose radius drifts from
  ~9 mm down to the flattened ~8.3 mm and back up to ~14.5 mm as the slice
  moves through the wall, rather than resolving a separate circular
  counterbore step the way `led_profiles.feet`/`stand`/`led_psu_enclosure.plate`
  do. Whether that is because this particular cutout's pocket is genuinely
  shaped differently (see `_sp17_counterbore` in `penetrations.py`, which cuts
  from the *inside* face rather than nesting on the same axis the front
  D-flat is cut from) or because four D-flat threads got individually
  rejected before pattern grouping ever saw them was not root-caused further
  in the time available -- recorded here rather than assumed away.
