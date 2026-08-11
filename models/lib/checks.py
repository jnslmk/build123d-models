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

from typing import NamedTuple

from build123d import Axis, Edge, GeomType, Part, ShapeList, Vector

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


def solid_probe(part: Part):
    """A reusable inside/outside test, for when one point is not enough.

    ``is_solid_at`` builds a fresh classifier per call, which is right for a
    handful of samples and far too slow for the thousands ``interior_angle``
    needs. This builds it once.

    Public because the cost is not a footnote on complicated parts: constructing
    the classifier scales with face count, and on a lofted shell of 168 B-spline
    faces (``spiral_vase_lampshade``) one ``is_solid_at`` measures 2.7 seconds
    against roughly a millisecond through a probe built once. Any ``checks.py``
    taking more than a handful of samples of the same solid should take them
    through this instead. Note the argument type: it takes a ``Vector``, not
    three floats, matching ``interior_angle``'s ``probe`` parameter.
    """
    clf = BRepClass3d_SolidClassifier(part.wrapped)

    def inside(v: Vector) -> bool:
        clf.Perform(gp_Pnt(v.X, v.Y, v.Z), TOL)
        return clf.State() in (TopAbs_IN, TopAbs_ON)

    return inside


def _outward(face, at: Vector, inside, step: float, edge: Edge) -> Vector | None:
    """A face's normal at a point, flipped to point out of the material.

    OCC does not promise a consistent orientation across the faces of a fused
    solid, so this is established by probing rather than trusted.

    Stepping straight off ``at`` along the face's own normal (``n``) is
    enough whenever the material wedge at this edge is at least 90 deg wide,
    which is the common case and all this ever had to handle before a real
    ~50 deg "feather" edge exposed the gap -- led_profiles' strap mouth,
    where the slot's flat floor meets a shell flank that grazes past it.
    For a wedge *narrower* than 90 deg, neither ``+n`` nor ``-n`` can ever
    land inside it, at *any* step size: that is a geometric fact, not a
    tolerance problem. A face's normal is 90 deg from its own tangent by
    construction, and an acute wedge's material lies entirely within less
    than 90 deg of that tangent, so the normal always overshoots into air on
    both sides. Shrinking ``step`` does not rescue it either -- probed the
    real feather edge above from ``step=1`` down to ``step=1e-9`` and it
    stayed indecisive the whole way, right up until the step dropped below
    the classifier's own ``TOL`` (1e-6). At that point *both* directions
    started reading "inside", not because either genuinely is, but because
    both probe points are now within tolerance of the surface itself --
    a false positive, not a resolution.

    So when the straight probe is indecisive, this nudges the probe's origin
    sideways first, along the face's own surface and perpendicular to the
    shared edge (``tangent x n``). That walks the origin out of the acute
    wedge's tip and into the face's interior, where the local material
    reliably spans more than 90 deg and the plain normal test works again.
    Which of the two sideways directions actually heads into the face is not
    known up front, so both are tried, at each rung of a small offset
    ladder -- 0.01 mm, then a 10x-wider 0.1 mm safety margin. Every real
    acute edge found so far (the strap mouth's 8, plus 2 more elsewhere on
    the same endcap this fix also newly caught -- see ``checks.py``'s
    ``sharp_convex_edges`` docs) resolves at the very first rung; the second
    exists for a model this repo has not built yet, not for one already in
    hand. Checked across all of those edges (the acute ones and the
    already-working ones alike): exactly one direction ever resolves, the
    other stays indecisive, and the resolved sign never disagrees between
    rungs -- so there is nothing here to arbitrate between candidates, only
    a search for the first one that answers. A genuine sliver -- a real edge
    this still cannot classify, as opposed to a wedge merely narrower than
    90 deg -- exhausts the whole ladder before answering ``None``, which is
    the expensive path; keeping the ladder at two rungs instead of a longer
    one bounds that cost at 4x today's per-edge probe count instead of a
    larger multiple, without giving up the margin.

    Before trusting a nudged reading, this also checks the nudge is still
    *on* the face at all (``face.distance_to(origin)`` small relative to the
    offset just taken), not merely that some direction happened to read
    decisively. Two directions off a real face are not symmetric: the one
    that heads into the face's own interior stays within a thousandth of the
    surface at either rung; the one that heads off its trimmed edge lands
    essentially the full offset away, because the closest point left on the
    face is now the boundary it just walked past. That gap is three orders
    of magnitude, on both a large plain face and the smallest real face this
    was checked against (a 0.0076 mm^2 sliver off one of led_profiles'
    endcap's own IsoThread flanks) -- cheap to tell apart, and worth telling
    apart: a solid-classifier reading from a point that has wandered off the
    face it claims to represent is answering a question about whatever
    unrelated geometry it landed near, not about this edge, and would look
    exactly as decisive as a real answer. Re-deriving ``face.normal_at`` at
    the nudged point was considered and rejected: it is not obviously
    cheaper than the distance check, and it is subtly wrong on a curved face
    -- the sign decision would use the *nudged* point's normal while the
    value this must return is ``n`` (or ``-n``) *at* ``at``, and those only
    agree while the surface turns by under 90 deg over the offset, which is
    exactly the kind of thing a small, tightly-curved face is not
    guaranteed to satisfy.

    The sideways ladder only runs once the direct probe has already failed,
    so an edge that resolves on the direct probe -- true 90 deg corners, the
    case ``sharp_convex_edges`` spent its time on before this existed --
    costs exactly what it did before this existed: two ``inside`` calls, no
    ``tangent_at``, no loop, no ``distance_to``.

    That is not, however, most probes on real production geometry, and the
    docstring used to imply otherwise. Measured on led_profiles.endcap's
    normal (fully filleted, threaded) build, across all 254 edges with a
    resolvable two-face pair (508 ``_outward`` calls): 84 calls (~17%) fall
    through to this ladder, not a handful of pathological outliers. Most of
    them cluster in two places: the IsoThread gland thread's own flank
    geometry (z roughly 0-7.7 mm, radius roughly 6.15-6.2 mm -- BSPLINE,
    CIRCLE and ELLIPSE edges from the helical flank, 46+12+10 of the 84
    fallback-triggering probes) and the shell's own genuinely-acute edges
    this fix newly caught (see ``sharp_convex_edges``'s docs). Of the 84,
    54 resolve via the ladder (some correctly reveal more real sharp angles,
    the same way the shell edges did); 30 exhaust it and correctly answer
    ``None`` -- spot-checked one of those and it is the 0.0076 mm^2 sliver
    face mentioned above, consistent with a genuine sliver, though the other
    29 were not each individually re-verified. None of this is a defect to
    fix on the fast path: Section one already showed, as a geometric fact
    and not an implementation gap, that any face bounding a wedge under
    90 deg needs more than a straight ``+-n`` probe to classify at all, at
    any step size -- ISO thread flanks routinely are that narrow, so this
    cost is inherent to correctly classifying real threaded geometry, not a
    rare-sliver tax. On the same build, ``sharp_convex_edges`` wall-clock
    rose across three back-to-back runs (this machine's own variance is
    part of the honest number: ~29 s -> ~32 s, ~32 s -> ~34 s, ~32 s ->
    ~36 s -- roughly a 6-13%, call it ~10%, increase) -- a real cost, not
    "the common case is unchanged" for this part as a whole, only for the
    individual edges that do resolve on the direct probe. It would be worse
    without the on-face check above: measured before that existed, the same
    before/after comparison was a ~40% increase (~24 s -> ~34 s) -- most of
    that gap was `inside` calls spent on nudge points that had already
    walked off a tiny face and were never going to answer anything real, and
    the on-face check turns out to be a genuine performance fix for that, on
    top of being the correctness safeguard it was added for.
    """
    try:
        n = face.normal_at(at)
    except Exception:  # noqa: BLE001 -- degenerate faces answer by raising
        return None

    def resolve(origin: Vector) -> Vector | None:
        out, into = inside(origin + n * step), inside(origin - n * step)
        if into and not out:
            return n
        if out and not into:
            return -n
        return None

    found = resolve(at)
    if found is not None:
        return found

    # Indecisive at the edge itself -- try again from a point nudged along
    # the face's own surface, away from the (possibly acute) wedge tip. See
    # the docstring above for why this, and not a smaller ``step``, is the
    # fix. ``tangent x n`` is perpendicular to the edge and lies in the
    # face's tangent plane; which of its two directions moves *into* the
    # face isn't known without walking the face's actual trim boundary, so
    # both are tried, smallest offset first.
    tangent = edge.tangent_at(0.5)
    u = tangent.cross(n)
    if u.length < TOL:
        return None  # tangent parallel to the normal: no sideways direction exists
    u = u.normalized()
    for offset in (0.01, 0.1):
        for direction in (u, -u):
            origin = at + direction * offset
            # A face that is small relative to the offset (a real case: an
            # IsoThread flank's boundary sliver) can have BOTH sideways
            # directions walk clean off its trimmed edge. A point that has
            # done that is no longer on this face at all, so a "decisive"
            # inside/outside reading from there answers a question about
            # whatever geometry it landed near, not about this face -- see
            # the docstring for why re-deriving the normal there instead is
            # not the fix. ``distance_to`` is a single nearest-point query
            # against one face, cheaper than the ``inside`` classification
            # against the whole solid it would otherwise spend two calls on,
            # so skipping here is not just safer, it is not obviously a
            # pessimisation of the sliver's already-expensive dead end.
            if face.distance_to(origin) > offset * 0.1:
                continue
            found = resolve(origin)
            if found is not None:
                return found
    return None  # a genuine sliver: not even the sideways nudge found material


