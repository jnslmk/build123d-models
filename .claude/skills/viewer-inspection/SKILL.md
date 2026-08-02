---
name: viewer-inspection
description: Explains how to identify a specific face, edge or vertex on a model with the CAD viewer's Element Picker and how to retrieve those picks in machine-readable form with `uv run selection`. Covers the click-to-select overlay and its toggle and clear behaviour, the exact JSON shape selection.py returns, its stdout and stderr split and exit code, how far to trust the suggested selector's confidence field, and turning a pick into a stable build123d selector expression. Use when the user points at geometry in the viewer and asks which face or edge it is, when a selector must be written for a particular hole, rim or wall, when `uv run selection` returns nothing, or when deciding which edge a fillet or chamfer should target. Keywords: element picker, select face, selection, pick edge, vertex, selector, which face, arc_center.
---

# Viewer inspection

When the user says "this face" or "that edge", the viewer can answer it precisely
— *if* the Element Picker described below is present in the build you are running.
The picker turns a click in the 3D view into a build123d selector, and
`uv run selection` hands those picks to an agent as JSON.

## Status: the picker could not be confirmed in current source

**The picker UI and its `/selection` HTTP endpoint could not be found anywhere in
the current sibling checkouts or the deployed viewer bundle.** Specifically:

- `~/git-projects/vscode-ocp-cad-viewer/ocp_vscode/backend.py` exposes no HTTP
  routes at all — it is websocket-based (`handle_event`, `handle_properties`,
  `handle_distance`). No `/selection` handler exists.
- This repo's `viewer.py` only starts and proxies to `python -m ocp_vscode`; it
  defines no `/selection` route either.
- `~/git-projects/three-cad-viewer/src/tools/cad_tools/select.ts`
  (`SelectObject`) tracks selected shape *indices* via `notify()` /
  `checkChanges({selected: indices})`. There is no `selector`, `confidence` or
  `expression` concept anywhere in that class.
- The deployed bundle,
  `~/git-projects/vscode-ocp-cad-viewer/ocp_vscode/static/js/three-cad-viewer.esm.js`,
  has zero occurrences of the string `"confidence"`.
- Neither sibling checkout has uncommitted work touching selection, picker or
  confidence, so this is not a build mid-flight either.

**Before relying on any of this, confirm the crosshairs/Picker button and a
populated `selector` field actually exist in your running viewer.** The workflow
below is documented because `AGENTS.md` describes it and a build the reviewer of
this skill could not see may still have it — but as far as current source shows,
it does not exist. The `selection.py` contract in the next section is a separate,
independently verified claim: it is real code in *this* repo regardless of
whether the frontend half exists, and it is safe to rely on for what
`uv run selection` itself does with whatever the buffer contains (including an
empty one).

## Picking in the viewer (the human half, per `AGENTS.md` — unconfirmed above)

1. Click the crosshairs button in the toolbar (or activate the Picker tool).
2. Click faces, edges or vertices in the 3D view.
3. An overlay shows the element type, its geometry info, and a build123d selector.
4. The selector is auto-copied to the clipboard.
5. Clicking the same element again deselects it — selection toggles.
6. `Escape` clears all selections.

Multiple elements can be selected at once; they accumulate into a buffer that the
CLI below reads.

## Reading the picks (the agent half)

```bash
uv run selection
```

`selection.py` GETs `http://127.0.0.1:3939/selection` with a 2 s timeout and
splits its output:

- **stdout** — the selection buffer as a JSON array, `json.dumps(..., indent=2)`.
  This is the machine-readable half; redirect or pipe it.
- **stderr** — a human summary (`Selected N element(s):` and one line per entry).
- **exit code 1** with `No elements selected (or viewer not running)` on stderr
  when the buffer is empty.

### JSON shape

Each entry in the array is an object. Derived from how `selection.py` reads them:

```json
[
  {
    "type": "face",
    "index": 12,
    "geometry": "string describing the element, printed verbatim",
    "selector": {
      "expression": "faces()[12]",
      "confidence": "high"
    }
  }
]
```

| Key | Required | Notes |
| --- | --- | --- |
| `type` | yes | Read with `entry["type"]`. Lower-case element kind — `face`, `edge`, `vertex`. Pluralised to build the fallback expression. |
| `index` | yes | Read with `entry["index"]`. Index of the element within its kind. |
| `geometry` | yes | Read with `entry["geometry"]`. Free-form geometry info, printed as-is in the summary. |
| `selector` | **no** | Read with `entry.get("selector", {})` — an entry may carry no selector at all. |
| `selector.expression` | no | The suggested build123d expression. Falls back to `f"{type}s()[{index}]"` when absent. |
| `selector.confidence` | no | Defaults to `"low"` when absent. `"low"` is flagged with a warning in the summary. |

### How much to trust `expression`

A **low-confidence** expression (or an absent `selector`, which is treated as low)
is a positional index, not a description. `faces()[12]` is valid only for the exact
solid that was on screen — any change to the model renumbers it silently and the
selector then points at unrelated geometry.

So use a pick as a **locator, not as the final code**: read the picked element's
geometry out of the JSON, then write a selector that describes it — a
`filter_by_position`, a `filter_by(Axis...)`, a `group_by(Axis.Z)[-1]`, a radius or
length predicate. That survives an edit to the model; a bare index does not.

High confidence means the expression is already descriptive enough to keep.

## Troubleshooting an empty result

`get_selection()` catches `urllib.error.URLError` and returns `[]`, so a viewer
that is not running and a viewer with nothing selected are **indistinguishable** in
the output — both give exit code 1 and the same message. Check in this order:

1. Is the viewer up? It listens on port 3939 (`viewer.py`, `PORT = 3939`). Start it
   with `uv run show <model>`.
2. Is anything actually selected? Selection toggles, so a second click on the same
   element empties the buffer, and `Escape` clears everything.
3. Does the running viewer build expose `/selection` at all? Current sibling
   source has no such route (see "Status" above) — a 404 or connection refusal
   here most likely means the picker is not present in this build, not that the
   viewer needs restarting. See the `viewer-frontend` skill for how the frontend
   and backend are built and deployed if you need to check what is actually
   running.

## Related gotcha

**`Edge.center()` on a full circle returns a point *on* the curve, not the
centre** — use `edge.arc_center` when matching a picked circular hole mouth back to
a position in code. The `build123d-geometry-ops` skill covers this and the rest of
edge selection in full.
