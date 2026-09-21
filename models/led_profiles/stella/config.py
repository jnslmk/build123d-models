"""Functional-core sizing inputs, not a suspended-use rating.

Measured hardware and assumption provenance: ../docs/cad-contract.md.
The rejected blank's dimensions and uniform-section calculation are not inputs.
"""

from math import cos, radians, sqrt

from models.lib import fits

from .. import config as profile
from .. import mount_config as hardware

MATERIAL = "abs"
BRANCH_ANGLES = (90.0, 210.0, 330.0)
FREE_CLEAR = fits.for_material(fits.FREE, MATERIAL)  # FREE, ABS; total gap.

# One organic outline carries the full body; only the outer top and bed edges taper.
TIP_CENTRE_R = 50.0
OUTLINE_TIP_RADIUS = 26.0
OUTLINE_ROOT_HANDLE = 20.0
CORE_H_TARGET = 12.0
# The 12 mm stack can physically contain a 6 mm pilot, 3 mm floor and 3 mm
# seat, but fails the actual post-cut short-event section screen. At 19 mm the
# outer seat section still fails; 20 mm is the first whole-mm height with margin.
CORE_H = 20.0
EDGE_CHAMFER = 0.6

# Drop-in keyed face: the later arm must have matching flat bearing surfaces.
SEAT_R = TIP_CENTRE_R
ARM_KEY_LENGTH = 28.0
ARM_KEY_WIDTH = 28.0
ARM_KEY_RADIUS = 2.5
SEAT_LENGTH = ARM_KEY_LENGTH + FREE_CLEAR
SEAT_WIDTH = ARM_KEY_WIDTH + FREE_CLEAR
SEAT_RADIUS = ARM_KEY_RADIUS + FREE_CLEAR / 2
SEAT_DEPTH = 3.0
SEAT_Z = CORE_H - SEAT_DEPTH
SEAT_LEAD = 0.8
INSERT_RADII = (SEAT_R - 9.0, SEAT_R + 9.0)
INSERT_OD = 4.0  # User inventory, external diameter; unidentified knurl/taper.
INSERT_LENGTH = 5.0
INSERT_PITCH = 0.5
INSERT_MELT_ALLOWANCE = 0.5  # Estimated diametral melt stock, NOT a fit recipe.
INSERT_FDM_COMPENSATION = 0.2  # Skill's vertical-hole estimate; not calibrated.
INSERT_PILOT_D = INSERT_OD - INSERT_MELT_ALLOWANCE + INSERT_FDM_COMPENSATION
INSERT_DEPTH = INSERT_LENGTH + 2 * INSERT_PITCH
INSERT_WALL = 3.0  # One M3 diameter around the installed insert envelope.
INSERT_FLOOR = 3.0  # Minimum material below the relief well, not actual web depth.
SCREW_D = 3.0
SCREW_LENGTH = 12.0
ARM_STACK = 7.5  # Reserved future arm thickness at each screw, not an arm model.
WASHER_D = 7.0  # ISO 7089 M3 nominal OD.
WASHER_T = 0.5
HEAD_D = 5.5  # ISO 4762 M3 socket head envelope.
HEAD_H = 3.0
DRIVER_D = 8.0  # Assumed bit/shaft envelope, not the full handle.
DRIVER_LENGTH = 50.0
IRON_TIP_D = 8.0  # Assumed installation tip/neck envelope before arms are fitted.
IRON_TIP_LENGTH = 12.0
IRON_BODY_D = 18.0
IRON_BODY_LENGTH = 35.0
ARM_CLEAR_D = SCREW_D + FREE_CLEAR  # FREE, ABS; smaller than this insert's pilot.

# Two-hole route for one short closed nominal-6 mm cord loop. The extra diameter
# is a functional handling/movement allowance, not a fit class or Petzl minimum.
CORD_D = 6.0
CORD_HOLE_ALLOWANCE = 2.0
SUSPENSION_HOLE_D = CORD_D + CORD_HOLE_ALLOWANCE
SUSPENSION_HOLE_SPACING = 22.0
SUSPENSION_HOLE_CENTRES = (
    -SUSPENSION_HOLE_SPACING / 2,
    SUSPENSION_HOLE_SPACING / 2,
)
SUSPENSION_CONTACT_R = 2.0  # Engineering choice; no manufacturer minimum found.
SUSPENSION_MIN_LIGAMENT = 8.0
SUSPENSION_BRIDGE_MOUTH = (
    SUSPENSION_HOLE_SPACING - SUSPENSION_HOLE_D - 2 * SUSPENSION_CONTACT_R
)
SUSPENSION_BRIDGE_THROAT = SUSPENSION_HOLE_SPACING - SUSPENSION_HOLE_D
SUSPENSION_EFFECTIVE_H = CORE_H - 2 * SUSPENSION_CONTACT_R

