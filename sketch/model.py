"""The sketch document: geometry + constraints, and JSON (de)serialisation.

The document is deliberately flat and id-addressable so that both the MCP tools
and a canvas UI can reference any element by a stable string id. Coordinates are
in millimetres; the sketch is drawn on ``plane`` and extruded ``extrude`` mm.

Entity kinds
------------
* ``points``    -- ``{id, x, y, fixed}``. The only things the solver moves.
* ``segments``  -- ``{id, p, q}`` straight line between two point ids.
* ``circles``   -- ``{id, c, r, role}`` centre point id + radius; role ``hole``
                   (subtract) or ``boss`` (add).
* ``constraints`` -- see ``sketch.solver`` for the residual each type contributes.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
SKETCH_DIR = REPO_ROOT / "sketches"

# Constraint types the solver understands, with the element ids each one carries.
# Used for validation so a bad command fails loudly instead of silently no-op-ing.
CONSTRAINT_SPECS: dict[str, tuple[str, ...]] = {
    "horizontal": ("seg",),
    "vertical": ("seg",),
    "coincident": ("a", "b"),
    "distance": ("a", "b"),  # + numeric "d"
    "parallel": ("s1", "s2"),
    "perpendicular": ("s1", "s2"),
    "equal": ("s1", "s2"),
    "point_on": ("p", "seg"),
    "radius": ("circle",),  # + numeric "r"
}


@dataclass
class Sketch:
    """A mutable sketch document. IDs are unique across the whole document."""

    name: str = "untitled"
    plane: str = "XY"
    extrude: float = 3.0
    points: list[dict[str, Any]] = field(default_factory=list)
    segments: list[dict[str, Any]] = field(default_factory=list)
    circles: list[dict[str, Any]] = field(default_factory=list)
    constraints: list[dict[str, Any]] = field(default_factory=list)
    _counter: int = 0

    # -- id allocation ----------------------------------------------------
    def new_id(self, prefix: str) -> str:
        """Return a fresh unique id like ``p7`` that is not already in use."""
        while True:
            self._counter += 1
            candidate = f"{prefix}{self._counter}"
            if candidate not in self._all_ids():
                return candidate

    def _all_ids(self) -> set[str]:
        out: set[str] = set()
        for bucket in (self.points, self.segments, self.circles, self.constraints):
            out.update(e["id"] for e in bucket)
        return out

    # -- lookups ----------------------------------------------------------
    def point(self, pid: str) -> dict[str, Any]:
        for p in self.points:
            if p["id"] == pid:
                return p
        raise KeyError(f"no point {pid!r}")

    def segment(self, sid: str) -> dict[str, Any]:
        for s in self.segments:
            if s["id"] == sid:
                return s
        raise KeyError(f"no segment {sid!r}")

    def find(self, eid: str) -> tuple[str, dict[str, Any]]:
        """Return ``(bucket_name, element)`` for any id, else raise KeyError."""
        for bucket_name, bucket in (
            ("points", self.points),
            ("segments", self.segments),
            ("circles", self.circles),
            ("constraints", self.constraints),
        ):
            for e in bucket:
                if e["id"] == eid:
                    return bucket_name, e
        raise KeyError(f"no element {eid!r}")

    def has(self, eid: str) -> bool:
        return eid in self._all_ids()

    # -- serialisation ----------------------------------------------------
    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "plane": self.plane,
            "extrude": self.extrude,
            "points": self.points,
            "segments": self.segments,
            "circles": self.circles,
            "constraints": self.constraints,
            "_counter": self._counter,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Sketch:
        sk = cls(
            name=data.get("name", "untitled"),
            plane=data.get("plane", "XY"),
            extrude=float(data.get("extrude", 3.0)),
            points=list(data.get("points", [])),
            segments=list(data.get("segments", [])),
            circles=list(data.get("circles", [])),
            constraints=list(data.get("constraints", [])),
        )
        # Rebuild the counter so freshly allocated ids never collide with loaded ones.
        max_n = data.get("_counter", 0)
        for eid in sk._all_ids():
            digits = "".join(ch for ch in eid if ch.isdigit())
            if digits:
                max_n = max(max_n, int(digits))
        sk._counter = max_n
        return sk

    # -- disk -------------------------------------------------------------
    @staticmethod
    def path_for(name: str) -> Path:
        return SKETCH_DIR / f"{name}.sketch.json"

    def save(self, path: Path | None = None) -> Path:
        target = path or self.path_for(self.name)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.to_dict(), indent=2) + "\n")
        return target

    @classmethod
    def load(cls, name: str) -> Sketch:
        path = cls.path_for(name)
        if not path.exists():
            raise FileNotFoundError(f"no sketch {name!r} at {path}")
        return cls.from_dict(json.loads(path.read_text()))

    @classmethod
    def list_names(cls) -> list[str]:
        if not SKETCH_DIR.exists():
            return []
        return sorted(
            p.name[: -len(".sketch.json")] for p in SKETCH_DIR.glob("*.sketch.json")
        )
