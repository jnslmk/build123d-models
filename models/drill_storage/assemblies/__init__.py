"""Assembly views: a holder with its tools actually in it.

Scenes, not print jobs -- each one is a model in its own right
(``uv run show drill_storage.assemblies.wood``) and each declares
``IS_ASSEMBLY = True``, so the website offers no STL for it. What you print is
the holder module next to it (``drill_storage.wood``).

They earn their place by catching interference the printed part cannot show on
its own: a drill standing in its bore is what proves the cover clears the longest
tip and that no two neighbouring bits foul each other.

| module | shows |
|---|---|
| ``wood`` | the 2-10 mm brad-point set + countersink, seated in the base, cover beside it |
"""

from .wood import create_wood_assembly

__all__ = ["create_wood_assembly"]
