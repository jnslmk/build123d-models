"""Dimensions shared by the stella-octangula connector parts and scene."""

from __future__ import annotations

from math import hypot, sqrt

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

# Arm: a triangular flange rises from the bed to the core's plane. The slope is
# fixed by a regular tetrahedron: radial normal = (-sqrt(2/3), 0, 1/sqrt(3))
# in tube-local coordinates, hence z = sqrt(2) * x on the mating face.
FLANGE_RUN = 16.0
FLANGE_H = sqrt(2) * FLANGE_RUN
FLANGE_W = 56.0
FLANGE_CHAMFER = 0.8
BEAM_W = 20.0
BEAM_T = m.TUBE_UNDER_Z
BEAM_END = CRADLE_START + m.BAND_LEN

# Two M5 bolts per arm. Clearance follows the repo table; the captive nut opens
# on the arm's mating face and is closed by the core during assembly.
BOLT_SIZE = "M5"
BOLT_CLEAR_D = 5.75
BOLT_FACE_X = 0.65 * FLANGE_RUN
BOLT_Y = 18.0
BOLT_LEAD_IN = 0.6
NUT_AF = 8.15
NUT_CIRCUM_R = NUT_AF / sqrt(3)
NUT_DEPTH = 5.0
NUT_RELIEF_D = 6.0

CORE_T = 10.0
CORE_EDGE_CHAMFER = 0.8
CORE_PAD_R = 11.0
CORE_MIN_WALL = 8.0

# A 10 mm soft sling passes through this rounded functional opening. This is not
# a fit clearance: the extra width is hand-threading room and bend-radius relief.
SLING_SLOT_W = 20.0
SLING_SLOT_H = 10.0
EYE_R = 22.0
EYE_NECK_OVERLAP = 9.0

# 12 x 0.65 kg lamps = 7.8 kg. Four upper vertices share the static weight;
# 250 N per hub includes the requested 5x factor, 2x imbalance, and margin for
# printed connectors/cabling. It is a design target, not an overhead rating.
LAMP_MASS_KG = 0.65
LAMP_COUNT = 12
SUSPENSION_POINTS = 4
DESIGN_FACTOR = 5.0
DESIGN_HUB_LOAD_N = 250.0
ASA_SUSTAINED_STRESS_MPA = 10.0


def core_hole_radius(offset: float) -> float:
    """Bolt-pair midpoint radius in the triangular core plane."""
    radial_endpoint = offset * sqrt(2 / 3)
    radial_flange = BOLT_FACE_X * sqrt(3)
    return radial_endpoint + radial_flange


def core_outline_radius(offset: float) -> float:
    """Minimum circumradius covering bolt heads with a structural wall."""
    bolt_extent = hypot(core_hole_radius(offset), BOLT_Y)
    return bolt_extent + BOLT_CLEAR_D / 2 + CORE_MIN_WALL


BASE_CORE_R = core_outline_radius(0.0)
OFFSET_CORE_R = core_outline_radius(EDGE_OFFSET)