def interior_angle(part: Part, edge: Edge, faces=None, probe=None) -> float | None:
    """The dihedral angle *through the material* at an edge, in degrees.

    A square corner answers ~90, the two edges a 45 deg chamfer leaves ~135
    each, a tangent or filleted edge ~180, a concave step ~270, and an acute
    "feather" edge (a face grazing past another at a shallow angle) whatever
    is left below 90. ``None`` means the edge genuinely could not be
    classified: not shared by exactly two faces, or a sliver where even
    ``_outward``'s sideways nudge (see its docstring) never lands decisively
    in or out of the material.

    The magnitude comes from the two faces' outward normals, but their *sign*
    cannot: a convex 90 deg edge and a concave one have the **same** pair of
    outward normals. What differs is which quadrants around the edge hold
    material. So convexity is settled by one probe into the quadrant that is
    empty only when the edge is convex -- the one along ``n_b - n_a``. Stepping
    along the normals' *sum* is the intuitive test and it is wrong for both
    cases at once, silently.
    """
    inside = probe or solid_probe(part)
    step = 1e-3
    pair = faces if faces is not None else _adjacent_faces(part).get(_edge_key(edge))
    if pair is None or len(pair) != 2:
        return None

    at = edge.position_at(0.5)
    n_a = _outward(pair[0], at, inside, step, edge)
    n_b = _outward(pair[1], at, inside, step, edge)
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


