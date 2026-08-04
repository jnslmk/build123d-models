"""The cradle: the shape every mount in this family grips the tube with.

Shared here rather than repeated, the same way ``profile.py`` shares the
extrusion's sketches. A cradle is an open trough that stops exactly at the
profile's rim, so the tube drops into it sideways and lifts back out -- see
``docs/design-notes.md`` S1 for why that beats a collar.

Built lying along +X with its near end on x=0, sitting on z=0 (the bed), mouth
opening +Z. Feet in this package position it; they never rebuild it.
"""

from __future__ import annotations

from build123d import (
    Align,
    Axis,
    BuildPart,
    BuildSketch,
    Cylinder,
    Locations,
    Mode,
    Part,
    Plane,
    Rectangle,
    Sketch,
    SlotOverall,
    add,
    extrude,
)

from models.lib.edges import chamfer_edge

from . import config as c
from . import mount_config as m


def _big() -> float:
    return 3 * c.HEIGHT


def tube_section(clearance: float = 0.0, lift: float = 0.0) -> Sketch:
    """The tube's stadium, grown by ``clearance`` diametrally, in mount-local z.

    ``lift`` raises it, for feet that stand their cradle on a plinth -- the
    corner does, so its floor can clear the gland hanging below the tube.
    """
    with BuildSketch() as s:
        with Locations((0, m.TUBE_AXIS_Z + lift)):
            SlotOverall(c.HEIGHT + clearance, c.WIDTH + clearance, rotation=90)
    return s.sketch


def body_section(lift: float = 0.0, floor: float | None = 0.0) -> Sketch:
    """The cradle's outer profile: the bore plus a wall, cut off at the rim.

    ``floor`` flattens the back at that height, which is what gives a
    bed-facing cradle its first layer. Pass ``None`` for a cradle that is not
    lying on the bed -- the stand's is extruded vertically, and clipping it at
    zero there would slice the trough off at the tube's axis and leave two fins.
    """
    with BuildSketch() as s:
        with Locations((0, m.TUBE_AXIS_Z + lift)):
            SlotOverall(
                c.HEIGHT + m.BORE_FIT + 2 * m.CRADLE_WALL,
                c.WIDTH + m.BORE_FIT + 2 * m.CRADLE_WALL,
                rotation=90,
            )
        with Locations((0, m.CRADLE_DEPTH + lift)):
            Rectangle(
                _big(), _big(), align=(Align.CENTER, Align.MIN), mode=Mode.SUBTRACT
            )
        if floor is not None:
            with Locations((0, floor)):
                Rectangle(
                    _big(), _big(), align=(Align.CENTER, Align.MAX), mode=Mode.SUBTRACT
                )
    return s.sketch


def outer_half_width() -> float:
    """Half the cradle's overall width, at the mouth."""
    return (c.WIDTH + m.BORE_FIT) / 2 + m.CRADLE_WALL


def back_z(lift: float = 0.0) -> float:
    """Height of the cradle body's outermost back face."""
    return m.TUBE_AXIS_Z + lift - (c.HEIGHT + m.BORE_FIT) / 2 - m.CRADLE_WALL


def boss_pad_section(lift: float = 0.0, base: float = 0.0) -> Sketch:
    """Cross-section of the two strap bosses, merged into the cradle walls.

    ``base`` is where the pad's underside sits. A cradle lying on the bed runs
    its pads all the way down to it; the stand's socket is vertical, so its pads
    stop at the cradle's own back face (``back_z``) instead of at zero.
    """
    top = m.CRADLE_DEPTH + lift
    with BuildSketch() as s:
        with Locations((-m.BOSS_U, top), (m.BOSS_U, top)):
            Rectangle(m.BOSS_OD, top - base, align=(Align.CENTER, Align.MAX))
    return s.sketch


def create_cradle(
    length: float = m.CRADLE_LEN, stations: tuple[float, ...] | None = None
) -> Part:
    """A trough for one tube end, near end on x=0, running +X.

    ``stations`` are the strap centres along the length, defaulting to half a
    strap in from each end -- far enough that the boss pads stay on the cradle,
    close enough that the clamp lands over the two contact bands.
    """
    if stations is None:
        stations = m.STRAP_STATIONS

    with BuildPart() as bp:
        with BuildSketch(Plane.YZ):
            add(body_section())
        extrude(amount=length)

        # Strap bosses, merged into the walls.
        for x in stations:
            with BuildSketch(Plane.YZ.offset(x - m.STRAP_W / 2)):
                add(boss_pad_section())
            extrude(amount=m.STRAP_W)

        # Bore, full length at the nominal fit...
        with BuildSketch(Plane.YZ):
            add(tube_section(m.BORE_FIT))
        extrude(amount=length, mode=Mode.SUBTRACT)

        # ...then relieved everywhere except the two end bands, so the middle
        # cannot bind on a 1.5 m extrusion and the joint keeps its compliance.
        relief_len = length - 2 * m.BAND_LEN
        if relief_len > 0:
            with BuildSketch(Plane.YZ.offset(m.BAND_LEN)):
                add(tube_section(m.BORE_FIT + 2 * m.BAND_RELIEF))
            extrude(amount=relief_len, mode=Mode.SUBTRACT)

        # Insert bosses. No lead-in chamfer -- deliberate exception, the
        # insert's own chamfer guides it and a printed one removes the material
        # it has to melt into.
        for x in stations:
            with Locations(
                (x, -m.BOSS_U, m.CRADLE_DEPTH),
                (x, m.BOSS_U, m.CRADLE_DEPTH),
            ):
                Cylinder(
                    m.INSERT_D / 2,
                    m.INSERT_DEPTH,
                    align=(Align.CENTER, Align.CENTER, Align.MAX),
                    mode=Mode.SUBTRACT,
                )

        add_drains(length)
        chamfer_edge(
            bp, bp.faces().sort_by(Axis.Z)[0].outer_wire().edges(), m.EDGE_CHAMFER
        )

    return bp.part


def add_drains(length: float, count: int = 2) -> None:
    """Punch drains through a cradle floor.

    The trough opens upward in every print pose in this family, so outdoors it
    is a gutter. Must be called inside an open ``BuildPart``, which it cuts into
    via the ambient builder context. See ``docs/design-notes.md`` S5.
    """
    spacing = length / (count + 1)
    for i in range(1, count + 1):
        with Locations((i * spacing, 0, 0)):
            Cylinder(
                m.DRAIN_D / 2,
                m.TUBE_UNDER_Z + 1,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )


def strap_land_z() -> float:
    """Height of the face a strap's feet bolt down onto."""
    return m.CRADLE_DEPTH


def create() -> Part:
    """Entry point for ``uv run show led_profiles.cradle``."""
    return create_cradle()


__all__ = [
    "add_drains",
    "body_section",
    "boss_pad_section",
    "create",
    "create_cradle",
    "outer_half_width",
    "strap_land_z",
    "tube_section",
]
