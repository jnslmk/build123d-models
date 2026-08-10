"""The top disc: the lid of the outer cable channel.

    uv run show cable_spool.cover
    uv run export cable_spool.cover      # the STL to print
    uv run check cable_spool

The same disc again, with the plainest bore of the three -- a circle, sliding
fit on the hub tube, and nothing else. That plainness *is* the mechanism: with
no relief pockets the bore cannot pass the hub's four guide ribs, so the cover
comes to rest on the rib tops at `COVER_Z` and leaves the second 7 mm channel
under it. The middle disc, cut from the same plate with four pockets added,
sails past the same ribs to `MIDDLE_Z`.

Its rim chamfer is the shallowest of the three (1 mm against the base's 3 mm),
which is the source model's proportioning and worth keeping: nothing rubs over
this edge, and a deeper chamfer would only take material out from under the
clips' upper jaws.

Print flat, chamfered face up, no supports.
"""

from __future__ import annotations

from build123d import BuildPart, BuildSketch, Circle, Mode, Part, Sketch, add, extrude

from . import config as cfg
from .plate import bore_mouth_chamfers, plate_body


def bore_sketch() -> Sketch:
    """A plain circular bore, sliding fit on the hub tube."""
    with BuildSketch() as sk:
        Circle(cfg.MIDDLE_BORE_R)
    return sk.sketch


def create() -> Part:
    """The cover disc, in print pose on `z = 0`."""
    bore = bore_sketch()
    lower, upper = bore_mouth_chamfers(bore)
    with BuildPart() as part:
        add(plate_body(cfg.COVER_RIM_CHAMFER_W))
        with BuildSketch():
            add(bore)
        extrude(amount=cfg.PLATE_T, mode=Mode.SUBTRACT)
        add(lower, mode=Mode.SUBTRACT)
        add(upper, mode=Mode.SUBTRACT)
    return part.part
