"""Turn a throwaway file of crude massing variants into one comparison sheet.

Usage:
    uv run sketch <name|path> [output.html] [--open]

This is the *idea* stage, and it exists because the repo's real loop is far too
expensive to answer "which shape?" with. Measured in this tree: a concept-grade
variant -- boxes and cylinders, no fillets, no clearances, no checks -- builds in
about 0.03 s and renders in about 0.05 s, while ``led_psu_enclosure.create()``
takes 37 s and ``drill_storage.wood.base`` 16 s, before lint, types, checks, a
commit and a Pages deploy. Four options therefore cost one interpreter start,
not four models.

A sketch file lives in ``sketches/``, which is **gitignored on purpose**. A
sketch is a disposable argument, not a model: it has invented dimensions, no
fits from ``models.lib.fits``, no edge treatments and no ``checks.py``, so
committing one would put something in the tree that looks like a model, fails
every rule in AGENTS.md, and cannot be told apart from the real thing six months
later. When a variant wins, it gets *rebuilt* under ``models/`` properly and the
sketch is deleted -- it was never load-bearing.

A sketch file is a plain module::

    \"\"\"How should a small parts box close?\"\"\"          # the question

    from build123d import *
    from sketch import variant

    FIDELITY = "Massing only -- dimensions invented"     # optional, stamped on the sheet

    @variant(spec={"Parts": "2", "Reopens": "freely"})
    def stepped_rabbet():
        \"\"\"Lid drops into a recessed shelf. No undercuts, prints either way up.\"\"\"
        with BuildPart() as bp:
            Box(60, 40, 25)
        return bp.part

Everything the sheet shows is read off that: the module docstring is the
question, each decorated function's name is a variant title, its docstring is
the prose under the drawing, and the ``spec`` dicts become the comparison table.
Variants are lettered A, B, C in definition order.

The output is one self-contained HTML file under ``exports/`` -- inline SVG, no
external anything -- meant to be **published as an artifact** and read on a
phone. It is not a viewer and it is not a model: no colour, no interaction, and
nothing here has been checked against a printer.
"""

from __future__ import annotations

import fontfix  # noqa: F401 -- preload system libfontconfig before OCP imports

import argparse
import contextlib
import html
import importlib.util
import inspect
import io
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from types import FunctionType, ModuleType
from typing import Any, Callable

import render_svg

HERE = Path(__file__).parent.resolve()
SKETCHES = HERE / "sketches"
EXPORTS = HERE / "exports"

DEFAULT_FIDELITY = "Concept grade — not a model"

#: Marker attribute the decorator hangs on a function. Discovery reads the
#: module namespace for it rather than keeping a registry, so importing a sketch
#: twice in one process cannot double-register or leak state between files.
MARKER = "_sketch_variant"


@dataclass
class VariantSpec:
    """What ``@variant`` recorded about one candidate."""

    spec: dict[str, str] = field(default_factory=dict)
    views: tuple[str, ...] = ("iso",)
    title: str | None = None


def variant(
    fn: Callable[[], Any] | None = None,
    *,
    spec: dict[str, Any] | None = None,
    views: tuple[str, ...] | list[str] = ("iso",),
    title: str | None = None,
) -> Any:
    """Mark a zero-arg function as one candidate on the sheet.

    Usable bare (``@variant``) or called (``@variant(spec=..., views=...)``).

    ``spec`` becomes one row of the comparison table -- keep the keys identical
    across variants, because the table's columns are the union of them and a key
    only one variant declares reads as a gap in the others rather than as the
    difference it is. ``views`` renders more than one projection into the same
    card, for the case where an isometric cannot settle the question; the names
    are ``render_svg.VIEWS``.
    """
    unknown = [v for v in views if v not in render_svg.VIEWS]
    if unknown:
        raise ValueError(
            f"Unknown view(s) {unknown}. Available: {', '.join(render_svg.VIEWS)}"
        )

    def wrap(target: Callable[[], Any]) -> Callable[[], Any]:
        setattr(
            target,
            MARKER,
            VariantSpec(
                spec={str(k): str(v) for k, v in (spec or {}).items()},
                views=tuple(views),
                title=title,
            ),
        )
        return target

    return wrap(fn) if fn is not None else wrap


