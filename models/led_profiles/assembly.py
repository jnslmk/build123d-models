"""Assembled views of one lamp's bought hardware.

``create()``          -- a full 1.5 m stick: profile + diffuser + COB strip
``create_section()``  -- a 60 mm slice of the same, for reading the cross-section
``create_extrusion()``-- the bare aluminium, re-exported for parts that need it
``create_print_layout()`` -- every printed part, in a row, in its print pose

The bought hardware here is the datum every printed part is designed against,
and the thing to interfere-check them with.
"""

from __future__ import annotations

from build123d import Compound, Part, Pos

from models.lib.edges import as_part

from . import config as c
from . import endcap as endcap_mod
from . import gland as gland_mod
from .profile import create_diffuser, create_extrusion, create_strip

# UI schema for the parametric web app. See tessellate_models.model_params().
# Only the length is worth a slider -- everything else is a measurement of a
# bought extrusion, not a choice, and lives in config.py.
PARAMS = [
    {
        "name": "length",
        "label": "Profile length (mm)",
        "type": "number",
        "min": 50.0,
        "max": 2000.0,
        "step": 10.0,
        "default": c.LENGTH,
    },
]


def hardware(length: float = c.LENGTH) -> list[Part]:
    """The bought pieces, each already in its installed place."""
    return [create_extrusion(length), *create_strip(length), create_diffuser(length)]


def parts(
    length: float = c.LENGTH, cable: bool = True, glands: bool = True
) -> list[Part]:
    """Everything in a finished lamp: bought hardware, endcaps, glands, cable.

    Two flags, each with exactly one caller, and neither is a style choice.

    ``cable`` drops the cable stubs while keeping the glands. It is for the
    triangle, where two caps face each other across a corner and their pigtails
    are a *jumper loop* living in the corner's own channel (``corner.py``'s
    docstring). A straight stub of a bend radius is the right mock for a run
    leaving a lamp into open air and the wrong one for a cable that demonstrably
    turns inside 40 mm -- there the two stubs would simply cross and report a
    foul the design already answers. The glands stay in that view, because
    clearing two of them nose to nose is what ``gland_setback`` sets the
    corner's whole geometry from.

    ``glands`` drops both. It is for ``checks.check_assembly``, which measures
    what the *mounts* have to bore for -- and with the cap flush, that is the
    tube's own stadium. A fitted gland used to hang ``corner.GLAND_DROP`` below
    the tube's underside and be outside that stadium by design; centring the
    gland on the cap took the drop to zero, and it is still checked against the
    plinth that clears it rather than against the bore.
    """
    fitted: list[Part] = []
    if glands:
        fitted = [
            *gland_mod.seated(length=length, cable=cable),
            *gland_mod.seated(at_far_end=True, length=length, cable=cable),
        ]
    return [
        *hardware(length),
        endcap_mod.seated(length=length),
        endcap_mod.seated(at_far_end=True, length=length),
        *fitted,
    ]


def create(length: float = c.LENGTH) -> Compound:
    """A whole lamp: profile, strip, diffuser and both glanded endcaps."""
    assembly = Compound(children=parts(length))
    assembly.label = f"T8 lamp ({length:.0f} mm)"
    return assembly


def create_bare(length: float = c.LENGTH) -> Compound:
    """Just the bought hardware, no endcaps -- the datum on its own."""
    assembly = Compound(children=hardware(length))
    assembly.label = f"T8 profile assembly ({length:.0f} mm)"
    return assembly


def printed_parts(angle: float = 60.0) -> list[Part]:
    """Every printed part, each already sitting in its own print pose."""
    from . import corner as corner_mod
    from . import feet as feet_mod
    from . import stand as stand_mod
    from . import strap as strap_mod
    from .endcap import create_endcap

    parts = [
        create_endcap(),
        strap_mod.create_strap(),
        corner_mod.create_corner(angle),
        stand_mod.create_stand_hub(),
        feet_mod.create_eye_foot(),
        feet_mod.create_wall_foot(),
    ]
    parts[0].label = "endcap"
    parts[1].label = "strap"
    return parts


def create_print_layout(angle: float = 60.0) -> Compound:
    """The printed parts laid out in a row, ready for the slicer.

    Exists because ``uv run export led_profiles`` exports the *assembled* view
    and writes an STL per child -- which would include the aluminium and the
    diffuser, neither of which is printed.
    """
    laid_out: list[Part] = []
    x = 0.0
    gap = 15.0
    for part in printed_parts(angle):
        bb = part.bounding_box()
        moved = as_part(Pos(x - bb.min.X, -bb.min.Y, -bb.min.Z) * part)
        moved.label = part.label
        moved.color = part.color
        laid_out.append(moved)
        x += bb.size.X + gap
    layout = Compound(children=laid_out)
    layout.label = "print layout"
    return layout


def create_section(length: float = c.SECTION_LENGTH) -> Compound:
    """A short slice of the same assembly -- the cross-section, close up.

    A 1.5 m stick renders as a line; this is what you actually look at when
    checking the channel, the screw ports or an endcap's fit.
    """
    assembly = create(length)
    assembly.label = f"T8 profile section ({length:.0f} mm)"
    return assembly
