"""Render model orthographic/isometric views into a DIN A4 PDF sheet.

Usage:
    uv run render-a4 <model_name> [output.pdf]

Example:
    uv run render-a4 lens_cap
    uv run render-a4 door_latch exports/door_latch_views.pdf
"""

from __future__ import annotations

import fontfix  # noqa: F401 -- preload system libfontconfig before OCP imports

import argparse
import math
import sys
from dataclasses import dataclass
from pathlib import Path

import cairo
from build123d import Edge, Part, PositionMode
from render_svg import get_model_part

A4_WIDTH_MM = 210
A4_HEIGHT_MM = 297
POINTS_PER_MM = 72 / 25.4

PAGE_WIDTH = A4_WIDTH_MM * POINTS_PER_MM
PAGE_HEIGHT = A4_HEIGHT_MM * POINTS_PER_MM

MARGIN_MM = 14
GAP_MM = 8
LABEL_HEIGHT_MM = 6
TITLE_SPACE_MM = 12

MARGIN = MARGIN_MM * POINTS_PER_MM
GAP = GAP_MM * POINTS_PER_MM
LABEL_HEIGHT = LABEL_HEIGHT_MM * POINTS_PER_MM
TITLE_SPACE = TITLE_SPACE_MM * POINTS_PER_MM

VIEW_LAYOUT: list[tuple[str, str]] = [
    ("top", "Top"),
    ("front", "Front"),
    ("left", "Left"),
    ("iso", "Isometric"),
]

# Explicit view-up vectors avoid roll ambiguity for top view.
ORTHO_VIEWPORTS: dict[
    str, tuple[tuple[float, float, float], tuple[float, float, float]]
] = {
    "top": ((0, 0, 100), (0, 1, 0)),
    "front": ((0, -100, 0), (0, 0, 1)),
    "left": ((-100, 0, 0), (0, 0, 1)),
    "iso": ((100, -100, 80), (0, 0, 1)),
}


@dataclass(frozen=True)
class ProjectedView:
    visible: list[list[tuple[float, float]]]
    hidden: list[list[tuple[float, float]]]
    line_segments: list[tuple[float, float, float, float]]
    circles: list[tuple[float, float, float, bool]]
    min_x: float
    min_y: float
    max_x: float
    max_y: float

    @property
    def width(self) -> float:
        return self.max_x - self.min_x

    @property
    def height(self) -> float:
        return self.max_y - self.min_y


def _edge_to_polyline(edge: Edge) -> list[tuple[float, float]]:
    """Convert an edge to sampled 2D points."""
    if edge.geom_type.name == "LINE":
        start = edge.start_point()
        end = edge.end_point()
        return [(start.X, start.Y), (end.X, end.Y)]

    # Sample non-linear edges by parameter for consistent PDF vector output.
    point_count = max(8, min(96, int(edge.length) + 8))
    params = [i / (point_count - 1) for i in range(point_count)]
    points = edge.positions(params, position_mode=PositionMode.PARAMETER)
    return [(point.X, point.Y) for point in points]


def _project_view(part: Part, view: str) -> ProjectedView:
    origin, up, look_at = _camera_for_view(part, view)
    # build123d declares ``project_to_viewport`` on ``Mixin1D``, so a type
    # checker reads a ``Part`` here as the wrong receiver. The hidden-line
    # removal it performs is a whole-``Shape`` operation and is documented for
    # solids -- ``Part.project_to_viewport`` resolves to this very method at
    # runtime and returns the right edges. The annotation upstream is what is
    # wrong, not the call.
    visible_edges, hidden_edges = part.project_to_viewport(  # ty: ignore[invalid-argument-type]
        origin,
        viewport_up=up,
        look_at=look_at,
    )

    visible = [_edge_to_polyline(edge) for edge in visible_edges]
    hidden = [_edge_to_polyline(edge) for edge in hidden_edges]
    line_segments: list[tuple[float, float, float, float]] = []
    circles: list[tuple[float, float, float, bool]] = []

    for edge in visible_edges:
        if edge.geom_type.name == "LINE":
            start = edge.start_point()
            end = edge.end_point()
            line_segments.append((start.X, start.Y, end.X, end.Y))
        elif edge.geom_type.name == "CIRCLE":
            center = edge.center()
            circles.append((center.X, center.Y, edge.radius, bool(edge.is_closed)))

    all_points = [point for polyline in (visible + hidden) for point in polyline]
    if not all_points:
        return ProjectedView(
            visible=visible,
            hidden=hidden,
            line_segments=line_segments,
            circles=circles,
            min_x=0,
            min_y=0,
            max_x=1,
            max_y=1,
        )

    xs = [point[0] for point in all_points]
    ys = [point[1] for point in all_points]
    return ProjectedView(
        visible=visible,
        hidden=hidden,
        line_segments=line_segments,
        circles=circles,
        min_x=min(xs),
        min_y=min(ys),
        max_x=max(xs),
        max_y=max(ys),
    )


