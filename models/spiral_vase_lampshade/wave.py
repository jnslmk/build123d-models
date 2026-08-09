"""The wave field: pure maths, no build123d, no solids.

Everything the shade's surface is comes from one scalar function of two
variables -- ``outer_radius(shade, theta, t)``, the distance from the axis at
angle ``theta`` and normalised height ``t``. ``__init__`` turns it into
cross-sections and lofts them; ``checks`` re-derives probe points from it. That
split is the point: the surface can be reasoned about, differentiated and
asserted against without a CAD kernel in the room.

The radius is a silhouette with a wave wrapped round it::

    r(theta, t) = R(t) + wave_depth * R(t) * fade(t) * W(theta, t)
    W(theta, t) = cos(lobes * (theta + 2*pi * twist_turns * t)) * E(t)
    E(t)        = (1 - pinch) + pinch * cos(2*pi * wave_cycles * t + env_phase)

Three factors, three jobs, and they are separable on purpose -- each slider on
the website moves exactly one of them:

* **The carrier** ``cos(lobes * (theta + ...))`` puts ``lobes`` crests round the
  section. The ``twist_turns * t`` inside it rotates that pattern with height,
  which is what makes a crest a leaning ridge rather than a vertical flute.
  Note where the ``lobes`` factor sits: *outside* the twist term, so a crest
  traces ``theta = -2*pi * twist_turns * t`` and ``twist_turns`` is turns of the
  pattern, full stop. Written the other way round -- ``cos(lobes * theta + 2*pi
  * twist_turns * t)``, which is the more obvious way to type it -- the same
  number would mean turns divided by the lobe count, so changing ``lobes``
  would silently change the twist as well.
* **The envelope** ``E(t)`` breathes the depth up and down the body, and it is
  the reason the shade reads as stacked petals rather than a fluted column.
  Note it is *signed*: at ``pinch > 0.5`` the envelope goes negative over part
  of the height, and where it does, crest and valley swap. The pinch bands
  where it passes through zero are the seams the lobes appear to overlap along.
* **The fade** ``fade(t)`` is a one-sided smoothstep over ``FADE_IN``, and it
  exists to make the bottom of the body an exact circle -- see ``config.FADE_IN``.

``pinch`` is the one knob worth understanding before turning: at 0 the envelope
is constant and the shade is a plain twisted flute, at 1 the lobes pinch away to
nothing at each node and come back inverted. The reference sits near 0.65 --
enough for the petals to read, not so much that the body is throttled at every
node.
"""

from __future__ import annotations

from math import atan2, cos, degrees, hypot, pi, sin

from .config import FADE_IN, Shade


def smoothstep(u: float) -> float:
    """Raised cosine on [0, 1], flat at both ends.

    Used for both the silhouette and the fade because zero slope at the joins
    is what keeps this a curve rather than a set of cones: it makes the profile
    C1 across ``bulge_at`` and, at ``t = 0``, lets the body leave the collar
    tangent to it instead of kinking away.
    """
    if u <= 0.0:
        return 0.0
    if u >= 1.0:
        return 1.0
    return (1.0 - cos(pi * u)) / 2.0


def silhouette(shade: Shade, t: float) -> float:
    """Radius of the wave-free profile at normalised body height ``t``.

    Two smoothsteps meeting at ``bulge_at``: base to widest, widest to mouth.
    Because both are flat where they meet, the widest point is a genuine
    tangent maximum rather than a corner, and because the lower one is flat at
    ``t = 0`` the profile leaves the collar vertically.
    """
    r_base, r_max = shade.base_r, shade.max_dia / 2
    r_mouth, b = shade.mouth_dia / 2, shade.bulge_at
    if t <= b:
        return r_base + (r_max - r_base) * smoothstep(t / b)
    return r_max + (r_mouth - r_max) * smoothstep((t - b) / (1.0 - b))


def envelope(shade: Shade, t: float) -> float:
    """How deep the waves run at height ``t``; signed, so crests can invert.

    ``env_phase`` slides the whole breathing pattern up and down the body, and it
    earns its place from the reference mesh rather than from taste: measured,
    that shade's lobe depth is *zero* where it leaves the collar, deepest around
    a third of the way up, back through zero at half height and deepest again at
    three-quarters. With the phase pinned at 0 the envelope is forced to an
    antinode at ``t = 0``, which puts a node a quarter of the way up instead --
    the pattern in the wrong place by half a lobe of height, and no other slider
    can move it back.
    """
    return (1.0 - shade.pinch) + shade.pinch * cos(
        2 * pi * shade.wave_cycles * t + shade.env_phase
    )


def fade(t: float) -> float:
    """Zero at the foot of the body, one above ``FADE_IN``."""
    return smoothstep(t / FADE_IN)


