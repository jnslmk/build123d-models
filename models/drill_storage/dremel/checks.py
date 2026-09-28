"""Physical gate for the seated Dremel parts and cover tool clearance.

A cover deliberately driven 2 mm below its seat overlaps the base by 483 mm³;
the nominal pose has zero overlap. The overlap assertion was exercised against
both shapes before this gate was added.
"""

from models.lib.checks import Report, is_solid_at
from models.lib.edges import as_part
from . import config as c, create


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
        and not is_solid_at(cover, 0, 0, tip_z + 9.9)
        and is_solid_at(cover, 0, 0, tip_z + 11),
        "50 mm tool clears the solid PETG roof",
        f"tool tip z={tip_z:.1f}",
    )
    return report


def main() -> None:
    report = run()
    print(report.render())
    if report.failures:
        raise SystemExit(1)
