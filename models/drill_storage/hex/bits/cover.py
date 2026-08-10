"""The cover for the BITS box: "BITS" engraved across one face.

24 mm (42 mm / 6U assembled, ``COVER_TIP_CLEARANCE`` over the longest bit tip).
The 25 mm driver bits stand 10 mm proud of the base rim. The cover is the
family's
41.5 mm -- the cover is the pad, flush with the base.

Its snap bead is eased to ``config.BITS_SNAP_PROTRUSION`` rather than the
family's, because at 24 mm there is nothing to grip but the mouth itself and a
pinch there presses the bead *onto* the collar. Cover-only: the base's groove is
the family's, so this cover still goes onto a base already printed.

Printed pillow-top down, mouth up, in translucent PETG, no supports.
"""

from __future__ import annotations

from build123d import Part

from .. import config as c
from ..cover import create_cover, label_fit


def create() -> Part:
    """Model entry point: the BITS box's cover, in print pose."""
    cover_h = c.cover_h_for(c.BITS_BIT_LEN, c.guide_floor_z("bits"))
    size, label_z, horizontal = label_fit(cover_h, "BITS")
    cover = create_cover(
        "BITS",
        cover_h=cover_h,
        label_size=size,
        label_z=label_z,
        label_horizontal=horizontal,
        snap_protrusion=c.cover_snap_protrusion("bits"),
    )
    cover.label = "cover_bits"
    cover.color = c.COVER_COLOR
    return cover


__all__ = ["create"]
