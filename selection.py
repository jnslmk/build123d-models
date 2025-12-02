#!/usr/bin/env python3
"""CLI to query the viewer's selection buffer."""

from __future__ import annotations

import json
import sys
import urllib.request
import urllib.error


VIEWER_URL = "http://127.0.0.1:3939"


def get_selection() -> list[dict]:
    """Fetch selection buffer from viewer server."""
    try:
        with urllib.request.urlopen(f"{VIEWER_URL}/selection", timeout=2) as response:
            return json.loads(response.read().decode())
    except urllib.error.URLError:
        return []


def format_entry(entry: dict) -> str:
    """Format a selection entry for human-readable output."""
    elem_type = entry["type"].capitalize()
    idx = entry["index"]
    geom = entry["geometry"]
    selector = entry.get("selector", {})
    expr = selector.get("expression", f"{entry['type']}s()[{idx}]")
    confidence = selector.get("confidence", "low")

    warning = " ⚠️" if confidence == "low" else ""
    return f"  {elem_type} {idx}: {geom}, {expr}{warning}"


def main() -> None:
    """Main entry point."""
    selection = get_selection()

    if not selection:
        print("No elements selected (or viewer not running)", file=sys.stderr)
        sys.exit(1)

    # Human-readable summary to stderr
    print(f"Selected {len(selection)} element(s):", file=sys.stderr)
    for entry in selection:
        print(format_entry(entry), file=sys.stderr)
    print(file=sys.stderr)

    # JSON to stdout (for machine consumption)
    print(json.dumps(selection, indent=2))


if __name__ == "__main__":
    main()
