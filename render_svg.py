"""Render a build123d model to SVG or PNG from a specified perspective.

Usage:
    uv run render <model_name> [output] [--view VIEW] [--scale SCALE] [--png]

Views:
    iso      - Isometric (default)
    front    - Front view
    back     - Back view
    left     - Left side
    right    - Right side
    top      - Top down
    bottom   - Bottom up

Examples:
    uv run render lens_cap
    uv run render lens_cap exports/lens_cap_top.svg --view top
    uv run render lens_cap --view iso --scale 2.0
    uv run render lens_cap --png                 # exports/lens_cap_iso.png
    uv run render lens_cap shot.png --px 2400    # .png output picks the raster

**SVG for a file, PNG for a person.** Both draw the same hidden-line
projection, so the choice is about who is looking. SVG stays vector -- it is
what `docs/` assets and anything that will be scaled or edited want. PNG exists
because a chat client will *display* a raster inline and hands an SVG back as a
download card instead, which shows the reader nothing. An agent putting a model
in front of the user wants `--png`; see AGENTS.md's Post-Update Verification.
"""

from __future__ import annotations

import fontfix  # noqa: F401 -- preload system libfontconfig before OCP imports

import argparse
import importlib
import sys
from pathlib import Path
from build123d import (
    Color,
    Compound,
    Edge,
    ExportSVG,
    LineType,
    Part,
    PositionMode,
)

# Camera positions for standard views (x, y, z)
VIEWS: dict[str, tuple[float, float, float]] = {
    "iso": (100, -100, 80),
    "front": (0, -100, 0),
    "back": (0, 100, 0),
    "left": (-100, 0, 0),
    "right": (100, 0, 0),
    "top": (0, 0, 100),
    "bottom": (0, 0, -100),
}

# Catppuccin Mocha colors
VISIBLE_COLOR = Color(205 / 255, 214 / 255, 244 / 255)  # text
HIDDEN_COLOR = Color(108 / 255, 112 / 255, 134 / 255)  # overlay0
# Only the raster needs one: an SVG is drawn on whatever the viewer's page is,
# but a PNG has no page behind it, and these two line colours are chosen
# against a dark one.
BACKGROUND_COLOR = Color(30 / 255, 30 / 255, 46 / 255)  # base

# The raster's defaults. PNG_PX is the long edge in pixels; the line weights
# are expressed as a fraction of it so a bigger image is a bigger *picture*
# rather than the same drawing with hairlines.
PNG_PX = 1600
PNG_MARGIN = 0.03
VISIBLE_WEIGHT = 1 / 700
HIDDEN_WEIGHT = 1 / 1400
HIDDEN_DASH = 1 / 450


def get_model_part(model_name: str) -> Part:
    """Import and return the part from a model module."""
    try:
        module = importlib.import_module(f"models.{model_name}")
    except ModuleNotFoundError:
        print(f"Error: Model 'models/{model_name}.py' not found")
        sys.exit(1)

    if hasattr(module, "create"):
        return module.create()

    print(f"Error: No create() function found in models/{model_name}.py")
    sys.exit(1)


def edge_to_polyline(edge: Edge) -> list[tuple[float, float]]:
    """Sample one projected edge into 2D points.

    Public because ``render_a4_pdf`` draws the same projection through cairo
    and needs the identical sampling -- two modules that disagreed about how
    finely a curve is walked would quietly render the same model differently.
    That module already imports ``get_model_part`` from here, so the helper
    lives on this side of the dependency rather than inverting it.
    """
    if edge.geom_type.name == "LINE":
        start = edge.start_point()
        end = edge.end_point()
        return [(start.X, start.Y), (end.X, end.Y)]

    # Sample non-linear edges by parameter, length-adaptive so a long arc does
    # not go polygonal and a short one does not cost 96 points.
    point_count = max(8, min(96, int(edge.length) + 8))
    params = [i / (point_count - 1) for i in range(point_count)]
    points = edge.positions(params, position_mode=PositionMode.PARAMETER)
    return [(point.X, point.Y) for point in points]


