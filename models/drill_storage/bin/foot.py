"""Common full/half Gridfinity foot layout for the bin and its stackable lid."""

from models.lib.gridfinity import GRID


def cell_layout(
    grid: float, half_base: bool, partial_on_positive: bool
) -> list[tuple[float, float]]:
    """Return ``(cell fraction, centred position)`` along one grid axis."""
    if grid < 0.5 or grid * 2 != round(grid * 2):
        raise ValueError("grid dimensions must be positive multiples of half a cell")
    if half_base:
        cells = [0.5] * round(grid * 2)
    else:
        full = int(grid)
        cells = [1.0] * full
        if grid != full:
            if partial_on_positive:
                cells.append(0.5)
            else:
                cells.insert(0, 0.5)
    cursor = -grid * GRID / 2
    result = []
    for size in cells:
        result.append((size, cursor + size * GRID / 2))
        cursor += size * GRID
    return result
