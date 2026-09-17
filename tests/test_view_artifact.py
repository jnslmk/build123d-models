from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import export as export_module
import view_artifact


class ViewArtifactTests(unittest.TestCase):
    def test_existing_asset_is_rebuilt_from_current_model(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            exports = Path(tmpdir)
            stale = exports / "soldering_aid.glb"
            stale.write_bytes(b"stale")
            original_dir = view_artifact.EXPORTS_DIR
            view_artifact.EXPORTS_DIR = exports
            module = Mock()
            part = object()
            module.create.return_value = part

            def export_current(_: object, name: str, *, step: bool) -> None:
                self.assertEqual((name, step), ("soldering_aid", False))
                stale.write_bytes(b"current")

            try:
                with (
                    patch.object(
                        view_artifact,
                        "importlib",
                        SimpleNamespace(import_module=Mock(return_value=module)),
                    ),
                    patch.object(
                        export_module, "export", side_effect=export_current
                    ) as export,
                ):
                    asset = view_artifact._ensure_model_asset("soldering_aid")
                export.assert_called_once_with(part, "soldering_aid", step=False)
                self.assertEqual(asset.read_bytes(), b"current")
            finally:
                view_artifact.EXPORTS_DIR = original_dir


if __name__ == "__main__":
    unittest.main()
