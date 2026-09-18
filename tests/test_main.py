from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import ANY, Mock, patch

import main


class PlanningTests(unittest.TestCase):
    def test_plan_carries_the_prebuild_fingerprint(self) -> None:
        with (
            patch.object(main, "MODELS", ["one", "two"]),
            patch.object(main, "_load_stamps", return_value={}),
            patch.object(
                main.model_deps,
                "fingerprints",
                return_value={"one": "fp-one", "two": "fp-two"},
            ) as fingerprints,
        ):
            stale, stamps = main.plan(False)

        self.assertEqual(stamps, {})
        self.assertEqual(
            stale,
            [
                ("one", "never built", "fp-one"),
                ("two", "never built", "fp-two"),
            ],
        )
        fingerprints.assert_called_once_with(("one", "two"))

    def test_stamp_schema_discards_version_one_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            stamps = Path(tmp) / ".build-stamps.json"
            stamps.write_text(
                json.dumps(
                    {
                        "version": main.STAMP_VERSION - 1,
                        "models": {"scene": {"fingerprint": "old", "outputs": []}},
                    }
                )
            )
            with patch.object(main, "STAMPS", stamps):
                self.assertEqual(main._load_stamps(), {})


class BuildWorkerTests(unittest.TestCase):
    def test_assembly_exports_only_glb_and_removes_old_downloads(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            exports = Path(tmp)
            for ext in ("stl", "step"):
                (exports / f"scene.{ext}").write_bytes(b"old")
            calls = []

            def export(_part, name, **kwargs):
                calls.append((name, kwargs))
                glb = exports / f"{name}.glb"
                glb.write_bytes(b"preview")
                return [glb]

            modules = {
                "export": SimpleNamespace(export=export),
                "tessellate_models": SimpleNamespace(
                    get_part=lambda _name: object(),
                    model_is_assembly=lambda _name: True,
                ),
            }
            with (
                patch.object(main, "EXPORTS_DIR", exports),
                patch.dict(sys.modules, modules),
            ):
                result = main._build("scene")

            self.assertNotIn("error", result)
            self.assertEqual(result["outputs"], ["scene.glb"])
            self.assertEqual(
                calls,
                [
                    (
                        "scene",
                        {"step": False, "stl": False, "children": False},
                    )
                ],
            )
            self.assertFalse((exports / "scene.stl").exists())
            self.assertFalse((exports / "scene.step").exists())

    def test_printable_keeps_stl_step_and_glb(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            exports = Path(tmp)

            def export(_part, name, **kwargs):
                return [exports / f"{name}.{ext}" for ext in ("stl", "step", "glb")]

            modules = {
                "export": SimpleNamespace(export=Mock(side_effect=export)),
                "tessellate_models": SimpleNamespace(
                    get_part=lambda _name: object(),
                    model_is_assembly=lambda _name: False,
                ),
            }
            with patch.dict(sys.modules, modules):
                result = main._build("part")

            self.assertEqual(result["outputs"], ["part.glb", "part.step", "part.stl"])
            modules["export"].export.assert_called_once_with(
                ANY,
                "part",
                step=True,
                stl=True,
                children=False,
            )


class StampRaceTests(unittest.TestCase):
    def test_success_uses_planned_fingerprint_not_postbuild_source(self) -> None:
        class Pool:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def imap_unordered(self, _build, _order):
                return iter(
                    [
                        {
                            "name": "scene",
                            "seconds": 1.0,
                            "outputs": ["scene.glb"],
                        }
                    ]
                )

        saved = []
        with (
            patch.object(sys, "argv", ["main.py", "--jobs", "1"]),
            patch.object(main, "MODELS", ["scene"]),
            patch.object(
                main,
                "plan",
                return_value=([("scene", "sources changed", "pre-build")], {}),
            ),
            patch.object(
                main.mp,
                "get_context",
                return_value=SimpleNamespace(Pool=lambda _jobs: Pool()),
            ),
            patch.object(
                main,
                "_save_stamps",
                side_effect=lambda stamps: saved.append(dict(stamps)),
            ),
            patch.object(
                main.model_deps,
                "fingerprint",
                side_effect=AssertionError("post-build hash"),
            ),
        ):
            main.main()

        self.assertEqual(saved[-1]["scene"]["fingerprint"], "pre-build")


if __name__ == "__main__":
    unittest.main()
