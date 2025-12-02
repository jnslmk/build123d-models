# Element Picker Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enable interactive click-to-select geometry in the viewer with auto-copy selectors and CLI access for AI agents.

**Architecture:** Extend existing selection/measurement infrastructure. Add new "Picker" tool type that captures selections into a buffer, computes semantic selectors server-side, and exposes via HTTP endpoint. Frontend overlay shows info and copies to clipboard.

**Tech Stack:** Python (Flask backend, build123d selectors), JavaScript (Three.js viewer, clipboard API)

---

## Task 1: Add Selection Buffer to Backend

**Files:**
- Modify: `/home/jonas/git-projects/vscode-ocp-cad-viewer/ocp_vscode/backend.py`

**Step 1: Add Picker tool type and buffer storage**

In `backend.py`, add after line 57 (after `Tool` class):

```python
@dataclass
class Tool:
    Distance = "DistanceMeasurement"
    Properties = "PropertiesMeasurement"
    Picker = "ElementPicker"  # Add this line
```

Add buffer storage in `ViewerBackend.__init__` (after line 92):

```python
def __init__(self, port: int):
    self.port = port
    self.model = {}
    self.activated_tool = None
    self.filter_type = "none"
    self.selection_buffer = []  # Add this line
```

**Step 2: Add method to clear buffer**

Add after `__init__`:

```python
def clear_selection_buffer(self):
    """Clear selection buffer - called when new model is shown."""
    self.selection_buffer = []
```

**Step 3: Commit**

```bash
cd /home/jonas/git-projects/vscode-ocp-cad-viewer
git add ocp_vscode/backend.py
git commit -m "feat(picker): add Picker tool type and selection buffer storage"
```

---

## Task 2: Create Selector Inference Module

**Files:**
- Create: `/home/jonas/git-projects/vscode-ocp-cad-viewer/ocp_vscode/selector_inference.py`

**Step 1: Create the selector inference module**

