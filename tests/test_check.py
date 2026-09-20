from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock
from unittest.mock import Mock, patch

import check as check_module


class NoChecksBackwardCompatTests(unittest.TestCase):
    """A model with neither `checks.main()` nor `check()` -- the plain-argv
    path must keep printing exactly the same message and exit 0, --json or
    not.

    This used to exercise `cube` as its example of "a model with no checks
    defined". That coupled the test to a roster fact rather than to
    check.py's own behaviour: every single-file model in the roster
    (including `cube`) is gaining a real `check()` as part of this same
    effort, which would flip `cube` from "no checks" to "has checks" and
    break this test on a premise it never meant to assert. A synthetic
    module with no `check` attribute and no `__path__` (so it isn't mistaken
    for a package with a `checks` submodule either) stands in instead --
    see `_install_fake_no_checks_module`, the same test-double technique
    `SingleFileCheckFnReportNoFlagsTests` already uses elsewhere in this
    file.
    """

    def _install_fake_no_checks_module(self, name: str) -> str:
        full_name = f"models.{name}"
        # No `.check` attribute and no `__path__` -- `_load_model` +
        # `_checks_submodule` + `getattr(module, "check", None)` see exactly
        # what a real single-file model with no checks looks like.
        sys.modules[full_name] = types.SimpleNamespace()  # ty: ignore[invalid-assignment]
        self.addCleanup(sys.modules.pop, full_name, None)
        return name

    def test_no_flags_prints_no_checks_and_exits_0(self) -> None:
        name = self._install_fake_no_checks_module("__fake_no_checks_model")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            with self.assertRaises(SystemExit) as ctx:
                sys.argv = ["check.py", name]
                check_module.main()
        self.assertEqual(ctx.exception.code, 0)
        self.assertEqual(
            out.getvalue(),
            f"Model '{name}' has no checks defined (no checks.main(), no check()).\n",
        )

    def test_json_flag_keeps_same_stdout_and_exit_and_writes_report(self) -> None:
        name = self._install_fake_no_checks_module("__fake_no_checks_model_json")
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "report.json")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                with self.assertRaises(SystemExit) as ctx:
                    sys.argv = ["check.py", name, "--json", path]
                    check_module.main()
            self.assertEqual(ctx.exception.code, 0)
            self.assertEqual(
                out.getvalue(),
                f"Model '{name}' has no checks defined (no checks.main(), no check()).\n",
            )
            payload = json.loads(Path(path).read_text())
            self.assertEqual(payload["model"], name)
            self.assertEqual(payload["status"], "no_checks")
            self.assertEqual(payload["assertions"], [])
            self.assertEqual(payload["passed"], 0)
            self.assertEqual(payload["failed"], 0)

    def test_unknown_model_still_exits_1_with_or_without_json(self) -> None:
        for extra in ([], ["--json", "/tmp/should-not-be-written-anywhere.json"]):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                with self.assertRaises(SystemExit) as ctx:
                    sys.argv = ["check.py", "definitely_not_a_real_model", *extra]
                    check_module.main()
            self.assertEqual(ctx.exception.code, 1)
            self.assertEqual(
                out.getvalue(),
                "Model 'definitely_not_a_real_model' not found in models/\n",
            )


class PackageChecksJsonTests(unittest.TestCase):
    """`_run_package_checks_json` against a fake `checks` module -- exercises
    the `run() -> Report` capture path without running any real (slow)
    model's geometry assertions."""

    def _fake_checks_with_run(self):
        from models.lib.checks import Report

        def run():
            r = Report()
            r.section("widgets")
            r.check(True, "widget A is round", "12.0mm")
            r.check(False, "widget B is square", "expected 4 sides, got 3")
            return r

        return types.SimpleNamespace(run=run)

    def test_captures_every_assertion_and_exits_on_failures(self) -> None:
        checks = self._fake_checks_with_run()
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "report.json")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                with self.assertRaises(SystemExit) as ctx:
                    check_module._run_package_checks_json(
                        "fake",
                        checks,  # ty: ignore[invalid-argument-type]
                        path,
                    )
            self.assertEqual(ctx.exception.code, 1)  # one of the two checks failed
            self.assertIn("widget A is round", out.getvalue())

            payload = json.loads(Path(path).read_text())
            self.assertEqual(payload["model"], "fake")
            self.assertEqual(payload["passed"], 1)
            self.assertEqual(payload["failed"], 1)
            names = {(a["section"], a["name"]): a for a in payload["assertions"]}
            self.assertTrue(names[("widgets", "widget A is round")]["passed"])
            self.assertFalse(names[("widgets", "widget B is square")]["passed"])
            self.assertEqual(
                names[("widgets", "widget B is square")]["detail"],
                "expected 4 sides, got 3",
            )

    def test_all_passing_exits_0(self) -> None:
        from models.lib.checks import Report

        def run():
            r = Report()
            r.check(True, "only check")
            return r

        checks = types.SimpleNamespace(run=run)
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "report.json")
            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit) as ctx:
                    check_module._run_package_checks_json(
                        "fake",
                        checks,  # ty: ignore[invalid-argument-type]
                        path,
                    )
            self.assertEqual(ctx.exception.code, 0)

    def test_checks_module_without_run_falls_back_to_main(self) -> None:
        """A checks.py with only main() (no run()) still works, just without
        structured detail -- and its own exit code still governs."""
        calls: list[str] = []

        def fake_main():
            calls.append("main-called")
            sys.exit(3)

        checks = types.SimpleNamespace(main=fake_main)
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "report.json")
            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit) as ctx:
                    check_module._run_package_checks_json(
                        "fake",
                        checks,  # ty: ignore[invalid-argument-type]
                        path,
                    )
            self.assertEqual(ctx.exception.code, 3)
            self.assertEqual(calls, ["main-called"])
            payload = json.loads(Path(path).read_text())
            self.assertEqual(payload["status"], "unsupported")


