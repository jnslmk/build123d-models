"""Geometry assertions for the stone set.

    uv run check drill_storage.stone

The assertions themselves live in ``drill_storage.checks`` and are shared with
the other two variants -- there is one design here, cut three ways, and a check
that only ran against one set would be a check the other two dodge. This runs
them against ``sets.STONE`` alone, which builds three parts instead of eleven.
"""

from __future__ import annotations

import sys

from ..checks import run_for
from ...lib.checks import Report
from ..sets import STONE as SET


def run() -> Report:
    return run_for(SET)


def main() -> None:
    r = run()
    print(r.render())
    sys.exit(1 if r.failures else 0)


if __name__ == "__main__":
    main()