```python
"""Infer build123d selector expressions from shape geometry."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from OCP.BRep import BRep_Tool
from OCP.BRepAdaptor import BRepAdaptor_Curve, BRepAdaptor_Surface
from OCP.BRepGProp import BRepGProp
from OCP.GeomAbs import (
    GeomAbs_Circle,
    GeomAbs_Cone,
    GeomAbs_Cylinder,
    GeomAbs_Line,
    GeomAbs_Plane,
    GeomAbs_Sphere,
    GeomAbs_Torus,
)
from OCP.GProp import GProp_GProps
from OCP.TopAbs import TopAbs_EDGE, TopAbs_FACE, TopAbs_VERTEX
from OCP.TopoDS import TopoDS

if TYPE_CHECKING:
    from OCP.TopoDS import TopoDS_Shape


class ElementType(str, Enum):
    VERTEX = "vertex"
    EDGE = "edge"
    FACE = "face"


@dataclass
class GeometryInfo:
    """Geometric properties of a shape element."""

    element_type: ElementType
    index: int
    geometry_type: str
    center: tuple[float, float, float]
    normal: tuple[float, float, float] | None  # faces only
    area: float | None  # faces only
    length: float | None  # edges only
    radius: float | None  # circular edges/cylindrical faces


@dataclass
class SelectorSuggestion:
    """A suggested build123d selector expression."""

    expression: str
    confidence: str  # "high", "medium", "low"
    description: str


def get_shape_type(shape: TopoDS_Shape) -> TopAbs_ShapeEnum:
    """Get the shape type."""
    return shape.ShapeType()


def analyze_face(face: TopoDS_Shape) -> GeometryInfo:
    """Extract geometric properties from a face."""
    face = TopoDS.Face_s(face)
    adaptor = BRepAdaptor_Surface(face)
    surface_type = adaptor.GetType()

    # Get geometry type name
    geom_type_map = {
        GeomAbs_Plane: "Plane",
        GeomAbs_Cylinder: "Cylinder",
        GeomAbs_Cone: "Cone",
        GeomAbs_Sphere: "Sphere",
        GeomAbs_Torus: "Torus",
    }
    geometry_type = geom_type_map.get(surface_type, "BSpline")

    # Compute center and area
    props = GProp_GProps()
    BRepGProp.SurfaceProperties_s(face, props)
    center_pnt = props.CentreOfMass()
    center = (round(center_pnt.X(), 4), round(center_pnt.Y(), 4), round(center_pnt.Z(), 4))
    area = round(props.Mass(), 4)

    # Get normal at center (for planar faces)
    normal = None
    if surface_type == GeomAbs_Plane:
        plane = adaptor.Plane()
        axis = plane.Axis()
        d = axis.Direction()
        normal = (round(d.X(), 4), round(d.Y(), 4), round(d.Z(), 4))

    # Get radius for cylindrical/spherical faces
    radius = None
    if surface_type == GeomAbs_Cylinder:
        radius = round(adaptor.Cylinder().Radius(), 4)
    elif surface_type == GeomAbs_Sphere:
        radius = round(adaptor.Sphere().Radius(), 4)

    return GeometryInfo(
        element_type=ElementType.FACE,
        index=-1,  # Set by caller
        geometry_type=geometry_type,
        center=center,
        normal=normal,
        area=area,
        length=None,
        radius=radius,
    )


def analyze_edge(edge: TopoDS_Shape) -> GeometryInfo:
    """Extract geometric properties from an edge."""
    edge = TopoDS.Edge_s(edge)
    adaptor = BRepAdaptor_Curve(edge)
    curve_type = adaptor.GetType()

    # Get geometry type name
    geom_type_map = {
        GeomAbs_Line: "Line",
        GeomAbs_Circle: "Circle",
    }
    geometry_type = geom_type_map.get(curve_type, "Curve")

    # Compute center and length
    props = GProp_GProps()
    BRepGProp.LinearProperties_s(edge, props)
    center_pnt = props.CentreOfMass()
    center = (round(center_pnt.X(), 4), round(center_pnt.Y(), 4), round(center_pnt.Z(), 4))
    length = round(props.Mass(), 4)

    # Get radius for circular edges
    radius = None
    if curve_type == GeomAbs_Circle:
        radius = round(adaptor.Circle().Radius(), 4)

    return GeometryInfo(
        element_type=ElementType.EDGE,
        index=-1,
        geometry_type=geometry_type,
        center=center,
        normal=None,
        area=None,
        length=length,
        radius=radius,
    )


def analyze_vertex(vertex: TopoDS_Shape) -> GeometryInfo:
    """Extract geometric properties from a vertex."""
    vertex = TopoDS.Vertex_s(vertex)
    pnt = BRep_Tool.Pnt_s(vertex)
    center = (round(pnt.X(), 4), round(pnt.Y(), 4), round(pnt.Z(), 4))

    return GeometryInfo(
        element_type=ElementType.VERTEX,
        index=-1,
        geometry_type="Point",
        center=center,
        normal=None,
        area=None,
        length=None,
        radius=None,
    )


def infer_selector(
    info: GeometryInfo,
    all_elements: list[GeometryInfo],
) -> SelectorSuggestion:
    """Infer a build123d selector expression for the given element.

    Args:
        info: The geometry info for the selected element
        all_elements: All elements of the same type in the shape (for uniqueness check)

    Returns:
        A selector suggestion with expression, confidence, and description
    """
    element_type = info.element_type
    collection = f"{element_type.value}s()"  # e.g., "faces()", "edges()", "vertices()"

    # Try position-based selectors (most reliable)
    for axis in ["Z", "Y", "X"]:
        axis_idx = {"X": 0, "Y": 1, "Z": 2}[axis]
        sorted_elements = sorted(all_elements, key=lambda e: e.center[axis_idx])

        if info == sorted_elements[-1]:
            # This is the max element on this axis
            expr = f"{collection}.sort_by(Axis.{axis})[-1]"
            return SelectorSuggestion(
                expression=expr,
                confidence="high",
                description=f"Topmost along {axis} axis",
            )
        elif info == sorted_elements[0]:
            # This is the min element on this axis
            expr = f"{collection}.sort_by(Axis.{axis})[0]"
            return SelectorSuggestion(
                expression=expr,
                confidence="high",
                description=f"Bottommost along {axis} axis",
            )

    # Try geometry type filter
    same_geom = [e for e in all_elements if e.geometry_type == info.geometry_type]
    if len(same_geom) == 1:
        expr = f"{collection}.filter_by(GeomType.{info.geometry_type.upper()})"
        return SelectorSuggestion(
            expression=expr,
            confidence="high",
            description=f"Only {info.geometry_type} {element_type.value}",
        )

    # Try area/length extremes for faces/edges
    if element_type == ElementType.FACE and info.area is not None:
        sorted_by_area = sorted(all_elements, key=lambda e: e.area or 0)
        if info == sorted_by_area[-1]:
            expr = f"{collection}.sort_by(SortBy.AREA)[-1]"
            return SelectorSuggestion(
                expression=expr,
                confidence="high",
                description="Largest face by area",
            )
        elif info == sorted_by_area[0]:
            expr = f"{collection}.sort_by(SortBy.AREA)[0]"
            return SelectorSuggestion(
                expression=expr,
                confidence="high",
                description="Smallest face by area",
            )

    if element_type == ElementType.EDGE and info.length is not None:
        sorted_by_length = sorted(all_elements, key=lambda e: e.length or 0)
        if info == sorted_by_length[-1]:
            expr = f"{collection}.sort_by(SortBy.LENGTH)[-1]"
            return SelectorSuggestion(
                expression=expr,
                confidence="high",
                description="Longest edge",
            )
        elif info == sorted_by_length[0]:
            expr = f"{collection}.sort_by(SortBy.LENGTH)[0]"
            return SelectorSuggestion(
                expression=expr,
                confidence="high",
                description="Shortest edge",
            )

    # Fallback to index-based
    expr = f"{collection}[{info.index}]"
    return SelectorSuggestion(
        expression=expr,
        confidence="low",
        description="Index-based (may break if model changes)",
    )


def geometry_info_to_dict(info: GeometryInfo) -> dict:
    """Convert GeometryInfo to JSON-serializable dict."""
    return {
        "type": info.element_type.value,
        "index": info.index,
        "geometry": info.geometry_type,
        "center": list(info.center),
        "normal": list(info.normal) if info.normal else None,
        "area": info.area,
        "length": info.length,
        "radius": info.radius,
    }


def selector_to_dict(suggestion: SelectorSuggestion) -> dict:
    """Convert SelectorSuggestion to JSON-serializable dict."""
    return {
        "expression": suggestion.expression,
        "confidence": suggestion.confidence,
        "description": suggestion.description,
    }
```