def _camera_for_view(
    part: Part,
    view: str,
) -> tuple[
    tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]
]:
    """Build an axis-aligned camera around the model center for a stable orthographic projection."""
    center = part.bounding_box().center()
    cx, cy, cz = center.X, center.Y, center.Z
    offset, up = ORTHO_VIEWPORTS[view]
    ox, oy, oz = offset
    origin = (cx + ox, cy + oy, cz + oz)
    look_at = (cx, cy, cz)
    return origin, up, look_at


def compute_uniform_scale(
    bounds: dict[str, tuple[float, float]],
    usable_width: float,
    usable_height: float,
) -> float:
    """Compute one scale factor shared by all views."""
    max_width = max((size[0] for size in bounds.values()), default=1.0)
    max_height = max((size[1] for size in bounds.values()), default=1.0)
    safe_width = max(max_width, 1e-9)
    safe_height = max(max_height, 1e-9)
    return min(usable_width / safe_width, usable_height / safe_height)


def format_drawing_scale(scale_points_per_model_mm: float) -> str:
    """Format the drawing scale as paper:model (e.g. 1:2.5 or 2:1)."""
    paper_mm_per_model_mm = scale_points_per_model_mm / POINTS_PER_MM
    if abs(paper_mm_per_model_mm - 1.0) < 1e-6:
        return "1:1"
    if paper_mm_per_model_mm < 1.0:
        return f"1:{(1.0 / paper_mm_per_model_mm):.2f}"
    return f"{paper_mm_per_model_mm:.2f}:1"


def parse_scale_option(value: str) -> float | None:
    """Parse --scale value into paper:mm per model:mm. None means auto."""
    normalized = value.strip().lower()
    if normalized == "auto":
        return None

    if ":" in normalized:
        left, right = normalized.split(":", maxsplit=1)
        try:
            paper = float(left)
            model = float(right)
        except ValueError as exc:
            raise ValueError(f"Invalid scale ratio '{value}'") from exc
        if paper <= 0 or model <= 0:
            raise ValueError(f"Scale values must be > 0: '{value}'")
        return paper / model

    try:
        ratio = float(normalized)
    except ValueError as exc:
        raise ValueError(f"Invalid scale '{value}'") from exc
    if ratio <= 0:
        raise ValueError(f"Scale must be > 0: '{value}'")
    return ratio


def _stroke_polylines(
    ctx: cairo.Context,
    polylines: list[list[tuple[float, float]]],
    tx: float,
    ty: float,
    scale: float,
) -> None:
    for polyline in polylines:
        if len(polyline) < 2:
            continue
        start = polyline[0]
        ctx.move_to(tx + start[0] * scale, ty - start[1] * scale)
        for point in polyline[1:]:
            ctx.line_to(tx + point[0] * scale, ty - point[1] * scale)
    ctx.stroke()


def _compute_view_transform(
    projection: ProjectedView,
    x: float,
    y: float,
    w: float,
    h: float,
    scale: float,
) -> tuple[float, float]:
    draw_width = projection.width * scale
    draw_height = projection.height * scale
    tx = x + (w - draw_width) / 2 - projection.min_x * scale
    ty = y + (h - draw_height) / 2 + projection.max_y * scale
    return tx, ty