def render_png(
    part: Part,
    output_path: Path,
    view: str = "iso",
    px: int = PNG_PX,
    show_hidden: bool = True,
) -> None:
    """Render a part to PNG from the specified view.

    The same projection ``render_svg`` draws, rasterised -- so this is a
    drawing, not a photograph: hidden-line art with no shading and **no part
    colour**, exactly like the SVG.

    ``cairo`` is imported here rather than at module scope on purpose. It comes
    from the ``pdf`` dependency group, and importing it at the top would make
    the plain SVG path -- which needs nothing but build123d -- fail wherever
    that group is not installed.
    """
    import cairo  # noqa: PLC0415 -- lazy, see docstring

    if view not in VIEWS:
        print(f"Error: Unknown view '{view}'. Available: {', '.join(VIEWS.keys())}")
        sys.exit(1)

    visible, hidden = part.project_to_viewport(VIEWS[view])  # type: ignore[arg-type]
    visible_lines = [edge_to_polyline(edge) for edge in visible]
    hidden_lines = [edge_to_polyline(edge) for edge in hidden] if show_hidden else []

    points = [p for line in visible_lines + hidden_lines for p in line]
    if not points:
        print(f"Error: {view} view of this model projected to nothing")
        sys.exit(1)
    min_x = min(p[0] for p in points)
    max_x = max(p[0] for p in points)
    min_y = min(p[1] for p in points)
    max_y = max(p[1] for p in points)

    # Fit the drawing to a square canvas. One scale for both axes, or the model
    # comes out stretched.
    inset = px * PNG_MARGIN
    span = max(max_x - min_x, max_y - min_y, 1e-9)
    scale = (px - 2 * inset) / span
    off_x = (px - (max_x - min_x) * scale) / 2 - min_x * scale
    # Screen y grows downward where the projection's grows up, so this maps
    # max_y to the top inset and the drawing is flipped about it below.
    off_y = (px + (max_y - min_y) * scale) / 2 + min_y * scale

    surface = cairo.ImageSurface(cairo.FORMAT_RGB24, px, px)
    ctx = cairo.Context(surface)
    ctx.set_source_rgb(*BACKGROUND_COLOR.to_tuple()[:3])
    ctx.paint()
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)

    for lines, color, weight, dash in (
        (hidden_lines, HIDDEN_COLOR, HIDDEN_WEIGHT, [px * HIDDEN_DASH] * 2),
        (visible_lines, VISIBLE_COLOR, VISIBLE_WEIGHT, []),
    ):
        ctx.set_source_rgb(*color.to_tuple()[:3])
        ctx.set_line_width(px * weight)
        ctx.set_dash(dash)
        for line in lines:
            if len(line) < 2:
                continue
            ctx.move_to(off_x + line[0][0] * scale, off_y - line[0][1] * scale)
            for x, y in line[1:]:
                ctx.line_to(off_x + x * scale, off_y - y * scale)
            ctx.stroke()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    surface.write_to_png(str(output_path))
    print(f"Rendered {output_path} (view: {view}, {px}x{px} px)")


def render_svg(
    part: Part,
    output_path: Path,
    view: str = "iso",
    scale: float | None = None,
    show_hidden: bool = True,
) -> None:
    """Render a part to SVG from the specified view."""
    if view not in VIEWS:
        print(f"Error: Unknown view '{view}'. Available: {', '.join(VIEWS.keys())}")
        sys.exit(1)

    viewport_origin = VIEWS[view]

    # Project to 2D (ty has issues with build123d's union types)
    visible, hidden = part.project_to_viewport(viewport_origin)  # type: ignore[arg-type]

    # Auto-scale to fit if not specified
    if scale is None:
        all_shapes = visible + hidden if hidden else visible
        if all_shapes:
            max_dim = max(*Compound(children=all_shapes).bounding_box().size)
            scale = 100 / max_dim if max_dim > 0 else 1.0
        else:
            scale = 1.0

    # Create SVG exporter
    exporter = ExportSVG(scale=scale)

    # Add layers with Catppuccin colors
    exporter.add_layer("Visible", line_color=VISIBLE_COLOR, line_weight=0.5)
    if show_hidden:
        exporter.add_layer(
            "Hidden",
            line_color=HIDDEN_COLOR,
            line_weight=0.25,
            line_type=LineType.ISO_DOT,
        )

    # Add shapes
    exporter.add_shape(visible, layer="Visible")
    if show_hidden and hidden:
        exporter.add_shape(hidden, layer="Hidden")

    # Write SVG
    output_path.parent.mkdir(parents=True, exist_ok=True)
    exporter.write(str(output_path))
    print(f"Rendered {output_path} (view: {view}, scale: {scale:.2f})")


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Render a build123d model to SVG",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("model", help="Model name (without .py)")
    parser.add_argument(
        "output",
        nargs="?",
        help="Output path (default: exports/<model>_<view>.svg). A .png "
        "extension selects the raster, so --png is only needed when the path "
        "is left to default.",
    )
    parser.add_argument(
        "--view",
        "-v",
        choices=list(VIEWS.keys()),
        default="iso",
        help="Camera view (default: iso)",
    )
    parser.add_argument(
        "--scale",
        "-s",
        type=float,
        default=None,
        help="Scale factor (default: auto-fit)",
    )
    parser.add_argument(
        "--no-hidden",
        action="store_true",
        help="Don't show hidden lines",
    )
    parser.add_argument(
        "--png",
        action="store_true",
        help="Write a PNG instead of an SVG -- the format a chat client will "
        "display inline rather than attach",
    )
    parser.add_argument(
        "--px",
        type=int,
        default=PNG_PX,
        help=f"PNG size in pixels, square (default: {PNG_PX}); PNG only",
    )

    args = parser.parse_args()

    # The extension wins where it is explicit, so `render m out.png` needs no
    # flag and `--png` is what names the default path's extension.
    want_png = args.png or (args.output is not None and args.output.endswith(".png"))

    # Get the part
    part = get_model_part(args.model)

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        suffix = "png" if want_png else "svg"
        output_path = Path(f"exports/{args.model}_{args.view}.{suffix}")

    # Render
    if want_png:
        render_png(
            part=part,
            output_path=output_path,
            view=args.view,
            px=args.px,
            show_hidden=not args.no_hidden,
        )
    else:
        render_svg(
            part=part,
            output_path=output_path,
            view=args.view,
            scale=args.scale,
            show_hidden=not args.no_hidden,
        )


if __name__ == "__main__":
    main()
