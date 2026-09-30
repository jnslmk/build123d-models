"""Alternate PETG Dremel cover with two full-depth stacking receivers."""

from build123d import BuildPart, BuildSketch, Plane, Pos, RectangleRounded, add, extrude

from models.drill_storage.box import (
    GRID,
    STACK_LIP_R,
    STACK_LIP_W,
    STACK_SOCKET_DEPTH,
    add_stacking_support,
    cut_stacking_socket,
)
from models.drill_storage.cover import SUPPORT_PARAM
from models.drill_storage.tools import COVER_GLASS
from models.lib.edges import as_part, reseat_on_bed
from . import cover

PARAMS = [SUPPORT_PARAM]
IS_ASSEMBLY = False
CELL_Y = (-GRID / 2, GRID / 2)
HEIGHT = cover.HEIGHT + STACK_SOCKET_DEPTH


def create(support: bool = True):
    """Return socket-down, mouth-up; remove both lattices before stacking."""
    # Build the receiver upright, then invert it onto the print bed. The
    # unchanged smooth cover starts above it, preserving its 2 mm cap and snap.
    with BuildPart() as receiver:
        with BuildSketch(Plane.XY):
            RectangleRounded(STACK_LIP_W, STACK_LIP_W + GRID, STACK_LIP_R)
        extrude(amount=STACK_SOCKET_DEPTH)
    lip = receiver.part
    for y in CELL_Y:
        # The shared socket helper owns explicit XY planes; translate the part,
        # rather than Locations (which does not move those sketch planes).
        with BuildPart() as cut:
            add(Pos(0, -y, 0) * lip)
            cut_stacking_socket(STACK_SOCKET_DEPTH)
        lip = as_part(Pos(0, y, 0) * cut.part)
    with BuildPart() as body:
        add(reseat_on_bed(lip, flip=True))
        add(Pos(0, 0, STACK_SOCKET_DEPTH) * cover.create())
    result = body.part
    if support:
        for y in CELL_Y:
            centered = as_part(Pos(0, -y, 0) * result)
            result = as_part(Pos(0, y, 0) * add_stacking_support(centered))
    result.color = COVER_GLASS
    return result


def check():
    """Prove both receivers, tool clearance and removable support behavior."""
    from build123d import Rotation

    from models.drill_storage import config as family
    from models.lib.checks import Report, is_solid_at
    from . import base, config as c, insert

    report = Report()
    clean = create(support=False)
    supported = create()
    bb = clean.bounding_box()
    report.check(clean.is_valid and len(clean.solids()) == 1, "clean cover is one valid solid")
    report.check(supported.is_valid and len(supported.solids()) == 1, "supported cover is one valid solid")
    report.check(abs(bb.min.Z) < 1e-6, "socket-down print pose rests on z=0")
    report.check(abs(bb.size.X - 42) < 1e-6 and abs(bb.size.Y - 84) < 1e-6, "two-cell lip is 42 × 84 mm")
    report.check(abs(c.SEAT_Z + bb.size.Z - STACK_SOCKET_DEPTH - 70) < 1e-6, "10U seated stack pitch")
    upright = as_part(Pos(0, 0, c.SEAT_Z + HEIGHT) * Rotation(180, 0, 0) * clean)
    lower = base.create()
    report.check((upright & lower).volume < 0.001, "unchanged collar and snap clear base")
    cartridge = Pos(0, 0, c.CAVITY_FLOOR_Z + family.CART_H) * Rotation(180, 0, 0) * insert.create()
    report.check((upright & cartridge).volume < 0.001, "seated TPU insert clears cover")
    upper = Pos(0, 0, 70) * lower
    report.check((upright & upper).volume < 0.001, "both feet fully seat without interference")
    too_low = Pos(0, 0, 69.7) * lower
    report.check((upright & too_low).volume > 1, "socket floors stop over-insertion")
    for y in CELL_Y:
        report.check(not is_solid_at(clean, 0, y, 2), f"clean socket at y={y} is open")
        report.check(is_solid_at(supported, 0, y, 2), f"support lattice at y={y} is present")
        report.check(not is_solid_at(supported, 0, y, STACK_SOCKET_DEPTH - 0.1), f"lattice at y={y} has one-layer release gap")
        report.check(is_solid_at(clean, 0, y, STACK_SOCKET_DEPTH + cover.CAP_H - 0.1), f"socket at y={y} retains 2 mm roof")
        report.check(not is_solid_at(upright, 0, y, c.GUIDE_FLOOR_Z + 50 + 6), f"50 mm tool at y={y} retains 6 mm headroom")
    return report