def load_sketch(target: str) -> ModuleType:
    """Import a sketch by bare name (``sketches/<name>.py``) or by path."""
    path = Path(target)
    if not path.suffix:
        path = SKETCHES / f"{target}.py"
    if not path.exists():
        print(f"Error: no sketch at '{path}'")
        sys.exit(1)

    # Imported by location rather than as ``sketches.<name>``: a sketch is
    # deliberately not part of the installed package, and requiring an
    # __init__.py in a gitignored directory would be one more thing to explain.
    spec = importlib.util.spec_from_file_location(f"_sketch_{path.stem}", path)
    loader = spec.loader if spec is not None else None
    if spec is None or loader is None:
        # ``raise SystemExit`` rather than ``sys.exit`` only because the type
        # checker follows a raise and does not follow the call, so the two
        # narrowings below are free instead of needing casts.
        raise SystemExit(f"Error: '{path}' is not importable as Python")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    loader.exec_module(module)
    return module


def variants(module: ModuleType) -> list[tuple[FunctionType, VariantSpec]]:
    """Every decorated function the sketch defines, in definition order.

    Ordered by source line rather than by a registry the decorator appends to,
    so the letters on the sheet follow the file you are reading. That ordering is
    also why this insists on a plain function rather than any callable: the line
    number comes from the object's own source, which a class or a ``partial``
    does not have.

    Functions imported *into* the sketch are skipped -- only what this file
    defines is a candidate, or a shared helper module of massing primitives
    would put its whole catalogue on every sheet.
    """
    found = [
        (obj, getattr(obj, MARKER))
        for obj in vars(module).values()
        if isinstance(obj, FunctionType)
        and hasattr(obj, MARKER)
        and obj.__module__ == module.__name__
    ]
    return sorted(found, key=lambda pair: inspect.getsourcelines(pair[0])[1])


def _stroke(color: Any) -> str:
    """The ``stroke="rgb(r,g,b)"`` attribute ``ExportSVG`` writes for a colour.

    Derived from ``render_svg``'s own constants rather than hardcoded, so
    retuning the palette there cannot silently stop the rebinding below from
    matching -- which would fail as unreadable lines on a light page rather than
    as an error.
    """
    r, g, b = (int(channel * 255) for channel in tuple(color)[:3])
    return f'stroke="rgb({r},{g},{b})"'


def _inline_svg(svg_text: str, label: str) -> str:
    """Rewrite one ``render_svg`` file into an SVG that can sit inside a page.

    Two changes. The outer element is rebuilt so the drawing scales to its box
    instead of carrying a millimetre width, and the two layer colours -- which
    ``render_svg`` bakes in for a dark page -- are rebound: the visible layer to
    ``currentColor`` so it follows the reader's theme, the hidden layer to a
    class the stylesheet drives. Without that a light-theme reader gets pale
    grey lines on white.
    """
    view_box = svg_text.split('viewBox="', 1)[1].split('"', 1)[0]
    body = svg_text.split(">", 2)[2].rsplit("</svg>", 1)[0]
    body = body.replace(_stroke(render_svg.VISIBLE_COLOR), 'stroke="currentColor"')
    body = body.replace(_stroke(render_svg.HIDDEN_COLOR), 'class="hidden-layer"')
    return (
        f'<svg class="dwg" viewBox="{view_box}" preserveAspectRatio="xMidYMid meet"'
        f' role="img" aria-label="{html.escape(label)}">{body}</svg>'
    )


