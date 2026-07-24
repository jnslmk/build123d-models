"""MCP server exposing the sketch editor to an agent.

Every tool is *stateless with respect to the process*: it loads the sketch from
``sketches/<name>.sketch.json``, mutates it through ``sketch.commands``, re-solves,
and saves. Disk is the shared state, so a human editing the same file (canvas or
by hand) and the agent driving these tools see each other's edits -- that is the
whole point: one document, two editors.

Run standalone with ``uv run sketch-mcp`` (stdio transport). It is registered for
this repo in ``.mcp.json`` so Claude Code can call the tools directly.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from sketch import codegen, commands
from sketch.model import Sketch
from sketch.solver import solve

mcp = FastMCP("sketch", instructions=__doc__)


# -- helpers --------------------------------------------------------------


def _snapshot(sk: Sketch) -> dict[str, Any]:
    """The full document plus a fresh solve report -- what the agent reads back."""
    report = solve(sk)
    sk.save()
    return {
        "name": sk.name,
        "plane": sk.plane,
        "extrude": sk.extrude,
        "points": sk.points,
        "segments": sk.segments,
        "circles": sk.circles,
        "constraints": sk.constraints,
        "solve": {
            "status": report.status,
            "dof": report.dof,
            "residual": report.residual,
            "satisfied": report.satisfied,
        },
    }


def _load(name: str) -> Sketch:
    return Sketch.load(name)


# -- read tools -----------------------------------------------------------


@mcp.tool()
def list_sketches() -> list[str]:
    """List the names of all sketches saved in this repo."""
    return Sketch.list_names()


@mcp.tool()
def get_sketch(name: str) -> dict[str, Any]:
    """Return the full sketch document (points, segments, circles, constraints) and
    its current solve status (degrees of freedom, residual). Call this first to see
    element ids before referencing them in other tools."""
    return _snapshot(_load(name))


@mcp.tool()
def create_sketch(name: str, plane: str = "XY", extrude: float = 3.0) -> dict[str, Any]:
    """Create a new, empty sketch called ``name`` on ``plane`` (XY/XZ/YZ), to be
    extruded ``extrude`` mm. Fails loudly if a sketch with that name already exists."""
    if name in Sketch.list_names():
        raise ValueError(
            f"sketch {name!r} already exists; use get_sketch to inspect it"
        )
    sk = Sketch(name=name, plane=plane, extrude=float(extrude))
    return _snapshot(sk)


# -- geometry tools -------------------------------------------------------


@mcp.tool()
def add_point(name: str, x: float, y: float, fixed: bool = False) -> dict[str, Any]:
    """Add a point at (x, y) mm. ``fixed`` points are anchors the solver never moves.
    Returns the new point id under ``created`` plus the updated document."""
    sk = _load(name)
    pid = commands.add_point(sk, x, y, fixed)
    return {"created": pid, **_snapshot(sk)}


@mcp.tool()
def add_line(name: str, x0: float, y0: float, x1: float, y1: float) -> dict[str, Any]:
    """Add a line segment between two coordinates. Endpoints that coincide with an
    existing point are welded onto it (so shared corners stay connected)."""
    sk = _load(name)
    sid = commands.add_line(sk, x0, y0, x1, y1)
    return {"created": sid, **_snapshot(sk)}


@mcp.tool()
def add_rect(name: str, x: float, y: float, w: float, h: float) -> dict[str, Any]:
    """Add a rectangle with lower-left corner at (x, y) and size w x h mm. Creates 4
    points + 4 segments and the horizontal/vertical constraints that keep it square;
    the lower-left corner is fixed as an anchor. Returns all created ids under
    ``created``."""
    sk = _load(name)
    ids = commands.add_rect(sk, x, y, w, h)
    return {"created": ids, **_snapshot(sk)}


@mcp.tool()
def add_circle(
    name: str, cx: float, cy: float, r: float, role: str = "hole"
) -> dict[str, Any]:
    """Add a circle of radius ``r`` at (cx, cy). ``role`` is ``hole`` (subtracted from
    the part) or ``boss`` (added). Returns the new circle id."""
    sk = _load(name)
    cid = commands.add_circle(sk, cx, cy, r, role)
    return {"created": cid, **_snapshot(sk)}


@mcp.tool()
def move_point(name: str, point_id: str, x: float, y: float) -> dict[str, Any]:
    """Move a point to (x, y) and re-solve. Equivalent to a human dragging it: the
    grabbed point goes where asked and the constraint solver adjusts the rest."""
    sk = _load(name)
    was_fixed = sk.point(point_id).get("fixed", False)
    commands.move(sk, point_id, x, y)
    commands.set_fixed(sk, point_id, True)  # pin at target while the rest re-solves
    snap = _snapshot(sk)
    commands.set_fixed(sk, point_id, was_fixed)  # restore original anchoring
    sk.save()
    return snap


@mcp.tool()
def set_fixed(name: str, point_id: str, fixed: bool = True) -> dict[str, Any]:
    """Anchor (``fixed=true``) or release a point. Anchored points are never moved by
    the solver -- use them to pin a sketch down so it is well-constrained."""
    sk = _load(name)
    commands.set_fixed(sk, point_id, fixed)
    return _snapshot(sk)


@mcp.tool()
def delete_element(name: str, element_id: str) -> dict[str, Any]:
    """Delete any element by id. Deleting a point cascades to the segments, circles,
    and constraints that referenced it. Returns the removed ids under ``removed``."""
    sk = _load(name)
    removed = commands.delete(sk, element_id)
    return {"removed": removed, **_snapshot(sk)}


# -- constraint tools -----------------------------------------------------


@mcp.tool()
def add_constraint(
    name: str,
    type: str,
    a: str | None = None,
    b: str | None = None,
    s1: str | None = None,
    s2: str | None = None,
    seg: str | None = None,
    p: str | None = None,
    circle: str | None = None,
    d: float | None = None,
    r: float | None = None,
) -> dict[str, Any]:
    """Add a geometric constraint and re-solve. ``type`` is one of:

    - ``horizontal`` / ``vertical`` -- pass ``seg``
    - ``coincident`` -- pass ``a``, ``b`` (two point ids)
    - ``distance`` -- pass ``a``, ``b``, ``d`` (target mm)
    - ``parallel`` / ``perpendicular`` / ``equal`` -- pass ``s1``, ``s2`` (two segment ids)
    - ``point_on`` -- pass ``p`` (point), ``seg`` (segment)
    - ``radius`` -- pass ``circle``, ``r`` (target mm)

    Watch the returned ``solve.status``: ``well-constrained`` is the goal;
    ``conflicting`` means the constraints can't all be met."""
    sk = _load(name)
    refs = {
        k: v
        for k, v in dict(
            a=a, b=b, s1=s1, s2=s2, seg=seg, p=p, circle=circle, d=d, r=r
        ).items()
        if v is not None
    }
    kid = commands.add_constraint(sk, type, **refs)
    return {"created": kid, **_snapshot(sk)}


@mcp.tool()
def set_dimension(name: str, constraint_id: str, value: float) -> dict[str, Any]:
    """Change the target of a ``distance`` or ``radius`` constraint to ``value`` mm and
    re-solve. This is how you make a parametric edit (e.g. 'make the slot 4 mm longer'
    = set its distance constraint to the new length)."""
    sk = _load(name)
    commands.set_dimension(sk, constraint_id, value)
    return _snapshot(sk)


# -- output tools ---------------------------------------------------------


@mcp.tool()
def generate_model(name: str) -> dict[str, Any]:
    """Re-solve and write ``models/<name>.py`` (a real build123d ``create()`` module).
    Returns the file path and the generated source. After this the user can run
    ``uv run show <name>`` to see the 3D part."""
    sk = _load(name)
    solve(sk)
    sk.save()
    path = codegen.write_model(sk)
    return {
        "path": str(path.relative_to(path.parents[1])),
        "source": codegen.generate(sk),
        "show_command": f"uv run show {sk.name}",
    }


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