**Step 2: Commit**

```bash
cd /home/jonas/git-projects/vscode-ocp-cad-viewer
git add ocp_vscode/selector_inference.py
git commit -m "feat(picker): add selector inference module for build123d expressions"
```

---

## Task 3: Add Picker Tool Handler to Backend

**Files:**
- Modify: `/home/jonas/git-projects/vscode-ocp-cad-viewer/ocp_vscode/backend.py`

**Step 1: Add imports at top of file**

After existing imports (around line 20):

```python
from ocp_vscode.selector_inference import (
    ElementType,
    analyze_edge,
    analyze_face,
    analyze_vertex,
    geometry_info_to_dict,
    infer_selector,
    selector_to_dict,
)
```

**Step 2: Store element lists during model loading**

In `load_model` method, after line 189 where shapes are stored, add storage for all elements:

```python
# After: self.model[id_] = compound.Moved(loc)
# Add element lists for selector inference
self.all_faces[id_] = []
self.all_edges[id_] = []
self.all_vertices[id_] = []
```

And initialize these in `__init__`:

```python
self.all_faces = {}
self.all_edges = {}
self.all_vertices = {}
```

**Step 3: Add picker toggle handler in handle_activated_tool**

After line 144 (after Properties handling), add:

```python
elif self.activated_tool == Tool.Picker:
    return self.handle_picker(selected_objs, changes.get("pickerAction"))
```

**Step 4: Add handle_picker method**

Add after `handle_properties` method:

```python
def handle_picker(self, selected_ids: list[str], action: str | None) -> dict | None:
    """Handle element picker selections.

    Args:
        selected_ids: List of selected shape IDs
        action: "add", "remove", or "clear"
    """
    if action == "clear":
        self.selection_buffer = []
        return self._picker_response()

    if not selected_ids:
        return None

    shape_id = selected_ids[0]
    if shape_id not in self.model:
        return None

    shape = self.model[shape_id]

    # Determine element type from ID
    if "/faces/" in shape_id:
        element_type = ElementType.FACE
        info = analyze_face(shape)
        # Extract index from ID like "obj/faces/faces_3"
        idx = int(shape_id.split("_")[-1])
        info.index = idx
        # Get all faces for selector inference
        parent_id = shape_id.split("/faces/")[0]
        all_elements = self._get_all_face_infos(parent_id)
    elif "/edges/" in shape_id:
        element_type = ElementType.EDGE
        info = analyze_edge(shape)
        idx = int(shape_id.split("_")[-1])
        info.index = idx
        parent_id = shape_id.split("/edges/")[0]
        all_elements = self._get_all_edge_infos(parent_id)
    elif "/vertices/" in shape_id:
        element_type = ElementType.VERTEX
        info = analyze_vertex(shape)
        idx = int(shape_id.split("_")[-1])
        info.index = idx
        parent_id = shape_id.split("/vertices/")[0]
        all_elements = self._get_all_vertex_infos(parent_id)
    else:
        return None

    # Infer selector
    selector = infer_selector(info, all_elements)

    # Build selection entry
    entry = {
        **geometry_info_to_dict(info),
        "selector": selector_to_dict(selector),
        "shape_id": shape_id,
    }

    # Toggle in buffer
    existing_idx = next(
        (i for i, e in enumerate(self.selection_buffer) if e["shape_id"] == shape_id),
        None
    )

    if existing_idx is not None:
        # Remove if already selected
        self.selection_buffer.pop(existing_idx)
        entry["action"] = "removed"
    else:
        # Add to buffer
        self.selection_buffer.append(entry)
        entry["action"] = "added"

    return self._picker_response(entry)

def _picker_response(self, latest: dict | None = None) -> dict:
    """Build picker response to send to frontend."""
    response = {
        "type": "backend_response",
        "subtype": "tool_response",
        "tool_type": Tool.Picker,
        "buffer": self.selection_buffer,
        "buffer_count": len(self.selection_buffer),
    }
    if latest:
        response["latest"] = latest
    send_response(response, self.port)
    return response

def _get_all_face_infos(self, parent_id: str) -> list:
    """Get GeometryInfo for all faces of a parent shape."""
    infos = []
    i = 0
    while True:
        face_id = f"{parent_id}/faces/faces_{i}"
        if face_id not in self.model:
            break
        info = analyze_face(self.model[face_id])
        info.index = i
        infos.append(info)
        i += 1
    return infos

def _get_all_edge_infos(self, parent_id: str) -> list:
    """Get GeometryInfo for all edges of a parent shape."""
    infos = []
    i = 0
    while True:
        edge_id = f"{parent_id}/edges/edges_{i}"
        if edge_id not in self.model:
            break
        info = analyze_edge(self.model[edge_id])
        info.index = i
        infos.append(info)
        i += 1
    return infos

def _get_all_vertex_infos(self, parent_id: str) -> list:
    """Get GeometryInfo for all vertices of a parent shape."""
    infos = []
    i = 0
    while True:
        vertex_id = f"{parent_id}/vertices/vertices_{i}"
        if vertex_id not in self.model:
            break
        info = analyze_vertex(self.model[vertex_id])
        info.index = i
        infos.append(info)
        i += 1
    return infos
```

**Step 5: Commit**

```bash
cd /home/jonas/git-projects/vscode-ocp-cad-viewer
git add ocp_vscode/backend.py
git commit -m "feat(picker): add picker tool handler with selector inference"
```

---

## Task 4: Clear Buffer on New Show

**Files:**
- Modify: `/home/jonas/git-projects/vscode-ocp-cad-viewer/ocp_vscode/backend.py`

**Step 1: Clear buffer in load_model**

At the start of `load_model` method (around line 146), add:

```python
def load_model(self, raw_model):
    self.clear_selection_buffer()  # Clear buffer when new model shown
    # ... rest of method
```

**Step 2: Commit**

```bash
cd /home/jonas/git-projects/vscode-ocp-cad-viewer
git add ocp_vscode/backend.py
git commit -m "feat(picker): clear selection buffer when new model is shown"
```

---

## Task 5: Add HTTP Endpoint for Selection Buffer

**Files:**
- Modify: `/home/jonas/git-projects/vscode-ocp-cad-viewer/ocp_vscode/standalone.py`