def render_variant(part: Any, views: tuple[str, ...], title: str) -> list[str]:
    """Hidden-line SVG for each requested view, ready to inline.

    Goes through ``render_svg.render_svg`` and a temporary file rather than
    driving ``ExportSVG`` directly. The round trip costs a few milliseconds
    against a build that costs tens, and it buys the guarantee that a sheet and
    a ``uv run render`` of the same part cannot drift apart -- the failure
    ``edge_to_polyline``'s docstring already warns about for the PDF path.
    """
    out: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        for view in views:
            path = Path(tmp) / f"{view}.svg"
            # Swallowed because render_svg reports every file it writes, and
            # here that is a temp path the reader can neither find nor use.
            with contextlib.redirect_stdout(io.StringIO()):
                render_svg.render_svg(part, path, view=view)
            out.append(_inline_svg(path.read_text(), f"{title}, {view} view"))
    return out


def _titlecase(name: str) -> str:
    """``stepped_rabbet`` -> ``Stepped rabbet``."""
    words = name.replace("_", " ").strip()
    return words[:1].upper() + words[1:]


def _prose(text: str) -> str:
    """Escape a docstring for HTML, collapsing whitespace and dashes.

    ``--`` becomes an em dash because that is how this repo writes one in
    Python source, and a sheet is read rather than imported -- leaving it as two
    hyphens is the tell that a page was generated from code and nobody looked.
    """
    return html.escape(" ".join(text.split())).replace("--", "—")