def adjacent_faces(part: Part, edge) -> list:
    """The faces of ``part`` that share ``edge``, matched by position.

    Two calls to ``Face.edges()`` hand back separate Python objects for the
    same geometry, so an edge cannot be matched across faces by ``is`` or
    ``==``; the identity has to be geometric -- an edge's centre plus its
    length, the same ``_edge_key`` that ``_adjacent_faces`` hashes every edge
    of the solid by. This is the public single-edge form of that lookup.
    Each face is reported at most once, even when two of its edges share the
    lookup key (coincident edges on a degenerate face).

    Builds the whole edge-to-faces map on every call, which is the right cost
    for the handful of edges an ``allow`` predicate tests and quadratic for a
    survey of most of a part's edges -- exactly the relationship
    ``is_periodic_seam`` has to ``periodic_seams``. Callers that need every
    edge at once should use the batch form ``_adjacent_faces`` directly (or
    pass a prebuilt ``faces`` pair to ``interior_angle``) instead of paying
    one full map build per edge.
    """
    # dict.fromkeys dedups by the OCC shape hash (same TShape + Location)
    # while preserving first-seen order, matching edge_faces' break-per-face
    # semantics.
    return list(dict.fromkeys(_adjacent_faces(part).get(_edge_key(edge), [])))


