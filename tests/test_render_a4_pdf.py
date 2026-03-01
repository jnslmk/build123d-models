from __future__ import annotations

import unittest

from build123d import Box
from render_a4_pdf import (
    ORTHO_VIEWPORTS,
    POINTS_PER_MM,
    _camera_for_view,
    compute_uniform_scale,
    format_drawing_scale,
    parse_scale_option,
)


class RenderA4PdfTests(unittest.TestCase):
    def test_top_view_uses_stable_up_vector(self) -> None:
        origin, up = ORTHO_VIEWPORTS["top"]
        self.assertEqual(origin, (0, 0, 100))
        self.assertEqual(up, (0, 1, 0))

    def test_uniform_scale_uses_largest_projected_extents(self) -> None:
        bounds = {
            "top": (20.0, 10.0),
            "front": (30.0, 40.0),
            "left": (10.0, 25.0),
            "iso": (35.0, 30.0),
        }

        scale = compute_uniform_scale(bounds, usable_width=140.0, usable_height=100.0)

        # max width = 35, max height = 40 -> min(140/35, 100/40) == 2.5
        self.assertEqual(scale, 2.5)

    def test_top_camera_is_centered_for_axis_true_projection(self) -> None:
        part = Box(20, 10, 4)
        origin, up, look_at = _camera_for_view(part, "top")
        center = part.bounding_box().center()

        self.assertEqual(origin[0], center.X)
        self.assertEqual(origin[1], center.Y)
        self.assertEqual(look_at, (center.X, center.Y, center.Z))
        self.assertEqual(up, (0, 1, 0))

    def test_format_drawing_scale(self) -> None:
        self.assertEqual(format_drawing_scale(POINTS_PER_MM), "1:1")
        self.assertEqual(format_drawing_scale(POINTS_PER_MM * 0.5), "1:2.00")
        self.assertEqual(format_drawing_scale(POINTS_PER_MM * 2.0), "2.00:1")

    def test_parse_scale_option(self) -> None:
        self.assertIsNone(parse_scale_option("auto"))
        self.assertEqual(parse_scale_option("1:1"), 1.0)
        self.assertEqual(parse_scale_option("1:2"), 0.5)
        self.assertEqual(parse_scale_option("2:1"), 2.0)
        self.assertEqual(parse_scale_option("1.25"), 1.25)

        with self.assertRaises(ValueError):
            parse_scale_option("0:1")
        with self.assertRaises(ValueError):
            parse_scale_option("foo")


if __name__ == "__main__":
    unittest.main()
