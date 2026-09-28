"""Static browser source assets: load a closure for rebuilds, all files for edits."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import model_deps
import website
from model_deps import model_files


class WebsiteSourceAssetsTests(unittest.TestCase):
    def test_model_assets_contain_import_closure_and_have_versioned_urls(self) -> None:
        models = [
            {"name": "lens_cap", "source": "models/lens_cap/__init__.py"},
            {
                "name": "led_profiles.stand",
                "source": "models/led_profiles/stand/__init__.py",
            },
        ]
        manifest = {"models": models}
        with tempfile.TemporaryDirectory() as tmp:
            website._write_source_assets(manifest, Path(tmp))
            for item in models:
                asset = item["sources"]
                self.assertRegex(asset, r"^model-sources/.+\.[0-9a-f]{16}\.json$")
                paths = json.loads((Path(tmp) / asset).read_text())
                self.assertEqual(
                    set(paths),
                    {
                        p.relative_to(website.HERE).as_posix()
                        for p in model_files(item["name"])
                    },
                )
                self.assertIn(item["source"], paths)
                self.assertIn("models/__init__.py", paths)
            self.assertNotEqual(models[0]["sources"], models[1]["sources"])
            edit_sources = manifest["editSources"]
            assert isinstance(edit_sources, str)
            all_sources = json.loads((Path(tmp) / edit_sources).read_text())
            self.assertIn("models/lens_cap/__init__.py", all_sources)
            self.assertIn("models/led_profiles/stand/__init__.py", all_sources)

    def test_content_change_mints_new_url_without_changing_other_closures(self) -> None:
        first = {
            "models": [
                {"name": "lens_cap", "source": "models/lens_cap/__init__.py"},
                {
                    "name": "led_profiles.stand",
                    "source": "models/led_profiles/stand/__init__.py",
                },
            ]
        }
        second = {"models": [dict(item) for item in first["models"]]}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            website._write_source_assets(first, root)
            sources = website._py_sources()
            sources["models/lens_cap/__init__.py"] += "\n# locally changed\n"
            with mock.patch.object(website, "_py_sources", return_value=sources):
                website._write_source_assets(second, root)
            self.assertNotEqual(
                first["models"][0]["sources"], second["models"][0]["sources"]
            )
            self.assertEqual(
                first["models"][1]["sources"], second["models"][1]["sources"]
            )
            self.assertNotEqual(first["editSources"], second["editSources"])

    def test_rebuild_refreshes_import_closure_after_import_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            models = root / "models"
            models.mkdir()
            (models / "__init__.py").write_text("")
            alpha = models / "alpha.py"
            alpha.write_text("def create():\n    return 1\n")
            manifest = {"models": [{"name": "alpha", "source": "models/alpha.py"}]}
            with (
                mock.patch.object(website, "HERE", root),
                mock.patch.object(website, "MODELS_DIR", models),
                mock.patch.object(model_deps, "ROOT", root),
            ):
                try:
                    website._write_source_assets(manifest, root / "site")
                    self.assertEqual(
                        set(
                            json.loads(
                                (
                                    root / "site" / manifest["models"][0]["sources"]
                                ).read_text()
                            )
                        ),
                        {"models/__init__.py", "models/alpha.py"},
                    )
                    (models / "other.py").write_text("dimension = 42\n")
                    alpha.write_text(
                        "from models.other import dimension\n"
                        "def create():\n    return dimension\n"
                    )
                    website._write_source_assets(manifest, root / "site")
                    files = json.loads(
                        (root / "site" / manifest["models"][0]["sources"]).read_text()
                    )
                    self.assertEqual(files["models/other.py"], "dimension = 42\n")
                finally:
                    model_deps.model_files.cache_clear()

    def test_static_closure_follows_cross_family_imports_and_initializers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            models = root / "models"
            (models / "other").mkdir(parents=True)
            (models / "__init__.py").write_text("")
            (models / "alpha.py").write_text(
                "from models.other import dimension\n"
                "def create():\n    return dimension\n"
            )
            (models / "other" / "__init__.py").write_text(
                "from .measurement import dimension\n"
            )
            (models / "other" / "measurement.py").write_text("dimension = 42\n")
            manifest = {"models": [{"name": "alpha", "source": "models/alpha.py"}]}
            with (
                mock.patch.object(website, "HERE", root),
                mock.patch.object(website, "MODELS_DIR", models),
                mock.patch.object(model_deps, "ROOT", root),
                mock.patch.object(
                    website,
                    "model_files",
                    side_effect=lambda name: model_deps._model_files(name, {}),
                ),
            ):
                website._write_source_assets(manifest, root / "site")
            files = json.loads(
                (root / "site" / manifest["models"][0]["sources"]).read_text()
            )
            self.assertEqual(
                set(files),
                {
                    "models/__init__.py",
                    "models/alpha.py",
                    "models/other/__init__.py",
                    "models/other/measurement.py",
                },
            )
            runtime = root / "runtime"
            for path, text in files.items():
                target = runtime / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(text)
            subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "from models.alpha import create; assert create() == 42",
                ],
                cwd=runtime,
                check=True,
                capture_output=True,
                text=True,
            )


if __name__ == "__main__":
    unittest.main()
