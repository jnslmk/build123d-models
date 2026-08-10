"""A 180 mm spool for a coiled patch cable, and a clip that stays on it.

    uv run show cable_spool             # the whole thing, assembled
    uv run show cable_spool.base        # the printed parts, each in print pose
    uv run show cable_spool.middle
    uv run show cable_spool.cover
    uv run show cable_spool.clip
    uv run check cable_spool

Four printed parts and no hardware. Three identical 180 mm discs stack on one
hub at three heights and leave two 7.2 mm channels between them, which is
enough for about 20 m of round Cat-6 patch cable wound in two layers. The cover
twists onto the hub on a bayonet; three clips hold the stack together at the
rim.

**Where it comes from.** The three discs are a parametric reconstruction of
[Printables 27496](https://www.printables.com/model/27496-cable-spool-ethernet-cable)
by rgeissler, measured from the published STLs with the tooling in the
`stl-reverse-engineering` skill. `docs/design-notes.md` is the measurement
ledger: what was read off the mesh, what was solved from it, and where this
model deliberately departs.

**The clip is not a reconstruction.** The original's does not stay on, and the
reason is three separate design faults that each show up in the mesh --- it is
straight over a curved rim, its jaws land inboard of the disc's solid ring
where there is nothing under them, and its arms are strained to 4.4% on
assembly against PETG's 1.0%. `clip.py` carries that argument in full. The
replacement does not clamp at all: it hangs on a curved cantilever whose tooth
drops into one of the base's own windows and catches on the window wall.

**How the stack spaces itself.** One hub radius at three heights does all of
it. Below `MIDDLE_Z` it is a full collar, so the middle disc lands there. From
there to `COVER_Z` the same radius survives as four ribs, which both upper
discs' relief pockets slide past. Above `COVER_Z` it returns as a flare over a
groove, and the cover's stepped bore twists under it: drop the cover on with
its pockets over the ribs, turn it `COVER_TWIST` degrees until its tabs stop
against the flares, and it is locked down on the rib tops. No spacers, no
fasteners.
"""

from __future__ import annotations

from build123d import Compound, Pos, Rotation

from ..lib.edges import as_part
from . import base as base_mod
from . import clip as clip_mod
from . import config as cfg
from . import cover as cover_mod
from . import middle as middle_mod

# A scene, not a print job -- see tessellate_models.model_is_assembly.
IS_ASSEMBLY = True


def parts() -> list:
    """Every printed part, each already in its own print pose."""
    out = [base_mod.create(), middle_mod.create(), cover_mod.create(), clip_mod.create()]
    for part, name in zip(out, ("base", "middle", "cover", "clip")):
        part.label = name
    return out


def create() -> Compound:
    """The assembled spool: three discs on the hub, three clips on the rim."""
    base = base_mod.create()
    base.label = "base"
    middle = as_part(Pos(0.0, 0.0, cfg.MIDDLE_Z) * middle_mod.create())
    middle.label = "middle"
    cover = as_part(Pos(0.0, 0.0, cfg.COVER_Z) * cover_mod.create())
    cover.label = "cover"

    children = [base, middle, cover]
    for i, angle in enumerate(cfg.clip_angles()):
        clip = as_part(Rotation(0.0, 0.0, angle) * clip_mod.build())
        clip.label = f"clip {i + 1}"
        children.append(clip)

    spool = Compound(children=children)
    spool.label = "cable spool"
    return spool