**Step 1: Add Flask route for selection endpoint**

In the `Viewer` class, after the existing routes (around line 394), add:

```python
@self.app.route("/selection")
def get_selection():
    """Return current selection buffer as JSON."""
    import json
    buffer = self.backend.selection_buffer if self.backend else []
    return json.dumps(buffer), 200, {"Content-Type": "application/json"}

@self.app.route("/selection/clear", methods=["POST"])
def clear_selection():
    """Clear the selection buffer."""
    import json
    if self.backend:
        self.backend.clear_selection_buffer()
    return json.dumps({"status": "cleared"}), 200, {"Content-Type": "application/json"}
```

**Step 2: Commit**

```bash
cd /home/jonas/git-projects/vscode-ocp-cad-viewer
git add ocp_vscode/standalone.py
git commit -m "feat(picker): add HTTP endpoints for selection buffer access"
```

---

## Task 6: Add Picker Tool to Frontend JavaScript

**Files:**
- Modify: `/home/jonas/git-projects/vscode-ocp-cad-viewer/ocp_vscode/static/js/three-cad-viewer.esm.js`

**Step 1: Add Picker to ToolTypes**

Find `ToolTypes` definition (search for `const ToolTypes`) and add:

```javascript
const ToolTypes = {
    SELECT: "Select",
    DISTANCE: "DistanceMeasurement",
    PROPERTIES: "PropertiesMeasurement",
    PICKER: "ElementPicker",  // Add this
};
```

**Step 2: Add picker response handler**

Find where backend responses are handled (search for `backend_response` or `tool_response`). Add handler for Picker responses:

```javascript
if (response.tool_type === "ElementPicker") {
    this.handlePickerResponse(response);
}
```

**Step 3: Add handlePickerResponse method**

