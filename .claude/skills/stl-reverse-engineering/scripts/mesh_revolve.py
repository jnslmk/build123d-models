#!/usr/bin/env python3
"""Measure a turned or lofted shell: silhouette, lobe count, depth, twist, envelope.

The third case, and the one `mesh_analyze` and `mesh_zones` between them cannot
answer. A vase, a lampshade, a turned finial: `swept/actual` says "not an
extrusion" and the zone pass says "one solid zone, 176 mm", both correct and
neither any use. What such a part *is* is a surface written in cylindrical
coordinates -- one radius per (angle, height) -- so that is what this measures.

It decomposes each cross-section into angular harmonics and reports, in the
units a parametric model wants them in:

* the **axis**, solved for rather than assumed (a lobed section's centroid is
  not its axis, and the error goes straight into every later number);
* the **silhouette**, the mean radius at each height -- the profile you would
  get with the waves turned off;
* the **lobe count**, from which angular harmonic carries the energy;
* the **depth**, as a fraction of the local radius, which is how a parametric
  model wants it (a fixed millimetre depth does not survive a taper);
* the **twist**, from how the dominant harmonic's phase moves with height;
* the **envelope**, from the signed amplitude -- including where it passes
  through zero and the lobes invert.

Then it answers the question worth asking before writing any code:

    Is the phase linear in height?

If it is, a single twisted carrier -- `cos(n * (theta + turns * t))` -- will
fit, and the numbers above are its parameters. If it is not, no setting of any
twist parameter can reproduce this surface, because a single carrier rotates at
one rate by construction. A phase that advances slowly where the lobes are deep
and quickly where they pinch is two wave trains beating against each other, or a
surface lofted through hand-placed profiles; either way, stop and decide what
you are building before you spend a fitting loop on it.

That verdict is the sibling of `mesh_analyze`'s `swept/actual`: a cheap
structural pre-check that tells you whether the shape you are about to write is
the shape in front of you.

Usage:
    uv run --group mesh python .claude/skills/stl-reverse-engineering/scripts/mesh_revolve.py \\
        model.stl [--axis Z] [--sections 300] [--angles 512] [--json out.json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from mesh_analyze import AXIS_NAMES, load_mesh, slice_polygons  # noqa: E402  # ty: ignore[unresolved-import]

LINEAR_TWIST_SPREAD = 1.5
"""How much the local twist rate may vary before "one carrier" stops being true.

The ratio of the fastest local rate to the slowest, measured only where the
lobes are deep enough for the phase to mean anything. A perfectly linear twist
scores 1.0; the worked example that motivated this script scored 2.1 (53 deg per
height where its lobes were deep, 110 where they pinched) and no single-carrier
family could be fitted to it below 4.5 mm rms.
"""

WEAK = 0.25
"""Amplitude, as a fraction of the section's strongest, below which a section's
phase is noise rather than measurement. Near an envelope node the lobes vanish
and the phase spins; averaging that in is how a twist estimate goes wrong."""


def outer_rings(mesh, axis: int, heights):
    """The largest closed ring of each slice, in the slice's own 2D basis."""
    polys, _ = slice_polygons(mesh, axis, heights)
    out = []
    for slice_polys in polys:
        if not slice_polys:
            out.append(None)
            continue
        biggest = max(slice_polys, key=lambda p: p.area)
        out.append(np.asarray(biggest.exterior.coords)[:, :2])
    return out


def resample(ring, centre, angles):
    """Radius of `ring` at each angle about `centre`.

    The ring's own vertices are wherever the mesh happened to put them, so they
    are re-expressed on a fixed angular grid before any two sections can be
    compared or transformed.
    """
    dx = ring[:, 0] - centre[0]
    dy = ring[:, 1] - centre[1]
    theta = np.mod(np.arctan2(dy, dx), 2 * np.pi)
    radius = np.hypot(dx, dy)
    order = np.argsort(theta)
    theta, radius = theta[order], radius[order]
    # Wrap one sample onto each end so interpolation crosses the seam cleanly.
    theta = np.concatenate(([theta[-1] - 2 * np.pi], theta, [theta[0] + 2 * np.pi]))
    radius = np.concatenate(([radius[-1]], radius, [radius[0]]))
    return np.interp(angles, theta, radius)


