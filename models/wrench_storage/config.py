"""Wrench evidence and the bin anchor's dimensional inputs, in millimetres.

Photo lengths/head widths are approximate A4-scaled silhouettes, not fit
measurements. Thicknesses are the user's maximum head/handle measurements.
See docs/evidence.md for provenance and docs/bin-cad-contract.md for the gate.
"""

from dataclasses import dataclass

from models.lib import fits


@dataclass(frozen=True)
class Wrench:
    """One measured wrench; label names its two marked jaw sizes."""

    label: str
    length: float
    head_width: float
    head_thickness: float
    handle_thickness: float


# Biggest first: photo length/head width, user-measured head/handle thickness.
WRENCHES = (
    Wrench("16/17", 203.80, 37.60, 6.1, 4.4),
    Wrench("14/15", 188.41, 33.34, 5.8, 4.15),
    Wrench("12/13", 172.47, 29.13, 5.5, 3.65),
    Wrench("10/11", 152.52, 25.29, 4.8, 3.3),
    Wrench("8/9", 136.87, 20.53, 4.3, 3.2),
    Wrench("6/7", 123.01, 15.78, 3.9, 2.8),
)

WALL = 1.0  # PETG: two 0.4 mm perimeters plus 0.2 mm slicer reserve.
TOOL_GAP = fits.FREE  # Free fit, PETG baseline: total head-to-head drop-in gap.
SLOT_CLEARANCE = fits.FREE  # Free fit, PETG baseline: total added to handle thickness.
PHOTO_END_ALLOWANCE = 1.0  # Not a fit: functional photo-envelope reserve at EACH end.
FUTURE_LID_HEADROOM = 3.0  # Not a fit: vertical envelope reserve; no lid geometry yet.
RACK_THICKNESS = 2.0  # Longitudinal support band used by profiles.HANDLE_SPANS.
DEFAULT_WRENCHES_PER_COLUMN = 6

# Existing browser schema: numeric control with integer bounds and step.
# The layout consumer groups consecutive WRENCHES slices of this size.
PARAMS = [
    {
        "name": "wrenches_per_column",
        "label": "Wrenches per column",
        "type": "number",
        "min": 1,
        "max": 6,
        "step": 1,
        "default": DEFAULT_WRENCHES_PER_COLUMN,
    },
]
