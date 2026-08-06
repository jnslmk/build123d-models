"""Shared utilities for displaying and exporting models."""

import fontfix  # noqa: F401 -- preload system libfontconfig before OCP imports

import io
import re
import sys
import warnings
from pathlib import Path

from build123d import Color, Compound, Part, export_gltf, export_step, export_stl
from ocp_vscode import show

# ocp_vscode warns when reset_camera=KEEP but no camera state is stored yet;
# harmless for CLI/headless use, so silence just that message.
warnings.filterwarnings("ignore", message=r".*reset_camera is set to KEEP.*")

EXPORTS_DIR = Path("exports")

# Meshing tolerances for every triangulated export (STL and glTF; STEP is B-rep
# and exact, so it is unaffected).
#
# ``build123d`` defaults to 0.001 mm linear / 0.1 rad angular. Both are far below
# anything an FDM printer can express -- a 0.4 mm nozzle laying 0.2 mm layers
# resolves roughly 0.1 mm -- and the angular one is what makes the files huge,
# because it keeps subdividing curves long after the linear limit is satisfied.
#
# The linear tolerance is a *hard cap* on the distance between the mesh and the
# real surface, so 0.01 mm bounds the error at a twentieth of a layer height no
# matter what the angular term does. Measured on the roster, moving to
# 0.01 mm / 0.2 rad cuts the STL bytes by roughly 4x and the meshing time with
# them, for a deviation nothing downstream can print or see.
STL_TOLERANCE = 0.01
STL_ANGULAR_TOLERANCE = 0.2

# House blue (#59a6ff) — the viewer's default so uncolored models still render in
# brand colour rather than glTF's material-less white. Kept in sync with the CSS
# accent in website/index.html.
DEFAULT_COLOR = Color(0.35, 0.65, 1.0)


def apply_default_colors(part: Part | Compound, default: Color = DEFAULT_COLOR) -> None:
    """Give every leaf that has no explicit ``.color`` the house default, in place.

    glTF drops the material entirely for an uncolored solid, which would render as
    a flat white default. Seeding a colour here means the GLB always carries a real
    material so the web viewer can render straight from it with no heuristics. STL /
    STEP ignore colour, so this only affects the glTF export.
    """
    leaves = list(part.leaves) if isinstance(part, Compound) else [part]
    for leaf in leaves:
        if leaf.color is None:
            leaf.color = default


def _slugify(value: str) -> str:
    """Convert labels to filesystem-friendly names."""
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug or "part"


def _export_child_stls(part: Part | Compound, name: str) -> list[Path]:
    """Export individual child STL files when a compound exposes named children."""
    if not isinstance(part, Compound) or not getattr(part, "children", None):
        return []

    written = []
    for index, child in enumerate(part.children, start=1):
        label = getattr(child, "label", None) or f"part_{index}"
        path = EXPORTS_DIR / f"{name}_{_slugify(label)}.stl"
        export_stl(
            child,
            path,
            tolerance=STL_TOLERANCE,
            angular_tolerance=STL_ANGULAR_TOLERANCE,
        )
        written.append(path)

    if written:
        print(f"Exported {len(written)} individual STL files for {name}")
    return written


def display(part: Part | Compound, name: str) -> None:
    """Send part to the viewer with suppressed ocp_vscode output."""
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    show(part)
    sys.stdout = old_stdout
    print(f"Sent {name} to viewer")


def export(
    part: Part | Compound,
    name: str,
    *,
    step: bool = False,
    children: bool = True,
) -> list[Path]:
    """Export model to STL (and child STLs); pass ``step=True`` to also emit STEP.

    ``children=False`` skips the per-child STLs. They are worth having locally --
    a compound's parts as separate files to drop in a slicer one at a time -- but
    nothing publishes them: ``website.build_web_bundle`` copies only the roster
    names, so in CI they are minutes of meshing and hundreds of megabytes written
    for files no page ever links to.

    Returns the paths actually written, so a caller can record what a model
    produced rather than assume it. That matters for the glTF, which is best
    effort and may legitimately be absent.
    """
    EXPORTS_DIR.mkdir(exist_ok=True)
    written = []
    if step:
        path = EXPORTS_DIR / f"{name}.step"
        export_step(part, path)
        written.append(path)
    stl = EXPORTS_DIR / f"{name}.stl"
    export_stl(
        part, stl, tolerance=STL_TOLERANCE, angular_tolerance=STL_ANGULAR_TOLERANCE
    )
    written.append(stl)
    if children:
        written += _export_child_stls(part, name)
    # Colour-carrying render asset for the web viewer (STL is colourless). Best
    # effort: a glTF failure must never block the STL/STEP build.
    try:
        apply_default_colors(part)
        glb = EXPORTS_DIR / f"{name}.glb"
        export_gltf(
            part,
            glb,
            binary=True,
            linear_deflection=STL_TOLERANCE,
            angular_deflection=STL_ANGULAR_TOLERANCE,
        )
        written.append(glb)
    except Exception as exc:  # noqa: BLE001 -- render asset is optional
        print(f"glTF export skipped for {name}: {exc}")
    print(f"Exported {name} to {EXPORTS_DIR}/")
    return written


def display_and_export(part: Part | Compound, name: str) -> None:
    """Display model in viewer and export to STEP/STL."""
    display(part, name)
    export(part, name)
