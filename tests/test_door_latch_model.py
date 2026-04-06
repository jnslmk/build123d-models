from __future__ import annotations

import inspect
import unittest

from models import door_latch


class DoorLatchModelTests(unittest.TestCase):
    def test_create_builds_without_fillet_error(self) -> None:
        part = door_latch.create()
        self.assertIsNotNone(part)

    def test_create_uses_sketch_extrude_builder_flow(self) -> None:
        source = inspect.getsource(door_latch.create)
        self.assertIn("BuildSketch", source)
        self.assertIn("extrude(", source)

    def test_create_rounds_small_hook_end_with_circle_profile(self) -> None:
        source = inspect.getsource(door_latch.create)
        self.assertIn("hook_stem_length", source)
        self.assertIn("Circle(ARM_WIDTH / 2)", source)


if __name__ == "__main__":
    unittest.main()
