"""The two drill holders side by side: the PETG original and the ASA+TPU variant.

A scene for the website, and the one view where the design argument is visible
rather than written down. Left is ``drill_storage.wood`` -- one PETG part, gripping
each drill on three compliant ribs low in the bore. Right is
``drill_storage.flex`` -- a rigid ASA shell that guides, and a short TPU collar
(the blue band at the top) that grips, with the ribs gone because the material is
the spring.

Both hold the same eleven brad-point drills and the same countersink, both are
1x1 Gridfinity, and both take the *same cover* -- which is the point of the
variant keeping ``BORE_FLOOR_Z`` and ``FOOT_TOP`` where the original has them.
Stand them next to each other and the covers are interchangeable.

Not a print job: the parts are downloadable from ``drill_storage.wood``,
``drill_storage.flex.shell`` and ``drill_storage.flex.insert``.
"""

from __future__ import annotations

from build123d import Compound, Pos

from ..box import GRID
from ..flex import create_flex_assembly
from .wood import create_wood_assembly

IS_ASSEMBLY = True

# One clear Gridfinity cell between them: they read as two units on a baseplate
# rather than one wide object, and the eye lands on the difference at the top.
GAP = GRID


def create_comparison() -> Compound:
    """PETG ribbed holder on the left, ASA shell + TPU collar on the right."""
    original = create_wood_assembly()
    original.label = "original_petg_ribbed"

    flex = create_flex_assembly()
    flex.label = "flex_asa_tpu"

    return Compound(
        label="drill_storage.assemblies.comparison",
        children=[Pos(-GAP / 2, 0, 0) * original, Pos(GAP / 2, 0, 0) * flex],
    )


def create() -> Compound:
    """Model entry point -- see ``create_comparison``."""
    return create_comparison()


__all__ = ["GAP", "IS_ASSEMBLY", "create", "create_comparison"]
