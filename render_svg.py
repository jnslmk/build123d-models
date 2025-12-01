"""Render a build123d model to SVG from a specified perspective.

Usage:
    uv run render <model_name> [output.svg] [--view VIEW] [--scale SCALE]

Views:
    iso      - Isometric (default)
    front    - Front view
    back     - Back view
    left     - Left side
    right    - Right side
    top      - Top down
    bottom   - Bottom up

Examples:
    uv run render cube
    uv run render cube exports/cube_top.svg --view top
    uv run render cube --view iso --scale 2.0
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path
from build123d import Color, Compound, ExportSVG, LineType, Part

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
        help="Output SVG path (default: exports/<model>_<view>.svg)",
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

    args = parser.parse_args()

    # Get the part
    part = get_model_part(args.model)

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = Path(f"exports/{args.model}_{args.view}.svg")

    # Render
    render_svg(
        part=part,
        output_path=output_path,
        view=args.view,
        scale=args.scale,
        show_hidden=not args.no_hidden,
    )


if __name__ == "__main__":
    main()
