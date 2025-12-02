# Interactive Element Picker for build123d Viewer

## Overview

An interactive element picker that lets users click on vertices/edges/faces in the 3D viewer to:
- See geometric properties and suggested build123d selectors
- Auto-copy selectors to clipboard
- Build a multi-selection buffer for AI agent retrieval

## User Workflow

```bash
# Show a model
$ uv run show my_model

# In viewer: Click on a face
# → Overlay shows: "Face 5 | Plane Z=10 | faces().sort_by(Axis.Z)[-1]"
# → Selector auto-copied to clipboard

# In code: Paste the selector
fillet(part.faces().sort_by(Axis.Z)[-1], radius=2)

# For AI agents: Query selection buffer
$ uv run selection
[
  {"type": "face", "index": 5, "geometry": "Plane", "center": [0, 0, 10],
   "normal": [0, 0, 1], "area": 100.0, "selector": "faces().sort_by(Axis.Z)[-1]"}
]
```

## Viewer UI

### Click Handling
- Raycast mouse clicks to identify hit vertex/edge/face
- Map hits back to original build123d object indices

### Visual Feedback
- Selected elements highlighted (Catppuccin yellow/peach)
- Toggle behavior: click to select, click again to deselect
- Multiple selections highlighted simultaneously

### Overlay Panel
- Floating panel (bottom-right) shows for most recent click:
  ```
  Face 5
  Plane | Z = 10.0 | Area: 100mm²
  faces().sort_by(Axis.Z)[-1]  [📋 Copied]
  ```
- Clear selection via Esc key or button

### Clipboard
- Each click auto-copies the selector
- Falls back to index-based (`faces()[5]`) if no semantic selector found

## Selection Buffer

### Storage
- In-memory list in viewer server process
- Clears on each new `show` call (indices become invalid)
- Clears on explicit user action (Esc/button)

### Entry Format
```json
{
  "type": "face",
  "index": 5,
  "geometry": "Plane",
  "properties": {
    "center": [0, 0, 10],
    "normal": [0, 0, 1],
    "area": 100.0
  },
  "selector": "faces().sort_by(Axis.Z)[-1]"
}
```

### CLI Access
```bash
$ uv run selection
```
- Queries `GET /selection` on viewer server
- Outputs JSON to stdout
- Human-friendly summary to stderr
- Exit 0 if selection exists, 1 if empty/viewer not running

## Selector Inference

Generate semantic selectors that survive model changes:

### Face Selectors
- Position extremes: `faces().sort_by(Axis.Z)[-1]` (topmost)
- Geometry type: `faces().filter_by(GeomType.CYLINDER)`
- Area extremes: `faces().sort_by(SortBy.AREA)[-1]`
- Combined: `faces().filter_by(GeomType.PLANE).sort_by(Axis.Z)[-1]`

### Edge Selectors
- Position extremes: `edges().sort_by(Axis.Z)[-1]`
- Geometry type: `edges().filter_by(GeomType.CIRCLE)`
- Length extremes: `edges().sort_by(SortBy.LENGTH)[-1]`

### Vertex Selectors
- Position extremes: `vertices().sort_by(Axis.Z)[-1]`

### Fallback
- Index-based with warning: `faces()[5] ⚠️ index-based`
- Shown when no unique semantic selector found

## Implementation

### Repository Locations

| Location | Changes |
|----------|---------|
| `vscode-ocp-cad-viewer/` | Backend API, JS picker, selector inference |
| `build123d-models/` | `selection.py` CLI + pyproject entry |

### Files to Modify/Create

**In vscode-ocp-cad-viewer:**

| File | Change |
|------|--------|
| `ocp_vscode/static/js/picker.js` | New - click handling, raycasting, overlay, clipboard |
| `ocp_vscode/backend.py` | Add `/selection` endpoint, buffer storage, clear on show |
| `ocp_vscode/show.py` | Signal buffer clear when new object shown |
| `ocp_vscode/selector_inference.py` | New - compute semantic selectors from geometry |

**In build123d-models:**

| File | Change |
|------|--------|
| `selection.py` | New - CLI entry point |
| `pyproject.toml` | Add `selection` script entry |

### Data Flow

```
Click in viewer
    ↓
picker.js: raycast → identify element → compute properties
    ↓
picker.js: POST /selection/add {type, index, geometry, properties}
    ↓
backend.py: store in buffer, compute selector suggestion
    ↓
picker.js: receive selector, update overlay, copy to clipboard
    ↓
(later) uv run selection → GET /selection → JSON output
```

## Design Decisions

1. **Semantic selectors over indices** - Indices break when model changes; selectors describe intent
2. **Buffer clears on show** - Old indices meaningless for new geometry
3. **Toggle selection** - Most flexible; click adds, click again removes
4. **CLI over MCP** - Simpler to implement and debug
5. **Upstream-friendly** - Changes designed for potential PR to ocp-vscode