def is_periodic_seam(part: Part, edge: Edge) -> bool:
    """True when ``edge``'s only two topological neighbours are the same face
    -- the closing seam of a periodic surface, not a boundary between two.

    OCC always parametrises a cone or cylinder's circumference to wrap rather
    than genuinely start and stop, so a bounded face cut from one needs a
    seam edge somewhere in its own wire. Where a model's boolean cuts happen
    to route that seam through the part's boundary (a bore or pocket wall
    opening through a flat face, say), it shows up in ``part.edges()`` as an
    ordinary-looking edge -- but ``_adjacent_faces`` can never find it a
    second neighbour: ``part.faces()`` visits the one real face once, and
    that face's own wire lists its own seam only once, so the dict entry the
    seam's key hashes to never accumulates a second face. ``interior_angle``
    then answers ``None`` for it (the "not shared by exactly two faces" case
    its docstring already documents) -- correctly: there genuinely is no
    second surface to take a dihedral angle against, so "unmeasurable" is the
    right answer here, not a gap in the probe.

    This checks that directly, against OCC's own edge-to-face ancestor map
    (``TopExp.MapShapesAndAncestors``), rather than inferring it from an
    edge's position, length or which face's bounding box it sits near. That
    distinction is not academic: this repo has already had a same-reasoning
    allow predicate go stale exactly that way once geometry it matched by
    position moved a few tenths of a millimetre under an unrelated redesign
    (see led_profiles' ``checks.py`` git history around its screw-seat
    predicates). A seam is a seam regardless of where the boolean cuts happen
    to have left it, so this answers the topology question once, robustly,
    for every caller that would otherwise re-derive a position heuristic.

    Not, on its own, a safety verdict. A same-face seam is *necessary*
    evidence that ``interior_angle`` cannot have measured a dihedral angle
    here, but it is not *sufficient* evidence that the edge is safe to leave
    unexplained: a genuine, reportable sliver -- the kind ``sharp_convex_edges``
    exists to surface, not hide (see its docstring) -- can satisfy this test
    too, since a real near-tangent boolean cut can itself land its seam at
    the cut. So a caller's ``allow`` predicate should combine this with its
    own scoping (location, length, which feature) and its own stated reason;
    this function only answers "is there a second surface here at all."
    """
    return periodic_seams(part)(edge)


def periodic_seams(part: Part):
    """A reusable ``is_periodic_seam``, for when one edge is not enough.

    Exactly the relationship ``solid_probe`` has to ``is_solid_at``, and for
    exactly the same reason: ``is_periodic_seam`` rebuilds OCC's entire
    edge-to-face ancestor map on every call, which is right for the handful of
    edges a boolean-built part needs it for and quadratic anywhere a large
    fraction of the edges are seams. ``spiral_vase_lampshade`` is a lofted shell
    of 168 faces in which 166 of the 334 edges are the periodic closure of a
    loft patch, so asking one at a time means rebuilding a 168-face map 166
    times; built once, the whole survey costs a second.

    Returns a predicate over a single ``Edge``, which is the shape an ``allow``
    entry wants. Everything ``is_periodic_seam``'s docstring says about what the
    answer does and does not license applies unchanged -- in particular that it
    is necessary but not sufficient evidence that an edge is safe to leave
    unexplained, so a caller should still scope it and still state its reason.
    """
    from OCP.TopAbs import TopAbs_EDGE, TopAbs_FACE  # ty: ignore[unresolved-import]
    from OCP.TopExp import TopExp  # ty: ignore[unresolved-import]
    from OCP.TopTools import TopTools_IndexedDataMapOfShapeListOfShape  # ty: ignore[unresolved-import]

    ancestors = TopTools_IndexedDataMapOfShapeListOfShape()
    TopExp.MapShapesAndAncestors_s(part.wrapped, TopAbs_EDGE, TopAbs_FACE, ancestors)

    def is_seam(edge: Edge) -> bool:
        if not ancestors.Contains(edge.wrapped):
            return False
        faces = list(ancestors.FindFromKey(edge.wrapped))
        return len(faces) == 2 and faces[0].IsSame(faces[1])

    return is_seam


