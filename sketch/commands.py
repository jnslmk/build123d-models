"""The single mutation API for a sketch.

Every edit -- whether it originates from the agent (MCP) or a human (canvas UI /
JSON) -- goes through one of these functions. Keeping one command surface is what
makes "the agent and the human edit the same sketch" literally true: both sides
call the same code, so an edit is an edit regardless of who made it.

Each function mutates the ``Sketch`` in place and returns the id(s) it created or
touched. Callers re-run ``solver.solve`` afterwards (``apply`` does this for you).
"""

from __future__ import annotations

import math
from typing import Any

from sketch.model import CONSTRAINT_SPECS, Sketch
from sketch.solver import SolveReport, solve


class CommandError(ValueError):
    """A command referenced a missing element or had bad arguments."""


# -- geometry -------------------------------------------------------------


def add_point(sk: Sketch, x: float, y: float, fixed: bool = False) -> str:
    pid = sk.new_id("p")
    sk.points.append({"id": pid, "x": float(x), "y": float(y), "fixed": bool(fixed)})
    return pid


def _point_at(sk: Sketch, x: float, y: float, tol: float = 1e-6) -> str:
    """Reuse an existing point at (x, y) if one is within ``tol``, else make one."""
    for p in sk.points:
        if math.hypot(p["x"] - x, p["y"] - y) <= tol:
            return p["id"]
    return add_point(sk, x, y)


def add_line(sk: Sketch, x0: float, y0: float, x1: float, y1: float) -> str:
    """Add a segment between two coordinates, welding onto coincident endpoints."""
    p = _point_at(sk, float(x0), float(y0))
    q = _point_at(sk, float(x1), float(y1))
    sid = sk.new_id("s")
    sk.segments.append({"id": sid, "p": p, "q": q})
    return sid


def add_segment(sk: Sketch, p: str, q: str) -> str:
    """Add a segment between two existing point ids."""
    for pid in (p, q):
        if pid not in {pt["id"] for pt in sk.points}:
            raise CommandError(f"no point {pid!r}")
    sid = sk.new_id("s")
    sk.segments.append({"id": sid, "p": p, "q": q})
    return sid


def add_rect(sk: Sketch, x: float, y: float, w: float, h: float) -> dict[str, Any]:
    """Add a rectangle (4 points, 4 segments) with H/V constraints keeping it square.

    ``(x, y)`` is the lower-left corner. Returns the ids of everything created so a
    caller can reference the corners/edges. The lower-left corner is fixed so the
    rectangle has a stable anchor when other constraints pull on it.
    """
    x, y, w, h = float(x), float(y), float(w), float(h)
    bl = add_point(sk, x, y, fixed=True)
    br = add_point(sk, x + w, y)
    tr = add_point(sk, x + w, y + h)
    tl = add_point(sk, x, y + h)
    bottom = add_segment(sk, bl, br)
    right = add_segment(sk, br, tr)
    top = add_segment(sk, tr, tl)
    left = add_segment(sk, tl, bl)
    ks = [
        add_constraint(sk, "horizontal", seg=bottom),
        add_constraint(sk, "horizontal", seg=top),
        add_constraint(sk, "vertical", seg=left),
        add_constraint(sk, "vertical", seg=right),
    ]
    return {
        "points": {"bl": bl, "br": br, "tr": tr, "tl": tl},
        "segments": {"bottom": bottom, "right": right, "top": top, "left": left},
        "constraints": ks,
    }


def add_circle(sk: Sketch, cx: float, cy: float, r: float, role: str = "hole") -> str:
    """Add a circle; ``role`` is ``hole`` (subtract) or ``boss`` (add)."""
    if role not in ("hole", "boss"):
        raise CommandError(f"role must be 'hole' or 'boss', got {role!r}")
    c = _point_at(sk, float(cx), float(cy))
    cid = sk.new_id("c")
    sk.circles.append({"id": cid, "c": c, "r": float(r), "role": role})
    return cid


def move(sk: Sketch, pid: str, x: float, y: float) -> None:
    """Move a point to (x, y). Used by dragging; caller re-solves afterwards."""
    p = sk.point(pid)
    p["x"], p["y"] = float(x), float(y)


def set_fixed(sk: Sketch, pid: str, fixed: bool = True) -> None:
    sk.point(pid)["fixed"] = bool(fixed)


