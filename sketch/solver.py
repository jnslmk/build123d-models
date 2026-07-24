"""A small geometric constraint solver (points only).

The only free variables are the ``(x, y)`` of non-``fixed`` points. Each
constraint contributes one or more scalar *residuals* that are zero when the
constraint is satisfied. We minimise the sum of squared residuals with a
Levenberg-Marquardt (damped Gauss-Newton) loop and a finite-difference
Jacobian -- no numpy, which keeps the dependency surface of this repo unchanged.

Sketches here are small (tens of points), so an O(vars x residuals) dense solve
per iteration is comfortably fast. Radii are *not* solved; a ``radius``
constraint sets a circle's ``r`` directly (see ``sketch.commands``).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from sketch.model import Sketch


@dataclass
class SolveReport:
    """Outcome of a solve, surfaced to the UI/agent as a degrees-of-freedom read."""

    residual: float  # RMS residual after solving; ~0 means all constraints met
    dof: int  # free vars - residual count: >0 under-, 0 well-, <0 over-constrained
    iterations: int
    satisfied: bool  # residual below tolerance
    status: str  # "well-constrained" | "under-constrained" | "conflicting" ...

    def summary(self) -> str:
        return f"{self.status} (dof={self.dof}, residual={self.residual:.4g})"


# -- residual assembly ----------------------------------------------------


def _free_points(sk: Sketch) -> list[dict]:
    return [p for p in sk.points if not p.get("fixed")]


def _residuals(sk: Sketch) -> list[float]:
    """Flatten every constraint into a list of scalar residuals (0 = satisfied)."""
    r: list[float] = []
    P = sk.point

    def seg_dir(sid: str) -> tuple[float, float, float]:
        s = sk.segment(sid)
        a, b = P(s["p"]), P(s["q"])
        dx, dy = b["x"] - a["x"], b["y"] - a["y"]
        length = math.hypot(dx, dy) or 1e-9
        return dx, dy, length

    for c in sk.constraints:
        t = c["type"]
        if t == "horizontal":
            s = sk.segment(c["seg"])
            r.append(P(s["p"])["y"] - P(s["q"])["y"])
        elif t == "vertical":
            s = sk.segment(c["seg"])
            r.append(P(s["p"])["x"] - P(s["q"])["x"])
        elif t == "coincident":
            a, b = P(c["a"]), P(c["b"])
            r.append(a["x"] - b["x"])
            r.append(a["y"] - b["y"])
        elif t == "distance":
            a, b = P(c["a"]), P(c["b"])
            r.append(math.hypot(a["x"] - b["x"], a["y"] - b["y"]) - float(c["d"]))
        elif t == "parallel":
            dx1, dy1, l1 = seg_dir(c["s1"])
            dx2, dy2, l2 = seg_dir(c["s2"])
            r.append((dx1 * dy2 - dy1 * dx2) / (l1 * l2))  # normalised cross product
        elif t == "perpendicular":
            dx1, dy1, l1 = seg_dir(c["s1"])
            dx2, dy2, l2 = seg_dir(c["s2"])
            r.append((dx1 * dx2 + dy1 * dy2) / (l1 * l2))  # normalised dot product
        elif t == "equal":
            _, _, l1 = seg_dir(c["s1"])
            _, _, l2 = seg_dir(c["s2"])
            r.append(l1 - l2)
        elif t == "point_on":
            s = sk.segment(c["seg"])
            a, b, p = P(s["p"]), P(s["q"]), P(c["p"])
            dx, dy = b["x"] - a["x"], b["y"] - a["y"]
            length = math.hypot(dx, dy) or 1e-9
            # signed distance of p from the infinite line through a,b
            r.append(((p["x"] - a["x"]) * dy - (p["y"] - a["y"]) * dx) / length)
        # radius is applied directly to circle.r by commands, not solved here.
    return r


def _residual_count(sk: Sketch) -> int:
    return len(_residuals(sk))


# -- tiny dense linear algebra -------------------------------------------


def _solve_linear(A: list[list[float]], b: list[float]) -> list[float]:
    """Solve ``A x = b`` by Gaussian elimination with partial pivoting."""
    n = len(b)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(M[r][col]))
        if abs(M[pivot][col]) < 1e-12:
            continue  # singular column; leave this variable unchanged
        M[col], M[pivot] = M[pivot], M[col]
        piv = M[col][col]
        for r in range(n):
            if r == col:
                continue
            factor = M[r][col] / piv
            if factor:
                for k in range(col, n + 1):
                    M[r][k] -= factor * M[col][k]
    return [M[i][n] / M[i][i] if abs(M[i][i]) > 1e-12 else 0.0 for i in range(n)]


# -- the LM loop ----------------------------------------------------------


def solve(sk: Sketch, iterations: int = 60, tol: float = 1e-7) -> SolveReport:
    """Run the solver in place, moving free points to satisfy the constraints."""
    free = _free_points(sk)
    n = 2 * len(free)
    nres = _residual_count(sk)

    def dof_report(res_rms: float, iters: int) -> SolveReport:
        dof = n - nres
        satisfied = res_rms < 1e-4
        if not satisfied:
            status = "conflicting"  # constraints can't all be met (over-/inconsistent)
        elif dof > 0:
            status = "under-constrained"
        elif dof < 0:
            status = "over-constrained (redundant)"
        else:
            status = "well-constrained"
        return SolveReport(res_rms, dof, iters, satisfied, status)

    if n == 0 or nres == 0:
        res = _residuals(sk)
        rms = math.sqrt(sum(v * v for v in res) / len(res)) if res else 0.0
        return dof_report(rms, 0)

    def get_x() -> list[float]:
        x: list[float] = []
        for p in free:
            x.extend((p["x"], p["y"]))
        return x

    def set_x(x: list[float]) -> None:
        for i, p in enumerate(free):
            p["x"], p["y"] = x[2 * i], x[2 * i + 1]

    def rms(res: list[float]) -> float:
        return math.sqrt(sum(v * v for v in res) / len(res)) if res else 0.0

    lam = 1e-3
    x = get_x()
    res = _residuals(sk)
    cost = rms(res)
    iters = 0
    for iters in range(1, iterations + 1):
        m = len(res)
        # Finite-difference Jacobian J (m x n).
        J = [[0.0] * n for _ in range(m)]
        eps = 1e-6
        for j in range(n):
            x[j] += eps
            set_x(x)
            rp = _residuals(sk)
            x[j] -= eps
            for i in range(m):
                J[i][j] = (rp[i] - res[i]) / eps
        set_x(x)
        # Normal equations: (JtJ + lam*I) dx = -Jt r
        JtJ = [
            [sum(J[k][i] * J[k][j] for k in range(m)) for j in range(n)]
            for i in range(n)
        ]
        Jtr = [sum(J[k][i] * res[k] for k in range(m)) for i in range(n)]
        for i in range(n):
            JtJ[i][i] += lam * (JtJ[i][i] + 1.0)
        dx = _solve_linear(JtJ, [-v for v in Jtr])

        trial = [x[i] + dx[i] for i in range(n)]
        set_x(trial)
        new_res = _residuals(sk)
        new_cost = rms(new_res)
        if new_cost < cost:  # accept step, ease damping toward Gauss-Newton
            x, res, cost = trial, new_res, new_cost
            lam = max(lam * 0.5, 1e-9)
            if cost < tol or (cost < 1e-6 and max(abs(d) for d in dx) < 1e-9):
                break
        else:  # reject, increase damping toward gradient descent
            set_x(x)
            lam = min(lam * 4.0, 1e6)
            if lam >= 1e6:
                break
    set_x(x)
    return dof_report(cost, iters)
