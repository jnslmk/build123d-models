"""Render model orthographic/isometric views into a DIN A4 PDF sheet.

Usage:
    uv run render-a4 <model_name> [output.pdf]

Example:
    uv run render-a4 cube
    uv run render-a4 door_latch exports/door_latch_views.pdf
"""

from __future__ import annotations

import argparse
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
ORTHO_VIEWPORTS: dict[str, tuple[tuple[float, float, float], tuple[float, float, float]]] = {
    "top": ((0, 0, 100), (0, 1, 0)),
    "front": ((0, -100, 0), (0, 0, 1)),
    "left": ((-100, 0, 0), (0, 0, 1)),
    "iso": ((100, -100, 80), (0, 0, 1)),
}

@dataclass(frozen=True)
class ProjectedView:
    visible: list[list[tuple[float, float]]]
    hidden: list[list[tuple[float, float]]]
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
    visible_edges, hidden_edges = part.project_to_viewport(
        origin,
        viewport_up=up,
        look_at=look_at,
    )

    visible = [_edge_to_polyline(edge) for edge in visible_edges]
    hidden = [_edge_to_polyline(edge) for edge in hidden_edges]

    all_points = [point for polyline in (visible + hidden) for point in polyline]
    if not all_points:
        return ProjectedView(visible=visible, hidden=hidden, min_x=0, min_y=0, max_x=1, max_y=1)

    xs = [point[0] for point in all_points]
    ys = [point[1] for point in all_points]
    return ProjectedView(
        visible=visible,
        hidden=hidden,
        min_x=min(xs),
        min_y=min(ys),
        max_x=max(xs),
        max_y=max(ys),
    )


def _camera_for_view(
    part: Part,
    view: str,
) -> tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]:
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


def _draw_projected_view(
    ctx: cairo.Context,
    projection: ProjectedView,
    x: float,
    y: float,
    w: float,
    h: float,
    scale: float,
) -> None:
    draw_width = projection.width * scale
    draw_height = projection.height * scale

    tx = x + (w - draw_width) / 2 - projection.min_x * scale
    ty = y + (h - draw_height) / 2 + projection.max_y * scale

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


def render_din_a4_views_pdf(model: str, output: Path, scale_ratio: float | None = None) -> None:
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
            {view: (projection.width, projection.height) for view, projection in projections.items()},
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
    args = parser.parse_args()

    output = Path(args.output) if args.output else Path(f"exports/{args.model}_din_a4_views.pdf")
    try:
        scale_ratio = parse_scale_option(args.scale)
    except ValueError as error:
        print(f"Error: {error}")
        sys.exit(2)

    try:
        render_din_a4_views_pdf(args.model, output, scale_ratio=scale_ratio)
    except ModuleNotFoundError:
        print(f"Model '{args.model}' not found in models/")
        sys.exit(1)

    print(f"Rendered {output}")


if __name__ == "__main__":
    main()
