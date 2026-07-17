"""Shared utilities for displaying and exporting models."""

import fontfix  # noqa: F401 -- preload system libfontconfig before OCP imports

import io
import re
import sys
import warnings
from pathlib import Path

from build123d import Compound, Part, export_step, export_stl
from ocp_vscode import show

# ocp_vscode warns when reset_camera=KEEP but no camera state is stored yet;
# harmless for CLI/headless use, so silence just that message.
warnings.filterwarnings("ignore", message=r".*reset_camera is set to KEEP.*")

EXPORTS_DIR = Path("exports")


def _slugify(value: str) -> str:
    """Convert labels to filesystem-friendly names."""
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug or "part"


def _export_child_stls(part: Part | Compound, name: str) -> None:
    """Export individual child STL files when a compound exposes named children."""
    if not isinstance(part, Compound) or not getattr(part, "children", None):
        return

    exported = 0
    for index, child in enumerate(part.children, start=1):
        label = getattr(child, "label", None) or f"part_{index}"
        export_stl(child, EXPORTS_DIR / f"{name}_{_slugify(label)}.stl")
        exported += 1

    if exported:
        print(f"Exported {exported} individual STL files for {name}")


def display(part: Part | Compound, name: str) -> None:
    """Send part to the viewer with suppressed ocp_vscode output."""
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    show(part)
    sys.stdout = old_stdout
    print(f"Sent {name} to viewer")


def export(part: Part | Compound, name: str, *, step: bool = False) -> None:
    """Export model to STL (and child STLs); pass ``step=True`` to also emit STEP."""
    EXPORTS_DIR.mkdir(exist_ok=True)
    if step:
        export_step(part, EXPORTS_DIR / f"{name}.step")
    export_stl(part, EXPORTS_DIR / f"{name}.stl")
    _export_child_stls(part, name)
    print(f"Exported {name} to {EXPORTS_DIR}/")


def display_and_export(part: Part | Compound, name: str) -> None:
    """Display model in viewer and export to STEP/STL."""
    display(part, name)
    export(part, name)