def _draw_projected_view(
    ctx: cairo.Context,
    projection: ProjectedView,
    x: float,
    y: float,
    w: float,
    h: float,
    scale: float,
) -> None:
    tx, ty = _compute_view_transform(projection, x=x, y=y, w=w, h=h, scale=scale)

    # Hidden edges first (lighter + dashed)
    ctx.set_source_rgb(0.55, 0.55, 0.55)
    ctx.set_line_width(0.4)
    ctx.set_dash([2.0, 2.0], 0)
    _stroke_polylines(ctx, projection.hidden, tx=tx, ty=ty, scale=scale)

    # Visible edges on top
    ctx.set_source_rgb(0.12, 0.12, 0.12)
    ctx.set_line_width(0.9)
    ctx.set_dash([], 0)
    _stroke_polylines(ctx, projection.visible, tx=tx, ty=ty, scale=scale)


def _dedupe_sorted(values: list[float], epsilon: float = 0.05) -> list[float]:
    if not values:
        return []
    sorted_values = sorted(values)
    result = [sorted_values[0]]
    for value in sorted_values[1:]:
        if abs(value - result[-1]) > epsilon:
            result.append(value)
    return result


def _format_length(length_mm: float, precision: int) -> str:
    return f"{length_mm:.{precision}f} mm"


def _draw_arrowhead(
    ctx: cairo.Context, x: float, y: float, angle: float, size: float = 6.0
) -> None:
    wing = math.radians(28)
    x1 = x - size * math.cos(angle - wing)
    y1 = y - size * math.sin(angle - wing)
    x2 = x - size * math.cos(angle + wing)
    y2 = y - size * math.sin(angle + wing)
    ctx.move_to(x, y)
    ctx.line_to(x1, y1)
    ctx.line_to(x2, y2)
    ctx.close_path()
    ctx.fill()


def _draw_linear_dimension(
    ctx: cairo.Context,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    text: str,
    text_offset: float = 10.0,
) -> None:
    ctx.set_source_rgb(0.2, 0.2, 0.2)
    ctx.set_line_width(0.7)
    ctx.set_dash([], 0)
    ctx.move_to(x1, y1)
    ctx.line_to(x2, y2)
    ctx.stroke()

    angle = math.atan2(y2 - y1, x2 - x1)
    _draw_arrowhead(ctx, x1, y1, angle, size=5.0)
    _draw_arrowhead(ctx, x2, y2, angle + math.pi, size=5.0)

    mid_x = (x1 + x2) / 2
    mid_y = (y1 + y2) / 2
    normal_x = -math.sin(angle)
    normal_y = math.cos(angle)

    ctx.set_source_rgb(0.15, 0.15, 0.15)
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(8)
    extents = ctx.text_extents(text)
    text_x = mid_x + normal_x * text_offset - extents.width / 2
    text_y = mid_y + normal_y * text_offset
    ctx.move_to(text_x, text_y)
    ctx.show_text(text)


def _draw_extension_line(
    ctx: cairo.Context, x1: float, y1: float, x2: float, y2: float
) -> None:
    ctx.set_source_rgb(0.5, 0.5, 0.5)
    ctx.set_line_width(0.5)
    ctx.set_dash([], 0)
    ctx.move_to(x1, y1)
    ctx.line_to(x2, y2)
    ctx.stroke()


