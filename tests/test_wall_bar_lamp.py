from __future__ import annotations

import inspect
import unittest

from build123d import Compound

from models import wall_bar_lamp


class WallBarLampModelTests(unittest.TestCase):
    def test_create_returns_labeled_compound_with_children(self) -> None:
        part = wall_bar_lamp.create()
        self.assertIsInstance(part, Compound)
        self.assertEqual(part.label, "wall_bar_lamp")
        self.assertEqual([child.label for child in part.children], [
            "wall_mount",
            "left_tube",
            "right_tube",
            "left_end_cap",
            "right_end_cap",
        ])

    def test_mount_is_one_piece(self) -> None:
        mount = wall_bar_lamp.create_mount()
        self.assertEqual(len(mount.solids()), 1)

    def test_mount_and_tube_use_builder_mode(self) -> None:
        mount_source = inspect.getsource(wall_bar_lamp.create_mount)
        tube_source = inspect.getsource(wall_bar_lamp.create_tube)
        self.assertIn("BuildSketch", mount_source)
        self.assertIn("extrude(", mount_source)
        self.assertIn("BuildSketch", tube_source)
        self.assertIn("Circle(outer_radius)", tube_source)

    def test_assembly_is_long_horizontal_bar(self) -> None:
        part = wall_bar_lamp.create()
        bbox = part.bounding_box()
        self.assertGreater(bbox.size.X, 2.5 * bbox.size.Z)
        self.assertLess(bbox.size.Y, bbox.size.X / 4)

    def test_print_layout_stacks_parts_apart(self) -> None:
        part = wall_bar_lamp.create_print_layout()
        bbox = part.bounding_box()
        self.assertGreater(bbox.size.Z, wall_bar_lamp.BACKPLATE_HEIGHT + wall_bar_lamp.TUBE_OUTER_DIAMETER)


if __name__ == "__main__":
    unittest.main()
