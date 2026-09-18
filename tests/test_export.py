from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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

    def test_preview_only_export_skips_stl_and_step_but_writes_glb(self) -> None:
        part = Compound(children=[Solid.make_box(1, 1, 1)])
        with tempfile.TemporaryDirectory() as tmpdir:
            with (
                patch.object(export_module, "EXPORTS_DIR", Path(tmpdir)),
                patch.object(export_module, "export_stl") as export_stl,
                patch.object(export_module, "export_step") as export_step,
                patch.object(export_module, "export_gltf") as export_gltf,
            ):
                written = export_module.export(
                    part,
                    "preview",
                    step=False,
                    stl=False,
                    children=False,
                )

        export_stl.assert_not_called()
        export_step.assert_not_called()
        export_gltf.assert_called_once()
        self.assertEqual([path.name for path in written], ["preview.glb"])


if __name__ == "__main__":
    unittest.main()