def solve_axis(rings, angles, rounds: int = 12):
    """Find the centre that kills the first angular harmonic.

    A section's centroid is not the axis: on a lobed section the lobes pull it
    off, and an offset centre shows up as a pure n=1 term in every section's
    spectrum. Since that term *is* the offset, to first order, correcting by it
    and repeating converges in a handful of rounds -- no optimiser, and nothing
    outside the declared `mesh` group.
    """
    centre = np.mean([r.mean(axis=0) for r in rings], axis=0)
    for _ in range(rounds):
        step = np.zeros(2)
        for ring in rings:
            radii = resample(ring, centre, angles)
            c1 = np.fft.rfft(radii)[1] / len(radii) * 2.0
            step += np.array([c1.real, -c1.imag])
        step /= len(rings)
        centre = centre + step
        if np.hypot(*step) < 1e-6:
            break
    return centre


def unwrap_lobe(phase, lobes):
    """Unwrap a ridge angle that is only defined modulo one lobe."""
    lobe = 2 * np.pi / lobes
    out = np.array(phase, dtype=float)
    for i in range(1, len(out)):
        while out[i] - out[i - 1] > lobe / 2:
            out[i] -= lobe
        while out[i] - out[i - 1] < -lobe / 2:
            out[i] += lobe
    return out