def drag(sk: Sketch, pid: str, x: float, y: float) -> None:
    """Move a point to (x, y) as a human drag: pin it there, re-solve the rest, then
    restore its original anchoring. The grabbed point ends up exactly at the cursor
    and every constraint-linked point follows."""
    p = sk.point(pid)
    was_fixed = p.get("fixed", False)
    p["x"], p["y"] = float(x), float(y)
    p["fixed"] = True
    solve(sk)
    p["fixed"] = was_fixed


def delete(sk: Sketch, eid: str) -> list[str]:
    """Delete an element and everything that references it. Returns removed ids."""
    bucket_name, _ = sk.find(eid)
    removed: list[str] = [eid]
    if bucket_name == "points":
        # cascade: segments/circles/constraints that reference this point
        for sid in [s["id"] for s in sk.segments if pid_in_seg(s, eid)]:
            removed += delete(sk, sid)
        removed += [c["id"] for c in sk.circles if c["c"] == eid]
        sk.circles = [c for c in sk.circles if c["c"] != eid]
        sk.points = [p for p in sk.points if p["id"] != eid]
    elif bucket_name == "segments":
        sk.segments = [s for s in sk.segments if s["id"] != eid]
    elif bucket_name == "circles":
        sk.circles = [c for c in sk.circles if c["id"] != eid]
    # drop any constraint that referenced a removed element
    sk.constraints = [
        k for k in sk.constraints if not any(v in removed for v in _constraint_refs(k))
    ]
    return removed


def pid_in_seg(seg: dict, pid: str) -> bool:
    return seg["p"] == pid or seg["q"] == pid


# -- constraints ----------------------------------------------------------


def _constraint_refs(k: dict) -> list[str]:
    return [k[field] for field in CONSTRAINT_SPECS.get(k["type"], ()) if field in k]


def add_constraint(sk: Sketch, ctype: str, **refs: Any) -> str:
    """Add a constraint of ``ctype``; ``refs`` are the element ids/values it needs.

    ``distance`` needs ``a``, ``b``, ``d``; ``radius`` needs ``circle``, ``r``; the
    rest take the ids named in ``model.CONSTRAINT_SPECS``.
    """
    if ctype not in CONSTRAINT_SPECS:
        raise CommandError(f"unknown constraint type {ctype!r}")
    needed = CONSTRAINT_SPECS[ctype]
    for field in needed:
        if field not in refs:
            raise CommandError(f"{ctype} needs {field!r}")
        if not sk.has(refs[field]):
            raise CommandError(
                f"{ctype}.{field} references missing element {refs[field]!r}"
            )

    # radius is not a solved variable: apply it to the circle directly.
    if ctype == "radius":
        for c in sk.circles:
            if c["id"] == refs["circle"]:
                c["r"] = float(refs["r"])
                break
    if ctype == "distance" and "d" not in refs:
        raise CommandError("distance needs numeric 'd'")

    kid = sk.new_id("k")
    entry: dict[str, Any] = {"id": kid, "type": ctype}
    for field in needed:
        entry[field] = refs[field]
    if ctype == "distance":
        entry["d"] = float(refs["d"])
    if ctype == "radius":
        entry["r"] = float(refs["r"])
    sk.constraints.append(entry)
    return kid


def set_dimension(sk: Sketch, kid: str, value: float) -> None:
    """Change the target value of a ``distance`` or ``radius`` constraint."""
    _, k = sk.find(kid)
    if k["type"] == "distance":
        k["d"] = float(value)
    elif k["type"] == "radius":
        k["r"] = float(value)
        for c in sk.circles:
            if c["id"] == k["circle"]:
                c["r"] = float(value)
    else:
        raise CommandError(f"{kid} is a {k['type']} constraint, not a dimension")


# -- dispatch -------------------------------------------------------------

_DISPATCH = {
    "add_point": add_point,
    "add_line": add_line,
    "add_segment": add_segment,
    "add_rect": add_rect,
    "add_circle": add_circle,
    "add_constraint": add_constraint,
    "set_dimension": set_dimension,
    "move": move,
    "set_fixed": set_fixed,
    "delete": delete,
}


def apply(
    sk: Sketch, command: str, /, solve_after: bool = True, **kwargs: Any
) -> dict[str, Any]:
    """Apply one named command, re-solve, and return ``{result, report}``.

    This is the entry point the MCP server and UI both call. ``command`` is one of
    the keys in ``_DISPATCH`` (``add_line``, ``add_constraint``, ...).
    """
    if command not in _DISPATCH:
        raise CommandError(f"unknown command {command!r}; know: {sorted(_DISPATCH)}")
    result = _DISPATCH[command](sk, **kwargs)
    report: SolveReport | None = solve(sk) if solve_after else None
    return {"result": result, "report": report}
