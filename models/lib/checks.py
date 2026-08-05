"""Building blocks for in-code geometry assertions.

Ribs, wall gaps, blind pockets and fit clearances are invisible in a projection,
so the house rule is to verify them in code. That needs two things, and neither
is model-specific:

* ``is_solid_at`` -- ask the kernel whether a point is inside the material,
  which is the only way to see *into* a solid.
* ``Report`` -- collect every pass/fail line so one run surfaces every problem.
  A bare ``assert`` stops at the first failure and hides the rest, which turns
  a single debugging session into five.

A model's own ``checks.py`` supplies the geometry knowledge; this supplies the
instrument.

Two of those instruments exist because prose did not work. ``AGENTS.md`` has
always said "never ship a part with raw square edges", and a corner shipped with
one chamfer and passed 185 assertions; the strap's bolt circle sat *on* its own
arch, so the part could not be bolted together, and nothing noticed. Both are
properties nobody could have violated had they been checkable, so:

* ``sharp_convex_edges`` -- the raw-edge rule, made falsifiable. Exceptions go
  in ``allow`` and each one carries a reason, which turns an oversight into a
  documented decision.
* ``fastener_clearance`` -- can the bolt actually be installed? Head and driver,
  not just "the clearance hole is smaller than the insert".
"""

from __future__ import annotations

from build123d import Axis, Edge, Part, ShapeList, Vector

# OCP ships no stubs for these; they resolve fine at runtime.
from OCP.BRepClass3d import BRepClass3d_SolidClassifier  # ty: ignore[unresolved-import]
from OCP.gp import gp_Pnt  # ty: ignore[unresolved-import]
from OCP.TopAbs import TopAbs_IN, TopAbs_ON  # ty: ignore[unresolved-import]

TOL = 1e-6


def is_solid_at(part: Part, x: float, y: float, z: float) -> bool:
    """True if (x, y, z) lies inside the material."""
    clf = BRepClass3d_SolidClassifier(part.wrapped)
    clf.Perform(gp_Pnt(x, y, z), TOL)
    return clf.State() in (TopAbs_IN, TopAbs_ON)


def _probe(part: Part):
    """A reusable inside/outside test, for when one point is not enough.

    ``is_solid_at`` builds a fresh classifier per call, which is right for a
    handful of samples and far too slow for the thousands ``interior_angle``
    needs. This builds it once.
    """
    clf = BRepClass3d_SolidClassifier(part.wrapped)

    def inside(v: Vector) -> bool:
        clf.Perform(gp_Pnt(v.X, v.Y, v.Z), TOL)
        return clf.State() in (TopAbs_IN, TopAbs_ON)

    return inside


def _outward(face, at: Vector, inside, step: float) -> Vector | None:
    """A face's normal at a point, flipped to point out of the material.

    OCC does not promise a consistent orientation across the faces of a fused
    solid, so this is established by probing rather than trusted.
    """
    try:
        n = face.normal_at(at)
    except Exception:  # noqa: BLE001 -- degenerate faces answer by raising
        return None
    out, into = inside(at + n * step), inside(at - n * step)
    if into and not out:
        return n
    if out and not into:
        return -n
    return None  # a knife edge or a sliver: neither side is decisive


def interior_angle(part: Part, edge: Edge, faces=None, probe=None) -> float | None:
    """The dihedral angle *through the material* at an edge, in degrees.

    A square corner answers ~90, the two edges a 45 deg chamfer leaves ~135
    each, a tangent or filleted edge ~180, and a concave step ~270. ``None``
    means the edge could not be classified -- a sliver, or not shared by exactly
    two faces.

    The magnitude comes from the two faces' outward normals, but their *sign*
    cannot: a convex 90 deg edge and a concave one have the **same** pair of
    outward normals. What differs is which quadrants around the edge hold
    material. So convexity is settled by one probe into the quadrant that is
    empty only when the edge is convex -- the one along ``n_b - n_a``. Stepping
    along the normals' *sum* is the intuitive test and it is wrong for both
    cases at once, silently.
    """
    inside = probe or _probe(part)
    step = 1e-3
    pair = faces if faces is not None else _adjacent_faces(part).get(_edge_key(edge))
    if pair is None or len(pair) != 2:
        return None

    at = edge.position_at(0.5)
    n_a = _outward(pair[0], at, inside, step)
    n_b = _outward(pair[1], at, inside, step)
    if n_a is None or n_b is None:
        return None

    between = n_a.get_angle(n_b)  # degrees, consistent with the rest of build123d's
    # public API (Vector.rotate, Axis.angle_between, Rotation, taper); wrapping
    # this in math.degrees() would silently double-convert it.
    if between < 1e-6:
        return 180.0  # tangent: the faces meet smoothly, there is no edge to break
    convex = not inside(at + (n_b - n_a).normalized() * step)
    return (180.0 - between) if convex else (180.0 + between)


