"""Assembled view of the wood drill storage: base + brad-point drills + cover.

A verification assembly for ``drill_storage.wood``. It drops a simple 3D model of
every drill in the set into its own bore on the base, seats the labelled cover
over the collar in its *use* pose, and makes the cover translucent so you can see
the drills standing inside it. Its whole reason to exist is to eyeball one thing:
the longest brad-point drill (the 10 mm, ``MAX_WOOD_DRILL_LEN`` = 121 mm) just
clears the cap, and the cover is the smallest whole Gridfinity Z unit that lets
it (19U / 133 mm assembled, ~3 mm above the tip).

This is a display/verification model, not something to print -- the drills are
generic representations (a fluted-diameter body plus a brad point), sized so the
set looks right and the longest is exactly 121 mm.
"""

from build123d import (
    Align,
    BuildPart,
    BuildSketch,
    Color,
    Compound,
    Cone,
    Cylinder,
    Locations,
    Part,
    Plane,
    Pos,
    RegularPolygon,
    Rotation,
    extrude,
)

from ..box import (
    BASE_COLOR,
    BASE_TOTAL_H,
    BORE_FLOOR_Z,
    FOOT_TOP,
    create_base,
    create_cover,
)
from ..wood import (
    COVER_H_WOOD,
    CSK_HEAD_D,
    DRILL_BORES,
    HEX_BORES,
    LABEL,
    MAX_WOOD_DRILL_LEN,
    POS,
    ROWS,
)

# "A display/verification model, not something to print" (above), which is
# exactly what tessellate_models.model_is_assembly means: no STL/STEP download
# on the website. The base and cover it shows are downloadable from
# ``drill_storage.wood``.
IS_ASSEMBLY = True

# Overall length (mm) of each drill in the set. Graduated like a real brad-point
# set -- small bits are short, the 10 mm is the longest at MAX_WOOD_DRILL_LEN so
# the fit check is honest. Edit MAX_WOOD_DRILL_LEN in drill_storage.wood to drive
# the longest; the rest are just plausible display lengths.
DRILL_LENGTHS = {
    2.0: 60.0,
    2.5: 62.0,
    3.0: 66.0,
    3.5: 70.0,
    4.0: 75.0,
    5.0: 86.0,
    6.0: 93.0,
    7.0: 100.0,
    8.0: 110.0,
    9.0: 117.0,
    10.0: MAX_WOOD_DRILL_LEN,  # longest drill -> sets the cover height
}

STEEL = Color(0.70, 0.72, 0.75)  # bright tool steel
COVER_GLASS = Color(0.86, 0.87, 0.84, 0.32)  # translucent so drills show through


def create_drill(diameter: float, length: float) -> Part:
    """A generic brad-point drill: a full-diameter fluted body topped by a
    conical point with a slim brad centre spur. Built from ``z=0`` up (shank end
    on the bed), tip up -- the pose it stands in inside a bore."""
    r = diameter / 2
    point_h = min(0.9 * diameter, 0.22 * length)  # brad point taper
    spur_h = 0.35 * diameter  # centre spur poking beyond the point
    body_h = length - point_h - spur_h
    with BuildPart() as bit:
        Cylinder(r, body_h, align=(Align.CENTER, Align.CENTER, Align.MIN))
        with Locations((0, 0, body_h)):
            # Main point: full diameter tapering nearly to the centre.
            Cone(r, 0.18 * r, point_h, align=(Align.CENTER, Align.CENTER, Align.MIN))
            with Locations((0, 0, point_h)):
                # Sharp brad centre spur.
                Cone(
                    0.18 * r, 0.0, spur_h, align=(Align.CENTER, Align.CENTER, Align.MIN)
                )
    return bit.part


def create_countersink(across_flats: float, head_d: float) -> Part:
    """A 10 mm countersink on a hex shank: a hex-prism shank, a fluted conical
    head, and a small pilot tip. Built shank-end (``z=0``) up."""
    shank_h = 40.0
    head_h = 0.5 * head_d
    pilot_h = 3.0
    with BuildPart() as csk:
        with BuildSketch(Plane.XY):
            RegularPolygon(across_flats / 3**0.5, 6)
        extrude(amount=shank_h)
        with Locations((0, 0, shank_h)):
            Cone(head_d / 2, 0.0, head_h, align=(Align.CENTER, Align.CENTER, Align.MIN))
        # A short cylindrical pilot poking out the tip of the countersink cone.
        with Locations((0, 0, shank_h + head_h)):
            Cylinder(1.0, pilot_h, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return csk.part


def create_wood_assembly() -> Compound:
    """The wood drill storage, fully assembled: base, every drill in its bore,
    and the translucent cover seated over the collar."""
    base = create_base(
        DRILL_BORES,
        hex_bores=HEX_BORES,
        clearance=0.0,
        ribbed=True,
        rows=ROWS,
        hole_pos=POS,
    )
    base.label = "base"
    base.color = BASE_COLOR

    # Drop each drill into its bore, shank end resting on the bore floor.
    drills = []
    for d, x, y in DRILL_BORES:
        length = DRILL_LENGTHS.get(d, 80.0)
        bit = create_drill(d, length)
        bit.label = f"drill_{d:g}mm"
        bit.color = STEEL
        drills.append(Pos(x, y, BORE_FLOOR_Z) * bit)

    # The countersink: its hex shank drops into the socket, head rests on top.
    for af, x, y in HEX_BORES:
        csk = create_countersink(af, CSK_HEAD_D)
        csk.label = "countersink_10mm"
        csk.color = STEEL
        # Seat the head on the base top face rather than the deep bore floor.
        drills.append(Pos(x, y, BASE_TOTAL_H - 40.0) * csk)

    # Cover in use pose: create_cover returns it in print pose (pillow on the
    # bed, mouth up). Flip it back so the mouth faces down and seat it on the
    # base shoulder at FOOT_TOP, then make it translucent to reveal the drills.
    cover = Rotation(180, 0, 0) * create_cover(LABEL, cover_h=COVER_H_WOOD)
    cover = Pos(0, 0, FOOT_TOP - cover.bounding_box().min.Z) * cover
    cover.label = "cover_wood"
    cover.color = COVER_GLASS

    return Compound(
        label="drill_storage.assemblies.wood",
        children=[base, *drills, cover],
    )


def create() -> Compound:
    """Model entry point -- see ``create_wood_assembly``."""
    return create_wood_assembly()


__all__ = ["IS_ASSEMBLY", "create", "create_wood_assembly"]