def _draw_diameter_callout(
    ctx: cairo.Context,
    sx: float,
    sy: float,
    radius_screen: float,
    text: str,
    outward_sign_x: float,
    outward_sign_y: float,
) -> None:
    """Draw a diameter annotation with an outside leader to reduce clutter."""
    anchor_x = sx + outward_sign_x * radius_screen
    anchor_y = sy + outward_sign_y * radius_screen
    elbow_x = anchor_x + outward_sign_x * 14.0
    elbow_y = anchor_y + outward_sign_y * 8.0
    end_x = elbow_x + outward_sign_x * 18.0
    end_y = elbow_y

    _draw_extension_line(ctx, anchor_x, anchor_y, elbow_x, elbow_y)
    _draw_extension_line(ctx, elbow_x, elbow_y, end_x, end_y)

    angle = math.atan2(anchor_y - elbow_y, anchor_x - elbow_x)
    ctx.set_source_rgb(0.2, 0.2, 0.2)
    _draw_arrowhead(ctx, anchor_x, anchor_y, angle, size=4.5)

    ctx.set_source_rgb(0.15, 0.15, 0.15)
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(8)
    extents = ctx.text_extents(text)
    text_x = end_x + (2 if outward_sign_x >= 0 else -extents.width - 2)
    text_y = end_y - 2
    ctx.move_to(text_x, text_y)
    ctx.show_text(text)


def _draw_dimensions(
    ctx: cairo.Context,
    projection: ProjectedView,
    view_name: str,
    x: float,
    y: float,
    w: float,
    h: float,
    scale: float,
    precision: int,
    max_dims_per_axis: int,
    min_dim_value_mm: float,
) -> None:
    if view_name not in {"top", "front", "left"}:
        return

    tx, ty = _compute_view_transform(projection, x=x, y=y, w=w, h=h, scale=scale)

    top_screen = ty - projection.max_y * scale
    right_screen = tx + projection.max_x * scale

    x_values: list[float] = []
    y_values: list[float] = []
    axis_tol = 0.05
    min_feature = 6.0
    for x1, y1, x2, y2 in projection.line_segments:
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        if dx <= axis_tol and dy >= min_feature:
            x_values.extend([x1, x2])
        if dy <= axis_tol and dx >= min_feature:
            y_values.extend([y1, y2])

    # Fallback to overall dimensions when no aligned features are found.
    if not x_values:
        x_values = [projection.min_x, projection.max_x]
    if not y_values:
        y_values = [projection.min_y, projection.max_y]

    x_positions = _dedupe_sorted(x_values, epsilon=0.2)
    y_positions = _dedupe_sorted(y_values, epsilon=0.2)

    dim_gap = 14.0
    ext_pad = 4.0

    # Horizontal chain dimensions above the geometry.
    seen_horizontal_lengths: list[float] = []
    horizontal_slot = 0
    for index, (mx1, mx2) in enumerate(zip(x_positions, x_positions[1:])):
        if horizontal_slot >= max_dims_per_axis:
            break
        dim_value = abs(mx2 - mx1)
        if dim_value < min_dim_value_mm:
            continue
        if any(abs(dim_value - seen) < 0.2 for seen in seen_horizontal_lengths):
            continue
        seen_horizontal_lengths.append(dim_value)
        horizontal_slot += 1
        y_dim = top_screen - dim_gap * horizontal_slot
        sx1 = tx + mx1 * scale
        sx2 = tx + mx2 * scale
        _draw_extension_line(ctx, sx1, top_screen - ext_pad, sx1, y_dim + ext_pad)
        _draw_extension_line(ctx, sx2, top_screen - ext_pad, sx2, y_dim + ext_pad)
        _draw_linear_dimension(
            ctx,
            sx1,
            y_dim,
            sx2,
            y_dim,
            _format_length(dim_value, precision),
            text_offset=9.0,
        )

    # Total horizontal dimension (outermost)
    y_dim = top_screen - dim_gap * (min(len(x_positions), max_dims_per_axis + 1) + 1)
    sx1 = tx + projection.min_x * scale
    sx2 = tx + projection.max_x * scale
    _draw_extension_line(ctx, sx1, top_screen - ext_pad, sx1, y_dim + ext_pad)
    _draw_extension_line(ctx, sx2, top_screen - ext_pad, sx2, y_dim + ext_pad)
    _draw_linear_dimension(
        ctx,
        sx1,
        y_dim,
        sx2,
        y_dim,
        f"TOTAL {_format_length(abs(projection.max_x - projection.min_x), precision)}",
        text_offset=9.0,
    )

    # Vertical chain dimensions to the right of the geometry.
    seen_vertical_lengths: list[float] = []
    vertical_slot = 0
    for index, (my1, my2) in enumerate(zip(y_positions, y_positions[1:])):
        if vertical_slot >= max_dims_per_axis:
            break
        dim_value = abs(my2 - my1)
        if dim_value < min_dim_value_mm:
            continue
        if any(abs(dim_value - seen) < 0.2 for seen in seen_vertical_lengths):
            continue
        seen_vertical_lengths.append(dim_value)
        vertical_slot += 1
        x_dim = right_screen + dim_gap * vertical_slot
        sy1 = ty - my1 * scale
        sy2 = ty - my2 * scale
        _draw_extension_line(ctx, right_screen + ext_pad, sy1, x_dim - ext_pad, sy1)
        _draw_extension_line(ctx, right_screen + ext_pad, sy2, x_dim - ext_pad, sy2)
        _draw_linear_dimension(
            ctx,
            x_dim,
            sy1,
            x_dim,
            sy2,
            _format_length(dim_value, precision),
            text_offset=11.0,
        )

    # Total vertical dimension (outermost)
    x_dim = right_screen + dim_gap * (min(len(y_positions), max_dims_per_axis + 1) + 1)
    sy1 = ty - projection.min_y * scale
    sy2 = ty - projection.max_y * scale
    _draw_extension_line(ctx, right_screen + ext_pad, sy1, x_dim - ext_pad, sy1)
    _draw_extension_line(ctx, right_screen + ext_pad, sy2, x_dim - ext_pad, sy2)
    _draw_linear_dimension(
        ctx,
        x_dim,
        sy1,
        x_dim,
        sy2,
        f"TOTAL {_format_length(abs(projection.max_y - projection.min_y), precision)}",
        text_offset=11.0,
    )

    # Diameter dimensions for visible circles.
    closed_circles = [circle for circle in projection.circles if circle[3]]
    for circle_index, (cx, cy, radius, _is_closed) in enumerate(closed_circles):
        if circle_index >= max_dims_per_axis:
            break
        sx = tx + cx * scale
        sy = ty - cy * scale
        radius_screen = radius * scale
        space_left = (sx - radius_screen) - x
        space_right = (x + w) - (sx + radius_screen)
        space_up = (sy - radius_screen) - y
        space_down = (y + h) - (sy + radius_screen)
        outward_sign_x = 1.0 if space_right >= space_left else -1.0
        outward_sign_y = 1.0 if space_down >= space_up else -1.0
        _draw_diameter_callout(
            ctx,
            sx=sx,
            sy=sy,
            radius_screen=radius_screen,
            text=f"d={_format_length(2 * radius, precision)}",
            outward_sign_x=outward_sign_x,
            outward_sign_y=outward_sign_y,
        )