```javascript
handlePickerResponse(response) {
    const latest = response.latest;
    if (!latest) return;

    // Update overlay
    this.showPickerOverlay(latest);

    // Copy selector to clipboard
    if (latest.selector && latest.action === "added") {
        const expr = latest.selector.expression;
        navigator.clipboard.writeText(expr).then(() => {
            console.log("Selector copied:", expr);
        });
    }
}

showPickerOverlay(info) {
    // Create or update overlay element
    let overlay = document.getElementById("picker-overlay");
    if (!overlay) {
        overlay = document.createElement("div");
        overlay.id = "picker-overlay";
        overlay.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: rgba(30, 30, 46, 0.95);
            color: #cdd6f4;
            padding: 12px 16px;
            border-radius: 8px;
            font-family: monospace;
            font-size: 13px;
            max-width: 400px;
            z-index: 10000;
            border: 1px solid #45475a;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        `;
        document.body.appendChild(overlay);
    }

    const action = info.action === "added" ? "Selected" : "Deselected";
    const typeLabel = info.type.charAt(0).toUpperCase() + info.type.slice(1);
    const geom = info.geometry;
    const selector = info.selector;

    let details = "";
    if (info.type === "face") {
        if (info.normal) {
            details = `Normal: (${info.normal.join(", ")})`;
        }
        if (info.area) {
            details += ` | Area: ${info.area}mm²`;
        }
    } else if (info.type === "edge") {
        if (info.length) {
            details = `Length: ${info.length}mm`;
        }
    }
    if (info.radius) {
        details += ` | R: ${info.radius}mm`;
    }

    const confidence = selector.confidence === "low" ? " ⚠️" : "";
    const copied = info.action === "added" ? " 📋" : "";

    overlay.innerHTML = `
        <div style="color: #f9e2af; margin-bottom: 4px;">${action}: ${typeLabel} ${info.index}</div>
        <div style="color: #a6adc8; font-size: 11px; margin-bottom: 6px;">${geom} | ${details}</div>
        <div style="color: #89b4fa;">${selector.expression}${confidence}${copied}</div>
        <div style="color: #6c7086; font-size: 10px; margin-top: 4px;">${selector.description}</div>
    `;

    // Auto-hide after 4 seconds
    clearTimeout(this.pickerOverlayTimeout);
    this.pickerOverlayTimeout = setTimeout(() => {
        overlay.style.opacity = "0";
        setTimeout(() => overlay.remove(), 300);
    }, 4000);
    overlay.style.opacity = "1";
}
```

**Step 4: Commit**

```bash
cd /home/jonas/git-projects/vscode-ocp-cad-viewer
git add ocp_vscode/static/js/three-cad-viewer.esm.js
git commit -m "feat(picker): add frontend picker tool with overlay and clipboard"
```

---

## Task 7: Add Picker Tool Button to Toolbar

**Files:**
- Modify: `/home/jonas/git-projects/vscode-ocp-cad-viewer/ocp_vscode/static/js/three-cad-viewer.esm.js`

**Step 1: Find toolbar button creation**

Search for where Distance and Properties buttons are created (search for `DistanceMeasurement` in toolbar context). Add Picker button nearby:

```javascript
// Add Picker tool button
const pickerButton = this.createToolbarButton({
    icon: "crosshairs",  // or appropriate icon
    title: "Element Picker (copy selectors)",
    onClick: () => {
        this.activateTool(ToolTypes.PICKER);
    }
});
```

**Step 2: Handle picker tool activation**

In the tool activation handler, add case for Picker:

```javascript
if (toolActivated === ToolTypes.PICKER) {
    this.viewer.checkChanges({ activeTool: ToolTypes.PICKER });
}
```

**Step 3: Commit**

```bash
cd /home/jonas/git-projects/vscode-ocp-cad-viewer
git add ocp_vscode/static/js/three-cad-viewer.esm.js
git commit -m "feat(picker): add picker tool button to toolbar"
```

---

## Task 8: Send pickerAction with Selection Changes

**Files:**
- Modify: `/home/jonas/git-projects/vscode-ocp-cad-viewer/ocp_vscode/static/js/three-cad-viewer.esm.js`

**Step 1: Modify selection notification to include pickerAction**

Find where `selectedShapeIDs` is sent (around line 80271-80276). When Picker tool is active, include the action:

```javascript
if (this.activeTool === ToolTypes.PICKER) {
    this.viewer.checkChanges({
        selectedShapeIDs: [...ids, this.shift],
        pickerAction: "add",  // or determine from toggle state
    }, true);
}
```

**Step 2: Add keyboard shortcut for clear (Escape)**

```javascript
document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && this.activeTool === ToolTypes.PICKER) {
        this.viewer.checkChanges({ pickerAction: "clear" }, true);
        // Clear visual selections
        this.selectedShapes = [];
        this.updateSelectionHighlights();
    }
});
```

**Step 3: Commit**

```bash
cd /home/jonas/git-projects/vscode-ocp-cad-viewer
git add ocp_vscode/static/js/three-cad-viewer.esm.js
git commit -m "feat(picker): send pickerAction with selections, add Escape to clear"
```

---

## Task 9: Create Selection CLI Command

**Files:**
- Create: `/home/jonas/git-projects/build123d-models/.worktrees/element-picker/selection.py`

**Step 1: Create the CLI script**

```python
#!/usr/bin/env python3
"""CLI to query the viewer's selection buffer."""

from __future__ import annotations

import json
import sys
import urllib.request
import urllib.error


VIEWER_URL = "http://127.0.0.1:3939"


def get_selection() -> list[dict]:
    """Fetch selection buffer from viewer server."""
    try:
        with urllib.request.urlopen(f"{VIEWER_URL}/selection", timeout=2) as response:
            return json.loads(response.read().decode())
    except urllib.error.URLError:
        return []


def format_entry(entry: dict) -> str:
    """Format a selection entry for human-readable output."""
    elem_type = entry["type"].capitalize()
    idx = entry["index"]
    geom = entry["geometry"]
    selector = entry.get("selector", {})
    expr = selector.get("expression", f"{entry['type']}s()[{idx}]")
    confidence = selector.get("confidence", "low")

    warning = " ⚠️" if confidence == "low" else ""
    return f"  {elem_type} {idx}: {geom}, {expr}{warning}"


def main() -> None:
    """Main entry point."""
    selection = get_selection()

    if not selection:
        print("No elements selected (or viewer not running)", file=sys.stderr)
        sys.exit(1)

    # Human-readable summary to stderr
    print(f"Selected {len(selection)} element(s):", file=sys.stderr)
    for entry in selection:
        print(format_entry(entry), file=sys.stderr)
    print(file=sys.stderr)

    # JSON to stdout (for machine consumption)
    print(json.dumps(selection, indent=2))