STYLE = """
:root {
  --ground:#E9ECF0; --sheet:#FFFFFF; --ink:#131922; --ink-2:#3B4757;
  --muted:#6C7A89; --rule:#C7CFD9; --rule-soft:#DDE3EA;
  --accent:#0E6B9E; --flag:#92600F; --line-hidden:#98A5B4;
  --mono: ui-monospace, SFMono-Regular, "SF Mono", "JetBrains Mono", Menlo, Consolas, monospace;
  --sans: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --ground:#0F131A; --sheet:#171C25; --ink:#DBE2EA; --ink-2:#AEB9C6;
    --muted:#7A8593; --rule:#2B333E; --rule-soft:#222933;
    --accent:#5CB0E2; --flag:#D6A24E; --line-hidden:#56616F;
  }
}
:root[data-theme="dark"] {
  --ground:#0F131A; --sheet:#171C25; --ink:#DBE2EA; --ink-2:#AEB9C6;
  --muted:#7A8593; --rule:#2B333E; --rule-soft:#222933;
  --accent:#5CB0E2; --flag:#D6A24E; --line-hidden:#56616F;
}
* { box-sizing: border-box; }
body {
  margin:0; background:var(--ground); color:var(--ink); font-family:var(--sans);
  font-size:16px; line-height:1.6; -webkit-font-smoothing:antialiased;
}
.wrap { max-width:62rem; margin:0 auto; padding:2.5rem 1.25rem 4rem;
        display:flex; flex-direction:column; gap:2.25rem; }
.titleblock { background:var(--sheet); border:1px solid var(--rule); }
.titleblock h1 {
  margin:0; padding:1.5rem 1.5rem 1.25rem; font-weight:640;
  font-size:clamp(1.8rem,4.2vw,2.6rem); line-height:1.1;
  letter-spacing:-0.025em; text-wrap:balance;
}
.fields { display:grid; grid-template-columns:repeat(auto-fit,minmax(9.5rem,1fr));
          border-top:1px solid var(--rule); }
.field { padding:0.7rem 1.5rem 0.8rem; border-right:1px solid var(--rule-soft); }
.field:last-child { border-right:0; }
.field dt, .eyebrow {
  font-family:var(--mono); font-size:0.66rem; letter-spacing:0.14em;
  text-transform:uppercase; color:var(--muted);
}
.field dd { margin:0.2rem 0 0; font-family:var(--mono); font-size:0.85rem;
            color:var(--ink); font-variant-numeric:tabular-nums; }
.field dd.flagged { color:var(--flag); }
.standfirst { padding:0 1.5rem 1.5rem; max-width:52ch; }
section { display:flex; flex-direction:column; gap:1rem; }
h2 { margin:0; font-size:1.3rem; font-weight:620; letter-spacing:-0.015em; text-wrap:balance; }
h3 { margin:0; font-size:1rem; font-weight:620; }
p { margin:0; max-width:68ch; color:var(--ink-2); }
code { font-family:var(--mono); font-size:0.86em;
       background:color-mix(in srgb, var(--rule) 38%, transparent);
       padding:0.08em 0.34em; border-radius:2px; }
/* Column count is set per sheet from the number of candidates, not by auto-fit:
   auto-fit leaves four candidates as 3 + 1, and the orphan's empty track reads
   as a broken cell rather than as a wrap. */
.grid { display:grid; grid-template-columns:repeat(var(--cols),minmax(0,1fr)); gap:1rem; }
@media (max-width:62rem) { .grid { grid-template-columns:repeat(2,minmax(0,1fr)); } }
@media (max-width:40rem) { .grid { grid-template-columns:1fr; } }
.variant { background:var(--sheet); border:1px solid var(--rule);
           padding:0.9rem 1rem 1.15rem; display:flex; flex-direction:column; gap:0.6rem; }
.variant header { display:flex; align-items:baseline; gap:0.55rem; }
.desig { font-family:var(--mono); font-size:0.72rem; font-weight:700;
         letter-spacing:0.08em; color:var(--sheet); background:var(--ink);
         padding:0.1rem 0.4rem; }
/* The aspect ratio belongs to the row, not to each drawing: a two-view card
   would otherwise be half the height of a one-view card, and the cards in a row
   would not line up. */
.views { display:flex; gap:0.5rem; aspect-ratio:4/3; }
.viewport {
  flex:1; min-width:0; display:grid; place-items:center; padding:0.4rem;
  background-color:color-mix(in srgb, var(--rule) 14%, transparent);
  background-image:
    linear-gradient(to right, color-mix(in srgb, var(--rule) 55%, transparent) 1px, transparent 1px),
    linear-gradient(to bottom, color-mix(in srgb, var(--rule) 55%, transparent) 1px, transparent 1px);
  background-size:1.25rem 1.25rem;
}
.dwg { width:100%; height:100%; color:var(--ink); }
.dwg .hidden-layer { stroke:var(--line-hidden); }
.variant p { font-size:0.88rem; line-height:1.5; }
.tablewrap { overflow-x:auto; background:var(--sheet);
             border:1px solid var(--rule); padding:0.4rem 1.1rem 0.6rem; }
table { width:100%; border-collapse:collapse; font-size:0.86rem; }
th, td { text-align:left; padding:0.55rem 1rem 0.55rem 0;
         border-bottom:1px solid var(--rule-soft); vertical-align:top; }
tr:last-child td, tr:last-child th { border-bottom:0; }
thead th { font-family:var(--mono); font-size:0.66rem; letter-spacing:0.12em;
           text-transform:uppercase; color:var(--muted); font-weight:400;
           border-bottom:1px solid var(--rule); white-space:nowrap; }
tbody th { font-family:var(--mono); font-weight:700; white-space:nowrap; color:var(--ink); }
td { color:var(--ink-2); font-variant-numeric:tabular-nums; }
.notes { background:var(--sheet); border:1px solid var(--rule);
         border-left:3px solid var(--accent); padding:1.1rem 1.3rem;
         display:flex; flex-direction:column; gap:0.7rem; }
footer { font-family:var(--mono); font-size:0.72rem; color:var(--muted);
         border-top:1px solid var(--rule); padding-top:1rem; line-height:1.7; }
:focus-visible { outline:2px solid var(--accent); outline-offset:2px; }
"""


