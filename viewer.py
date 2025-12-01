"""Viewer utilities for programmatic control of OCP CAD Viewer.

This module provides functions for Claude Code to interact with the viewer:
- Take screenshots for visual feedback
- Control camera position (rotate, zoom, pan)
- Set camera to preset views (ISO, TOP, FRONT, etc.)
"""

from pathlib import Path

from ocp_vscode import (
    Camera,
    save_screenshot,
    set_defaults,
    show,
)

# Catppuccin Mocha color palette
CATPPUCCIN_MOCHA = {
    "rosewater": (245, 224, 220),
    "flamingo": (242, 205, 205),
    "pink": (245, 194, 231),
    "mauve": (203, 166, 247),
    "red": (243, 139, 168),
    "maroon": (235, 160, 172),
    "peach": (250, 179, 135),
    "yellow": (249, 226, 175),
    "green": (166, 227, 161),
    "teal": (148, 226, 213),
    "sky": (137, 220, 235),
    "sapphire": (116, 199, 236),
    "blue": (137, 180, 250),
    "lavender": (180, 190, 254),
    "text": (205, 214, 244),
    "subtext1": (186, 194, 222),
    "subtext0": (166, 173, 200),
    "overlay2": (147, 153, 178),
    "overlay1": (127, 132, 156),
    "overlay0": (108, 112, 134),
    "surface2": (88, 91, 112),
    "surface1": (69, 71, 90),
    "surface0": (49, 50, 68),
    "base": (30, 30, 46),
    "mantle": (24, 24, 37),
    "crust": (17, 17, 27),
}


def apply_catppuccin_theme() -> None:
    """Apply Catppuccin Mocha Rosewater theme to the viewer."""
    set_defaults(
        default_color=CATPPUCCIN_MOCHA["rosewater"],
        default_edgecolor=CATPPUCCIN_MOCHA["overlay0"],
    )


def start_viewer() -> None:
    """Start the OCP viewer with Catppuccin Mocha theme.

    Run with: uv run viewer
    """
    import subprocess
    import sys

    # Convert RGB to hex for CLI
    rosewater_hex = "#f5e0dc"
    overlay0_hex = "#6c7086"

    cmd = [
        sys.executable,
        "-m",
        "ocp_vscode",
        "--theme",
        "dark",
        "--default_color",
        rosewater_hex,
        "--default_edgecolor",
        overlay0_hex,
    ]
    subprocess.run(cmd)


def screenshot(filename: str = "exports/screenshot.png") -> str:
    """Take a screenshot of the current viewer state.

    Args:
        filename: Path to save the screenshot (default: exports/screenshot.png)

    Returns:
        The path to the saved screenshot.
    """
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    save_screenshot(str(path))
    return str(path)


def set_camera(
    view: str = "ISO",
    zoom: float = 1.0,
    rotate_speed: int = 1,
    zoom_speed: int = 1,
    pan_speed: int = 1,
) -> None:
    """Set camera position and controls.

    Args:
        view: Camera preset - ISO, TOP, BOTTOM, LEFT, RIGHT, FRONT, BACK
        zoom: Zoom factor (default: 1.0)
        rotate_speed: Mouse rotation speed (default: 1)
        zoom_speed: Mouse zoom speed (default: 1)
        pan_speed: Mouse pan speed (default: 1)
    """
    camera_presets = {
        "ISO": Camera.ISO,
        "TOP": Camera.TOP,
        "BOTTOM": Camera.BOTTOM,
        "LEFT": Camera.LEFT,
        "RIGHT": Camera.RIGHT,
        "FRONT": Camera.FRONT,
        "BACK": Camera.BACK,
        "RESET": Camera.RESET,
        "KEEP": Camera.KEEP,
    }

    reset_camera = camera_presets.get(view.upper(), Camera.ISO)

    set_defaults(
        reset_camera=reset_camera,
        zoom=zoom,
        rotate_speed=rotate_speed,
        zoom_speed=zoom_speed,
        pan_speed=pan_speed,
    )


def show_and_screenshot(
    obj,
    filename: str = "exports/screenshot.png",
    view: str = "ISO",
    zoom: float = 1.0,
) -> str:
    """Show an object and take a screenshot.

    Args:
        obj: The build123d object to display
        filename: Path to save the screenshot
        view: Camera preset - ISO, TOP, BOTTOM, LEFT, RIGHT, FRONT, BACK
        zoom: Zoom factor

    Returns:
        The path to the saved screenshot.
    """
    set_camera(view=view, zoom=zoom)
    show(obj)
    return screenshot(filename)


# Convenience functions for common views
def view_iso(obj, filename: str = "exports/screenshot.png") -> str:
    """Show object from isometric view and screenshot."""
    return show_and_screenshot(obj, filename, view="ISO")


def view_top(obj, filename: str = "exports/screenshot.png") -> str:
    """Show object from top view and screenshot."""
    return show_and_screenshot(obj, filename, view="TOP")


def view_front(obj, filename: str = "exports/screenshot.png") -> str:
    """Show object from front view and screenshot."""
    return show_and_screenshot(obj, filename, view="FRONT")


def view_right(obj, filename: str = "exports/screenshot.png") -> str:
    """Show object from right view and screenshot."""
    return show_and_screenshot(obj, filename, view="RIGHT")