if __name__ == "__main__":
    main()
```

**Step 2: Commit**

```bash
cd /home/jonas/git-projects/build123d-models/.worktrees/element-picker
git add selection.py
git commit -m "feat: add selection CLI to query viewer's selection buffer"
```

---

## Task 10: Add Selection Script Entry Point

**Files:**
- Modify: `/home/jonas/git-projects/build123d-models/.worktrees/element-picker/pyproject.toml`

**Step 1: Add script entry**

In `[project.scripts]` section, add:

```toml
[project.scripts]
show = "show:main"
export = "export_model:main"
render = "render_svg:main"
selection = "selection:main"
```

**Step 2: Add selection.py to setuptools modules**

In `[tool.setuptools]` section:

```toml
py-modules = ["show", "export_model", "main", "viewer", "render_svg", "export", "selection"]
```

**Step 3: Commit**

```bash
cd /home/jonas/git-projects/build123d-models/.worktrees/element-picker
git add pyproject.toml
git commit -m "feat: add selection command to pyproject.toml"
```

---

## Task 11: Update CLAUDE.md Documentation

**Files:**
- Modify: `/home/jonas/git-projects/build123d-models/.worktrees/element-picker/CLAUDE.md`

**Step 1: Add selection command documentation**

In the Commands section, add:

```markdown
# Query selection buffer (elements clicked in viewer)
uv run selection                      # JSON output + human summary
```

Add a new section after "## Viewer":

```markdown
## Element Picker

The viewer includes an Element Picker tool for interactive geometry selection:

1. Click the crosshairs button in the toolbar (or activate Picker tool)
2. Click on faces/edges/vertices in the 3D view
3. Overlay shows: element type, geometry info, and build123d selector
4. Selector auto-copies to clipboard
5. Click again to deselect (toggle behavior)
6. Press Escape to clear all selections

**For AI agents:** Use `uv run selection` to retrieve selected elements as JSON with suggested selectors.
```

**Step 2: Commit**

```bash
cd /home/jonas/git-projects/build123d-models/.worktrees/element-picker
git add CLAUDE.md
git commit -m "docs: add element picker documentation to CLAUDE.md"
```

---

## Task 12: Integration Test

**Step 1: Rebuild and test manually**

```bash
# In build123d-models worktree
cd /home/jonas/git-projects/build123d-models/.worktrees/element-picker
uv sync

# Show a test model
uv run show cube

# In viewer:
# 1. Click Picker tool button
# 2. Click on a face
# 3. Verify overlay appears with selector
# 4. Verify clipboard has selector

# Test CLI
uv run selection
```

**Step 2: Verify JSON output format**

Expected output:
```json
[
  {
    "type": "face",
    "index": 5,
    "geometry": "Plane",
    "center": [0, 0, 10],
    "normal": [0, 0, 1],
    "area": 100.0,
    "length": null,
    "radius": null,
    "selector": {
      "expression": "faces().sort_by(Axis.Z)[-1]",
      "confidence": "high",
      "description": "Topmost along Z axis"
    },
    "shape_id": "cube/faces/faces_5"
  }
]
```

**Step 3: Test toggle and clear**

1. Click same face again → should deselect
2. Select multiple elements → buffer should accumulate
3. Press Escape → buffer should clear
4. `uv run selection` should return empty (exit code 1)

---

## Summary

| Task | Files | Purpose |
|------|-------|---------|
| 1 | backend.py | Add Picker tool type and buffer storage |
| 2 | selector_inference.py | Create selector inference module |
| 3 | backend.py | Add picker tool handler |
| 4 | backend.py | Clear buffer on new show |
| 5 | standalone.py | Add HTTP endpoint for selection |
| 6 | three-cad-viewer.esm.js | Add frontend picker with overlay |
| 7 | three-cad-viewer.esm.js | Add toolbar button |
| 8 | three-cad-viewer.esm.js | Send pickerAction, add Escape handler |
| 9 | selection.py | Create CLI command |
| 10 | pyproject.toml | Add script entry point |
| 11 | CLAUDE.md | Update documentation |
| 12 | - | Integration testing |
