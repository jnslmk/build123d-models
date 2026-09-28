"""Parametric empty-bin controls and the shared dimensional budget."""

from build123d import Color

from models.drill_storage.box import BASE_H, CORNER_R, GRID, HEIGHT_UNIT, PAD
from models.drill_storage.tools import COVER_GLASS
from models.lib import fits

WALL = 1.0  # PETG: two 0.4 mm perimeters, 0.2 mm reserve for slicer variance
RIM_CHAMFER = 0.2  # outer top edge; preserve a flat lid-bearing rim at 1 mm wall
MOUTH_CHAMFER = 0.2  # inner lip lead-in, leaving 0.6 mm flat even at 1 mm wall
FLOOR_SEAM_CHAMFER = (
    0.2  # soften exposed cell-boundary ridge without thinning the side walls
)
MAGNET_FIT = fits.SLIDING  # sliding fit, PETG baseline, for nominal magnet diameter
LID_SOCKET_DEPTH = 2.5  # lower foot bevel + straight band; upper bevel remains proud
LID_ROOF = 1.0  # five solid 0.2 mm layers above the receiving socket
LID_SKIRT_MIN = 3.0  # lift-off locating engagement inside the body wall
LID_MIN_HEIGHT = LID_SOCKET_DEPTH + LID_ROOF + LID_SKIRT_MIN  # 6.5 mm overall
FEATURE_HEADROOM = LID_SKIRT_MIN + 0.6  # clearance below the seated locating skirt
BASE_COLOR = Color(0.1, 0.1, 0.1)  # same black as drill_storage.hex.config.BASE_COLOR
LID_COLOR = COVER_GLASS  # translucent PETG, shared with the other drill covers


def _number(
    name: str, label: str, minimum: float, maximum: float, step: float, default: float
) -> dict:
    return {
        "name": name,
        "label": label,
        "type": "number",
        "min": minimum,
        "max": maximum,
        "step": step,
        "default": default,
    }


def _boolean(name: str, label: str, default: bool) -> dict:
    return {"name": name, "label": label, "type": "boolean", "default": default}


PARAMS = [
    _number("grid_x", "Grid width (cells)", 0.5, 6, 0.5, 1),
    _number("grid_y", "Grid depth (cells)", 0.5, 6, 0.5, 2),
    _number("height_u", "Bin height (7 mm units)", 2, 20, 1, 3),
    _boolean("half_grid_base", "Half-grid feet throughout", False),
    _boolean("half_grid_right", "Partial foot on +X", True),
    _boolean("half_grid_top", "Partial foot on +Y", True),
    _number("wall_thickness", "Wall thickness (mm)", 1, 4, 0.1, WALL),
    _boolean("ultra_light_base", "Ultra light base", True),
    _number("bottom_thickness", "Bottom thickness (mm; 0 = wall)", 0, 4, 0.1, 0),
    _boolean("ultra_light_labels", "Ultra light labels", True),
    _boolean("magnets", "Magnet pockets", False),
    _number("magnet_diameter", "Magnet diameter (mm)", 3, 8, 0.05, 6.15),
    _number("magnet_depth", "Magnet depth (mm)", 1, 3, 0.1, 2.2),
    _boolean("dividers", "Dividers", True),
    _number("dividers_x", "X divider count", 0, 8, 1, 0),
    _number("dividers_y", "Y divider count", 0, 8, 1, 0),
    _boolean("labels", "Label tabs", False),
    _boolean("label_for_each_section", "Label every section", True),
    {
        "name": "label_position",
        "label": "Label alignment",
        "type": "choice",
        "options": ["Full", "Left", "Center", "Right"],
        "default": "Full",
    },
    _number("label_width", "Label width (mm)", 8, 80, 1, 30),
    _number("label_depth", "Label depth (mm)", 4, 20, 1, 13),
    _boolean("scoops", "Scooped floor", False),
    _number("scoop_radius", "Scoop radius (mm)", 3, 30, 1, 30),
]

__all__ = [
    "BASE_H",
    "CORNER_R",
    "GRID",
    "HEIGHT_UNIT",
    "PAD",
    "WALL",
    "PARAMS",
    "MAGNET_FIT",
    "RIM_CHAMFER",
    "MOUTH_CHAMFER",
]
