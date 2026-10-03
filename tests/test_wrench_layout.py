"""Boundary/invariant tests for occupied cells and measured transverse packing."""

from dataclasses import replace
import unittest
from typing import Any, cast

from models.lib.gridfinity import GRID, TOLERANCE
from models.wrench_storage import config as c
from models.wrench_storage import layout as l


class WrenchLayoutTests(unittest.TestCase):
    def test_cell_length_at_ceil_threshold(self) -> None:
        for cells in (1, 3, 4, 5):
            threshold = (
                cells * GRID - TOLERANCE - 2 * c.WALL - 2 * c.PHOTO_END_ALLOWANCE
            )
            self.assertEqual(l.cells_for_length(threshold - 1e-6), cells)
            self.assertEqual(l.cells_for_length(threshold), cells)
            self.assertEqual(l.cells_for_length(threshold + 1e-6), cells + 1)
        for value in (0, -1, float("inf"), float("nan")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                l.cells_for_length(value)

    def test_grouping_is_complete_consecutive_and_connected(self) -> None:
        for count in range(1, 7):
            with self.subTest(count=count):
                layout = l.arrange(count)
                flattened = tuple(
                    lane.wrench for col in layout.columns for lane in col.lanes
                )
                self.assertEqual(flattened, c.WRENCHES)
                self.assertTrue(
                    all(1 <= len(col.lanes) <= count for col in layout.columns)
                )
                reached = {next(iter(layout.occupied))}
                pending = list(reached)
                while pending:
                    x, y = pending.pop()
                    for cell in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                        if cell in layout.occupied and cell not in reached:
                            reached.add(cell)
                            pending.append(cell)
                self.assertEqual(reached, layout.occupied)
                for column in layout.columns:
                    required = (
                        max(l.envelope(lane.wrench)[0] for lane in column.lanes)
                        + 2 * c.PHOTO_END_ALLOWANCE
                        + 2 * c.WALL
                    )
                    self.assertGreaterEqual(column.cells * GRID - TOLERANCE, required)
                    self.assertLess((column.cells - 1) * GRID - TOLERANCE, required)

    def test_three_per_column_omits_tenth_bounding_cell(self) -> None:
        layout = l.arrange(3)
        self.assertEqual(tuple(col.cells for col in layout.columns), (5, 4))
        self.assertEqual(len(layout.occupied), 9)
        self.assertNotIn((1, 4), layout.occupied)

    def test_head_width_overfill_and_thin_teeth_are_rejected(self) -> None:
        wide = replace(c.WRENCHES[0], head_thickness=40)
        with self.assertRaises(ValueError):
            l.pack_lanes((wide,), 0)
        thin_teeth = replace(c.WRENCHES[0], head_thickness=4.5, handle_thickness=4.4)
        with self.assertRaises(ValueError):
            l.pack_lanes((thin_teeth, thin_teeth), 0)
        with self.assertRaises(ValueError):
            l.pack_lanes((), 0)

    def test_invalid_groups_are_rejected_and_browser_integers_work(self) -> None:
        for count in (True, False, 0, 7, -1, 2.5, float("nan"), "3", None):
            with self.subTest(count=count), self.assertRaises(ValueError):
                l.arrange(cast(Any, count))
        self.assertEqual(l.arrange(3.0), l.arrange(3))


if __name__ == "__main__":
    unittest.main()