def _edge_key(edge: Edge) -> tuple:
    """A geometric identity for an edge, for matching it across faces.

    Shapes off two different ``Face.edges()`` calls are separate Python objects
    for the same geometry, so adjacency is keyed on position, not identity.
    """
    m = edge.center()
    return (round(m.X, 4), round(m.Y, 4), round(m.Z, 4), round(edge.length, 4))


def _adjacent_faces(part: Part) -> dict:
    """Every edge of the solid, mapped to the faces that share it.

    The ``ty`` suppressions are build123d's own stubs: ``faces()``/``edges()``
    are declared on the ``Mixin2D``/``Mixin1D`` bases, so a ``Part`` receiver
    resolves to a union the checker will not accept. Both calls are correct at
    runtime -- the same false positive the repo already carries in
    ``render_a4_pdf.py``.
    """
    faces: dict = {}
    for face in part.faces():  # ty: ignore[invalid-argument-type]
        for edge in face.edges():  # ty: ignore[invalid-argument-type]
            faces.setdefault(_edge_key(edge), []).append(face)
    return faces


def sharp_convex_edges(
    part: Part,
    min_length: float = 2.0,
    max_interior: float = 120.0,
    allow: tuple = (),
) -> ShapeList[Edge]:
    """Convex edges sharp enough to want breaking, that carry no treatment.

    The house rule -- chamfer horizontal edges, fillet vertical ones -- turned
    into something a check can fail on. An edge is reported when both of:

    * it is at least ``min_length`` long, so slivers and tangency seams do not
      drown the signal;
    * its interior angle is at most ``max_interior``. That one test carries the
      convexity too, since a concave edge measures over 180. The default of 120
      reports a raw 90 deg corner and passes the ~135 an existing 45 deg chamfer
      leaves behind, so a treated part comes back clean.

    ``allow`` holds ``(predicate, reason)`` pairs. Anything a predicate matches
    is excluded, and the reason is what the caller prints. Real parts have
    legitimate square edges -- sealing faces, thread flanks, heat-set insert
    mouths -- and the point of the pair is that each one has to be *stated*
    rather than merely not noticed. That is the whole difference between this
    check and the prose rule it replaces.
    """
    inside = _probe(part)
    adjacency = _adjacent_faces(part)  # built once; it is the expensive part
    sharp = []
    for edge in part.edges():  # ty: ignore[invalid-argument-type]
        if edge.length < min_length:
            continue
        if any(predicate(edge) for predicate, _ in allow):
            continue
        angle = interior_angle(
            part, edge, faces=adjacency.get(_edge_key(edge)), probe=inside
        )
        if angle is not None and angle <= max_interior:
            sharp.append(edge)
    return ShapeList(sharp)


def fastener_clearance(
    part: Part,
    at: tuple[float, float, float],
    head_d: float,
    head_h: float,
    direction: Axis | None = None,
    driver_d: float | None = None,
    driver_len: float = 0.0,
) -> float:
    """Material in the way of a fastener's head and driver, in mm^3.

    Non-zero means the part cannot be assembled. This exists because the family
    once asserted only ``BOLT_CLEAR_D < INSERT_D`` -- true, and useless: the
    bolt axis sat on the strap's own arch, so the head fouled the flank by
    2.6 mm and no bolt could be seated. "The hole is the right size" is not the
    same question as "the fastener fits".

    ``at`` is where the head's bearing face lands and ``direction`` is the way
    it stands off (default +Z). ``driver_d`` adds a socket or key above the
    head, which is usually the binding constraint on a recessed fastener.
    """
    from build123d import Align, Cylinder, Location, Plane, Rotation

    axis = direction or Axis.Z
    plane = Plane(origin=at, z_dir=axis.direction)

    tools = [
        Cylinder(head_d / 2, head_h, align=(Align.CENTER, Align.CENTER, Align.MIN))
    ]
    if driver_d and driver_len:
        tools.append(
            Location((0, 0, head_h))
            * Cylinder(
                driver_d / 2, driver_len, align=(Align.CENTER, Align.CENTER, Align.MIN)
            )
        )

    fouled = 0.0
    for tool in tools:
        placed = plane.location * Rotation(0, 0, 0) * tool
        try:
            common = part.intersect(placed)
        except Exception:  # noqa: BLE001 -- OCC raises instead of returning empty
            continue
        if common is None:
            continue
        shapes = list(common) if isinstance(common, list) else [common]
        fouled += float(sum(s.volume for s in shapes))
    return fouled


class Report:
    """Collects pass/fail lines so one run shows every problem, not just the first."""

    def __init__(self) -> None:
        self.failures: list[str] = []
        self.lines: list[str] = []

    def check(self, ok: bool, label: str, detail: str = "") -> None:
        mark = "PASS" if ok else "FAIL"
        self.lines.append(f"  [{mark}] {label}{(' -- ' + detail) if detail else ''}")
        if not ok:
            self.failures.append(label)

    def section(self, title: str) -> None:
        self.lines.append(f"\n{title}")

    def render(self) -> str:
        tail = (
            f"\n{len(self.failures)} FAILED: {', '.join(self.failures)}"
            if self.failures
            else "\nall checks passed"
        )
        return "\n".join(self.lines) + tail
