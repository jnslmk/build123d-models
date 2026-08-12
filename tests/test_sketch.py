"""``sketch.py``'s discovery, ordering and sheet emission.

The geometry here is deliberately trivial -- two boxes -- because what is under
test is the contract between a sketch file and the sheet, not build123d. It also
doubles as the committed worked example of that contract, since ``sketches/`` is
gitignored and so no real sketch can serve as one.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import sketch

FIXTURE = '''
"""Which way up?

Two ways of standing the same block.
"""

from build123d import Box, BuildPart

from sketch import variant

FIDELITY = "Massing only"
NOTES = "First note -- with a dash.\\n\\nSecond note."


@variant(spec={"Footprint": "wide"})
def lying_down():
    """Flat on its back."""
    with BuildPart() as bp:
        Box(40, 30, 10)
    return bp.part


@variant(spec={"Footprint": "narrow", "Overhangs": "none"}, views=("iso", "front"))
def standing_up():
    """Up on end."""
    with BuildPart() as bp:
        Box(10, 30, 40)
    return bp.part
'''


class SketchTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        path = Path(self._tmp.name) / "which_way_up.py"
        path.write_text(FIXTURE)
        self.path = path
        self.module = sketch.load_sketch(str(path))

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_discovers_variants_in_definition_order(self) -> None:
        names = [fn.__name__ for fn, _ in sketch.variants(self.module)]
        self.assertEqual(names, ["lying_down", "standing_up"])

    def test_records_decorator_metadata(self) -> None:
        _, meta = sketch.variants(self.module)[1]
        self.assertEqual(meta.views, ("iso", "front"))
        self.assertEqual(meta.spec["Footprint"], "narrow")

    def test_rejects_an_unknown_view(self) -> None:
        with self.assertRaises(ValueError):
            sketch.variant(views=("sideways",))

    def test_ignores_functions_imported_into_the_sketch(self) -> None:
        """A helper module of shared massing must not put its catalogue on every sheet."""
        other = Path(self._tmp.name) / "borrower.py"
        other.write_text(
            "from which_way_up import lying_down  # noqa: F401\n"
            "from sketch import variant\n"
            "from build123d import Box, BuildPart\n"
            "@variant\n"
            "def only_mine():\n"
            "    '''Mine.'''\n"
            "    with BuildPart() as bp:\n"
            "        Box(5, 5, 5)\n"
            "    return bp.part\n"
        )
        import sys

        sys.path.insert(0, self._tmp.name)
        try:
            module = sketch.load_sketch(str(other))
            names = [fn.__name__ for fn, _ in sketch.variants(module)]
        finally:
            sys.path.remove(self._tmp.name)
            sys.modules.pop("which_way_up", None)
        self.assertEqual(names, ["only_mine"])

    def test_builds_a_self_contained_sheet(self) -> None:
        html = sketch.build_sheet(self.module, self.path)

        # The question, the candidates and the fidelity stamp all reach the page.
        self.assertIn("Which way up?", html)
        self.assertIn("Lying down", html)
        self.assertIn("Standing up", html)
        self.assertIn("Massing only", html)
        self.assertIn("Not a model", html)

        # Lettered in definition order, and the second card carries both views.
        self.assertLess(html.index('class="desig">A'), html.index('class="desig">B'))
        self.assertEqual(html.count("<svg class=\"dwg\""), 3)

        # The comparison table is the union of the spec keys, with a gap marked
        # rather than left blank where a variant did not declare one.
        self.assertIn("Overhangs", html)
        self.assertIn("<td>—</td>", html)

        # Nothing external: no fetch, no CDN, no <img src>.
        for forbidden in ("http://", "https://", "<img", "<script"):
            self.assertNotIn(forbidden, html)

        # Both theme paths are defined, and prose dashes are rendered.
        self.assertIn("prefers-color-scheme: dark", html)
        self.assertIn('[data-theme="dark"]', html)
        self.assertIn("First note — with a dash.", html)

    def test_drawings_follow_the_reader_theme(self) -> None:
        """The baked-in dark-page colours must not survive into the page."""
        html = sketch.build_sheet(self.module, self.path)
        self.assertIn('stroke="currentColor"', html)
        self.assertNotIn(sketch._stroke(sketch.render_svg.VISIBLE_COLOR), html)
        self.assertNotIn(sketch._stroke(sketch.render_svg.HIDDEN_COLOR), html)


if __name__ == "__main__":
    unittest.main()
