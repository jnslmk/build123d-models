from __future__ import annotations

import unittest

from check_diff import diff_reports, render_diff


def _report(assertions):
    return {"model": "fake", "assertions": assertions, "passed": 0, "failed": 0}


class DiffReportsTests(unittest.TestCase):
    def test_identical_reports_have_no_differences(self) -> None:
        entries = [{"section": "s", "name": "a", "passed": True, "detail": "1.0mm"}]
        diff = diff_reports(_report(entries), _report(entries))
        self.assertEqual(diff, {"added": [], "removed": [], "changed": []})
        self.assertEqual(render_diff(diff), "no differences")

    def test_flip_from_pass_to_fail_is_reported_as_changed(self) -> None:
        old = _report([{"section": "s", "name": "a", "passed": True, "detail": ""}])
        new = _report([{"section": "s", "name": "a", "passed": False, "detail": ""}])
        diff = diff_reports(old, new)
        self.assertEqual(len(diff["changed"]), 1)
        c = diff["changed"][0]
        self.assertEqual((c["old_passed"], c["new_passed"]), (True, False))
        self.assertIn("PASS -> FAIL", render_diff(diff))

    def test_moved_measured_value_is_reported_as_changed_even_if_still_passing(
        self,
    ) -> None:
        old = _report(
            [{"section": "s", "name": "a", "passed": True, "detail": "1.0mm"}]
        )
        new = _report(
            [{"section": "s", "name": "a", "passed": True, "detail": "1.4mm"}]
        )
        diff = diff_reports(old, new)
        self.assertEqual(len(diff["changed"]), 1)
        c = diff["changed"][0]
        self.assertEqual(c["old_detail"], "1.0mm")
        self.assertEqual(c["new_detail"], "1.4mm")
        rendered = render_diff(diff)
        self.assertIn("1.0mm", rendered)
        self.assertIn("1.4mm", rendered)

    def test_assertion_added(self) -> None:
        old = _report([])
        new = _report([{"section": "s", "name": "a", "passed": True, "detail": ""}])
        diff = diff_reports(old, new)
        self.assertEqual(len(diff["added"]), 1)
        self.assertEqual(diff["removed"], [])
        self.assertEqual(diff["changed"], [])
        self.assertIn("added", render_diff(diff))

    def test_assertion_removed(self) -> None:
        old = _report([{"section": "s", "name": "a", "passed": True, "detail": ""}])
        new = _report([])
        diff = diff_reports(old, new)
        self.assertEqual(len(diff["removed"]), 1)
        self.assertEqual(diff["added"], [])
        self.assertEqual(diff["changed"], [])
        self.assertIn("removed", render_diff(diff))

    def test_same_name_different_section_are_distinct_assertions(self) -> None:
        old = _report([{"section": "s1", "name": "a", "passed": True, "detail": ""}])
        new = _report([{"section": "s2", "name": "a", "passed": True, "detail": ""}])
        diff = diff_reports(old, new)
        self.assertEqual(len(diff["added"]), 1)
        self.assertEqual(len(diff["removed"]), 1)
        self.assertEqual(diff["changed"], [])

    def test_moved_embedded_coordinate_is_reported_as_changed_not_remove_add(
        self,
    ) -> None:
        """Round 1 finding: 42/159 real assertion names in a led_psu_enclosure
        report embed a sampled coordinate, e.g. "yoke pilot was cut (y=-40,
        z=52)". A config tweak that moves that coordinate must not turn into a
        remove+add pair -- that's exactly the regression this tool exists to
        surface."""
        old = _report(
            [
                {
                    "section": "yoke",
                    "name": "yoke pilot was cut (y=-40, z=52)",
                    "passed": True,
                    "detail": "",
                }
            ]
        )
        new = _report(
            [
                {
                    "section": "yoke",
                    "name": "yoke pilot was cut (y=-42, z=52)",
                    "passed": True,
                    "detail": "",
                }
            ]
        )
        diff = diff_reports(old, new)
        self.assertEqual(diff["added"], [])
        self.assertEqual(diff["removed"], [])
        self.assertEqual(len(diff["changed"]), 1)
        c = diff["changed"][0]
        self.assertEqual(c["old_name"], "yoke pilot was cut (y=-40, z=52)")
        self.assertEqual(c["new_name"], "yoke pilot was cut (y=-42, z=52)")
        rendered = render_diff(diff)
        self.assertIn(
            "yoke pilot was cut (y=-40, z=52) -> yoke pilot was cut (y=-42, z=52)",
            rendered,
        )

    def test_multiple_occurrences_of_the_same_base_name_stay_distinct(self) -> None:
        """Four boss positions all report "floor is sealed (...)" in one run --
        stripping the coordinate must not collapse them into a single key and
        silently drop three of the four."""
        old = _report(
            [
                {
                    "section": "s",
                    "name": f"floor is sealed ({x}, 0)",
                    "passed": True,
                    "detail": "",
                }
                for x in (-100, -50, 50, 100)
            ]
        )
        # Only the third position's coordinate moves; the rest are untouched.
        new_assertions = [
            {
                "section": "s",
                "name": f"floor is sealed ({x}, 0)",
                "passed": True,
                "detail": "",
            }
            for x in (-100, -50, 50, 100)
        ]
        new_assertions[2]["name"] = "floor is sealed (55, 0)"
        new = _report(new_assertions)

        diff = diff_reports(old, new)
        self.assertEqual(diff["added"], [])
        self.assertEqual(diff["removed"], [])
        self.assertEqual(len(diff["changed"]), 1)
        self.assertEqual(diff["changed"][0]["old_name"], "floor is sealed (50, 0)")
        self.assertEqual(diff["changed"][0]["new_name"], "floor is sealed (55, 0)")

    def test_non_numeric_trailing_parenthetical_is_not_stripped(self) -> None:
        """ "(open)"/"(shut)" style suffixes distinguish real, different
        assertions within one run and must not be normalised away."""
        entries = [
            {
                "section": "s",
                "name": "slider seats (open)",
                "passed": True,
                "detail": "",
            },
            {
                "section": "s",
                "name": "slider seats (shut)",
                "passed": True,
                "detail": "",
            },
        ]
        diff = diff_reports(_report(entries), _report(entries))
        self.assertEqual(diff, {"added": [], "removed": [], "changed": []})


class RenderDiffHeaderTests(unittest.TestCase):
    def test_header_shows_which_two_reports_were_compared(self) -> None:
        diff = {"added": [], "removed": [], "changed": []}
        rendered = render_diff(diff, "old_report.json", "new_report.json")
        self.assertEqual(rendered, "old_report.json -> new_report.json\nno differences")

    def test_header_also_shown_when_there_are_differences(self) -> None:
        old = _report([{"section": "s", "name": "a", "passed": True, "detail": ""}])
        new = _report([{"section": "s", "name": "a", "passed": False, "detail": ""}])
        diff = diff_reports(old, new)
        rendered = render_diff(diff, "led_psu_enclosure", "led_psu_enclosure")
        self.assertTrue(rendered.startswith("led_psu_enclosure -> led_psu_enclosure\n"))

    def test_no_header_when_model_names_are_not_given(self) -> None:
        diff = {"added": [], "removed": [], "changed": []}
        self.assertEqual(render_diff(diff), "no differences")


if __name__ == "__main__":
    unittest.main()
