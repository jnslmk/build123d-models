"""Display models of the tools themselves, for the assembly scenes.

Not printed and not precise -- these are stand-ins whose only job is to make an
assembly answer real questions: does the longest bit clear the cap, does a bit
foul its neighbour, does a countersink's head land where the layout reserved room
for it. Overall length is the one dimension that is taken seriously, because it
is the one the cover height is derived from.

Three drill point styles, because the three sets do not look alike and the
difference is not decoration:

* ``brad``    -- a conical point with a slim centre spur (wood).
* ``twist``   -- a plain conical point (metal).
* ``masonry`` -- a carbide tip **wider than the shank**, over a shank ground
  under the nominal size. That is the geometry ``sets.STONE``'s measured
  per-drill ``shank`` values exist for, so the scene draws it rather than
  pretending a masonry bit is a cylinder.

Every bit is built shank-end on ``z=0``, tip up: the pose it stands in inside a
bore, so an assembly places it with a single ``Pos``.
"""

from __future__ import annotations

from build123d import (
    Align,
    BuildPart,
    BuildSketch,
    Color,
    Cone,
    Cylinder,
    Locations,
    Part,
    Plane,
    RegularPolygon,
    extrude,
)

STEEL = Color(0.70, 0.72, 0.75)  # bright tool steel
CARBIDE = Color(0.45, 0.46, 0.48)  # the darker brazed tip on a masonry bit
COVER_GLASS = Color(0.86, 0.87, 0.84, 0.32)  # translucent so tools show through


def create_drill(
    diameter: float, length: float, style: str = "brad", shank_d: float | None = None
) -> Part:
    """A generic drill bit of ``diameter`` and overall ``length``.

    ``shank_d`` is the ground shank behind the cutting end, defaulting to the
    full diameter. On a masonry bit it is smaller, and that is exactly what the
    bores are cut to -- see ``sets``.
    """
    r = diameter / 2
    shank_r = (shank_d if shank_d is not None else diameter) / 2

    if style == "masonry":
        # A carbide tip brazed across the top of a fluted shank: the tip is the
        # nominal size, the body behind it is not.
        tip_h = min(0.9 * diameter, 0.10 * length)
        point_h = 0.5 * diameter  # the roof-shaped grind on top of the tip
        body_h = length - tip_h - point_h
        with BuildPart() as bit:
            Cylinder(shank_r, body_h, align=(Align.CENTER, Align.CENTER, Align.MIN))
            with Locations((0, 0, body_h)):
                Cylinder(r, tip_h, align=(Align.CENTER, Align.CENTER, Align.MIN))
                with Locations((0, 0, tip_h)):
                    Cone(
                        r,
                        0.25 * r,
                        point_h,
                        align=(Align.CENTER, Align.CENTER, Align.MIN),
                    )
        return bit.part

    point_h = min(0.9 * diameter, 0.22 * length)
    spur_h = 0.35 * diameter if style == "brad" else 0.0
    body_h = length - point_h - spur_h
    with BuildPart() as bit:
        Cylinder(shank_r, body_h, align=(Align.CENTER, Align.CENTER, Align.MIN))
        with Locations((0, 0, body_h)):
            # Main point: full diameter tapering nearly to the centre.
            Cone(r, 0.18 * r, point_h, align=(Align.CENTER, Align.CENTER, Align.MIN))
            if spur_h:
                with Locations((0, 0, point_h)):
                    # Sharp brad centre spur.
                    Cone(
                        0.18 * r,
                        0.0,
                        spur_h,
                        align=(Align.CENTER, Align.CENTER, Align.MIN),
                    )
    return bit.part


def create_hex_tool(
    across_flats: float, length: float, head_d: float = 0.0, head_frac: float = 0.5
) -> Part:
    """A hex-shank tool: a hex prism, optionally topped by a conical head.

    ``head_d`` > 0 draws a countersink -- a fluted cone plus a small pilot -- and
    is the width the layout had to reserve even though the socket is only
    shank-sized. Without it the tool is a plain hex shank (a tap), which is its
    own widest part.
    """
    with BuildPart() as tool:
        with BuildSketch(Plane.XY):
            RegularPolygon(across_flats / 3**0.5, 6)
        if head_d <= 0.0:
            extrude(amount=length)
            return tool.part

        head_h = head_frac * head_d
        pilot_h = 3.0
        shank_h = length - head_h - pilot_h
        extrude(amount=shank_h)
        with Locations((0, 0, shank_h)):
            Cone(head_d / 2, 0.0, head_h, align=(Align.CENTER, Align.CENTER, Align.MIN))
        # A short cylindrical pilot poking out the tip of the countersink cone.
        with Locations((0, 0, shank_h + head_h)):
            Cylinder(1.0, pilot_h, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return tool.part


def create_step_drill(
    across_flats: float,
    length: float,
    shank_len: float,
    d_min: float,
    d_max: float,
    step: float = 2.0,
) -> Part:
    """A step drill: a hex shank under a cone of stacked cylindrical steps.

    Drawn **widest at the bottom**, which is the whole reason it is not a
    ``create_hex_tool`` head: a countersink's cone flares upward and a step
    drill's tapers upward, and the difference lands exactly where the question
    is -- at tray level, among the other bits' bodies.

    The rungs are cosmetic; the envelope is not. What the scene has to get right
    is ``d_max`` at the shoulder, ``d_min`` at the tip, and the shoulder's height
    (``shank_len`` above the shank end), because those are what the layout
    reserved room for and what the cover has to clear.
    """
    shank_h = shank_len or length
    body_h = length - shank_h
    n = max(1, round((d_max - d_min) / step) + 1)
    rung_h = body_h / n

    with BuildPart() as tool:
        with BuildSketch(Plane.XY):
            RegularPolygon(across_flats / 3**0.5, 6)
        extrude(amount=shank_h)
        for i in range(n):
            # Biggest step at the bottom, against the shoulder that carries the
            # tool's weight on the cartridge's top face.
            d = d_max - i * (d_max - d_min) / max(n - 1, 1)
            with Locations((0, 0, shank_h + i * rung_h)):
                Cylinder(
                    d / 2, rung_h, align=(Align.CENTER, Align.CENTER, Align.MIN)
                )
    return tool.part


__all__ = [
    "CARBIDE",
    "COVER_GLASS",
    "STEEL",
    "create_drill",
    "create_hex_tool",
    "create_step_drill",
]
