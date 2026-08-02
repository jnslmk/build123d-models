"""Named FDM fit classes.

A clearance written as a bare ``0.22`` tells the next reader nothing about what
was intended -- was it measured, guessed, or copied? Naming the class records
the intent, so a later change is an argument about the *fit* rather than about
an anonymous number.

All values are **diametral** (total, not per-side) clearance in millimetres, for
a **desktop FDM machine with a 0.4 mm nozzle**, and calibrated against **PETG**
as the baseline material.

Do not reach for industrial figures here. A Markforged-class machine quotes
0.05--0.20 mm for the same fits; applied to a desktop printer those become an
unassemblable press fit, because the desktop error budget (nozzle wander, over-
extrusion, first-layer squish, thermal shrink) is several times larger than the
clearance itself.

Per-material adjustment is ``for_material`` below. The reasoning behind the
numbers, and how to re-measure them for your own machine, lives in the
``fdm-fits-and-clearances`` skill.
"""

from __future__ import annotations

PRESS = -0.10
"""Interference fit: assembled with force, not meant to come apart."""

SNUG = 0.10
"""Located fit: goes together by hand, no perceptible play."""

SLIDING = 0.22
"""Moves freely along its axis while staying located -- lids, slides, shafts."""

FREE = 0.40
"""Drops in with clearance to spare: tool holders, dowels, loose captives."""

# Offset from the PETG baseline, in mm of diametral clearance. PLA prints
# dimensionally tighter than PETG (less die swell, less stringing on the inner
# perimeter) so it needs less room; ABS/ASA shrink most on cooling and so
# arrive undersized already; TPU squashes and drags, and wants more.
_MATERIAL_OFFSET = {
    "pla": -0.10,
    "petg": 0.0,
    "abs": -0.15,
    "asa": -0.15,
    "tpu": 0.10,
}


def for_material(fit: float, material: str) -> float:
    """Adjust a PETG-baseline fit for another material.

    Takes one of the fit constants above and returns the clearance to actually
    cut. Raises ``ValueError`` for a material with no measured offset rather
    than silently handing back the PETG number, because a wrong clearance is
    invisible until the parts are printed.
    """
    key = material.strip().lower()
    try:
        return fit + _MATERIAL_OFFSET[key]
    except KeyError:
        known = ", ".join(sorted(_MATERIAL_OFFSET))
        raise ValueError(f"unknown material {material!r}; known: {known}") from None