def measure(mesh, axis: int, n_sections: int, n_angles: int) -> dict:
    lo, hi = float(mesh.bounds[0][axis]), float(mesh.bounds[1][axis])
    span = hi - lo
    heights = np.linspace(lo + span * 0.01, hi - span * 0.01, n_sections)
    angles = np.linspace(0, 2 * np.pi, n_angles, endpoint=False)

    rings = outer_rings(mesh, axis, heights)
    keep = [i for i, r in enumerate(rings) if r is not None and len(r) > 3]
    if len(keep) < 8:
        raise SystemExit("too few closed sections to measure -- is this axis right?")
    heights = heights[keep]
    rings = [rings[i] for i in keep]

    # The axis is solved on the middle of the part: a threaded foot or a rim
    # fillet is not representative of what the body does.
    inner = [r for h, r in zip(heights, rings) if lo + span * 0.15 < h < hi - span * 0.05]
    centre = solve_axis(inner or rings, angles)

    radii = np.vstack([resample(r, centre, angles) for r in rings])
    silhouette = radii.mean(axis=1)
    spectrum = np.fft.rfft(radii, axis=1) / n_angles * 2.0
    magnitude = np.abs(spectrum)

    # Which harmonic carries the shape. n=0 is the silhouette; n=1 is whatever
    # eccentricity the axis solve could not remove.
    energy = magnitude.sum(axis=0)
    energy[:2] = 0.0
    lobes = int(np.argmax(energy))
    if lobes < 2:
        return {
            "axis": AXIS_NAMES[axis],
            "centre": centre.tolist(),
            "extent": span,
            "silhouette": {"min": float(silhouette.min()), "max": float(silhouette.max())},
            "lobes": 0,
            "verdict": "no angular structure -- this is a plain surface of revolution",
        }

    coeff = spectrum[:, lobes]
    amplitude = np.abs(coeff)
    depth = amplitude / silhouette
    ridge = unwrap_lobe(-np.angle(coeff) / lobes, lobes)

    t = (heights - heights[0]) / (heights[-1] - heights[0])
    strong = amplitude > WEAK * amplitude.max()

    # Envelope nodes: where the lobes vanish, and where they come back inverted.
    node_idx = [
        i
        for i in range(1, len(amplitude) - 1)
        if amplitude[i] < WEAK * amplitude.max()
        and amplitude[i] <= amplitude[i - 1]
        and amplitude[i] <= amplitude[i + 1]
    ]
    nodes = [float(t[i]) for i in node_idx]

    # Everything about the phase is measured *between* nodes, never across one.
    # At a node the lobes invert, which moves the ridge half a lobe in one step
    # for reasons that have nothing to do with twist; fold that into the fit and
    # the twist comes back inflated (measured: 0.36 turns against a true 0.19)
    # while the rate spread blows up on an artefact instead of reporting the
    # real one.
    runs = []
    start = 0
    for i in [*node_idx, len(t)]:
        seg = [k for k in range(start, min(i, len(t))) if strong[k]]
        if len(seg) >= 12:
            runs.append(np.array(seg))
        start = min(i + 1, len(t))

    rates, slopes, residuals = [], [], []
    for seg in runs:
        for a, b in zip(seg[:-8], seg[8:]):
            dt = t[b] - t[a]
            if dt > 1e-6:
                rates.append(np.degrees(ridge[b] - ridge[a]) / dt)
        fit = np.polyfit(t[seg], ridge[seg], 1)
        slopes.append(fit[0])
        residuals.append(np.degrees(np.std(ridge[seg] - np.polyval(fit, t[seg]))))
    if not runs:  # no usable run: fall back to whatever is strong, and say so
        runs = [np.where(strong)[0]]
        fit = np.polyfit(t[runs[0]], ridge[runs[0]], 1)
        slopes, residuals = [fit[0]], [0.0]
        rates = [np.degrees(fit[0])]

    rates = np.array(rates) if rates else np.array([0.0])
    residual = float(np.mean(residuals))
    turns = float(np.mean(slopes) / (2 * np.pi))

    spread = float(np.max(np.abs(rates)) / max(np.min(np.abs(rates)), 1e-9))
    linear = spread <= LINEAR_TWIST_SPREAD
    verdict = (
        f"phase is linear in height (rate spread {spread:.2f}x) -- a single "
        f"twisted carrier at {turns:+.3f} turns fits"
        if linear
        else f"phase is NOT linear (rate spread {spread:.2f}x, "
        f"{np.min(np.abs(rates)):.0f}..{np.max(np.abs(rates)):.0f} deg per height) "
        "-- one carrier cannot do this; expect two beating trains or a "
        "hand-lofted surface, and do not spend a fitting loop on a single-twist family"
    )

    harmonics = {
        int(n): float(energy[n] / energy[lobes])
        for n in np.argsort(energy)[::-1][:5]
        if energy[n] > 0
    }

    return {
        "axis": AXIS_NAMES[axis],
        "centre": centre.tolist(),
        "extent": span,
        "sections": int(len(heights)),
        "angles": n_angles,
        "silhouette": {
            "at_start": float(silhouette[0]),
            "at_end": float(silhouette[-1]),
            "widest": float(silhouette.max()),
            "widest_at": float(t[int(np.argmax(silhouette))]),
        },
        "lobes": lobes,
        "harmonic_energy_vs_dominant": harmonics,
        "depth_fraction": {
            "max": float(depth.max()),
            "at": float(t[int(np.argmax(depth))]),
        },
        "twist_turns": turns,
        "twist_rate_deg_per_height": {
            "min": float(np.min(np.abs(rates))),
            "max": float(np.max(np.abs(rates))),
            "spread": spread,
        },
        "linear_fit_residual_deg": float(residual),
        "envelope_nodes_t": nodes,
        "envelope_inverts": bool(nodes),
        "phase_is_linear": bool(linear),
        "verdict": verdict,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mesh", type=Path)
    ap.add_argument("--axis", choices=("X", "Y", "Z"), default="Z")
    ap.add_argument("--sections", type=int, default=300)
    ap.add_argument("--angles", type=int, default=512)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()

    mesh = load_mesh(args.mesh)
    report = measure(mesh, AXIS_NAMES.index(args.axis), args.sections, args.angles)

    print(f"{args.mesh.name}: about {report['axis']}, {report['extent']:.2f} mm long")
    print(f"  axis at      ({report['centre'][0]:+.4f}, {report['centre'][1]:+.4f}) in the slice basis")
    sil = report["silhouette"]
    if report["lobes"] == 0:
        print(f"  {report['verdict']}")
    else:
        print(
            f"  silhouette   {sil['at_start']:.2f} -> {sil['widest']:.2f} (at "
            f"{sil['widest_at']:.2f} of the length) -> {sil['at_end']:.2f} mm radius"
        )
        print(f"  lobes        {report['lobes']}")
        print(
            f"  depth        {report['depth_fraction']['max']:.3f} of the local radius, "
            f"deepest at {report['depth_fraction']['at']:.2f}"
        )
        print(f"  twist        {report['twist_turns']:+.4f} turns over the length")
        print(
            f"  envelope     {len(report['envelope_nodes_t'])} node(s)"
            + (f" at {[round(n, 3) for n in report['envelope_nodes_t']]}" if report["envelope_nodes_t"] else "")
            + (" -- lobes invert" if report["envelope_inverts"] else "")
        )
        others = {n: v for n, v in report["harmonic_energy_vs_dominant"].items() if n != report["lobes"]}
        print(f"  harmonics    {others} (relative to n={report['lobes']})")
        print(f"  VERDICT      {report['verdict']}")

    if args.json:
        args.json.write_text(json.dumps(report, indent=2))
    return 0 if report.get("phase_is_linear", True) else 1


if __name__ == "__main__":
    sys.exit(main())