class SingleFileCheckFnJsonTests(unittest.TestCase):
    def test_passing_check_fn(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "report.json")
            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit) as ctx:
                    check_module._run_check_fn_json("fake", lambda: True, path)
            self.assertEqual(ctx.exception.code, 0)
            payload = json.loads(Path(path).read_text())
            self.assertEqual(payload["passed"], 1)
            self.assertEqual(payload["failed"], 0)
            self.assertTrue(payload["assertions"][0]["passed"])

    def test_failing_check_fn_returns_false(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "report.json")
            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit) as ctx:
                    check_module._run_check_fn_json("fake", lambda: False, path)
            self.assertEqual(ctx.exception.code, 1)
            payload = json.loads(Path(path).read_text())
            self.assertFalse(payload["assertions"][0]["passed"])

    def test_failing_check_fn_raises_assertion_error(self) -> None:
        def fn():
            raise AssertionError("bad geometry")

        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "report.json")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                with self.assertRaises(SystemExit) as ctx:
                    check_module._run_check_fn_json("fake", fn, path)
            self.assertEqual(ctx.exception.code, 1)
            self.assertIn("bad geometry", out.getvalue())
            payload = json.loads(Path(path).read_text())
            self.assertFalse(payload["assertions"][0]["passed"])
            self.assertEqual(payload["assertions"][0]["detail"], "bad geometry")


class SingleFileCheckFnReportJsonTests(unittest.TestCase):
    """A tier-1 `check()` that returns a `models.lib.checks.Report` -- the
    same instrumentation a package's `run()` uses -- must be captured with
    full per-assertion detail, exactly like `_run_package_checks_json`."""

    def test_passing_report_is_captured_in_full(self) -> None:
        from models.lib.checks import Report

        def fn():
            r = Report()
            r.section("widgets")
            r.check(True, "widget A is round", "12.0mm")
            return r

        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "report.json")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                with self.assertRaises(SystemExit) as ctx:
                    check_module._run_check_fn_json("fake", fn, path)
            self.assertEqual(ctx.exception.code, 0)
            self.assertIn("widget A is round", out.getvalue())

            payload = json.loads(Path(path).read_text())
            self.assertEqual(payload["model"], "fake")
            self.assertEqual(payload["passed"], 1)
            self.assertEqual(payload["failed"], 0)
            self.assertEqual(
                payload["assertions"],
                [
                    {
                        "section": "widgets",
                        "name": "widget A is round",
                        "passed": True,
                        "detail": "12.0mm",
                    }
                ],
            )

    def test_failing_report_exits_1_with_failed_assertions_in_json(self) -> None:
        from models.lib.checks import Report

        def fn():
            r = Report()
            r.section("widgets")
            r.check(True, "widget A is round", "12.0mm")
            r.check(False, "widget B is square", "expected 4 sides, got 3")
            return r

        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "report.json")
            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit) as ctx:
                    check_module._run_check_fn_json("fake", fn, path)
            self.assertEqual(ctx.exception.code, 1)  # matches the package Report path

            payload = json.loads(Path(path).read_text())
            self.assertEqual(payload["passed"], 1)
            self.assertEqual(payload["failed"], 1)
            names = {a["name"]: a for a in payload["assertions"]}
            self.assertTrue(names["widget A is round"]["passed"])
            self.assertFalse(names["widget B is square"]["passed"])
            self.assertEqual(
                names["widget B is square"]["detail"], "expected 4 sides, got 3"
            )

    def test_report_json_shape_matches_package_report_json_shape(self) -> None:
        """Same `Report`, run through both tiers' `--json` capture paths, must
        produce byte-identical JSON payloads (module name aside) -- a
        consumer like `check_diff.py` should not need to know which tier
        produced a report."""
        from models.lib.checks import Report

        def make_report():
            r = Report()
            r.section("widgets")
            r.check(True, "widget A is round", "12.0mm")
            r.check(False, "widget B is square", "expected 4 sides, got 3")
            return r

        with tempfile.TemporaryDirectory() as tmp:
            single_path = str(Path(tmp) / "single.json")
            package_path = str(Path(tmp) / "package.json")

            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit):
                    check_module._run_check_fn_json("fake", make_report, single_path)
            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit):
                    check_module._run_package_checks_json(
                        "fake",
                        types.SimpleNamespace(run=make_report),  # ty: ignore[invalid-argument-type]
                        package_path,
                    )

            single_payload = json.loads(Path(single_path).read_text())
            package_payload = json.loads(Path(package_path).read_text())
            self.assertEqual(single_payload, package_payload)


