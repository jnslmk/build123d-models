"""Vase-mode lampshade: six soft petals breathing up a 186 mm ovoid.

    uv run show spiral_vase_lampshade
    uv run export spiral_vase_lampshade     # the STL to print, in vase mode
    uv run check spiral_vase_lampshade

A shell 0.8 mm thick standing on an 83 mm collar, whose surface is one scalar
function of angle and height: ``lobes`` crests round the section, twisted a
fifth of a turn over the body, their depth breathing through one cycle so the
lobes pinch away at half height, invert, and come back overlapping the way a
wave does. ``wave.py`` is that function and the argument for every term in it;
everything here just cuts sections through it and lofts them.

The design is after JH's "Waves" Designer Lamp (Printables 1261597, CC-BY),
which is a whole lamp this repo does not otherwise attempt: no base, no thread,
no LED kit. What is reproduced is the shade, parametrically.

**Every number in it is measured, not judged.** The reference STL was
downloaded, sliced into 300 cross-sections and Fourier-decomposed, and
``config.Shade``'s defaults are what that decomposition says: six lobes, a wave
depth of 0.44 of the local radius, a 185.8 mm height, and a silhouette fitted to
the mean radius of every slice. What it is *not* is a copy of that mesh -- the
reference's ridge rotates at a rate that varies with height, which no single
twisting carrier can reproduce, so this model is the closest member of a
parametric family rather than the same surface. README.md gives the residual and
the evidence.

**Everything is a slider** (``PARAMS``, thirteen of them), and ``Shade.of()``
clamps whatever comes back, so no combination on the website can produce a part
that fails to build. Two are worth turning first: ``pinch``, which takes the
surface from a plain twisted flute to fully interlocking petals, and
``wave_depth``, which is a fraction of the local radius rather than a fixed
depth so the lobes stay in proportion as the silhouette swells.

**Printing.** Vase mode, 0.4 mm nozzle with the external extrusion width pushed
to 0.6 mm, and solid bottom layers for the first 6 mm so the collar prints as a
foot rather than a hoop -- 30 of them at a 0.2 mm layer height. It comes back
already in print pose, collar down on the bed, and it has to be printed that way
round: the mouth is the last thing to print and there is nothing to support it
on the other way up.

Two things this does *not* have, both deliberate. There is no top lip: the
version this replaces carried an inward ring at the mouth, which cannot be
printed in vase mode at all -- a spiralising single perimeter has no way to
step inward over air. And there is no thread. Meeting the reference base is a
matter of the 83 mm register plus glue, because a thread cut to a profile
nobody here has measured would be a fit this repo cannot stand behind.
"""

from __future__ import annotations

from math import cos, pi, sin

from build123d import (
    BuildLine,
    BuildPart,
    BuildSketch,
    Mode,
    Part,
    Plane,
    Spline,
    loft,
    make_face,
)

from . import config, wave
from .config import COLLAR_HOLD, DEFAULT, PARAMS, Shade
from .wave import inner_point, outer_point

__all__ = [
    "DEFAULT",
    "PARAMS",
    "Shade",
    "config",
    "create",
    "create_shade",
    "section_heights",
    "wave",
]


def _ring(outer: list[tuple[float, float]], inner: list[tuple[float, float]], z: float):
    """One annular cross-section: outer curve with the inner offset as its hole.

    Lofting *annuli* is what makes this a shell in one operation instead of two
    solids and a boolean. An 80-section outer loft is a couple of seconds; the
    same loft again for the bore and then a cut between two lofted B-rep solids
    was thirty-odd, for identical geometry. Both wires are sampled at the same
    angles in the same order so the loft pairs them the way it is drawn.
    """
    with BuildSketch(Plane.XY.offset(z)) as section:
        with BuildLine():
            Spline(outer, periodic=True)
        make_face()
        with BuildLine():
            Spline(inner, periodic=True)
        make_face(mode=Mode.SUBTRACT)
    return section.sketch


