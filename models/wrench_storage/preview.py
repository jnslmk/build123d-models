"""Open bin with photo silhouettes, not measured replicas or printable tools.

Head thickness is conservative away from the two proven handle bands. The
5 mm transitions are illustrative, not a measured thickness map. The contours
carry 0.15 mm display simplification; a physical fit trial remains necessary.
"""

from build123d import (
    BuildPart,
    BuildSketch,
    Color,
    Compound,
    Mode,
    Part,
    Plane,
    Polygon,
    add,
    extrude,
)

from . import base
from . import config as c
from . import layout as l
from . import profiles as p

IS_ASSEMBLY = True
PARAMS = c.PARAMS
HEAD_TRANSITION = 5.0  # Illustrative transition outside proven handle bands.
COLORS = (
    (0.85, 0.36, 0.24),
    (0.93, 0.65, 0.18),
    (0.38, 0.70, 0.35),
    (0.24, 0.68, 0.78),
    (0.42, 0.48, 0.85),
    (0.73, 0.42, 0.73),
)


def thickness_outline(wrench: c.Wrench) -> tuple[tuple[float, float], ...]:
    """Transverse/longitudinal envelope: measured widths, assumed transitions."""
    widths = [(0.0, wrench.head_thickness)]
    for station in p.HANDLE_STATIONS:
        start, end = (
            station - p.HANDLE_BAND_WIDTH / 2,
            station + p.HANDLE_BAND_WIDTH / 2,
        )
        widths.extend(
            (
                (start - HEAD_TRANSITION, wrench.head_thickness),
                (start, wrench.handle_thickness),
                (end, wrench.handle_thickness),
                (end + HEAD_TRANSITION, wrench.head_thickness),
            )
        )
    widths.append((l.envelope(wrench)[0], wrench.head_thickness))
    return tuple((-width / 2, y) for y, width in widths) + tuple(
        (width / 2, y) for y, width in reversed(widths)
    )


def tool_envelope(lane: l.Lane, lift: float = 0.0) -> Part:
    """Photo-only occupied volume, or its continuous straight-up removal sweep.

    Each silhouette edge sweeps a quadrilateral, so this is not a handful of
    poses that can miss a collision between samples. Thickness remains an
    explicitly approximate consumer envelope, not a physical fit guarantee.
    """
    wrench = lane.wrench
    contour = p.PROFILES[wrench.label]
    plane = Plane(
        origin=(lane.x - wrench.head_thickness / 2, l.TOOL_START_Y, l.SEAT_Z),
        x_dir=(0, 1, 0),
        z_dir=(1, 0, 0),
    )
    with BuildPart() as tool:
        with BuildSketch(plane):
            if lift > 0:
                # Keep every source face private until one batched union.
                # Incremental sketch additions repeatedly enumerate/fuse the
                # growing contour and make the exact sweep prohibitively slow.
                faces = [
                    Polygon(*contour, align=None, mode=Mode.PRIVATE),
                    Polygon(
                        *((y, z + lift) for y, z in contour),
                        align=None,
                        mode=Mode.PRIVATE,
                    ),
                ]
                for a, b in zip(contour, (*contour[1:], contour[0])):
                    if abs(a[0] - b[0]) > 1e-6:
                        faces.append(
                            Polygon(
                                a,
                                b,
                                (b[0], b[1] + lift),
                                (a[0], a[1] + lift),
                                align=None,
                                mode=Mode.PRIVATE,
                            )
                        )
                add(faces)
            else:
                Polygon(*contour, align=None)
        extrude(amount=wrench.head_thickness)
        with BuildPart(mode=Mode.PRIVATE) as width_mask:
            with BuildSketch(Plane.XY.offset(l.SEAT_Z - l.PREVIEW_ERROR)):
                Polygon(
                    *(
                        (lane.x + x, l.TOOL_START_Y + y)
                        for x, y in thickness_outline(wrench)
                    ),
                    align=None,
                )
            extrude(amount=l.envelope(wrench)[1] + lift + 2 * l.PREVIEW_ERROR)
        add(width_mask.part, mode=Mode.INTERSECT)
    tool.part.label = f"WORKZONE {wrench.label} (photo approximation)"
    return tool.part


def create(
    wrenches_per_column: int | float = c.DEFAULT_WRENCHES_PER_COLUMN,
) -> Compound:
    layout = l.arrange(wrenches_per_column)
    bin_part = base.create(wrenches_per_column)
    bin_part.color = Color(0.25, 0.48, 0.68)
    children = [bin_part]
    for column in layout.columns:
        for lane in column.lanes:
            tool = tool_envelope(lane)
            tool.color = Color(*COLORS[c.WRENCHES.index(lane.wrench)])
            children.append(tool)
    scene = Compound(children=children)
    scene.label = "Open on-edge WORKZONE storage (no lid)"
    return scene