class SingleFileCheckFnReportNoFlagsTests(unittest.TestCase):
    """A tier-1 `check()` returning a `Report` must behave the same through
    the plain `uv run check <name>` path (no `--json`) as it does through
    `--json`: rendered output, and exit 1 iff the report has failures.

    Without this, a `Report` with failures is merely truthy -- not `False` --
    and `main()`'s old `sys.exit(1 if result is False else 0)` would report
    success on a failing model, silently, with the failures never printed.
    That is the exact path CI and a human typing `uv run check <name>` use.
    """

    def _install_fake_module(self, name: str, fn) -> str:
        full_name = f"models.{name}"
        # A plain object with a `.check` attribute stands in for a real module
        # here: `_load_model` only ever does `sys.modules.get(full_name)` (via
        # `importlib.import_module`) and `getattr(module, "check", None)`,
        # neither of which cares that this isn't a real `ModuleType`.
        sys.modules[full_name] = types.SimpleNamespace(  # ty: ignore[invalid-assignment]
            check=fn
        )
        self.addCleanup(sys.modules.pop, full_name, None)
        return name

    def test_failing_report_no_flags_exits_1_and_prints_assertions(self) -> None:
        from models.lib.checks import Report

        def fn():
            r = Report()
            r.section("widgets")
            r.check(True, "widget A is round", "12.0mm")
            r.check(False, "widget B is square", "expected 4 sides, got 3")
            return r

        name = self._install_fake_module("__fake_report_fail_noflags", fn)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            with self.assertRaises(SystemExit) as ctx:
                sys.argv = ["check.py", name]
                check_module.main()
        self.assertEqual(ctx.exception.code, 1)
        rendered = out.getvalue()
        self.assertIn("widget A is round", rendered)
        self.assertIn("widget B is square", rendered)
        self.assertIn("1 FAILED: widget B is square", rendered)

    def test_passing_report_no_flags_exits_0(self) -> None:
        from models.lib.checks import Report

        def fn():
            r = Report()
            r.check(True, "only check")
            return r

        name = self._install_fake_module("__fake_report_pass_noflags", fn)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            with self.assertRaises(SystemExit) as ctx:
                sys.argv = ["check.py", name]
                check_module.main()
        self.assertEqual(ctx.exception.code, 0)
        self.assertIn("all checks passed", out.getvalue())

    def test_no_flags_and_json_paths_agree_on_output_and_exit_code(self) -> None:
        """For the same `Report`, `uv run check <name>` and
        `uv run check <name> --json <path>` must print the same thing and
        exit with the same code -- the two tiers of `--json` capture already
        do this for each other; this pins it across the flag too."""
        from models.lib.checks import Report

        def fn():
            r = Report()
            r.section("widgets")
            r.check(True, "widget A is round", "12.0mm")
            r.check(False, "widget B is square", "expected 4 sides, got 3")
            return r

        name = self._install_fake_module("__fake_report_agree", fn)

        out_noflags = io.StringIO()
        with contextlib.redirect_stdout(out_noflags):
            with self.assertRaises(SystemExit) as ctx_noflags:
                sys.argv = ["check.py", name]
                check_module.main()

        with tempfile.TemporaryDirectory() as tmp:
            json_path = str(Path(tmp) / "report.json")
            out_json = io.StringIO()
            with contextlib.redirect_stdout(out_json):
                with self.assertRaises(SystemExit) as ctx_json:
                    sys.argv = ["check.py", name, "--json", json_path]
                    check_module.main()

        self.assertEqual(ctx_noflags.exception.code, ctx_json.exception.code)
        self.assertEqual(out_noflags.getvalue(), out_json.getvalue())


