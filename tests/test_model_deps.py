"""Tests for the import-graph walk that decides what an incremental build skips.

The expensive one is ``RuntimeParityTests``: it imports each model alone in a
fresh interpreter and asserts the static closure matches the files Python really
loaded. That is the test that caught the graph missing every package
``__init__.py``, so it is worth running whenever ``model_deps`` changes:

    MODEL_DEPS_RUNTIME_PARITY=1 uv run python -m unittest tests.test_model_deps

It is opt-in because it pays the OCP import cost once per model -- minutes, not
seconds -- which does not belong in the default suite.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import model_deps
from tessellate_models import MODELS

ROOT = model_deps.ROOT


def rel(paths) -> set[str]:
    return {str(p.relative_to(ROOT)) for p in paths}


class ModelFilesTests(unittest.TestCase):
    def test_single_file_model_pulls_in_its_own_source(self) -> None:
        self.assertIn("models/cube.py", rel(model_deps.model_files("cube")))

    def test_every_model_includes_the_package_init_python_runs_first(self) -> None:
        # models/__init__.py executes on the way to any model, so a change to it
        # has to invalidate all of them.
        for name in MODELS:
            with self.subTest(model=name):
                self.assertIn("models/__init__.py", rel(model_deps.model_files(name)))

    def test_part_in_a_package_includes_its_package_init(self) -> None:
        files = rel(model_deps.model_files("led_psu_enclosure.tray"))
        self.assertIn("models/led_psu_enclosure/__init__.py", files)
        self.assertIn("models/led_psu_enclosure/tray.py", files)

    def test_cross_package_import_is_followed(self) -> None:
        # The drill_fit_tester coupons reach into drill_storage.box, which the
        # grep in AGENTS.md warns is easy to miss by hand.
        self.assertIn(
            "models/drill_storage/box.py",
            rel(model_deps.model_files("drill_fit_tester.full")),
        )

    def test_unknown_model_raises(self) -> None:
        with self.assertRaises(ModuleNotFoundError):
            model_deps.model_files("no_such_model")

    def test_only_model_sources_are_tracked(self) -> None:
        for path in model_deps.model_files("led_profiles.stand"):
            self.assertTrue(str(path).startswith(str(ROOT / "models")), path)


class AffectedModelsTests(unittest.TestCase):
    def test_a_models_own_file_selects_only_it(self) -> None:
        self.assertEqual(
            model_deps.affected_models(["models/cube.py"], list(MODELS)), ["cube"]
        )

    def test_unrelated_file_selects_nothing(self) -> None:
        self.assertEqual(
            model_deps.affected_models(["website/index.html"], list(MODELS)), []
        )

    def test_global_input_selects_the_whole_roster(self) -> None:
        for name in model_deps.GLOBAL_INPUTS:
            with self.subTest(input=name):
                self.assertEqual(
                    model_deps.affected_models([name], list(MODELS)), list(MODELS)
                )

    def test_shared_engine_selects_the_family(self) -> None:
        hits = model_deps.affected_models(["models/drill_storage/box.py"], list(MODELS))
        self.assertIn("drill_storage.wood", hits)
        self.assertIn("drill_fit_tester.full", hits)
        self.assertNotIn("cube", hits)


class FingerprintTests(unittest.TestCase):
    def test_is_stable_across_calls(self) -> None:
        self.assertEqual(model_deps.fingerprint("cube"), model_deps.fingerprint("cube"))

    def test_differs_between_models(self) -> None:
        self.assertNotEqual(
            model_deps.fingerprint("cube"), model_deps.fingerprint("lens_cap")
        )

    def test_changing_a_global_input_changes_every_fingerprint(self) -> None:
        lock = ROOT / "uv.lock"
        before = {name: model_deps.fingerprint(name) for name in ("cube", "lens_cap")}
        original = lock.read_bytes()
        try:
            lock.write_bytes(original + b"\n# scratch\n")
            for name, digest in before.items():
                with self.subTest(model=name):
                    self.assertNotEqual(digest, model_deps.fingerprint(name))
        finally:
            lock.write_bytes(original)
        for name, digest in before.items():
            self.assertEqual(digest, model_deps.fingerprint(name))

    def test_missing_global_input_does_not_raise(self) -> None:
        # A fingerprint has to be computable in a checkout that is missing an
        # optional input rather than blowing up the whole build.
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(model_deps._digest(Path(tmp) / "absent"), "absent")


PROBE = (
    "import importlib, json, sys;"
    "from pathlib import Path;"
    "importlib.import_module('models.{name}');"
    "print('@@' + json.dumps(sorted(str(Path(m.__file__).resolve())"
    " for n, m in sys.modules.items()"
    " if n.startswith('models') and getattr(m, '__file__', None))))"
)


@unittest.skipUnless(
    os.environ.get("MODEL_DEPS_RUNTIME_PARITY") == "1",
    "slow: set MODEL_DEPS_RUNTIME_PARITY=1 to import every model in a subprocess",
)
class RuntimeParityTests(unittest.TestCase):
    def test_static_closure_matches_what_python_actually_imports(self) -> None:
        def probe(name: str) -> tuple[str, set[str] | None, str]:
            done = subprocess.run(
                [sys.executable, "-c", PROBE.format(name=name)],
                capture_output=True,
                text=True,
                cwd=ROOT,
            )
            for line in done.stdout.splitlines():
                if line.startswith("@@"):
                    return name, set(json.loads(line[2:])), ""
            return name, None, done.stderr[-500:]

        with ThreadPoolExecutor(max_workers=os.cpu_count() or 1) as pool:
            for name, loaded, err in pool.map(probe, MODELS):
                with self.subTest(model=name):
                    self.assertIsNotNone(loaded, f"probe failed: {err}")
                    static = {str(p) for p in model_deps.model_files(name)}
                    # A missed edge ships a stale STL; an extra edge only costs
                    # a rebuild. Only the first is a failure.
                    self.assertEqual(set(), loaded - static, "missed import edge")


if __name__ == "__main__":
    unittest.main()
