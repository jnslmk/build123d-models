# OCC and edge-selection gotchas

Each entry is: the symptom you will actually observe, then the fix.

## Contents

- [1. A failed fillet/chamfer corrupts the builder, and failures cascade](#1-a-failed-filletchamfer-corrupts-the-builder-and-failures-cascade)
- [2. `Edge.center()` on a full circle is a point on the curve, not the centre](#2-edgecenter-on-a-full-circle-is-a-point-on-the-curve-not-the-centre)
- [3. `fillet`/`chamfer` are all-or-nothing over the edge set](#3-filletchamfer-are-all-or-nothing-over-the-edge-set)
- [4. Stale edge references](#4-stale-edge-references)
- [5. OCC ops are genuinely flaky](#5-occ-ops-are-genuinely-flaky)

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
- Round or hex bore mouth — subtract `Cone(r, r + ch, ch)` positioned at
  `top_z - ch` with `align=(Align.CENTER, Align.CENTER, Align.MIN)`. See
  `models/drill_storage_gridfinity.py:966-991`, which does exactly this for every
  round bore and every hex socket in one pass, and explains the choice inline.
- Rounded-square rim, no lib import — `_rim_chamfer_tool` at
  `models/drill_storage_gridfinity.py:447-464`.

**Rule of thumb.** Two failed attempts on an edge op is the signal to switch
instruments, not to try a third size.