class ReportStructuredCaptureTests(unittest.TestCase):
    """`Report.entries`/`to_dict()` are additive -- `lines`/`render()`/`failures`
    (what every existing `checks.py` already depends on) must be untouched."""

    def test_to_dict_matches_entries_and_render_is_unaffected(self) -> None:
        from models.lib.checks import Report

        r = Report()
        r.section("alpha")
        r.check(True, "first", "1.0mm")
        r.section("beta")
        r.check(False, "second", "expected 2, got 3")

        rendered = r.render()
        self.assertIn("[PASS] first -- 1.0mm", rendered)
        self.assertIn("[FAIL] second -- expected 2, got 3", rendered)
        self.assertIn("1 FAILED: second", rendered)
        self.assertEqual(r.failures, ["second"])

        payload = r.to_dict()
        self.assertEqual(payload["passed"], 1)
        self.assertEqual(payload["failed"], 1)
        self.assertEqual(
            payload["assertions"],
            [
                {
                    "section": "alpha",
                    "name": "first",
                    "passed": True,
                    "detail": "1.0mm",
                },
                {
                    "section": "beta",
                    "name": "second",
                    "passed": False,
                    "detail": "expected 2, got 3",
                },
            ],
        )


class FontPreloadTests(unittest.TestCase):
    def test_importing_check_preloads_fontfix_without_ocp(self) -> None:
        probe = (
            "import sys; import check; "
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


class AncestorCheckDispatchTests(unittest.TestCase):
    def test_nearest_claiming_parent_supplies_targeted_report(self) -> None:
        report = object()
        checks = types.SimpleNamespace(
            handles_model=lambda name: name == "family.part",
            run_model=Mock(return_value=report),
        )
        with (
            patch.object(
                check_module.importlib.util, "find_spec", return_value=object()
            ),
            patch.object(check_module.importlib, "import_module", return_value=checks),
        ):
            run = check_module._ancestor_check("family.part")
        self.assertIsNotNone(run)
        self.assertIs(run(), report)
        checks.run_model.assert_called_once_with("family.part")

    def test_parent_hook_that_does_not_claim_model_is_ignored(self) -> None:
        checks = types.SimpleNamespace(
            handles_model=lambda _name: False,
            run_model=Mock(),
        )
        with (
            patch.object(
                check_module.importlib.util, "find_spec", return_value=object()
            ),
            patch.object(check_module.importlib, "import_module", return_value=checks),
        ):
            self.assertIsNone(check_module._ancestor_check("family.part"))
        checks.run_model.assert_not_called()

    def test_led_profile_targets_cover_registered_children(self) -> None:
        from models.led_profiles import checks
        from tessellate_models import MODELS

        children = {name for name in MODELS if name.startswith("led_profiles.")}
        self.assertEqual(children, set(checks.TARGET_CHECKS))


class ReportSolidProbeTests(unittest.TestCase):
    def test_repeated_samples_share_one_classifier_per_solid(self) -> None:
        from models.lib import checks

        part = Mock()
        probe = Mock(side_effect=(True, False))
        with patch.object(checks, "solid_probe", return_value=probe) as factory:
            report = checks.Report()
            self.assertTrue(report.solid_at(part, 1, 2, 3))
            self.assertFalse(report.solid_at(part, 4, 5, 6))

        factory.assert_called_once_with(part)
        self.assertEqual(probe.call_args_list[0].args, (1, 2, 3))
        self.assertEqual(probe.call_args_list[1].args, (4, 5, 6))


class LedProfilesRunShapeTests(unittest.TestCase):
    """The led_profiles family's targeted dispatch."""

    def test_unknown_registered_target_is_not_claimed(self) -> None:
        from models.led_profiles import checks

        self.assertFalse(checks.handles_model("not_a_family_member"))
        self.assertIsNone(checks.run_model("not_a_family_member"))

    def test_assembly_targets_dispatch_their_scene_only(self) -> None:
        from models.led_profiles import checks

        assemblies = Mock()
        assemblies.create_standing = Mock(return_value=object())
        with (
            patch.object(checks, "assemblies", assemblies),
            patch.object(checks, "_check_scene_clearance") as clearance,
            patch.object(checks, "_check_triangle_geometry") as triangle,
            patch.object(checks, "_check_suspended_bessel_points") as bessel,
        ):
            checks.run_model("led_profiles.assemblies.standing")
            checks.run_model("led_profiles.assemblies.triangle")
            checks.run_model("led_profiles.assemblies.suspended")

        clearance.assert_any_call(mock.ANY, "standing", mock.ANY, expected_bought=4)
        clearance.assert_any_call(mock.ANY, "triangle", mock.ANY, expected_bought=12)
        bessel.assert_called_once()
        triangle.assert_called_once()
        assemblies.create_standing.assert_called_once()
        assemblies.create_triangle.assert_called_once()
        assemblies.create_suspended.assert_called_once()


if __name__ == "__main__":
    unittest.main()