def is_vertical_seam(part: Part, edge: Edge, tolerance: float = 1e-6) -> bool:
    """True when ``edge`` is a straight, purely-vertical LINE whose only two
    topological neighbours are the same face -- a bore or wall's own periodic
    closing seam, not a boundary between two surfaces.

    This is the scoped form of ``is_periodic_seam`` that every bore/wall
    seam allow-predicate in this repo used to re-derive for itself, line for
    line: the edge must be a LINE, its bounding box must be degenerate in X
    and Y (the edge runs straight down at one (x, y), which is exactly what
    a cylinder or cone wall's seam looks like once a boolean cut has trimmed
    it open), and then ``is_periodic_seam`` answers the topology question
    against OCC's own edge-to-face ancestor map. The two scoping checks
    exist because the bare ``is_periodic_seam`` would just as happily claim
    a seam that happens to land on a genuine near-tangent sliver elsewhere
    on the part -- the confusion this repo has already had once (see its
    docstring) -- and the repo's five one-off copies of exactly this
    predicate (door_latch, lens_cap, round_snap_box, drill_storage's bore
    family, and led_profiles' bolt-bore site) are why it finally earns a
    home here. Two other led_profiles predicates --
    ``_is_periodic_bore_seam`` and ``_is_stand_periodic_seam`` -- share
    only the broad shape (LINE, some bounding-box guard, then
    ``is_periodic_seam``), not this exact predicate: their guards differ
    from the X/Y degeneracy this one enforces (a Z-position/span window at
    CAP_T, and none at all), so they stay inline rather than migrate.

    Not, on its own, a safety verdict. ``is_periodic_seam``'s caveat applies
    unchanged: this is *necessary* evidence that ``interior_angle`` could not
    have measured a dihedral angle here, not *sufficient* evidence that the
    edge is safe to leave unexplained -- a real near-tangent boolean cut can
    itself land its seam at a vertical line. So a caller's ``allow`` entry
    should still scope this to its own feature (which bore or wall, that
    nothing cuts sideways into it) and still state its own reason; this
    predicate only answers "is this the periodic closing seam of a purely
    vertical surface".

    ``tolerance`` is the allowance on the X/Y bounding-box degeneracy. 1e-6
    absorbs the floating noise of an actually-vertical line. A larger value
    is a deliberate loosening for walls that are merely *near*-vertical:
    led_profiles' bolt-bore site passes 0.05 because those bores' walls are
    not perfectly plumb, and the tighter default would reject their seams.
    A value smaller than 1e-6 is not meaningful: it would reject a genuinely
    vertical edge whose bbox measures a few ulps off zero.

    One-edge form only, deliberately -- exactly the relationship
    ``is_periodic_seam`` has to ``periodic_seams``, and no batch variant is
    built because none of this repo's callers audits vertical seams in bulk
    (the lofted-shell case that motivated ``periodic_seams`` has no
    X/Y-degenerate seams to batch). If one ever appears, add
    ``vertical_seams(part, tolerance)`` next to this the same way.
    """
    if edge.geom_type != GeomType.LINE:
        return False
    bb = edge.bounding_box()
    if bb.size.X > tolerance or bb.size.Y > tolerance:
        return False
    return is_periodic_seam(part, edge)


def is_flush_seam(part: Part, edge) -> bool:
    """A convex edge that measures a genuine, exact 180 deg -- not a corner at
    all, but a residual split where a boolean subtract's own tool boundary
    landed exactly flush with a face the part already had.

    The drill family's ``base.key_slot_tool`` is the worked example: its mouth
    fillet is anchored tangent to the cavity wall on purpose (see that
    function's docstring for why: a fillet offset *short* of the wall is
    always a tighter, worse angle than the plain corner it replaces, so full
    tangency is the only geometry that actually helps). OCC leaves the
    coincident plane as two abutting faces rather than silently merging them
    into one -- ``Part.clean()`` does not remove it either, checked rather
    than assumed -- so the edge between them survives into ``part.edges()``
    with nothing on either side of it.

    ``sharp_convex_edges`` reports such an edge as *unclassifiable*, not
    sharp: its own probe cannot find an "inside" wedge here because there
    genuinely isn't one to find, which is a different claim from "could not
    be measured". This confirms that claim independently of the probe, by a
    direct measurement rather than an absence of one: both adjacent faces'
    normals, sampled at three points along the edge (not just its centre, so
    a seam that is only *partly* flush cannot slip through), are
    antiparallel -- the same plane, seen from both sides.
    """
    if edge.geom_type != GeomType.LINE:
        return False
    faces = adjacent_faces(part, edge)
    if len(faces) != 2:
        return False
    for t in (0.1, 0.5, 0.9):
        at = edge.position_at(t)
        try:
            n0 = faces[0].normal_at(at)
            n1 = faces[1].normal_at(at)
        except Exception:
            return False
        if n0.get_angle(n1) < 180 - 1e-3:
            return False
    return True


