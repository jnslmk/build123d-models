"""Physical gate for Dremel inventory, seated bores and cover tool clearance.

A cover deliberately driven 2 mm below its seat overlaps the base by 483 mm³;
the nominal pose has zero overlap. The overlap assertion was exercised against
both shapes before this gate was added.
"""

from collections import Counter
from math import cos, pi, sin

from models.drill_storage import config as family
from models.lib.checks import Report, is_solid_at
from models.lib.edges import as_part
from . import cover as cap_model
from . import config as c, create

PROBE = 0.02  # resolve the close shank sizes without sampling an OCC boundary


def run() -> Report:
    scene = create()
    shell, cartridge, cap = scene.children
    report = Report()
    report.section("Dremel 1×2 assembly")
    for name, first, second in (
        ("base / TPU insert", shell, cartridge),
        ("base / PETG cover", shell, cap),
        ("TPU insert / PETG cover", cartridge, cap),
    ):
        overlap = (first & second).volume
        report.check(overlap < 0.001, f"no {name} interference", f"{overlap:.4f} mm³")
    seated_z = cap.bounding_box().min.Z
    report.check(
        abs(seated_z - c.SEAT_Z) < 0.01,
        "cover seats on the accepted flat shoulder",
        f"rim z={seated_z:.3f}, shoulder z={c.SEAT_Z:.3f}",
    )
    cover = as_part(cap)
    tip_z = c.GUIDE_FLOOR_Z + 50
    report.check(
        not is_solid_at(cover, 0, 0, tip_z)
        and not is_solid_at(
            cover, 0, 0, cap.bounding_box().max.Z - cap_model.CAP_H - 0.1
        )
        and is_solid_at(cover, 0, 0, cap.bounding_box().max.Z - cap_model.CAP_H + 0.1),
        "50 mm tool clears the solid PETG roof",
        f"tool tip z={tip_z:.1f}",
    )

    report.section("Dremel shank inventory")
    expected_counts = {1.0: 1, 1.5: 1, 2.0: 1, 2.35: 10, 2.9: 25, 3.1: 17}
    actual_counts = Counter(nominal_d for _x, _y, nominal_d in c.BORES)
    report.check(
        actual_counts == expected_counts,
        "55 positions hold the accepted inventory and spare diameters",
        f"nominal diameter counts={dict(actual_counts)}",
    )

    report.section("Dremel seated guide, land and relief bores")
    base = as_part(shell)
    insert = as_part(cartridge)
    guide_z = (c.GUIDE_FLOOR_Z + c.CAVITY_FLOOR_Z) / 2
    land_z = c.CAVITY_FLOOR_Z + family.LAND_H / 2
    # Sample the straight relief, above its land lead-in and below its mouth.
    relief_z = (
        c.CAVITY_FLOOR_Z
        + (family.LAND_H + family.LAND_LEAD_IN + family.CART_H - family.CART_MOUTH_CH)
        / 2
    )
    directions = ((1, 0), (-1, 0), (0, 1), (0, -1))
    solid_at = report.solid_at
    for x, y, cut_d in c.CUT_BORES:
        guide_r = (cut_d + family.GUIDE_FIT) / 2
        land_r = (cut_d + family.LAND_FIT) / 2
        relief_r = (cut_d + family.RELIEF_FIT) / 2
        label = f"bore at ({x:g}, {y:g}), cut diameter {cut_d:.3f} mm"
        report.check(
            all(
                solid_at(
                    base,
                    x + r * cos(angle),
                    y + r * sin(angle),
                    z,
                )
                for r in (0.0, guide_r - PROBE)
                for angle in (i * pi / 4 for i in range(8))
                for z in (PROBE, c.GUIDE_FLOOR_Z / 2, c.GUIDE_FLOOR_Z - PROBE)
            ),
            f"{label}: entire guide floor is closed, including between the feet",
        )
        for name, part, radius, z in (
            ("ASA guide", base, guide_r, guide_z),
            ("TPU land", insert, land_r, land_z),
            ("TPU relief", insert, relief_r, relief_z),
        ):
            report.check(
                all(
                    not solid_at(
                        part, x + dx * (radius - PROBE), y + dy * (radius - PROBE), z
                    )
                    and solid_at(
                        part, x + dx * (radius + PROBE), y + dy * (radius + PROBE), z
                    )
                    for dx, dy in directions
                ),
                f"{label}: {name} has the specified radius",
                f"r={radius:.3f} mm at seated z={z:.3f}",
            )
        report.check(
            solid_at(base, x, y, c.GUIDE_FLOOR_Z - PROBE)
            and all(
                not solid_at(base, x, y, z)
                for z in (
                    c.GUIDE_FLOOR_Z + PROBE,
                    guide_z,
                    c.CAVITY_FLOOR_Z - PROBE,
                )
            ),
            f"{label}: guide is open above an intact ASA floor",
            f"floor z={c.GUIDE_FLOOR_Z:.3f}",
        )
        step_r = (land_r + relief_r) / 2
        report.check(
            all(
                solid_at(insert, x + dx * step_r, y + dy * step_r, land_z)
                and not solid_at(insert, x + dx * step_r, y + dy * step_r, relief_z)
                for dx, dy in directions
            ),
            f"{label}: short grip land is distinct from the sliding relief",
            f"diametral step={2 * (relief_r - land_r):.3f} mm",
        )
    return report


def main() -> None:
    report = run()
    print(report.render())
    if report.failures:
        raise SystemExit(1)
