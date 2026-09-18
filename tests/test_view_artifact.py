from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import export as export_module
import view_artifact


class FontPreloadTests(unittest.TestCase):
    def test_importing_view_artifact_preloads_fontfix_without_ocp(self) -> None:
        probe = (
            "import sys; import view_artifact; "
            "assert 'fontfix' in sys.modules, 'fontfix not preloaded'; "
            "heavy = [n for n in sys.modules "
            "if n == 'build123d' or n == 'OCP' or n.startswith(('OCP.', 'build123d.'))]; "
            "assert not heavy, heavy; print('ok')"
        )
        done = subprocess.run(
            [sys.executable, "-c", probe],
            cwd=Path(__file__).resolve().parent.parent,
            capture_output=True,
            text=True,
        )
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(done.stdout.strip(), "ok")


class ViewArtifactTests(unittest.TestCase):
    def test_corrupt_stamp_entry_falls_back_to_rebuild(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            exports = Path(tmpdir)
            (exports / ".build-stamps.json").write_text(
                json.dumps(
                    {
                        "version": view_artifact.STAMP_VERSION,
                        "models": {"soldering_aid": "not-a-dict"},
                    }
                )
            )
            with (
                patch.object(view_artifact, "EXPORTS_DIR", exports),
                patch.object(
                    view_artifact.model_deps, "fingerprint", return_value="current"
                ),
            ):
                self.assertIsNone(view_artifact._stamped_model_asset("soldering_aid"))

    def test_current_stamped_glb_is_reused_without_model_import(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            exports = Path(tmpdir)
            glb = exports / "soldering_aid.glb"
            glb.write_bytes(b"current")
            (exports / ".build-stamps.json").write_text(
                json.dumps(
                    {
                        "version": view_artifact.STAMP_VERSION,
                        "models": {
                            "soldering_aid": {
                                "fingerprint": "current",
                                "outputs": [glb.name],
                            }
                        },
                    }
                )
            )
            with (
                patch.object(view_artifact, "EXPORTS_DIR", exports),
                patch.object(
                    view_artifact.model_deps,
                    "fingerprint",
                    return_value="current",
                ),
                patch.object(view_artifact.importlib, "import_module") as import_model,
            ):
                asset = view_artifact._ensure_model_asset("soldering_aid")
            self.assertEqual(asset, glb)
            import_model.assert_not_called()

    def test_stale_asset_is_rebuilt_once_without_child_stls(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            exports = Path(tmpdir)
            stale = exports / "soldering_aid.glb"
            stale.write_bytes(b"stale")
            (exports / ".build-stamps.json").write_text(
                json.dumps(
                    {
                        "version": view_artifact.STAMP_VERSION,
                        "models": {
                            "soldering_aid": {
                                "fingerprint": "old",
                                "outputs": [stale.name],
                            }
                        },
                    }
                )
            )
            module = Mock()
            part = object()
            module.create.return_value = part
            module.IS_ASSEMBLY = False

            def export_current(
                _: object, name: str, *, step: bool, stl: bool, children: bool
            ) -> None:
                self.assertEqual(
                    (name, step, stl, children), ("soldering_aid", False, True, False)
                )
                stale.write_bytes(b"current")

            with (
                patch.object(view_artifact, "EXPORTS_DIR", exports),
                patch.object(
                    view_artifact.model_deps,
                    "fingerprint",
                    return_value="current",
                ),
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

            export.assert_called_once_with(
                part, "soldering_aid", step=False, stl=True, children=False
            )
            self.assertEqual(asset.read_bytes(), b"current")


if __name__ == "__main__":
    unittest.main()
