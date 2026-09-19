"""Two interpenetrating tetrahedra made from twelve finished LED lamps.

One tetrahedron stays on the mathematical cube faces. The other moves each edge
outward by one profile envelope, so the six apparent crossings pass in parallel
planes instead of occupying the same volume. Each vertex uses one flat core,
three support-free cradle arms and six existing profile straps.

    uv run show led_profiles.assemblies.stella_octangula
"""

from __future__ import annotations

from math import sqrt
from typing import NamedTuple

from build123d import Compound, Part, Plane, Vector

from models.lib.edges import as_part

from .. import config as c
from .. import mount_config as m
from .. import stella_config as s
from .. import strap as strap_mod
from ..assembly import PARAMS, parts as lamp_parts
from ..stella_arm import create_arm
from ..stella_core import create_core

IS_ASSEMBLY = True

TETRA_EDGES = [(i, j) for i in range(4) for j in range(i + 1, 4)]
BASE_SIGNS = [(1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1)]
OFFSET_SIGNS = [(-x, y, z) for x, y, z in BASE_SIGNS]


class LampSegment(NamedTuple):
    """One lamp's tube axis in world coordinates, in millimetres.

    ``name`` is the wiring label used by the ``gled2`` and ``beamhouse``
    projects: ``b0..b5`` on the base tetrahedron, ``o0..o5`` on the offset one;
    ``edge_index`` is the ``TETRA_EDGES`` slot, ``vertices`` the tetra vertex
    indices the lamp spans, and ``outward`` its diffuser-facing normal.
    """

    name: str
    tetra: str
    edge_index: int
    vertices: tuple[int, int]
    start: Vector
    end: Vector
    outward: Vector


def lamp_segments(length: float = c.LENGTH) -> list[LampSegment]:
    """The twelve lamp axes exactly as ``create_stella_octangula`` places them.

    Same arithmetic as the assembly's tube placement — vertex, face offset,
    gland setback, under-band lift — so the show-control projects and the CAD
    cannot drift apart. Light-control consumers (SVG installations, patches)
    build off this, never off re-derived geometry.
    """
    segments: list[LampSegment] = []
    for prefix, tetra, signs, offset in (
        ("b", "base", BASE_SIGNS, 0.0),
        ("o", "offset", OFFSET_SIGNS, s.EDGE_OFFSET),
    ):
        vertices = tetra_vertices(length, signs)
        for edge_index, (a_index, b_index) in enumerate(TETRA_EDGES):
            a, b = vertices[a_index], vertices[b_index]
            direction = _unit(b - a)
            outward = _face_normal(a, _face_axis(a, b))
            origin = (
                a
                + outward * offset
                + direction * s.CRADLE_START
                + outward * m.TUBE_UNDER_Z
            )
            segments.append(
                LampSegment(
                    name=f"{prefix}{edge_index}",
                    tetra=tetra,
                    edge_index=edge_index,
                    vertices=(a_index, b_index),
                    start=origin,
                    end=origin + direction * length,
                    outward=outward,
                )
            )
    return segments


def tetra_vertices(length: float, signs: list[tuple[int, int, int]]) -> list[Vector]:
    """Vertices whose edge length includes one lamp and both gland setbacks."""
    side = length + 2 * s.CRADLE_START
    half_cube = side / sqrt(8)
    return [Vector(x * half_cube, y * half_cube, z * half_cube) for x, y, z in signs]


def _unit(vector: Vector) -> Vector:
    return vector.normalized()


def _components(vector: Vector) -> tuple[float, float, float]:
    return vector.X, vector.Y, vector.Z


def _face_axis(a: Vector, b: Vector) -> int:
    """Coordinate held constant by one tetrahedron edge: its cube face."""
    return next(
        axis
        for axis, (a_value, b_value) in enumerate(zip(_components(a), _components(b)))
        if abs(a_value - b_value) < 1e-9
    )


def _face_normal(vertex: Vector, axis: int) -> Vector:
    components = [0.0, 0.0, 0.0]
    components[axis] = 1.0 if _components(vertex)[axis] > 0 else -1.0
    return Vector(*components)


def _edge_frame(origin: Vector, direction: Vector, outward: Vector) -> Plane:
    """Tube-local frame: +X along the lamp and +Z through its diffuser."""
    return Plane(origin=origin, x_dir=direction, z_dir=outward)