def render_din_a4_views_pdf(
    model: str,
    output: Path,
    scale_ratio: float | None = None,
    dimensions: str = "full",
    dim_precision: int = 1,
    max_dims_per_axis: int = 6,
    min_dim_value_mm: float = 3.0,
) -> None:
    """Render top/front/left/isometric model views into a DIN A4 PDF."""
    part = get_model_part(model)
    output.parent.mkdir(parents=True, exist_ok=True)

    projections = {view: _project_view(part, view) for view, _label in VIEW_LAYOUT}

    surface = cairo.PDFSurface(str(output), PAGE_WIDTH, PAGE_HEIGHT)
    ctx = cairo.Context(surface)

    # White background
    ctx.set_source_rgb(1, 1, 1)
    ctx.paint()

    # Title
    ctx.set_source_rgb(0.1, 0.1, 0.1)
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(14)
    ctx.move_to(MARGIN, MARGIN)
    ctx.show_text(f"{model} - DIN A4 projection sheet")

    # Compute a 2x2 grid for the view rectangles
    content_top = MARGIN + TITLE_SPACE
    content_height = PAGE_HEIGHT - content_top - MARGIN
    cell_width = (PAGE_WIDTH - (2 * MARGIN) - GAP) / 2
    cell_height = (content_height - GAP) / 2
    frame_height = cell_height - LABEL_HEIGHT

    inner_padding = 6.0
    if scale_ratio is None:
        shared_scale = compute_uniform_scale(
            {
                view: (projection.width, projection.height)
                for view, projection in projections.items()
            },
            usable_width=cell_width - (2 * inner_padding),
            usable_height=frame_height - (2 * inner_padding),
        )
    else:
        shared_scale = scale_ratio * POINTS_PER_MM
    drawing_scale_label = format_drawing_scale(shared_scale)

    # Scale label (paper:model) in top-right header area
    ctx.set_source_rgb(0.2, 0.2, 0.2)
    ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(10)
    scale_text = f"Scale {drawing_scale_label}"
    text_extents = ctx.text_extents(scale_text)
    ctx.move_to(PAGE_WIDTH - MARGIN - text_extents.width, MARGIN)
    ctx.show_text(scale_text)

    for idx, (view, label) in enumerate(VIEW_LAYOUT):
        row = idx // 2
        col = idx % 2
        x = MARGIN + col * (cell_width + GAP)
        y = content_top + row * (cell_height + GAP)

        _draw_projected_view(
            ctx=ctx,
            projection=projections[view],
            x=x + inner_padding,
            y=y + inner_padding,
            w=cell_width - (2 * inner_padding),
            h=frame_height - (2 * inner_padding),
            scale=shared_scale,
        )
        if dimensions == "full":
            _draw_dimensions(
                ctx=ctx,
                projection=projections[view],
                view_name=view,
                x=x + inner_padding,
                y=y + inner_padding,
                w=cell_width - (2 * inner_padding),
                h=frame_height - (2 * inner_padding),
                scale=shared_scale,
                precision=dim_precision,
                max_dims_per_axis=max_dims_per_axis,
                min_dim_value_mm=min_dim_value_mm,
            )

        ctx.set_source_rgb(0.15, 0.15, 0.15)
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        ctx.set_font_size(10)
        ctx.move_to(x, y + frame_height + (LABEL_HEIGHT * 0.75))
        ctx.show_text(label)

    surface.show_page()
    surface.finish()


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Render top/front/left/isometric model views into a DIN A4 PDF",
    )
    parser.add_argument("model", help="Model name (without .py)")
    parser.add_argument(
        "output",
        nargs="?",
        help="Output PDF path (default: exports/<model>_din_a4_views.pdf)",
    )
    parser.add_argument(
        "--scale",
        default="auto",
        help="Drawing scale as paper:model (e.g. 1:1, 1:2, 2:1) or 'auto' (default)",
    )
    parser.add_argument(
        "--dimensions",
        choices=["none", "full"],
        default="full",
        help="Dimension mode (default: full)",
    )
    parser.add_argument(
        "--dim-precision",
        type=int,
        default=1,
        help="Dimension precision in decimal places (default: 1)",
    )
    parser.add_argument(
        "--max-dims-per-axis",
        type=int,
        default=6,
        help="Maximum chain dimensions per axis and view (default: 6)",
    )
    parser.add_argument(
        "--min-dim-mm",
        type=float,
        default=3.0,
        help="Ignore chain dimensions smaller than this value in mm (default: 3.0)",
    )
    args = parser.parse_args()

    output = (
        Path(args.output)
        if args.output
        else Path(f"exports/{args.model}_din_a4_views.pdf")
    )
    try:
        scale_ratio = parse_scale_option(args.scale)
    except ValueError as error:
        print(f"Error: {error}")
        sys.exit(2)

    try:
        render_din_a4_views_pdf(
            args.model,
            output,
            scale_ratio=scale_ratio,
            dimensions=args.dimensions,
            dim_precision=max(args.dim_precision, 0),
            max_dims_per_axis=max(args.max_dims_per_axis, 1),
            min_dim_value_mm=max(args.min_dim_mm, 0.1),
        )
    except ModuleNotFoundError:
        print(f"Model '{args.model}' not found in models/")
        sys.exit(1)

    print(f"Rendered {output}")


if __name__ == "__main__":
    main()
