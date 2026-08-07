from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from build123d import Compound, Solid

import export as export_module


class ExportTests(unittest.TestCase):
    def test_export_child_stls_uses_child_labels(self) -> None:
        left = Solid.make_box(1, 1, 1)
        left.label = "Left Tube"
        right = Solid.make_box(1, 1, 1)
        right.label = "Right Cap"
        part = Compound(label="lamp", children=[left, right])

        with tempfile.TemporaryDirectory() as tmpdir:
            original_dir = export_module.EXPORTS_DIR
            export_module.EXPORTS_DIR = Path(tmpdir)
            try:
                export_module._export_child_stls(part, "bar_lamp")
                self.assertTrue((Path(tmpdir) / "bar_lamp_left_tube.stl").exists())
                self.assertTrue((Path(tmpdir) / "bar_lamp_right_cap.stl").exists())
            finally:
                export_module.EXPORTS_DIR = original_dir


if __name__ == "__main__":
    unittest.main()
