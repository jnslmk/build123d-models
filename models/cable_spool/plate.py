"""The six-window disc all three plates are cut from.

Not a model -- there is no `create()` here. Base, middle and cover differ only
in what happens at the middle and how deep the chamfer on the rim is, so the
disc itself is written once and each of them asks for it.

The window is the interesting part, and it is not an annular sector. Its two
straight sides are *chords* that pass `SPOKE_HALF_W` from the axis, so the six
spokes between them are straight 10 mm bars of constant width rather than
wedges that fatten with radius. Sampling one window edge of the source mesh at
r = 36.5, 55.5 and 74.5 puts all three points on one line 5.000 mm off-centre,
which is what settled it.

Everything here is cut with booleans -- a wedge intersected into an annulus, a
tapered prism subtracted for each chamfer -- and nothing with an OCC edge op. A
plate carries 6 windows, a bore and two rim circles on the same two faces, which
is exactly the arrangement `build123d-geometry-ops` warns makes `chamfer()`
refuse, and refuse *silently* for every later call once one has failed.
"""

from __future__ import annotations

from math import cos, radians, sin, tan

from build123d import (
    Axis,
    BuildLine,
    BuildPart,
    BuildSketch,
    Circle,
    Locations,
    Mode,
    Part,
    Plane,
    Polygon,
    Polyline,
    Rotation,
    Sketch,
    add,
    extrude,
    fillet,
    make_face,
    mirror,
    revolve,
)

from . import config as cfg


def polar(count: int, phase: float = 0.0) -> Locations:
    """`count` rotations about Z, evenly spaced, starting at `phase`.

    `PolarLocations` would be the obvious tool and is not usable here: it
    wants a positive radius, and every pattern in this model is about the
    axis itself.
    """
    step = 360.0 / count
    return Locations(*[Rotation(0.0, 0.0, phase + i * step) for i in range(count)])


def sector(r_in: float, r_out: float, arc: float) -> Sketch:
    """An annular sector centred on +X, `arc` degrees wide.

    Lives here rather than beside its first caller because three of the four
    parts want one: the middle disc's relief pockets and keys, and the base's
    bore relief under each guide rib.
    """
    far = 4.0 * r_out
    half = radians(arc / 2.0)
    with BuildSketch() as sk:
        Circle(r_out)
        if r_in > 0.0:
            Circle(r_in, mode=Mode.SUBTRACT)
        Polygon(
            (0.0, 0.0),
            (far, far * tan(half)),
            (far, -far * tan(half)),
            align=None,
            mode=Mode.INTERSECT,
        )
    return sk.sketch


def window_sketch() -> Sketch:
    """One window, centred on +X, with its four corners filleted."""
    far = 3.0 * cfg.OUTER_R
    half = radians(cfg.WINDOW_HALF_ANGLE)
    apex = cfg.WINDOW_APEX_R
    with BuildSketch() as sk:
        Circle(cfg.RIM_INNER_R)
        Circle(cfg.SPOKE_RING_R, mode=Mode.SUBTRACT)
        Polygon(
            (apex, 0.0),
            (apex + far * cos(half), far * sin(half)),
            (apex + far * cos(half), -far * sin(half)),
            align=None,
            mode=Mode.INTERSECT,
        )
        fillet(sk.vertices(), cfg.WINDOW_FILLET)
    return sk.sketch


def mouth_chamfer(profile: Sketch, z_root: float, z_mouth: float) -> Part:
    """A frustum that breaks the mouth of a straight-walled cut at 45 degrees.

    `z_root` is the plane where the cut keeps its nominal size and `z_mouth`
    the face it opens through, so the same call serves either face of a plate
    by swapping the two.

    Cut as a *tapered prism* rather than a loft between two sketches. A loft
    does this correctly for a circle and refuses outright ("BRep_API: command
    not done") for the middle disc's bore, whose outline carries four relief
    bumps and two key notches -- there is no wire correspondence for it to
    interpolate. `extrude(taper=...)` is one operation and does not care.
    """
    up = z_mouth >= z_root
    with BuildPart() as tool:
        with BuildSketch(Plane.XY.offset(min(z_root, z_mouth))):
            add(profile)
        extrude(amount=abs(z_mouth - z_root), taper=-45.0)
    part = tool.part
    if not up:
        part = mirror(part, about=Plane.XY.offset((z_root + z_mouth) / 2.0))
    return part  # ty: ignore[invalid-return-type]


def _rim_chamfer(z_face: float, width: float, height: float, up: bool) -> Part:
    """The ring wedge taken off a disc's outer edge at one face, as a revolve.

    Built as a solid of revolution rather than an edge chamfer for the reason
    in the module docstring, and drawn oversize on the outside so the boolean
    never has to reconcile a coincident cylindrical face.
    """
    sign = 1.0 if up else -1.0
    r_out = cfg.OUTER_R + 2.0
    with BuildPart() as tool:
        with BuildSketch(Plane.XZ) as sk:
            with BuildLine():
                Polyline(
                    (cfg.OUTER_R - width, z_face),
                    (cfg.OUTER_R - width, z_face + sign * 2.0),
                    (r_out, z_face + sign * 2.0),
                    (r_out, z_face - sign * height),
                    (cfg.OUTER_R, z_face - sign * height),
                    close=True,
                )
            make_face()
        _ = sk
        revolve(axis=Axis.Z)
    return tool.part


def plate_body(rim_chamfer_w: float) -> Part:
    """A whole disc: rim, six windows, six spokes -- no middle yet.

    The bore is left to the caller. It is the only thing that differs between
    the three plates, and it is where all three of them get interesting.
    """
    t = cfg.PLATE_T
    c = cfg.WINDOW_CHAMFER
    win = window_sketch()

    with BuildPart() as plate:
        with BuildSketch():
            Circle(cfg.OUTER_R)
            with polar(cfg.WINDOW_COUNT, cfg.WINDOW_PHASE):
                add(win, mode=Mode.SUBTRACT)
        extrude(amount=t)

        top = mouth_chamfer(win, t - c, t)
        bottom = mouth_chamfer(win, c, 0.0)
        with polar(cfg.WINDOW_COUNT, cfg.WINDOW_PHASE):
            add(top, mode=Mode.SUBTRACT)
            add(bottom, mode=Mode.SUBTRACT)

        add(_rim_chamfer(t, rim_chamfer_w, cfg.RIM_CHAMFER_H, up=True), mode=Mode.SUBTRACT)
        add(_rim_chamfer(0.0, cfg.BED_CHAMFER, cfg.BED_CHAMFER, up=False), mode=Mode.SUBTRACT)
    return plate.part


def bore_mouth_chamfers(bore: Sketch) -> tuple[Part, Part]:
    """Mouth breaks for a plate's central bore, one for each face."""
    t, c = cfg.PLATE_T, cfg.WINDOW_CHAMFER
    return mouth_chamfer(bore, t - c, t), mouth_chamfer(bore, c, 0.0)
