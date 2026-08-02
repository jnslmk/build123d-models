"""Building blocks for in-code geometry assertions.

Ribs, wall gaps, blind pockets and fit clearances are invisible in a projection,
so the house rule is to verify them in code. That needs two things, and neither
is model-specific:

* ``is_solid_at`` -- ask the kernel whether a point is inside the material,
  which is the only way to see *into* a solid.
* ``Report`` -- collect every pass/fail line so one run surfaces every problem.
  A bare ``assert`` stops at the first failure and hides the rest, which turns
  a single debugging session into five.

A model's own ``checks.py`` supplies the geometry knowledge; this supplies the
instrument.
"""

from __future__ import annotations

from build123d import Part

# OCP ships no stubs for these; they resolve fine at runtime.
from OCP.BRepClass3d import BRepClass3d_SolidClassifier  # ty: ignore[unresolved-import]
from OCP.gp import gp_Pnt  # ty: ignore[unresolved-import]
from OCP.TopAbs import TopAbs_IN, TopAbs_ON  # ty: ignore[unresolved-import]

TOL = 1e-6


def is_solid_at(part: Part, x: float, y: float, z: float) -> bool:
    """True if (x, y, z) lies inside the material."""
    clf = BRepClass3d_SolidClassifier(part.wrapped)
    clf.Perform(gp_Pnt(x, y, z), TOL)
    return clf.State() in (TopAbs_IN, TopAbs_ON)


class Report:
    """Collects pass/fail lines so one run shows every problem, not just the first."""

    def __init__(self) -> None:
        self.failures: list[str] = []
        self.lines: list[str] = []

    def check(self, ok: bool, label: str, detail: str = "") -> None:
        mark = "PASS" if ok else "FAIL"
        self.lines.append(f"  [{mark}] {label}{(' -- ' + detail) if detail else ''}")
        if not ok:
            self.failures.append(label)

    def section(self, title: str) -> None:
        self.lines.append(f"\n{title}")

    def render(self) -> str:
        tail = (
            f"\n{len(self.failures)} FAILED: {', '.join(self.failures)}"
            if self.failures
            else "\nall checks passed"
        )
        return "\n".join(self.lines) + tail