def crest_angle(shade: Shade, t: float) -> float:
    """Angle where the *carrier* peaks at height ``t`` -- the ridge line's phase.

    This is the carrier alone, so it is the right thing to reason about when
    the question is where the twist has put the pattern, and the wrong thing to
    probe with. Where the envelope is negative the surface's actual maximum is
    half a lobe away from here; see ``ridge_angle``.
    """
    return -2 * pi * shade.twist_turns * t


def ridge_angle(shade: Shade, t: float) -> float:
    """Angle where the surface actually stands furthest out at height ``t``.

    ``crest_angle`` plus the envelope's sign, and the distinction is not
    pedantic: above ``pinch = 0.5`` the envelope spends part of the height
    negative, and everywhere it does, the carrier's peak is the bottom of a
    valley. Anything looking for material -- every probe in ``checks`` -- has to
    ask for this one, or it will go hunting for a ridge in the one place the
    surface is guaranteed not to have one.
    """
    base = crest_angle(shade, t)
    return base if envelope(shade, t) >= 0 else base + pi / shade.lobes


def field(shade: Shade, theta: float, t: float) -> float:
    """The wave itself, in [-1, 1]: carrier times envelope."""
    carrier = cos(shade.lobes * (theta - crest_angle(shade, t)))
    return carrier * envelope(shade, t)


def amplitude(shade: Shade, t: float) -> float:
    """Wave amplitude in millimetres at height ``t``.

    A fraction of the *local* radius rather than a fixed depth, so the lobes
    stay in proportion as the silhouette swells and narrows instead of
    swamping the mouth.
    """
    return shade.wave_depth * silhouette(shade, t) * fade(t)


def outer_radius(shade: Shade, theta: float, t: float) -> float:
    """Distance from the axis to the outer surface. The whole model, really."""
    return silhouette(shade, t) + amplitude(shade, t) * field(shade, theta, t)


def d_radius_d_theta(shade: Shade, theta: float, t: float) -> float:
    """``d r / d theta``, analytically.

    Only the carrier depends on ``theta``, so this is the carrier's derivative
    carried through the same amplitude and envelope. Analytic rather than
    finite-differenced because it decides the direction of the wall offset at
    every one of the ~4000 points in a build, and a differenced normal wobbles
    exactly where the surface is most curved.
    """
    d_carrier = -shade.lobes * sin(shade.lobes * (theta - crest_angle(shade, t)))
    return amplitude(shade, t) * envelope(shade, t) * d_carrier


def outer_point(shade: Shade, theta: float, t: float) -> tuple[float, float]:
    """Cartesian point on the outer surface, in the plane of its section."""
    r = outer_radius(shade, theta, t)
    return (r * cos(theta), r * sin(theta))


def outward_normal(shade: Shade, theta: float, t: float) -> tuple[float, float]:
    """Unit outward normal of the cross-section curve at ``theta``.

    *Not* the radial direction, and the difference is the whole reason the wall
    is honest. On a section with 20 mm of lobe on a 79 mm radius the surface
    leans up to ~30 degrees away from radial; offsetting radially by 0.8 mm
    would leave a wall of 0.8 * cos(30) = 0.69 mm on the flanks while the
    checks, measuring radially too, cheerfully reported 0.8.
    """
    r = outer_radius(shade, theta, t)
    dr = d_radius_d_theta(shade, theta, t)
    tx = dr * cos(theta) - r * sin(theta)
    ty = dr * sin(theta) + r * cos(theta)
    length = hypot(tx, ty)
    return (ty / length, -tx / length)


def inner_point(
    shade: Shade, theta: float, t: float, wall: float
) -> tuple[float, float]:
    """The outer point pushed ``wall`` along the inward normal.

    A true 2D offset of the section curve, which is also what a vase-mode
    slicer's single perimeter follows: one bead per layer, laid on the XY
    outline. ``Shade.of`` clamps ``wave_depth`` so this offset cannot cross
    itself -- see ``config._max_wave_depth``.
    """
    x, y = outer_point(shade, theta, t)
    nx, ny = outward_normal(shade, theta, t)
    return (x - wall * nx, y - wall * ny)


def overhang_angle(shade: Shade, theta: float, t: float, step: float = 1e-3) -> float:
    """Degrees the outer surface leans away from vertical at (theta, t).

    Positive means overhanging -- the surface growing outward as it rises, so
    each layer is laid partly on air. Vase mode has no supports and no
    perimeters to bridge from, so this is the number that decides whether a
    given set of sliders prints at all rather than merely renders.

    Measured along the surface's own outward lean (``dr/dz``) at fixed
    ``theta``, which is the direction a printed bead is unsupported in; the
    twist makes the true steepest ascent slightly steeper still, and the
    tolerance in ``checks`` allows for that.
    """
    lo, hi = max(0.0, t - step), min(1.0, t + step)
    dz = (hi - lo) * shade.body_h
    if dz <= 0.0:
        return 0.0
    dr = outer_radius(shade, theta, hi) - outer_radius(shade, theta, lo)
    return degrees(atan2(dr, dz))
