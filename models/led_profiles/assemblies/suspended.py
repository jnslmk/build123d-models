"""One lamp hung from two eye feet -- the common case, overhead.

    uv run show led_profiles.assemblies.suspended
    uv run export led_profiles.assemblies.suspended

The eye feet do not go at the ends. They go at the Bessel points, which is
what keeps a 1.5 m stick reading as a straight line rather than a sag between
two hooks -- see ``bessel_points``.
"""

from __future__ import annotations

from build123d import Compound, Part, Pos

from models.lib.edges import as_part

from .. import config as c
from .. import feet as feet_mod
from .. import mount_config as m
from .. import strap as strap_mod
from ..assembly import PARAMS, parts as lamp_parts

# Airy/Bessel points: the two-point support that levels a simply-supported
# beam's ends with its own midspan sag -- the standard way to rest or hang a
# long, floppy thing (an optical flat, a surveyor's staff) without visible
# droop at the tips.
BESSEL_FRACTION = 0.2203


def bessel_points(length: float = c.LENGTH) -> tuple[float, float]:
    """The two support x's along the tube -- where the eye bolts actually hang."""
    span = BESSEL_FRACTION * length
    return span, length - span


def _foot_and_straps(support_x: float, tag: str) -> list[Part]:
    """An eye foot centred on ``support_x``, plus its two straps.

    ``feet.seated``/``strap.seated`` both take the cradle's *near end*, but
    the actual hang point -- the eye-bolt holes -- sits at the cradle's own
    mid (``mount_config.CRADLE_LEN / 2``), so the near end is back-solved from
    the support point rather than the other way round.
    """
    near_end = support_x - m.CRADLE_LEN / 2
    parts: list[Part] = [feet_mod.seated(near_end)]
    for station in m.STRAP_STATIONS:
        strap = as_part(
            Pos(0, 0, -m.TUBE_UNDER_Z) * strap_mod.seated(near_end + station)
        )
        parts.append(strap_mod.labelled(strap, tag))
    return parts


def create_suspended(length: float = c.LENGTH) -> Compound:
    """One lamp hung from two eye feet at the Bessel points, straps fitted."""
    x1, x2 = bessel_points(length)
    children = [
        *lamp_parts(length),
        *_foot_and_straps(x1, "near"),
        *_foot_and_straps(x2, "far"),
    ]
    assembly = Compound(children=children)
    assembly.label = f"suspended lamp ({length:.0f} mm, Bessel points)"
    return assembly


def create(length: float = c.LENGTH) -> Compound:
    """Entry point for ``uv run show led_profiles.assemblies.suspended``."""
    return create_suspended(length)


__all__ = [
    "BESSEL_FRACTION",
    "PARAMS",
    "bessel_points",
    "create",
    "create_suspended",
]
