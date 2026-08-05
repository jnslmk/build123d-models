"""Diff two ``uv run check <name> --json <path>`` reports.

Adapted from cyberchitta/cad-khana (https://github.com/cyberchitta/cad-khana,
Apache-2.0 licensed), whose ``khana diff <old> <new>`` compares two
``mechanism.json`` diagnostics runs. This is the same idea against this repo's
own report shape (see ``check.py`` and ``models/lib/checks.py``): every
assertion an old and a new run share is compared for a pass/fail flip or a
changed measured/expected detail; anything only on one side is reported as
added or removed.

    uv run check-diff old.json new.json

Exit code follows the ``diff``(1) convention: 0 if the two reports carry the
same assertions with the same results, 1 if anything differs, 2 if a file
could not be read as a report.

**Identity key.** Assertions are matched across the two reports by section
plus a *base name* -- the raw ``name`` with one trailing, digit-bearing
parenthesised group stripped (round 1 review measured this against a real
``led_psu_enclosure`` report: 42 of 159 assertion names there embed a sampled
coordinate this way, e.g. ``"yoke pilot was cut (y=-40, z=52)"``). Stripping
it is what lets a moved coordinate read as one *changed* assertion instead of
a remove+add pair -- exactly the geometry-regression case this tool exists
for. Because several distinct samples in one run legitimately share a base
name (four boss positions each report "floor under the stud is sealed
(...)"), the base name alone is not unique *within* a report; matching also
needs each base name's occurrence index (the 1st, 2nd, ... assertion with
that section+base name, in report order) to tell them apart. Two runs of the
same code sample points in the same order, so pairing by occurrence index is
stable across old/new even though the underlying loop -- and the label text
its samples carry -- never changes shape between them. The full, unstripped
name is always what gets displayed; only the matching key is normalised.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# One trailing parenthesised group that contains a digit -- a sampled
# coordinate or index baked into the label text, e.g. " (-100, -48)" or
# " (y=-40, z=52)". Groups with no digit (" (open)", " (no weld)") are left
# alone: they distinguish genuinely different assertions within one run, not
# a measurement that moves between runs.
_TRAILING_COORD_RE = re.compile(r"\s*\([^()]*\d[^()]*\)\s*$")


def _load(path: str) -> dict:
    return json.loads(Path(path).read_text())


def _base_name(name: str) -> str:
    """``name`` with one trailing digit-bearing parenthesised group stripped."""
    return _TRAILING_COORD_RE.sub("", name)


def _keyed(assertions: list[dict]) -> dict[tuple[str, str, int], dict]:
    """Every assertion in report order, keyed by (section, base name, Nth).

    The occurrence count is per (section, base name): the first "floor under
    the stud is sealed (...)" in "PSU plate snap studs" is occurrence 0, the
    second is 1, and so on -- which is what keeps four sampled positions that
    share a base name distinct while still letting each pair with its
    counterpart in the other report.
    """
    counts: dict[tuple[str, str], int] = {}
    keyed: dict[tuple[str, str, int], dict] = {}
    for e in assertions:
        section = e.get("section", "")
        base = _base_name(e.get("name", ""))
        k = (section, base)
        idx = counts.get(k, 0)
        counts[k] = idx + 1
        keyed[(section, base, idx)] = e
    return keyed


def diff_reports(old: dict, new: dict) -> dict:
    """Compare two report dicts (as produced by ``Report.to_dict()``).

    Returns a dict with ``added``, ``removed`` (assertion entries present in
    only one report) and ``changed`` (entries present in both whose ``passed``
    and/or ``detail`` differ, or whose raw ``name`` differs even though the
    base name and occurrence matched -- the coordinate-moved case).
    """
    old_entries = _keyed(old.get("assertions", []))
    new_entries = _keyed(new.get("assertions", []))

    added = [new_entries[k] for k in new_entries if k not in old_entries]
    removed = [old_entries[k] for k in old_entries if k not in new_entries]

    changed = []
    for k in old_entries:
        if k not in new_entries:
            continue
        o, n = old_entries[k], new_entries[k]
        if (
            o.get("passed") != n.get("passed")
            or o.get("detail") != n.get("detail")
            or o.get("name") != n.get("name")
        ):
            changed.append(
                {
                    "section": k[0],
                    "old_name": o.get("name", ""),
                    "new_name": n.get("name", ""),
                    "old_passed": o.get("passed"),
                    "new_passed": n.get("passed"),
                    "old_detail": o.get("detail", ""),
                    "new_detail": n.get("detail", ""),
                }
            )

    return {"added": added, "removed": removed, "changed": changed}


def render_diff(diff: dict, old_model: str = "", new_model: str = "") -> str:
    """Render a ``diff_reports()`` result. ``old_model``/``new_model`` -- the
    report identifiers ``main()`` passes (a model name, or the file path as a
    fallback) -- head the output, so the printed diff always says which two
    reports it compared rather than leaving that to the caller's own output.
    """
    header = f"{old_model} -> {new_model}" if (old_model or new_model) else ""

    lines: list[str] = []
    if not diff["added"] and not diff["removed"] and not diff["changed"]:
        body = "no differences"
        return f"{header}\n{body}" if header else body

    if diff["changed"]:
        lines.append(f"{len(diff['changed'])} assertion(s) changed:")
        for c in diff["changed"]:
            flipped = c["old_passed"] != c["new_passed"]
            renamed = c["old_name"] != c["new_name"]
            old_mark = "PASS" if c["old_passed"] else "FAIL"
            new_mark = "PASS" if c["new_passed"] else "FAIL"
            name = (
                c["new_name"] if not renamed else f"{c['old_name']} -> {c['new_name']}"
            )
            label = f"  [{c['section']}] {name}" if c["section"] else f"  {name}"
            lines.append(label)
            if flipped:
                lines.append(f"    {old_mark} -> {new_mark}")
            if c["old_detail"] != c["new_detail"]:
                lines.append(f"    detail: {c['old_detail']!r} -> {c['new_detail']!r}")

    if diff["removed"]:
        lines.append(f"\n{len(diff['removed'])} assertion(s) removed:")
        for e in diff["removed"]:
            label = (
                f"[{e.get('section')}] {e.get('name')}"
                if e.get("section")
                else e.get("name")
            )
            lines.append(f"  - {label}")

    if diff["added"]:
        lines.append(f"\n{len(diff['added'])} assertion(s) added:")
        for e in diff["added"]:
            label = (
                f"[{e.get('section')}] {e.get('name')}"
                if e.get("section")
                else e.get("name")
            )
            mark = "PASS" if e.get("passed") else "FAIL"
            lines.append(f"  + [{mark}] {label}")

    body = "\n".join(lines)
    return f"{header}\n{body}" if header else body


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: uv run check-diff <old.json> <new.json>")
        sys.exit(2)

    old_path, new_path = sys.argv[1], sys.argv[2]
    try:
        old = _load(old_path)
        new = _load(new_path)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Could not read a report: {exc}")
        sys.exit(2)

    diff = diff_reports(old, new)
    print(render_diff(diff, old.get("model", old_path), new.get("model", new_path)))
    sys.exit(1 if (diff["added"] or diff["removed"] or diff["changed"]) else 0)


if __name__ == "__main__":
    main()