def build_sheet(module: ModuleType, source: Path) -> str:
    """Build every variant in ``module`` and return the whole sheet as HTML."""
    found = variants(module)
    if not found:
        print(f"Error: {source} defines no @variant functions")
        sys.exit(1)

    question = (module.__doc__ or "").strip().splitlines()
    heading = question[0].strip() if question else source.stem
    standfirst = " ".join(line.strip() for line in question[1:]).strip()
    fidelity = str(getattr(module, "FIDELITY", DEFAULT_FIDELITY))
    notes = str(getattr(module, "NOTES", "")).strip()

    cards: list[str] = []
    rows: list[tuple[str, str, dict[str, str]]] = []
    for index, (fn, meta) in enumerate(found):
        letter = chr(ord("A") + index)
        title = meta.title or _titlecase(fn.__name__)
        drawings = render_variant(fn(), meta.views, title)
        viewports = "".join(f'<div class="viewport">{d}</div>' for d in drawings)
        cards.append(
            f'<article class="variant">'
            f'<header><span class="desig">{letter}</span>'
            f"<h3>{_prose(title)}</h3></header>"
            f'<div class="views">{viewports}</div>'
            f"<p>{_prose(fn.__doc__ or '')}</p></article>"
        )
        rows.append((letter, title, meta.spec))
        print(f"  {letter}  {title} ({', '.join(meta.views)})")

    columns: list[str] = []
    for _, _, spec in rows:
        columns.extend(key for key in spec if key not in columns)

    table = ""
    if columns:
        head = "".join(f"<th scope='col'>{html.escape(c)}</th>" for c in columns)
        body = "".join(
            f"<tr><th scope='row'>{letter}</th><td>{html.escape(title)}</td>"
            + "".join(f"<td>{html.escape(spec.get(c, '—'))}</td>" for c in columns)
            + "</tr>"
            for letter, title, spec in rows
        )
        table = (
            "<section><h2>Side by side</h2><div class='tablewrap'><table>"
            f"<thead><tr><th scope='col'>Var</th><th scope='col'>Candidate</th>{head}</tr></thead>"
            f"<tbody>{body}</tbody></table></div></section>"
        )

    notes_html = ""
    if notes:
        paragraphs = "".join(
            f"<p>{_prose(block)}</p>" for block in notes.split("\n\n") if block.strip()
        )
        notes_html = f"<section><h2>Notes</h2><div class='notes'>{paragraphs}</div></section>"

    standfirst_html = (
        f'<p class="standfirst">{_prose(standfirst)}</p>' if standfirst else ""
    )

    # Four candidates read better as 2x2 than as a row of three and an orphan;
    # anything larger stays at three across so the drawings keep their size.
    grid_columns = 2 if len(found) == 4 else min(len(found), 3)

    return f"""<title>{_prose(heading)}</title>
<style>{STYLE}</style>
<div class="wrap">
  <header class="titleblock">
    <h1>{_prose(heading)}</h1>
    {standfirst_html}
    <dl class="fields">
      <div class="field"><dt>Sketch</dt><dd>{html.escape(source.stem)}</dd></div>
      <div class="field"><dt>Candidates</dt><dd>{len(found)}</dd></div>
      <div class="field"><dt>Fidelity</dt><dd class="flagged">{_prose(fidelity)}</dd></div>
      <div class="field"><dt>Status</dt><dd>Not a model</dd></div>
    </dl>
  </header>
  <section><h2>Candidates</h2>
    <div class="grid" style="--cols:{grid_columns}">{"".join(cards)}</div>
  </section>
  {table}
  {notes_html}
  <footer>
    Hidden-line projections from build123d via <code>render_svg</code>, no colour and no shading.
    Dimensions are for comparison only: nothing here has named fits, edge treatments or geometry
    checks, and no candidate is printable until it is rebuilt under <code>models/</code>.
  </footer>
</div>
"""


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Render a file of crude variants into one comparison sheet",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("sketch", help="Sketch name (sketches/<name>.py) or a path")
    parser.add_argument("output", nargs="?", help="Output HTML (default: exports/sketch-<name>.html)")
    args = parser.parse_args()

    module = load_sketch(args.sketch)
    source = Path(module.__file__ or args.sketch)

    print(f"Building {source}:")
    sheet = build_sheet(module, source)

    output = Path(args.output) if args.output else EXPORTS / f"sketch-{source.stem}.html"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(sheet)
    print(f"\nWrote {output} ({len(sheet) / 1024:.1f} KB) — publish it as an artifact")


if __name__ == "__main__":
    main()