class SharpEdgeSurvey(NamedTuple):
    """The result of one ``sharp_convex_edges`` pass: two claims, not one.

    ``sharp`` is "measured, and the angle is too tight" -- the house rule's
    original complaint. ``unclassifiable`` is a different claim entirely: "the
    angle could not be measured at all," which covers a genuine sliver, a
    non-manifold or self-seaming edge, or a face OCC would not hand a normal
    to (see ``_outward``'s and ``interior_angle``'s docstrings for what drives
    a ``None``). An edge nobody can classify is not evidence that it is safe --
    it is evidence that this check has nothing to say about it -- so it gets
    reported instead of merged into, or silently dropped from, ``sharp``.

    Deliberately a plain ``NamedTuple`` with no ``__bool__``/``__len__``
    override, which matters for a reason beyond style: a 2-item tuple is
    always truthy and always ``len() == 2``, so a caller written against the
    *old* ``ShapeList`` contract -- ``bad = sharp_convex_edges(part); if not
    bad: ...`` -- does not quietly keep working with half the picture. ``not
    bad`` is now always ``False`` (a tuple with items in it is truthy), so
    that caller's "no sharp edges" assertion starts failing outright the
    moment this lands, on every run, until it is rewritten against
    ``.sharp``/``.unclassifiable``. A loud, permanent failure is the point:
    the alternative -- keeping some backward-compatible ``ShapeList``-like
    shape so old call sites "still work" -- is exactly the false-green this
    type exists to rule out, just moved one level up. Every caller in this
    repo has already been migrated (see the ones listed in
    ``sharp_convex_edges``'s own docstring); this guard is for whichever one
    gets missed.
    """

    sharp: ShapeList[Edge]
    unclassifiable: ShapeList[Edge]


