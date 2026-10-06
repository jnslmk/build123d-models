"""Explicit, stock-oriented removal tools for upright passage corners.

The cylindrical middle has the nominal radius over the complete original edge.
Local conical ends run that same section out to a point; unlike a capped prism,
they cannot leave a horizontal shelf in the mouth, shoulder, or rack cap.
"""

from collections.abc import Sequence
from math import isfinite
from typing import cast

from build123d import (
    BuildPart,
    BuildSketch,
    Circle,
    Edge,
    Face,
    GeomType,
    Locations,
    Mode,
    Part,
    Plane,
    Rectangle,
    Shape,
    Sketch,
    Vertex,
    add,
    loft,
)

from models.lib.checks import solid_probe

_TOL = 1e-6  # Topological matching tolerance, not a dimensional allowance.


def _section(x: float, y: float, z: float, sx: int, sy: int, radius: float) -> Sketch:
    """The material-side square less its tangent, radius-sized keep circle."""
    with BuildSketch(Plane.XY.offset(z), mode=Mode.PRIVATE) as section:
        with Locations((x + sx * radius / 2, y + sy * radius / 2)):
            Rectangle(radius, radius)
        with Locations((x + sx * radius, y + sy * radius)):
            Circle(radius, mode=Mode.SUBTRACT)
    return section.sketch


def passage_corner_tools(stock: Part, edges: Sequence[Edge], radius: float) -> Part:
    """Return removal tools derived only from original stock and its edges.

    Only axis-aligned, upright right-angle material corners are compatible with
    this passage primitive. The actual two incident planes and all four local
    material quadrants establish that fact; an internal (270-degree) corner is
    diagnosed, because rounding it would require *adding* material.

    The full-radius middle occupies one radius-sized material-side XY square
    and spans the exact original upright endpoints. Each ruled end contracts
    that section to an apex in an independently classified endpoint air
    quadrant, in two radii of Z travel. Its X/Y offsets are exactly one radius
    with signs selected from the three quadrants empty beside the upright
    edge. Opposite-both is preferred, but a shoulder can occupy that quadrant
    above the edge while a one-axis-flipped candidate stays in the passage.
    The maximum per-axis retreat is 45 degrees. Moving the apex into actual
    air avoids a new square corner or blind notch where the cap grows stock.
    An endpoint with no compatible air apex is diagnosed, never omitted.

    The complete tool stays within original XY +/- radius and endpoint Z
    +/- two radii. Stock itself trims the leads against the real passage-mouth,
    shoulder, and cap faces; no horizontal terminal cut face or tall mask is
    introduced. The keep-circle is tangent to both original upright planes.

    The caller constructs every tool before subtracting any of them. Neither
    edge identities nor material orientation may come from an already-rounded
    part. This function has no side effects on an enclosing BuildPart.
    """
    if not isfinite(radius) or radius <= _TOL:
        raise ValueError(f"Passage corner radius must be positive: {radius}")
    if not edges:
        raise ValueError("Declared passages have no upright corners to round")
    if not stock.solids() or not stock.is_valid:
        raise ValueError("Passage corner tools require valid original stock")

    # Shape equality/hash match TShape and location, not Python object identity.
    # Keep one adjacency map and classifier for all corners in this stock.
    adjacent: dict[Edge, list[Face]] = {}
    for face in cast(Shape, stock).faces():
        for boundary in cast(Shape, face).edges():
            adjacent.setdefault(boundary, []).append(face)
    inside = solid_probe(stock)
    tools = []
    seen: set[Edge] = set()
    for edge in edges:
        box = edge.bounding_box()
        point = edge.center()
        where = f"({point.X:.9g}, {point.Y:.9g}), z=[{box.min.Z:.9g}, {box.max.Z:.9g}]"
        if edge in seen:
            raise ValueError(f"Duplicate designated passage corner at {where}")
        seen.add(edge)
        if (
            edge.geom_type != GeomType.LINE
            or box.max.X - box.min.X > _TOL
            or box.max.Y - box.min.Y > _TOL
            or box.max.Z - box.min.Z <= _TOL
        ):
            raise ValueError(
                f"Passage corner is not a straight upright edge at {where}"
            )
        faces = adjacent.get(edge, [])
        if len(faces) != 2 or any(not face.is_planar_face for face in faces):
            raise ValueError(
                f"Passage corner lacks two original planar faces at {where}"
            )
        normals = [face.normal_at(point) for face in faces]
        axes = []
        for normal in normals:
            if abs(normal.Z) > _TOL:
                raise ValueError(
                    f"Passage corner has a non-upright incident plane at {where}"
                )
            if abs(abs(normal.X) - 1) < _TOL and abs(normal.Y) < _TOL:
                axes.append("x")
            elif abs(abs(normal.Y) - 1) < _TOL and abs(normal.X) < _TOL:
                axes.append("y")
            else:
                raise ValueError(
                    f"Passage corner has a non-axis-aligned incident plane at {where}"
                )
        if set(axes) != {"x", "y"}:
            raise ValueError(f"Passage corner is not a right angle at {where}")

        step = min(radius / 8, edge.length / 8)
        if step <= 10 * _TOL:
            raise ValueError(f"Passage corner is too short to classify at {where}")
        material = [
            (sx, sy)
            for sx in (-1, 1)
            for sy in (-1, 1)
            if inside(point.X + sx * step, point.Y + sy * step, point.Z)
        ]
        if len(material) == 3:
            raise ValueError(
                f"Concave passage corner at {where}; material quadrants={material}. "
                "Nominal rounding requires an addition, not a removal tool."
            )
        if len(material) != 1:
            raise ValueError(
                f"Cannot classify a convex passage corner at {where}; "
                f"material quadrants={material}"
            )
        sx, sy = material[0]
        apices = []
        for end, z in (
            ("lower", box.min.Z - 2 * radius),
            ("upper", box.max.Z + 2 * radius),
        ):
            # The shoulder need not preserve the upright edge's air quadrant.
            # Classify each real endpoint independently against original stock.
            candidates = []
            for dx, dy in ((-sx, -sy), (-sx, sy), (sx, -sy)):
                x, y = point.X + dx * radius, point.Y + dy * radius
                candidates.append((x, y, z))
                if not inside(x, y, z):
                    apices.append(Vertex(x, y, z))
                    break
            else:
                raise ValueError(
                    f"Passage corner has no {end} air-side lead at {where}; "
                    f"endpoint candidates={candidates}"
                )
        lower = _section(point.X, point.Y, box.min.Z, sx, sy, radius)
        upper = _section(point.X, point.Y, box.max.Z, sx, sy, radius)
        with BuildPart(mode=Mode.PRIVATE) as tool:
            loft(
                sections=[
                    apices[0],
                    lower,
                    upper,
                    apices[1],
                ],
                ruled=True,
            )
        if not tool.part.solids() or not tool.part.is_valid:
            raise ValueError(f"Invalid explicit passage corner tool at {where}")
        tools.append(tool.part)

    with BuildPart(mode=Mode.PRIVATE) as combined:
        add(tools)
    if not combined.part.solids() or not combined.part.is_valid:
        raise ValueError("Invalid union of explicit passage corner tools")
    return combined.part
