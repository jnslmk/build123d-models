"""Pure dimensional layout: occupied cells and photo-qualified tool poses."""

from dataclasses import dataclass
from math import ceil, isfinite

from models.lib.gridfinity import BASE_H, GRID, HEIGHT_UNIT, PAD, TOLERANCE

from . import config as c
from . import profiles as p

BED_THICKNESS = c.WALL
SEAT_Z = BASE_H + c.WALL
RIM_Z = 2 * HEIGHT_UNIT  # Low 2U tray, not the future cover envelope.
EDGE_BREAK = 0.2
SLOT_LEAD = 0.05  # Smallest measured tooth is 1.1 mm: retain 1 mm at both mouths.
RACK_CORNER_R = 0.8
SLOT_FLOOR_RESERVE = 0.2  # Functional photo/noise reserve, NOT a fit/error bound.
SLOT_ENGAGEMENT = 2 * c.WALL  # Minimum straight tooth height above highest seat.
PREVIEW_ERROR = p.PROFILE_SIMPLIFICATION + 0.001  # Display checks only.
TOOL_START_Y = -GRID / 2 + TOLERANCE / 2 + c.WALL + c.PHOTO_END_ALLOWANCE


@dataclass(frozen=True)
class Lane:
    wrench: c.Wrench
    x: float

    @property
    def slot_width(self) -> float:
        return self.wrench.handle_thickness + c.SLOT_CLEARANCE

    def floor_z(self, station_index: int) -> float:
        return (
            SEAT_Z
            + p.HANDLE_SPANS[self.wrench.label][station_index][0]
            - SLOT_FLOOR_RESERVE
        )


@dataclass(frozen=True)
class Column:
    index: int
    cells: int
    lanes: tuple[Lane, ...]

    @property
    def x(self) -> float:
        return self.index * GRID

    @property
    def rack_top(self) -> float:
        return (
            max(lane.floor_z(i) for lane in self.lanes for i in range(2))
            + SLOT_ENGAGEMENT
            + EDGE_BREAK
        )


@dataclass(frozen=True)
class Layout:
    columns: tuple[Column, ...]

    @property
    def occupied(self) -> frozenset[tuple[int, int]]:
        return frozenset(
            (col.index, row) for col in self.columns for row in range(col.cells)
        )

    @property
    def tool_top(self) -> float:
        return SEAT_Z + max(
            envelope(lane.wrench)[1] for col in self.columns for lane in col.lanes
        )

    @property
    def future_cover_ceiling(self) -> float:
        return (
            max(self.tool_top, *(col.rack_top for col in self.columns))
            + c.FUTURE_LID_HEADROOM
        )


def envelope(wrench: c.Wrench) -> tuple[float, float]:
    """Do not silently replace the dimensional ledger with aligned bounds."""
    length, height = p.PROFILE_EXTENTS[wrench.label]
    return max(wrench.length, length), max(wrench.head_width, height)


def cells_for_length(length: float) -> int:
    if not isfinite(length) or length <= 0:
        raise ValueError("Wrench length must be finite and positive")
    return ceil((length + 2 * c.PHOTO_END_ALLOWANCE + 2 * c.WALL + TOLERANCE) / GRID)


def pack_lanes(wrenches: tuple[c.Wrench, ...], x: float) -> tuple[Lane, ...]:
    if not wrenches:
        raise ValueError("A column must contain at least one wrench")
    used = sum(w.head_thickness for w in wrenches) + (len(wrenches) - 1) * c.TOOL_GAP
    if used + c.TOOL_GAP > PAD - 2 * c.WALL:
        raise ValueError("Head thicknesses and free gaps overfill a one-cell column")
    cursor = x - used / 2
    lanes = []
    for wrench in wrenches:
        lanes.append(Lane(wrench, cursor + wrench.head_thickness / 2))
        cursor += wrench.head_thickness + c.TOOL_GAP
    for left, right in zip(lanes, lanes[1:]):
        tooth = (
            right.x - left.x - (right.slot_width + left.slot_width) / 2 - 2 * SLOT_LEAD
        )
        if tooth < c.WALL - 1e-9:
            raise ValueError("Rack teeth would be thinner than the PETG wall minimum")
    return tuple(lanes)


def arrange(wrenches_per_column: int | float = c.DEFAULT_WRENCHES_PER_COLUMN) -> Layout:
    # Browser number controls can supply integral floats. Reject bools/fractions.
    if isinstance(wrenches_per_column, bool) or wrenches_per_column not in range(1, 7):
        raise ValueError("wrenches_per_column must be an integer from 1 to 6")
    count = int(wrenches_per_column)
    if c.RACK_THICKNESS != p.HANDLE_BAND_WIDTH:
        raise ValueError("Rack thickness requires matching raw-trace support bands")
    columns = []
    for index, start in enumerate(range(0, len(c.WRENCHES), count)):
        group = c.WRENCHES[start : start + count]
        cells = cells_for_length(max(envelope(w)[0] for w in group))
        columns.append(Column(index, cells, pack_lanes(group, index * GRID)))
    return Layout(tuple(columns))
