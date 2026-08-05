"""Build every model in the roster and export it to STL + STEP.

There is no model list here. The roster is ``tessellate_models.MODELS`` and this
builds straight from it, so CI, the website and this command can never disagree
about what a model is -- which is exactly what the two hand-kept lists that used
to live here did whenever one of them was updated alone.

To add a model to the build, add its name to ``MODELS``. Nothing else.
"""

from export import export
from tessellate_models import MODELS, get_part


def main() -> None:
    """Build and export every model to STL + STEP."""
    print(f"Building {len(MODELS)} models...")
    for name in MODELS:
        export(get_part(name), name, step=True)
    print("Done!")


if __name__ == "__main__":
    main()
