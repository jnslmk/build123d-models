"""Emit a build123d model file from a solved sketch.

The output follows this repo's convention: a module with a ``create()`` function
that returns a ``Part`` in builder mode (see ``models/cube.py``,
``models/slotted_plate.py``). Segments are chained into a closed profile and
extruded; ``hole`` circles are subtracted, ``boss`` circles added.

The generated file is *derived*: a header points editors back at the
``.sketch.json`` so nobody hand-edits geometry that the next solve will overwrite.
"""

from __future__ import annotations

from pathlib import Path

from sketch.model import REPO_ROOT, Sketch

MODELS_DIR = REPO_ROOT / "models"


def _fmt(v: float) -> str:
    """Format a coordinate: trim to 3 dp, drop trailing zeros, avoid '-0.0'."""
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _ordered_loop(sk: Sketch) -> list[str] | None:
    """Return point ids in traversal order if the segments form ONE closed loop.

    Returns ``None`` when the segments don't form a single closed cycle (open
    profile, multiple loops, or a branch) -- the caller then falls back to
    emitting individual lines.
    """
    if not sk.segments:
        return None
    adj: dict[str, list[str]] = {}
    for s in sk.segments:
        adj.setdefault(s["p"], []).append(s["q"])
        adj.setdefault(s["q"], []).append(s["p"])
    # every vertex in a simple closed loop has degree exactly 2
    if any(len(neighbours) != 2 for neighbours in adj.values()):
        return None
    start = sk.segments[0]["p"]
    order = [start]
    prev, cur = None, start
    while True:
        a, b = adj[cur]
        nxt = a if a != prev else b
        if nxt == start:
            break
        if nxt in order:  # ran into a sub-cycle -> not a single simple loop
            return None
        order.append(nxt)
        prev, cur = cur, nxt
    if len(order) != len(adj):  # didn't visit every vertex -> multiple loops
        return None
    return order


def generate(sk: Sketch) -> str:
    """Return the Python source for ``models/<name>.py``."""
    P = sk.point
    plane = sk.plane if sk.plane.startswith("Plane.") else f"Plane.{sk.plane}"

    # The body is emitted first so the import block can name exactly what it
    # uses -- an unused import would fail the repo's ruff check on every codegen.
    body: list[str] = []
    w = body.append
    used = {"BuildPart", "BuildSketch", "Part", "Plane", "extrude"}

    w("def create() -> Part:")
    w(f'    """Extruded profile generated from the {sk.name!r} sketch."""')
    w("    with BuildPart() as builder:")
    w(f"        with BuildSketch({plane}):")

    loop = _ordered_loop(sk)
    if loop:
        used |= {"BuildLine", "Polyline", "make_face"}
        w("            with BuildLine():")
        coords = ", ".join(
            f"({_fmt(P(pid)['x'])}, {_fmt(P(pid)['y'])})" for pid in loop
        )
        w(f"                Polyline({coords}, close=True)")
        w("            make_face()")
    elif sk.segments:
        used |= {"BuildLine", "Line", "make_face"}
        w("            with BuildLine():")
        for s in sk.segments:
            a, b = P(s["p"]), P(s["q"])
            w(
                f"                Line(({_fmt(a['x'])}, {_fmt(a['y'])}), "
                f"({_fmt(b['x'])}, {_fmt(b['y'])}))"
            )
        w(
            "            make_face()  # NOTE: open/multi-loop profile may not close cleanly"
        )

    if sk.circles:
        used |= {"Circle", "Locations", "Mode"}
    for c in sk.circles:
        centre = P(c["c"])
        mode = "Mode.SUBTRACT" if c.get("role") == "hole" else "Mode.ADD"
        w(f"            with Locations(({_fmt(centre['x'])}, {_fmt(centre['y'])})):")
        w(f"                Circle({_fmt(c['r'])}, mode={mode})")

    w("        extrude(amount=EXTRUDE)")
    w("    return builder.part")
    w("")

    head: list[str] = []
    h = head.append
    h(f'"""Generated from sketches/{sk.name}.sketch.json by the sketch editor.')
    h("")
    h("Do not hand-edit the geometry here -- edit the sketch (canvas or MCP) and")
    h("re-run `uv run sketch codegen " + sk.name + "`; this file is overwritten.")
    h('"""')
    h("")
    h("from build123d import (")
    for name in sorted(used):
        h(f"    {name},")
    h(")")
    h("")
    h(f"EXTRUDE = {_fmt(sk.extrude)}  # mm")
    h("")
    h("")
    return "\n".join(head + body)


def write_model(sk: Sketch, path: Path | None = None) -> Path:
    """Write the generated source to ``models/<name>.py`` and return the path."""
    target = path or (MODELS_DIR / f"{sk.name}.py")
    target.write_text(generate(sk))
    return target