# Electrical cables stay outside. These are explicit core-only service
# corridors, not a claim for the deferred arm or complete assembly route.
CABLE_OD = hardware.CABLE_OD
CABLE_BEND_R = hardware.CABLE_BEND_R
CABLE_SLEEVE_T = 0.5  # Assumed split abrasion sleeve thickness, not fit clearance.
CABLE_ENVELOPE_D = CABLE_OD + 2 * CABLE_SLEEVE_T
VALLEY_SOLID_INNER_R = (
    SUSPENSION_HOLE_SPACING / 2
    + SUSPENSION_HOLE_D / 2
    + SUSPENSION_CONTACT_R
    + SUSPENSION_MIN_LIGAMENT
    + 1.0
)
VALLEY_SOLID_OUTER_R = VALLEY_SOLID_INNER_R + CABLE_ENVELOPE_D
CABLE_SERVICE_R = 45.0  # First 5 mm-grid radial corridor clearing the finished core.
CONNECTOR_D = hardware.SP16_D
CONNECTOR_LENGTH = hardware.SP16_LEN
CONNECTOR_COUPLED_LENGTH = 90.0  # Two 45 mm bodies; conservative local envelope.
CONNECTOR_SERVICE_R = 50.0  # First 5 mm-grid corridor clearing coupled Ø21 bodies.
COUPLING_HAND_D = 40.0  # Functional finger/grip space, not a mating fit.
COUPLING_STROKE = 25.0  # Assumed unplugging motion; supplier variant unmeasured.
COUPLING_SERVICE_R = 60.0  # First 5 mm-grid corridor clearing the hand envelope.
SERVICE_OUTER_R = TIP_CENTRE_R + OUTLINE_TIP_RADIUS + CABLE_BEND_R

# Re-evaluated forces: ideal axial tetrahedral members, not solved rigid-frame loads.
TOTAL_MASS_KG = 12.0  # Unweighed complete-frame allowance, two 6 kg tetrahedra.
LOADED_LINES = 2  # Unequal sharing: one loaded line per structurally separate frame.
BRIDLE_ANGLE_DEG = 45.0
GRAVITY = 9.81
LINE_STATIC_N = (
    TOTAL_MASS_KG * GRAVITY / (LOADED_LINES * cos(radians(BRIDLE_ANGLE_DEG)))
)
MEMBER_STATIC_N = sqrt(3 / 2) * LINE_STATIC_N
SUSTAINED_FACTOR = 1.5  # Assumed static uncertainty multiplier.
EVENT_FACTOR = 5.0  # Short-event screen, not an impact or safety-arrest model.
HANDLING_FORCE_N = 10.0  # Assumed transverse load at a supported lamp's midpoint.
HANDLING_FACTOR = 2.0
HANDLING_MOMENT_NMM = HANDLING_FACTOR * HANDLING_FORCE_N * profile.LENGTH / 4
# Both lamp ends supported: use the full simply-supported span bending envelope
# at one joint. An unsupported cantilever (F L / 2) is outside the service basis.
LOAD_Z = SEAT_Z + ARM_STACK / 2
ROOT_STATIONS = (16.0, 24.0, 32.0, 36.0, *INSERT_RADII, SEAT_R, 63.0)
PART_TEMPERATURE_C = 40.0
DURATION_DAYS = 28
ABS_REFERENCE_Z_MPA = 29.7  # Published PolyLite specimen; not the user's print.
PROCESS_FACTOR = 0.75
TEMPERATURE_FACTOR = 0.60
DURATION_FACTOR = 0.40
ABS_EVENT_MPA = ABS_REFERENCE_Z_MPA * PROCESS_FACTOR * TEMPERATURE_FACTOR
ABS_SUSTAINED_MPA = ABS_EVENT_MPA * DURATION_FACTOR
LOCAL_STRESS_FACTOR = 1.5  # Assumed notch multiplier, not a resolved stress field.
PRELOAD_N = 80.0  # Illustrative clamp preload per insert; no torque prescription.
