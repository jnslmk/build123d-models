from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path

import check as check_module


class NoChecksBackwardCompatTests(unittest.TestCase):
    """`cube` has neither `checks.main()` nor `check()` -- the plain-argv path
    must keep printing exactly the same message and exit 0, --json or not."""

    def test_no_flags_prints_no_checks_and_exits_0(self) -> None:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            with self.assertRaises(SystemExit) as ctx:
                sys.argv = ["check.py", "cube"]
                check_module.main()
        self.assertEqual(ctx.exception.code, 0)
        self.assertEqual(
            out.getvalue(),
            "Model 'cube' has no checks defined (no checks.main(), no check()).\n",
        )

    def test_json_flag_keeps_same_stdout_and_exit_and_writes_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "report.json")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                with self.assertRaises(SystemExit) as ctx:
                    sys.argv = ["check.py", "cube", "--json", path]
                    check_module.main()
            self.assertEqual(ctx.exception.code, 0)
            self.assertEqual(
                out.getvalue(),
                "Model 'cube' has no checks defined (no checks.main(), no check()).\n",
            )
            payload = json.loads(Path(path).read_text())
            self.assertEqual(payload["model"], "cube")
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


if __name__ == "__main__":
    unittest.main()
