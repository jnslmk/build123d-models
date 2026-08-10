"""The per-model "last edited" date the site shows, and the ways it can lie.

The date is the one field in the manifest a reader cannot sanity-check by
looking at the model: a wrong STL is visibly wrong, a wrong timestamp just looks
like a timestamp. So the failure modes get pinned here rather than trusted.

Three of them are worth naming, because all three produce a plausible answer:

* Dating a part by the file its own name resolves to. Most parts in this repo
  are four lines over a shared engine (``drill_storage.wood.base`` over
  ``drill_storage/box.py``), so that reads a week old the morning after the
  engine changed. ``_last_edited`` takes the whole import closure instead.
* Letting the closure carry ``checks.py`` with it. ``models/lib/checks.py`` is
  in nearly every model's closure, so one commit tightening a shared assertion
  would redate half the site without a single model having changed.
* A shallow clone, where one commit adds every file and every model comes out
  with the identical date. Nothing raises; the site just shows 41 lies. The
  test below builds a real shallow clone and asserts the flattening it causes,
  so the ``fetch-depth: 0`` in ``build.yml`` has a reason recorded next to it.

These tests run ``git`` in temporary repositories rather than reading this one's
history, so they do not go stale as commits land. Nothing imports a model, so
the suite stays fast.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import website
from model_deps import model_files


def git(repo: Path, *args: str, when: str | None = None) -> None:
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@e"}
    env |= {"GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@e"}
    if when:
        env |= {"GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when}
    subprocess.run(["git", "-C", str(repo), *args], check=True, env=env,
                   capture_output=True)


class CommitDatesTests(unittest.TestCase):
    """``_commit_dates`` -- one git log, newest date per path."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.addCleanup(website._commit_dates.cache_clear)
        website._commit_dates.cache_clear()
        # The module caches its answer *and* reads the repo it lives in, so both
        # have to be redirected for the duration of a test.
        self._real_here = website.HERE
        website.HERE = self.tmp
        self.addCleanup(setattr, website, "HERE", self._real_here)

        git(self.tmp, "init", "-q", "-b", "main")
        (self.tmp / "old.py").write_text("x = 1\n")
        git(self.tmp, "add", "-A")
        git(self.tmp, "commit", "-qm", "one", when="2020-01-01T00:00:00+00:00")
        (self.tmp / "old.py").write_text("x = 2\n")
        (self.tmp / "new.py").write_text("y = 1\n")
        git(self.tmp, "add", "-A")
        git(self.tmp, "commit", "-qm", "two", when="2021-06-02T03:04:05+00:00")

    def test_a_path_takes_its_newest_commit(self) -> None:
        dates = website._commit_dates()
        self.assertEqual(
            dates["old.py"].astimezone(timezone.utc),
            datetime(2021, 6, 2, 3, 4, 5, tzinfo=timezone.utc),
        )

    def test_a_path_untouched_since_its_first_commit_keeps_that_date(self) -> None:
        (self.tmp / "old.py").write_text("x = 3\n")
        git(self.tmp, "add", "-A")
        git(self.tmp, "commit", "-qm", "three", when="2022-01-01T00:00:00+00:00")
        website._commit_dates.cache_clear()
        dates = website._commit_dates()
        self.assertEqual(dates["new.py"].year, 2021)
        self.assertEqual(dates["old.py"].year, 2022)

    def test_no_repository_is_not_an_error(self) -> None:
        # A tarball of the sources still has to build a bundle; _last_edited
        # falls back to mtimes, so the empty map is the contract here.
        outside = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, outside, ignore_errors=True)
        website.HERE = outside
        website._commit_dates.cache_clear()
        self.assertEqual(website._commit_dates(), {})


class LastEditedTests(unittest.TestCase):
    """``_last_edited`` -- newest date over a model's whole import closure."""

    def setUp(self) -> None:
        self.addCleanup(website._commit_dates.cache_clear)
        website._commit_dates.cache_clear()

    def test_iso_utc_to_the_second(self) -> None:
        stamp = website._last_edited("lens_cap")
        assert stamp is not None
        self.assertRegex(stamp, r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")
        self.assertEqual(
            datetime.fromisoformat(stamp).tzinfo,
            timezone.utc,
        )

    def test_every_model_gets_a_date(self) -> None:
        from tessellate_models import MODELS

        undated = [name for name in MODELS if website._last_edited(name) is None]
        self.assertEqual(undated, [])

    def test_a_shared_engine_dates_the_parts_cut_from_it(self) -> None:
        # The whole reason the closure is used: base.py is a thin module over
        # drill_storage/box.py, so its date has to be able to come from box.py.
        dates = website._commit_dates()
        engine = dates[str(Path("models/drill_storage/box.py"))]
        stamp = website._last_edited("drill_storage.wood.base")
        assert stamp is not None
        self.assertGreaterEqual(datetime.fromisoformat(stamp), engine)

    def test_a_shared_checks_module_does_not_redate_the_model(self) -> None:
        # Driven off a stubbed history rather than the real one, so it keeps
        # testing the rule after the next commit to models/lib/checks.py.
        files = model_files("lens_cap")
        self.assertTrue(
            any(p.name == "checks.py" for p in files),
            "the case this guards is gone: lens_cap no longer imports a checks module",
        )
        old = datetime(2020, 1, 1, tzinfo=timezone.utc)
        new = datetime(2030, 1, 1, tzinfo=timezone.utc)
        fake = {
            str(p.relative_to(website.HERE)): (new if p.name == "checks.py" else old)
            for p in files
        }
        self.addCleanup(setattr, website, "_commit_dates", website._commit_dates)
        website._commit_dates = lambda: fake
        self.assertEqual(website._last_edited("lens_cap"), "2020-01-01T00:00:00Z")

    def test_a_model_is_never_older_than_its_own_source(self) -> None:
        dates = website._commit_dates()
        own = dates[str(Path("models/lens_cap.py"))]
        stamp = website._last_edited("lens_cap")
        assert stamp is not None
        self.assertGreaterEqual(datetime.fromisoformat(stamp), own)


class ShallowCloneTests(unittest.TestCase):
    """Why ``build.yml`` checks out the full history for the bundle job."""

    def test_depth_one_flattens_every_date_onto_the_last_commit(self) -> None:
        src = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, src, ignore_errors=True)
        git(src, "init", "-q", "-b", "main")
        (src / "a.py").write_text("a = 1\n")
        git(src, "add", "-A")
        git(src, "commit", "-qm", "a", when="2020-01-01T00:00:00+00:00")
        (src / "b.py").write_text("b = 1\n")
        git(src, "add", "-A")
        git(src, "commit", "-qm", "b", when="2024-01-01T00:00:00+00:00")

        shallow = Path(tempfile.mkdtemp()) / "clone"
        self.addCleanup(shutil.rmtree, shallow.parent, ignore_errors=True)
        subprocess.run(
            ["git", "clone", "-q", "--depth", "1", f"file://{src}", str(shallow)],
            check=True, capture_output=True,
        )

        self.addCleanup(setattr, website, "HERE", website.HERE)
        website.HERE = shallow
        website._commit_dates.cache_clear()
        self.addCleanup(website._commit_dates.cache_clear)
        dates = website._commit_dates()
        # a.py has not been touched since 2020, but the shallow clone has only
        # the 2024 commit -- which adds both files. Hence fetch-depth: 0.
        self.assertEqual(dates["a.py"].year, 2024)
        self.assertEqual(dates["b.py"].year, 2024)


if __name__ == "__main__":
    unittest.main()
