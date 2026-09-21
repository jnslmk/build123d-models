"""Dimensions shared by the stella-octangula connector parts and scene."""

from __future__ import annotations

from math import sqrt

from models.lib import fits

from . import config as c
from . import mount_config as m
from .endcap import CAP_T

MATERIAL = m.MATERIAL
TETRA_ANGLE = 60.0
CRADLE_START = m.gland_setback(TETRA_ANGLE) + CAP_T

# One tetrahedron stays on the mathematical cube faces; the other moves outward
# by one full profile envelope. At every face crossing the two complete lamps
# are therefore parallel instead of occupying the same volume.
CROSSING_CLEAR = fits.for_material(fits.FREE, MATERIAL)  # free fit, ASA baseline
CROSSING_GAP = c.HEIGHT + CROSSING_CLEAR
EDGE_OFFSET = CROSSING_GAP

# Arm-to-core joint. A flat tab sits on two printable ribs at the tetrahedral
# slope; one M5 through-bolt clamps it to the round core while two shallow keys
# carry shear and prevent rotation.
RIB_W = 5.0
TAB_W = 28.0
TAB_H = 20.0
TAB_T = 6.0
TAB_CORNER_R = 2.0
FLANGE_CHAMFER = 0.8
RIB_EDGE_FILLET = 1.5
BEAM_W = TAB_W  # continuous full-width web overlaps the tab-support ribs.
BEAM_T = m.TUBE_UNDER_Z

# The core is thick enough to carry the joint, but every profile cable crosses
# it obliquely. Each cable passage is therefore the full swept projection
# through CORE_T and opens tangentially at the rim: the cable slides in from the
# side, so its fitted Ø21 mm SP16 connector never has to pass through the plate.
CORE_T = 10.0
CORE_EDGE_CHAMFER = 0.8
CORE_MIN_WALL = 8.0
CORE_TAB_EDGE = 2.0
CABLE_SLOT_CLEAR = fits.for_material(fits.FREE, MATERIAL)  # free fit, ASA baseline
CABLE_SLOT_W = m.CABLE_OD + CABLE_SLOT_CLEAR
CABLE_AXIS_BASE_R = m.TUBE_AXIS_Z * sqrt(3 / 2)
CABLE_JOINT_WALL = 2.0  # not a fit: two printed perimeters beside each key pocket
CABLE_MOUTH_FILLET = 1.0

# Two tapered keys flank the bolt and carry shear. Their radial depth, rather
# than the smaller bolt radius, is what sets the joint clear of the cable slot.
KEY_Y = 8.0
KEY_W = 5.0
KEY_D = 8.0
KEY_PROTRUSION = 3.0
KEY_LEAD_IN = 0.6
KEY_FIT = fits.for_material(fits.FREE, MATERIAL)  # free fit, ASA baseline
KEY_DEPTH_RELIEF = 0.2  # not a fit: lets the tab face seat before the key bottoms

BOLT_SIZE = "M5"
BOLT_NOMINAL_D = 5.0
BOLT_CLEAR_D = 5.75  # M5 normal clearance + FDM correction
BOLT_LEAD_IN = 0.6
BOLT_HEAD_D = 8.5  # ISO 4762 M5 socket head
BOLT_HEAD_H = 5.0
BOLT_DRIVER_D = 10.0
BOLT_DRIVER_LEN = 20.0
BOLT_NUT_D = 9.25  # ISO 4032 M5 hex nut, across corners
BOLT_NUT_H = 4.0
BOLT_LENGTH = 25.0
# At the tab's rear face the oblique cable has moved TAB_T / sqrt(2) farther
# out than at the core face; that worst section sets the joint radius.
BOLT_FACE_X = (
    CABLE_AXIS_BASE_R
    + TAB_T / sqrt(2)
    + CABLE_SLOT_W / 2
    + CABLE_JOINT_WALL
    + (KEY_D + KEY_FIT) / 2
) / sqrt(3)
BOLT_END_MARGIN = 3.0  # not a fit: tab/rib material beyond the joint centre
FLANGE_RUN = BOLT_FACE_X + BOLT_END_MARGIN
FLANGE_H = sqrt(2) * FLANGE_RUN

