"""Shared utilities for displaying and exporting models."""

import io
import sys
from pathlib import Path

from build123d import Part, export_step, export_stl
from ocp_vscode import show

EXPORTS_DIR = Path("exports")


def display(part: Part, name: str) -> None:
    """Send part to the viewer with suppressed ocp_vscode output."""
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    show(part)
    sys.stdout = old_stdout
    print(f"Sent {name} to viewer")


def export(part: Part, name: str) -> None:
    """Export part to STEP and STL formats."""
    EXPORTS_DIR.mkdir(exist_ok=True)
    export_step(part, EXPORTS_DIR / f"{name}.step")
    export_stl(part, EXPORTS_DIR / f"{name}.stl")
    print(f"Exported {name} to {EXPORTS_DIR}/")


def display_and_export(part: Part, name: str) -> None:
    """Display part in viewer and export to STEP/STL."""
    display(part, name)
    export(part, name)
