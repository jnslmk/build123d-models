# OCC and edge-selection gotchas

Each entry is: the symptom you will actually observe, then the fix.

## Contents

- [1. A failed fillet/chamfer corrupts the builder, and failures cascade](#1-a-failed-filletchamfer-corrupts-the-builder-and-failures-cascade)
- [2. `Edge.center()` on a full circle is a point on the curve, not the centre](#2-edgecenter-on-a-full-circle-is-a-point-on-the-curve-not-the-centre)
- [3. `fillet`/`chamfer` are all-or-nothing over the edge set](#3-filletchamfer-are-all-or-nothing-over-the-edge-set)
- [4. Stale edge references](#4-stale-edge-references)
- [5. OCC ops are genuinely flaky](#5-occ-ops-are-genuinely-flaky)
- [6. A `BasePartObject` built inside a builder is already added](#6-a-basepartobject-built-inside-a-builder-is-already-added)
- [7. Fusing a thread whose lead-in cuts into it returns the thread alone](#7-fusing-a-thread-whose-lead-in-cuts-into-it-returns-the-thread-alone)
- [8. A `BuildSketch` opened in a helper function does not reach the caller's `BuildPart`](#8-a-buildsketch-opened-in-a-helper-function-does-not-reach-the-callers-buildpart)
- [9. Indexing into a sorted face/edge list breaks the moment two are tied](#9-indexing-into-a-sorted-faceedge-list-breaks-the-moment-two-are-tied)
- [10. Re-querying between chamfer passes reorders the list, so an index is not an identity](#10-re-querying-between-chamfer-passes-reorders-the-list-so-an-index-is-not-an-identity)

## 1. A failed fillet/chamfer corrupts the builder, and failures cascade

**Symptom.** You wrap each `fillet` in `try`/`except`, run the build, and see one
warning printed. You conclude one mouth went unfilleted. In fact *every* fillet
after that point also failed — the part has no fillets from the first failure
onward. The single warning is a lie of omission, because the later calls raised
too and you swallowed them, or because they "succeeded" against a builder state
that OCC had already left inconsistent.

This is the most expensive gotcha in the list, because the false signal points you
at the wrong feature.

**Fix.** Snapshot the builder's part before the attempt and restore it on failure,
so the failure is genuinely isolated:

```python
saved = builder.part
try:
    chamfer(edges, length=size)
except Exception as exc:  # noqa: BLE001 -- OCC edge ops are flaky
    builder.part = saved
    print(f"warning: chamfer skipped ({exc})")
```

That is exactly `chamfer_edge` in `models/lib/edges.py:47-60`, which additionally
returns `True`/`False` so the caller can react. Use it rather than re-inlining the
pattern. Two models predate the lib helper and carry a private copy —
`models/round_snap_box.py:120-127` and `models/led_psu_enclosure/tray.py:102-109` —
both with the same snapshot/restore shape.

Once restore is in place, a per-feature warning tells the truth: exactly the
features that warned are the ones missing their edge treatment.

## 2. `Edge.center()` on a full circle is a point on the curve, not the centre

**Symptom.** You select hole mouths and try to match them to known hole positions
by comparing `edge.center()` to `(x, y)`. Nothing matches, or the wrong edge
matches, and the mismatch is roughly one hole radius.

**Fix.** For a circular edge use `edge.arc_center`, which is the centre of the
circle. Non-circular edges raise `ValueError` on that attribute, so guard it:

```python
try:
    c = edge.arc_center
except ValueError:
    continue  # not a circular edge
```

Straight edges — the flats of a hex socket, a rectangular pocket — have no
`arc_center`; `edge.center()` on a line is its midpoint and is the right thing to
use there. `models/door_latch.py:53-60` uses `.center()` legitimately: it is
filtering *vertical straight* edges by X, where the midpoint is exactly the value
wanted.

## 3. `fillet`/`chamfer` are all-or-nothing over the edge set

**Symptom.** You pass a group of edges — say every top edge from
`edges().group_by(Axis.Z)[-1]` — and the call raises. Filleting them one at a time
shows that most of them were fine; a single edge beside a thin wall could not take
the requested radius, and it took the whole call down with it.

**Fix, in order of preference.**

1. Split the call so each feature is chamfered independently. One bad edge then
   costs you one edge, not the set.
2. Reduce the size. If the size is a design value you can trade, retry down a
   decreasing ladder and keep the first that succeeds, so each feature still gets
   the largest treatment that fits:

   ```python
   for size in (ch, ch * 0.6, ch * 0.3):
       if chamfer_edge(builder, edges, size):
           break
   ```

   `chamfer_edge` prints `warning: chamfer skipped (...)` on every failing rung
   unconditionally (`models/lib/edges.py:59`), so a ladder that succeeds on its
   second or third rung still logs one or two warnings on the way there. That is
   expected and not itself a problem — the loop's own `break` on `True` is the
   signal that the feature succeeded. Only a warning with **no subsequent
   success for that feature** means the part is missing the treatment; see the
   stop criterion in `SKILL.md`.

3. Switch to a boolean. If the size cannot shrink without stopping being useful
   (a lead-in that must clear a tool, a seat chamfer that must match a mating
   part), the edge op is the wrong instrument. See `SKILL.md`.

Keep at least ~0.4 mm of wall left after the cut, per the `AGENTS.md` edge-design
rules — an op that "works" but eats a wall down to nothing is a worse outcome than
one that raises.

## 4. Stale edge references

**Symptom.** You collect a list of edges once, then loop over it filleting each in
turn. The first one or two work; the rest raise, or apply to visibly the wrong
place.

**Cause.** Every successful `fillet`/`chamfer` rebuilds the solid. The edges in
your list belong to the *previous* topology and no longer refer to the geometry
you meant.

**Fix.** Select and treat **per feature**, re-querying the live edges each pass, in
the shape `models/round_snap_box.py:171-176` actually uses — sort the current
faces, then sort that face's current edges, inside the builder context:

```python
with BuildPart() as box:
    ...
    bottom = box.faces().sort_by(Axis.Z).first
    _chamfer_edge(box, bottom.edges().sort_by(SortBy.RADIUS).last, RING_CHAMFER)
    top = box.faces().sort_by(Axis.Z).last
    _chamfer_edge(box, top.edges().sort_by(SortBy.RADIUS).last, LEAD_IN)
```

Each call re-runs its own selection against the builder as it stands at that
moment, rather than reusing a list captured earlier — that is the part that
matters, not the particular selector.

If you instead need to re-select by a known Z (several mouths at different
heights, for instance), `filter_by_position` filters by each edge's **center**
position, not its extent (`filter_by_position(axis, minimum, maximum,
inclusive=(True, True))`) — a degenerate `minimum == maximum` band depends on
exact float equality against a center that usually carries kernel rounding, and
commonly returns an empty `ShapeList`. Give it a real tolerance band instead:

```python
edges = builder.edges().filter_by_position(Axis.Z, z - 0.01, z + 0.01)
chamfer_edge(builder, edges, LEAD_IN)
```

An empty selection passed to `chamfer`/`fillet` raises, and `chamfer_edge`'s
blanket `except Exception` (`models/lib/edges.py:57-60`) swallows that raise and
prints the same `warning: chamfer skipped` as a genuine OCC failure — so a
selection bug here is easy to misdiagnose as kernel flakiness. If a chamfer you
expected keeps "failing," check the selection is non-empty before blaming OCC.

The same applies to faces and to any selector result held across a modelling
operation. Treat a selection as valid only until the next op on that builder.

## 5. OCC ops are genuinely flaky

**Symptom.** The same code, the same geometry, succeeds on one run and fails on the
next. Or it fails at 0.8 mm, succeeds at 0.6 mm, and fails again at 0.4 mm — there
is no monotone threshold to find. Typical triggers: a ribbed bore mouth, a rim next
to holes, a face carrying countersinks or engraved text.

This is not your bug. It is the kernel, and no amount of parameter tuning converges.

**Worked example from this repo.** OCC refused to chamfer a screw-down lid's
perimeter at *any* length once 14 countersinks existed on the same face — even
though the countersinks were 5 mm clear of the edge being chamfered. Recorded in
`models/lib/edges.py:11-14`. The boolean cannot fail that way, and that is why
`top_chamfer_tool` exists.

**Fix.** Cut a boolean instead:

- Rounded-rect body, top or bottom outer ring — `top_chamfer_tool` /
  `bottom_chamfer_tool` from `models/lib/edges.py`. Both build an oversized slab
  and subtract a lofted keep-frustum, then you subtract the result from your part.
- Round bore mouth — subtract `Cone(r, r + ch, ch)` positioned at `top_z - ch`
  with `align=(Align.CENTER, Align.CENTER, Align.MIN)`. `cut_holes` in
  `models/drill_storage/box.py` does exactly this for every round bore in one
  pass, and explains the choice inline.
- Hex socket mouth — **not** a cone. Loft a hex frustum: `RegularPolygon(r, 6)`
  at `top_z - ch` to `RegularPolygon(r + ch, 6)` at `top_z`, with `r` the
  socket's circumradius. That is `hex_mouth_tool` in
  `models/drill_storage/box.py`, and the same shape `shell.hex_guide_tool` and
  `insert.hex_mouth_tool` already used.

  **The boolean tool's cross-section has to match the hole's.** Swapping an edge
  op for a boolean buys you a cut that cannot fail; it does not by itself buy you
  a chamfer. A chamfer's bevel has to *start on the hole wall*, and a circle of
  the socket's circumradius `rc` lies on a hexagon's wall only at the six
  vertices — along a flat's normal the wall is an apothem `rc * cos(30)` away, a
  further 0.51 mm in on this base. So `Cone(rc, rc + ch, ch)` opened the flat to
  3.79 mm the instant it began, where the wall below it stood at 3.28: a 0.52 mm
  horizontal ledge encircling the mouth. The defect was over-cutting, not an
  unbevelled flat — a counterbore, not a lead-in — and the ledge *was* the sharp
  edge: 6 per socket, one per flat, 48 on the hex base's eight sockets. They
  shipped. Nothing raised, nothing checked, and a manual audit is what found them
  (`models/drill_storage/checks.py:1112-1115`, now covered by
  `sharp_convex_edges`).

  The frustum therefore cuts strictly *less* than the cone did along a flat, and
  is identical to it at the six corners. Growing the *circumradius* by `ch` puts
  the bevel at 45 deg at the corners and ~40 deg to vertical across the flats,
  which is the convention all three tools share. Neither angle is an overhang
  concern: the base prints bores-up and the mouth widens toward +Z, so it is
  self-supporting by construction.
- Rounded-square rim, no lib import — `rim_chamfer_tool` in
  `models/drill_storage/box.py`.

**Rule of thumb.** Two failed attempts on an edge op is the signal to switch
instruments, not to try a third size.

## 6. A `BasePartObject` built inside a builder is already added

**Symptom.** You construct a thread — `IsoThread`, `AcmeThread`,
`TrapezoidalThread` — inside a `BuildPart`, then `add()` it at the position you
want. Either the part comes out slightly too heavy for no reason you can name,
or it is *only the thread*: the cap, the boss, everything else you built is
gone. No exception either way. The severe form reads in the viewer as "my part
disappeared", which points you at the boolean or the sketch, neither of which is
at fault; the mild form does not read as anything at all.

**Cause.** `bd_warehouse`'s thread classes are `BasePartObject` subclasses with
`mode: Mode = Mode.ADD` (`thread.py:489`, `:611`, `:753`), and every
`BasePartObject` **auto-adds itself to the enclosing builder at construction
time, at the origin**. That is the same mechanism that makes `Box(10, 10, 10)`
inside a `BuildPart` do something without an explicit `add`. So constructing the
thread already dropped a copy at the origin, and your `add(thread)` puts a
*second* one where you actually wanted it.

What that costs you depends on what is at the origin. Measured on the endcap and
on a minimal box, not inferred:

| What sits at the origin | Result |
| --- | --- |
| Solid material, or nothing in particular | Part survives with a **stray thread fused in at the origin**. On the endcap, 7322 mm³ instead of 7254 — same bounding box, silently wrong geometry, nothing raised. |
| A bore mouth that has a lead-in cone cut into it | **Part collapses to the thread alone.** The stray copy is then exactly the §7 case: 219 mm³ and a 12.7 x 12.7 bounding box where the real part is 10231 mm³ and 30 x 30. |

The second row is why this is usually reported as "the whole part vanished" —
the auto-added copy lands at `z = 0`, which on a bed-facing bore is precisely
where the lead-in was cut. But the two traps are independent: the endcap's gland
bore is off-origin, so a double-add there costs a stray thread rather than the
part, while its collapse (§7) happens whether or not the construction was
correct.

Either way the fix is the same, and neither symptom announces itself.

**Fix.** Construct the thread **outside** the `BuildPart`, then add it exactly
once, where you want it:

```python
# Outside any builder: nothing auto-adds.
thread = IsoThread(
    major_diameter=GLAND_MAJOR_D,
    pitch=GLAND_PITCH,
    length=GLAND_THREAD_L,
    external=False,
    end_finishes=("fade", "fade"),
)

with BuildPart() as bp:
    ...  # body, bore, lead-ins
    with Locations((0, y, GLAND_COLLAR)):
        add(thread)
```

That is `models/led_profiles/endcap.py:153-164` and `:215-216`, with the reason
in an inline comment so it is not re-learned.

The alternative — construct it inside the builder with `mode=Mode.PRIVATE` and
never `add()` it — works too, but "build it outside, add it once" is the shape
this repo uses: it keeps the one placement of the feature in one place.

This generalises past threads. Any `BasePartObject` (and any `BaseSketchObject`
in a `BuildSketch`) behaves this way. Treat "constructing it is adding it" as
the default, and only reach for `add()` on objects you built somewhere else.

## 7. Fusing a thread whose lead-in cuts into it returns the thread alone

**Symptom.** The same disappearing act as §6, and the mechanism §6 bottoms out
in — but reachable on its own, with the construction done correctly. You cut a
`Cone` lead-in at the bore mouth, then fuse the thread at that same mouth, and
the fuse returns only the thread. Again silent.

**Cause.** The lead-in cone and the thread's first turn occupy the same region.
Fusing a thread whose starting turns have been sliced into by a previous
subtraction gives OCC a degenerate input, and its answer is the thread solid
rather than the union. It does not raise.

Isolated in a minimal case: an M12x1.5 internal thread fused into a bore through
a 30 mm box gives the full part (10231 mm³) with no lead-in cut, and the thread
alone (183 mm³) once a 0.8 mm `Cone` lead-in is cut at the same mouth. Nothing
else changed between the two. Move the thread up one pitch and the full part
comes back.

The endcap behaves the same way: as shipped it is 7254 mm³ with a 27.2 x 31.2 x
18 bounding box, and setting `GLAND_COLLAR = 0` so the lead-in reaches the
thread drops it to 254 mm³ at 12.7 x 12.7 x 11.8. That is the whole cap gone,
from one constant.

**Fix, geometric, not parametric.** Keep the two features apart along the axis:
give the bore **one full pitch of plain collar** below the thread, and cut the
lead-in into that collar. The thread then starts above the cone and the two
never meet:

```python
GLAND_COLLAR = GLAND_PITCH          # plain bore below the thread
GLAND_THREAD_L = CAP_T - GLAND_COLLAR
...
with Locations((0, y, GLAND_COLLAR)):
    add(thread)                     # sits on top of the collar
```

`models/led_profiles/endcap.py:96-101` and `:214-216`. The collar is not a
workaround bolted on for OCC's sake — the printed-thread rule already says not
to start a thread at `z = 0` (see the `fasteners-and-inserts` skill), so the
same millimetre of plain bore satisfies both. Do not try to shrink the lead-in
until the fuse happens to work; the failure is topological and has no reliable
threshold.

**Detection for both 6 and 7.** These are silent, so only a check catches them —
and an ordinary check does, without being written for the purpose. A collapsed
part fails an overall-size assertion instantly, because the thread's footprint is
nothing like the body's:

```python
bb = cap.bounding_box()
r.check(abs(bb.size.X - e.CAP_W) < 0.01 and abs(bb.size.Y - e.CAP_H) < 0.01, "collar size", ...)
r.check(abs(bb.size.Z - (e.CAP_T + e.LIP_DEPTH)) < 0.01, "overall depth", ...)
r.check(len(cap.solids()) == 1, "one solid", ...)
```

`models/led_profiles/checks.py:190-202`. Those three lines were written to check
the collar, not to catch a fuse failure, but a 12.7 x 12.7 x 11.8 thread fails
all three against a 27.2 x 31.2 x 18 cap. The stray-thread variant of §6 is the
harder one — the bounding box is unchanged there, so it takes a volume
comparison or a point sample at the origin
(`references/verification.md`).

The general rule: **assert the part's overall envelope in every model's checks.**
It is one cheap line, and it is the only thing standing between a silent OCC
boolean failure and a slicer.

---

## 8. A `BuildSketch` opened in a helper function does not reach the caller's `BuildPart`

Factor a few sketch-and-extrude steps out into a helper, call it from inside an
open `BuildPart`, and the extrude raises:

```
ValueError: A face or sketch must be provided
```

Minimal reproduction:

```python
def helper():
    with BuildSketch(Plane.XY.offset(10)):
        Circle(5)
    extrude(amount=5)            # <-- raises

with BuildPart() as bp:
    Box(40, 40, 10)
    helper()
```

**What makes it confusing is that object creation *does* cross the boundary.**
The same helper written with `Locations` and a `Cylinder` works perfectly:

```python
def cut_holes():
    with Locations((10, 0, 0), (-10, 0, 0)):
        Cylinder(3, 20, mode=Mode.SUBTRACT)   # works, volume drops
```

So a file can have several helpers that all look alike, and only the ones that
open a `BuildSketch` fail. It reads as an arbitrary error in one function.

### The rule

**Helpers return standalone parts; the function that owns the `BuildPart` does
all the adding and subtracting.** Build them *before* the builder is opened, so
a nested `BuildPart` cannot auto-add itself either (§6):

```python
def create_corner(angle: float = 60.0) -> Part:
    bosses = _strap_boss_solid(angle, start)   # its own BuildPart, no parent
    label = _label_solid(angle)

    with BuildPart() as bp:
        ...
        add(bosses)
        add(label, mode=Mode.SUBTRACT)
```

`models/led_profiles/corner.py` is written this way throughout, and its module
docstring says so, because the file would otherwise look like it factors its
helpers inconsistently. `models/led_profiles/cradle.py:add_drains` is the
exception that proves the rule — it is `Cylinder`-only, so it may stay a helper,
and its docstring notes that it cuts into the ambient builder.

This is the same family as §6 and §7: build123d resolves the enclosing builder
in a way that does not always follow the call stack, so **anything that has to
reach the caller's builder should be a value you pass, not a side effect you
rely on.**

## 9. Indexing into a sorted face/edge list breaks the moment two are tied

**Symptom.** You select "the" bottom face with `bp.faces().sort_by(Axis.Z)[0]`
(or `.first`) and chamfer its `outer_wire()`. It works. Ship a second part in the
same family that happens to have *two* faces at that same Z instead of one, and
the selector still returns exactly one of them — the other is left with raw
square edges, indistinguishable from the treated one in an SVG projection or a
viewer screenshot.

**Cause.** `sort_by` breaks ties in whatever order the underlying OCC face list
already has, which is unspecified and not guaranteed stable across a rebuild.
Indexing `[0]` after the sort silently assumes the key is unique among the
faces present; nothing checks that assumption, and there is no error when it is
false — only fewer edges getting treated than intended.

Three real states of exactly this bug, all in `models/led_profiles`:

- **The strap** used to chamfer its bed with this exact call. Both feet's bed
  faces are coplanar at `z=0`, so it treated one foot and shipped the other
  with four raw edges. Recorded, with the fix, in
  `models/led_profiles/checks.py:773-780` and `strap.py:172-176` — the strap
  now selects both bed faces by position (`_bed_edges`), never by index.
- **The corner** (`models/led_profiles/corner.py:220-222`) still uses
  `bp.faces().sort_by(Axis.Z)[0].outer_wire().edges()` today, against three
  coplanar bed faces — confirmed by querying the built part:
  `create_corner(60).faces().filter_by(Axis.Z).filter_by_position(Axis.Z,
  -0.01, 0.01)` returns 3. It chamfers the right one only because today's
  tie-break happens to favour it; nothing pins that down, and the call has no
  way to notice if a future change adds a fourth bed face that sorts first.
- **`endcap.py:224,228` and `stand.py:273`** use the same idiom and are safe
  *today* only because each is called at a point in the build where exactly one
  face sits at that extreme Z (verified: both parts currently have a single
  face at their `sort_by(Axis.Z)[0]`/`[-1]` target). That is an invariant of
  the current geometry, not something the call itself enforces — it is worth
  re-checking whenever a caller adds a second boss, foot, or lip to either
  part.

**Fix.** Select by predicate over the *whole* set, never by position in a
sorted list — by geometric position, by a purpose-built filter such as
`cradle.bed_pads()` (`models/led_profiles/cradle.py:199-217`, which explicitly
returns every bed pad rather than the lowest-indexed one), or by auditing the
finished part with `models.lib.checks.sharp_convex_edges` to confirm nothing
was left untreated.

## 10. Re-querying between chamfer passes reorders the list, so an index is not an identity

**Symptom.** The second-order form of §9, and harder to catch because the fix
for stale references (§4) — re-query the live face list on every pass — is
already in place. You collect "the four bed pads," then loop, re-querying and
addressing each by index: `for i, pad in enumerate(bed_pads(bp)):
chamfer_edge(bp, pad...)`. Every call returns `True`. One pad still comes out
chamfered **twice** (1.6 mm off its footprint), and its mirror is left
completely untreated.

**Cause.** Re-querying fixes staleness, but a face list is not a stable
identity across the operation that rebuilds it. Chamfering a pad insets its
outline and nudges its centroid — enough to change where that pad falls in a
`sort_by` ordering on the very next pass. An index that pointed at "pad 2"
before the first chamfer can point at a *different* pad afterward, so
addressing pads by index across passes silently double-treats one and skips
another, and `chamfer_edge`'s return value cannot tell you this happened — it
only reports whether the OCC call it was given succeeded, not whether that
call targeted the right face.

**Fix.** Capture identity *before* anything is touched — the pad centroids —
then on each pass re-query the live list and match back to the **nearest**
remaining centroid, never by index:

```python
for target in [face.center() for face in bed_pads(bp)]:
    # Re-queried each pass, then matched back to where the pad *was* rather
    # than by the index it had — chamfering moves a centroid by hundredths,
    # and pads are tens of millimetres apart, so nearest-match is unambiguous
    # even though the list order is not stable.
    pad = min(bed_pads(bp), key=lambda f: (f.center() - target).length)
    took.append(chamfer_edge(bp, pad.outer_wire().edges(), m.EDGE_CHAMFER))
```

`models/led_profiles/cradle.py:199-217` (`bed_pads`) and `:220-253`
(`treat_edges`), with the regression recorded in both docstrings.

**Detection.** A single sample per pad is not enough to catch this, and the
obvious sample — diagonally out from the corner — is actively misleading:
doubling a chamfer insets the flat face by 2x but barely moves the diagonal,
so a diagonal-from-corner sample passes a footprint that has already lost
1.6 mm. `models/led_profiles/checks.py:547-562` (`_chamfer_pair`) samples
along one face instead, 1.5x the chamfer size in from the edge, which is what
actually catches a double application; `check_boss_pad_edges`
(`checks.py:565-571`) then runs that pair **per pad** rather than once for
all four, because a single sample anywhere on the part would have passed
regardless of which pad was wrong.