def _circle_points(shade: Shade, radius: float) -> list[tuple[float, float]]:
    """A circle sampled at the same angles as every wavy section above it.

    Sampled rather than drawn with ``Circle`` so that every section in the loft
    is the same kind of periodic spline with the same number of poles. Mixing an
    exact circle into a stack of splines is what makes a loft twist between the
    two, because the kernel has no correspondence to work from.
    """
    n = shade.facets
    return [
        (radius * cos(2 * pi * i / n), radius * sin(2 * pi * i / n)) for i in range(n)
    ]


def _collar_heights(shade: Shade) -> list[float]:
    """Where the collar's three sections sit: bed, top of chamfer, end of the hold."""
    return [0.0, shade.chamfer(), shade.collar_h * COLLAR_HOLD]


def _body_heights(shade: Shade) -> list[float]:
    """Where the body's sections sit, collar top to mouth inclusive."""
    return [
        shade.collar_h + shade.body_h * i / shade.z_sections
        for i in range(shade.z_sections + 1)
    ]


def section_heights(shade: Shade = DEFAULT) -> list[float]:
    """Every z the part has a lofted section at, in order.

    Public because those heights are also where the finished solid carries a
    horizontal seam edge between one ruled patch and the next -- an artefact of
    how the surface is built rather than a feature of the design, and something
    ``checks.check_edges`` has to be able to name precisely in order to exempt
    it from the sharp-edge rule without exempting a real edge by accident.
    """
    return _collar_heights(shade) + _body_heights(shade)


def _collar_sections(shade: Shade) -> list:
    """The foot: an 83 mm register, chamfered onto the bed, thinning to the shell.

    Three sections, and the first two carry the elephant's-foot relief as part
    of the loft rather than as an edge op afterwards. That is not timidity about
    OCC (though a chamfer on a lofted B-spline solid is exactly the all-or-
    nothing call the ``build123d-geometry-ops`` skill warns about) -- it is that
    the chamfer here *is* a change of section, so drawing it as one costs
    nothing and cannot fail.
    """
    ch = shade.chamfer()
    r_out = shade.base_r
    r_bore = r_out - shade.collar_wall
    z_bed, z_ch, z_hold = _collar_heights(shade)
    # The bed section is pulled in on *both* sides: squash spreads the outer
    # face past the register and the bore inward, and only one of those is
    # cosmetic. See config.BASE_CHAMFER for why it is a quarter of the wall.
    return [
        _ring(
            _circle_points(shade, r_out - ch), _circle_points(shade, r_bore + ch), z_bed
        ),
        _ring(_circle_points(shade, r_out), _circle_points(shade, r_bore), z_ch),
        _ring(_circle_points(shade, r_out), _circle_points(shade, r_bore), z_hold),
    ]


def _body_sections(shade: Shade) -> list:
    """The wavy shell, ``z_sections`` slices of the field from collar to mouth.

    The first of these sits exactly on top of the collar and is a true circle of
    ``base_dia`` -- ``wave.fade`` is zero at ``t = 0`` -- so the register the
    whole design is named for survives being the join between two zones.
    """
    n = shade.facets
    angles = [2 * pi * i / n for i in range(n)]
    sections = []
    for i, z in enumerate(_body_heights(shade)):
        t = i / shade.z_sections
        outer = [outer_point(shade, a, t) for a in angles]
        inner = [inner_point(shade, a, t, shade.wall) for a in angles]
        sections.append(_ring(outer, inner, z))
    return sections


def create_shade(shade: Shade = DEFAULT) -> Part:
    """The shell, in print pose: collar on the bed at z = 0, mouth up.

    One ruled loft through every section. Ruled rather than smooth for two
    reasons that point the same way: it is a third of the cost, and a smooth
    loft interpolates *through* the sections and overshoots between them, which
    on a surface made of crests means lobes 6% deeper than the field says they
    are. A chord across 2.4 mm of a surface curving no tighter than ~9 mm
    misses by well under a printed layer, and it misses on the inside, which is
    the honest direction for a shell to err.
    """
    with BuildPart() as builder:
        loft(_collar_sections(shade) + _body_sections(shade), ruled=True)
    return builder.part


def create(**params) -> Part:
    """The wave shade. Every website slider lands here, via ``Shade.of``."""
    return create_shade(Shade.of(**params))
