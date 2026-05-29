import argparse
import importlib
import json
from pathlib import Path

from ocp_tessellate.convert import to_ocpgroup, tessellate_group
from ocp_tessellate.utils import numpy_to_buffer_json

EXPORTS = Path("exports")

MODELS = [
    "cube",
    "door_latch",
    "lens_cap",
    "satellite_led",
    "slotted_plate",
    "spiral_vase_lampshade",
    "wall_bar_lamp",
]


def get_part(name: str):
    return importlib.import_module(f"models.{name}").create()


def tessellate_to_json(name: str) -> dict:
    part = get_part(name)
    group, instances = to_ocpgroup(part)
    meshed_instances, shapes, _mapping = tessellate_group(group, instances)
    return numpy_to_buffer_json({"instances": meshed_instances, "shapes": shapes})


def write_model(name: str) -> None:
    EXPORTS.mkdir(exist_ok=True)
    data = tessellate_to_json(name)
    out_path = EXPORTS / f"{name}_shapes.json"
    out_path.write_text(json.dumps(data))
    print(f"Tessellated {name} → {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Tessellate models for three-cad-viewer"
    )
    parser.add_argument("model", nargs="?", default=None, help="Model name or 'all'")
    args = parser.parse_args()

    if args.model and args.model != "all":
        targets = [args.model]
    else:
        targets = MODELS

    for name in targets:
        write_model(name)

    print("Done!")


if __name__ == "__main__":
    main()