def _placed(part: Part, frame: Plane, label: str) -> Part:
    moved = as_part(frame.location * part)
    moved.label = label
    moved.color = part.color
    return moved


def _vertex_core_frame(
    vertex: Vector,
    vertices: list[Vector],
    index: int,
    offset: float,
) -> Plane:
    """Core frame aligned to the x-face arm's bolt pair and radial normal."""
    signs = Vector(*(1.0 if value > 0 else -1.0 for value in _components(vertex)))
    radial = _unit(signs)
    centre = vertex + signs * (offset / 3)

    x_neighbour = next(
        other
        for j, other in enumerate(vertices)
        if j != index and _face_axis(vertex, other) == 0
    )
    edge = _unit(x_neighbour - vertex)
    face_normal = _face_normal(vertex, 0)
    pair_axis = _unit(face_normal.cross(edge))

    # The core is authored z=0..CORE_T; its top is the arm-mating plane.
    return Plane(origin=centre - radial * s.CORE_T, x_dir=pair_axis, z_dir=radial)


def _arm_straps(
    frame: Plane, tag: str, strap_sources: list[tuple[Part, float]]
) -> list[Part]:
    straps: list[Part] = []
    for local, station in strap_sources:
        straps.append(_placed(local, frame, f"strap ({tag}, {station:.0f} mm)"))
    return straps


def create_stella_octangula(length: float = c.LENGTH) -> Compound:
    """Twelve lamps, 24 arms, eight cores and 48 straps in the final form."""
    children: list[Part] = []
    arm_source = create_arm()
    strap_sources = [
        (strap_mod.seated(s.CRADLE_START + station), station)
        for station in m.STRAP_STATIONS
    ]
    lamp_sources = lamp_parts(length, cable=False)

    for tetra_name, signs, offset in (
        ("base", BASE_SIGNS, 0.0),
        ("offset", OFFSET_SIGNS, s.EDGE_OFFSET),
    ):
        vertices = tetra_vertices(length, signs)
        core_source = create_core(offset)

        for index, vertex in enumerate(vertices):
            core_frame = _vertex_core_frame(vertex, vertices, index, offset)
            children.append(
                _placed(
                    core_source,
                    core_frame,
                    (
                        f"stella offset vertex core {index}"
                        if offset
                        else f"stella vertex core {index}"
                    ),
                )
            )

        for edge_index, (a_index, b_index) in enumerate(TETRA_EDGES):
            a, b = vertices[a_index], vertices[b_index]
            direction = _unit(b - a)
            axis = _face_axis(a, b)
            outward = _face_normal(a, axis)
            shift = outward * offset
            near_endpoint, far_endpoint = a + shift, b + shift
            near_frame = _edge_frame(near_endpoint, direction, outward)
            far_frame = _edge_frame(far_endpoint, -direction, outward)

            children.append(
                _placed(
                    arm_source,
                    near_frame,
                    f"stella vertex arm ({tetra_name} {edge_index} near)",
                )
            )
            children.append(
                _placed(
                    arm_source,
                    far_frame,
                    f"stella vertex arm ({tetra_name} {edge_index} far)",
                )
            )
            children.extend(
                _arm_straps(
                    near_frame, f"{tetra_name} edge {edge_index} near", strap_sources
                )
            )
            children.extend(
                _arm_straps(
                    far_frame, f"{tetra_name} edge {edge_index} far", strap_sources
                )
            )

            tube_origin = (
                near_endpoint + direction * s.CRADLE_START + outward * m.TUBE_UNDER_Z
            )
            tube_frame = _edge_frame(tube_origin, direction, outward)
            for part in lamp_sources:
                children.append(
                    _placed(
                        part,
                        tube_frame,
                        f"{part.label} ({tetra_name} lamp {edge_index})",
                    )
                )

    assembly = Compound(children=children)
    assembly.label = f"stella octangula ({length:.0f} mm lamps)"
    return assembly


def create(length: float = c.LENGTH) -> Compound:
    """Entry point for ``uv run show led_profiles.assemblies.stella_octangula``."""
    return create_stella_octangula(length)


__all__ = [
    "BASE_SIGNS",
    "IS_ASSEMBLY",
    "LampSegment",
    "OFFSET_SIGNS",
    "PARAMS",
    "TETRA_EDGES",
    "create",
    "create_stella_octangula",
    "lamp_segments",
    "tetra_vertices",
]