# The Stella uses one short saddle and one keeper instead of the shared 60 mm
# cradle's two straps.
SADDLE_LEN = 36.0
KEEPER_STATION = SADDLE_LEN / 2
BEAM_END = CRADLE_START + m.BAND_LEN

# The round core carries the sling in its centre rather than growing a side lobe.
SLING_SLOT_W = 20.0
SLING_SLOT_H = 10.0

# Drop-on keeper: the arch still clears the diffuser, while its straight legs
# pass outside the saddle. Doubling FREE makes one FREE-class gap per side.
KEEPER_W = 10.0
KEEPER_LEG_T = m.CRADLE_WALL
KEEPER_SPAN_CLEAR = 2 * fits.for_material(
    fits.FREE, MATERIAL
)  # free fit per side, ASA baseline
KEEPER_LEG_INNER_U = m.CRADLE_OUTER_HALF_W + KEEPER_SPAN_CLEAR / 2
KEEPER_LEG_CENTER_U = KEEPER_LEG_INNER_U + KEEPER_LEG_T / 2
KEEPER_LEG_OUTER_U = KEEPER_LEG_INNER_U + KEEPER_LEG_T
KEEPER_FOOT_T = m.TUBE_UNDER_Z
KEEPER_AXIS_Z = m.TUBE_AXIS_Z - KEEPER_FOOT_T
KEEPER_LAND_Z = m.CRADLE_DEPTH - KEEPER_FOOT_T
KEEPER_INNER_CLEAR = 2 * m.DIFFUSER_CLEAR
KEEPER_BOLT_SIZE = "M4"
KEEPER_BOLT_CLEAR_D = 4.75  # M4 normal clearance + FDM correction
KEEPER_BOLT_LEAD_IN = 0.5
KEEPER_BOLT_HEAD_D = 7.0  # ISO 4762 M4 socket head
KEEPER_BOLT_HEAD_CLEAR = 0.75
KEEPER_BOLT_U = KEEPER_LEG_OUTER_U + KEEPER_BOLT_HEAD_D / 2 + KEEPER_BOLT_HEAD_CLEAR
KEEPER_WASHER_OD = 9.0  # DIN 125 M4 washer
KEEPER_EAR_EDGE = 1.0
KEEPER_EAR_OUT = KEEPER_BOLT_U + KEEPER_WASHER_OD / 2 + KEEPER_EAR_EDGE
KEEPER_EAR_CORNER_R = 2.0
KEEPER_EDGE_CHAMFER = m.EDGE_CHAMFER
KEEPER_FUSION_OVERLAP = KEEPER_EDGE_CHAMFER + 0.1
KEEPER_SCREW_LENGTH = 16.0

# 12 x 0.65 kg lamps = 7.8 kg. Four upper vertices share the static weight;
# 250 N per hub includes the requested 5x factor, 2x imbalance, and margin for
# printed connectors/cabling. It is a design target, not an overhead rating.
LAMP_MASS_KG = 0.65
LAMP_COUNT = 12
SUSPENSION_POINTS = 4
DESIGN_FACTOR = 5.0
DESIGN_HUB_LOAD_N = 250.0
ASA_SUSTAINED_STRESS_MPA = 10.0


def cable_axis_radius(offset: float, z: float) -> float:
    """Profile-cable axis radius where it crosses core-local height ``z``."""
    radial_endpoint = offset * sqrt(2 / 3)
    return radial_endpoint + CABLE_AXIS_BASE_R - z / sqrt(2)


def core_hole_radius(offset: float) -> float:
    """Single-bolt radius in the round core plane."""
    radial_endpoint = offset * sqrt(2 / 3)
    radial_flange = BOLT_FACE_X * sqrt(3)
    return radial_endpoint + radial_flange


def core_outline_radius(offset: float) -> float:
    """Round core radius covering the bolt wall and the whole arm tab."""
    hole_wall = core_hole_radius(offset) + BOLT_CLEAR_D / 2 + CORE_MIN_WALL
    tab_cover = core_hole_radius(offset) + TAB_H / 2 + CORE_TAB_EDGE
    return max(hole_wall, tab_cover)


BASE_CORE_R = core_outline_radius(0.0)
OFFSET_CORE_R = core_outline_radius(EDGE_OFFSET)