def sharp_convex_edges(
    part: Part,
    min_length: float = 2.0,
    max_interior: float = 120.0,
    allow: tuple = (),
) -> SharpEdgeSurvey:
    """Convex edges sharp enough to want breaking, that carry no treatment --
    plus every edge this check could not even measure.

    Returns a ``SharpEdgeSurvey(sharp, unclassifiable)``. Every caller must read
    both fields; see that type's docstring for why a caller that only reads
    ``.sharp`` cannot silently pass. The house rule -- chamfer horizontal
    edges, fillet vertical ones -- turned into something a check can fail on.
    An edge lands in ``sharp`` when both of:

    * it is at least ``min_length`` long, so slivers and tangency seams do not
      drown the signal;
    * its interior angle is at most ``max_interior``. That one test carries the
      convexity too, since a concave edge measures over 180. The default of 120
      reports a raw 90 deg corner and passes the ~135 an existing 45 deg chamfer
      leaves behind, so a treated part comes back clean.

    An edge lands in ``unclassifiable`` instead when it clears the same
    ``min_length``/``allow`` gates but ``interior_angle`` answers ``None`` --
    it could not be measured, not that it was measured and found blunt. Both
    lists are subject to the *same* ``min_length`` and ``allow`` filtering,
    for the same reason in both directions: ``min_length`` existing to keep a
    tangency seam's harmless residue out of ``sharp`` applies just as much to
    ``unclassifiable`` -- a sub-``min_length`` sliver nobody can measure is
    exactly the kind of noise that rule was written to drop, on either side of
    the sharp/unmeasurable line. This was checked against a real case rather
    than assumed: led_profiles.endcap has four short (<1.6 mm) ``None`` edges
    at 45 deg screw-seat cone tails/gland lead-in seams that ``min_length``
    quietly excludes from ``unclassifiable`` the same way it always excluded
    their sharp counterparts, and three longer (>=8 mm) ``None`` edges -- the
    periodic seam of a bore or pocket wall opening through a flat face, where
    OCC's own topology explorer confirms the edge's two "adjacent" faces are
    literally the same ``TopoDS_Face`` (there is no second surface to take a
    dihedral angle against) -- that do clear ``min_length`` and do need a
    named reason; see led_profiles' ``checks.py`` for that entry.

    ``allow`` holds ``(predicate, reason)`` pairs, applied identically to both
    buckets before classification -- a predicate matches an edge's geometry,
    not its angle, so it does not care which list would otherwise have caught
    it. Anything a predicate matches is excluded from both, and the reason is
    what the caller prints. Real parts have legitimate square edges --
    sealing faces, thread flanks, heat-set insert mouths -- and legitimate
    unmeasurable ones too -- a genuine sliver at the tail of a tangent cut,
    the seam of a periodic bore wall. The point of the pair is that each one
    has to be *stated* rather than merely not noticed, for either bucket.
    That is the whole difference between this check and the prose rule it
    replaces, and it is also why ``unclassifiable`` is reported at all
    instead of quietly folded into ``sharp`` or dropped: "measured and sharp"
    and "could not be measured" are different claims, and an ``allow`` entry
    for one is not evidence about the other.

    Callers, all migrated to the two-field return: ``door_latch.py``,
    ``lens_cap.py``, ``round_snap_box.py``, ``drill_storage/checks.py``,
    ``drill_storage/hex/checks.py``, and ``led_profiles/checks.py`` (through
    its own ``_check_sharp_edges`` wrapper, which applies its allow-list
    triples to both fields).
    """
    inside = solid_probe(part)
    adjacency = _adjacent_faces(part)  # built once; it is the expensive part
    sharp = []
    unclassifiable = []
    for edge in part.edges():  # ty: ignore[invalid-argument-type]
        if edge.length < min_length:
            continue
        if any(predicate(edge) for predicate, _ in allow):
            continue
        angle = interior_angle(
            part, edge, faces=adjacency.get(_edge_key(edge)), probe=inside
        )
        if angle is None:
            unclassifiable.append(edge)
        elif angle <= max_interior:
            sharp.append(edge)
    return SharpEdgeSurvey(ShapeList(sharp), ShapeList(unclassifiable))


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
    """Collects pass/fail lines so one run shows every problem, not just the first.

    Alongside the human-readable ``lines``/``failures`` this has always kept,
    every ``check()`` call is also recorded in ``entries`` -- one dict per
    assertion with its section, name, result and (free-text) measured/expected
    detail. That is what lets ``uv run check <name> --json <path>`` (see
    ``check.py``) hand back the whole run as structured data instead of only
    its pass/fail lines, an idea adapted from cyberchitta/cad-khana's
    ``mechanism.json`` (Apache-2.0) -- see ``check.py`` for the attribution.
    ``entries`` is purely additive: nothing that reads ``lines``, ``failures``
    or ``render()`` sees a difference.
    """

    def __init__(self) -> None:
        self.failures: list[str] = []
        self.lines: list[str] = []
        self.entries: list[dict] = []
        self._section: str = ""

    def check(self, ok: bool, label: str, detail: str = "") -> None:
        mark = "PASS" if ok else "FAIL"
        self.lines.append(f"  [{mark}] {label}{(' -- ' + detail) if detail else ''}")
        self.entries.append(
            {"section": self._section, "name": label, "passed": ok, "detail": detail}
        )
        if not ok:
            self.failures.append(label)

    def section(self, title: str) -> None:
        self.lines.append(f"\n{title}")
        self._section = title

    def render(self) -> str:
        tail = (
            f"\n{len(self.failures)} FAILED: {', '.join(self.failures)}"
            if self.failures
            else "\nall checks passed"
        )
        return "\n".join(self.lines) + tail

    def to_dict(self) -> dict:
        """The same run as JSON-serialisable data: every assertion, in order.

        ``passed``/``failed`` are counts over ``entries``, not over ``lines``,
        so they match ``entries`` exactly even though ``failures`` (kept for
        backward compatibility) records only failing labels.
        """
        return {
            "assertions": self.entries,
            "passed": sum(1 for e in self.entries if e["passed"]),
            "failed": sum(1 for e in self.entries if not e["passed"]),
        }
