"""Command-line access to sketches -- the same operations the MCP server exposes.

uv run sketch list                 # list sketches on disk
uv run sketch show <name>          # print the document + solve status
uv run sketch solve <name>         # re-solve and save
uv run sketch codegen <name>       # (re-solve and) write models/<name>.py
uv run sketch demo                 # create an example bracket sketch
"""

from __future__ import annotations

import json
import sys

from sketch import codegen, commands
from sketch.model import Sketch
from sketch.solver import solve


def _demo() -> Sketch:
    """A 40x24 mm bracket plate with two mounting holes -- exercises the whole stack."""
    sk = Sketch(name="demo_bracket", extrude=3.0)
    commands.add_rect(sk, 0, 0, 40, 24)
    commands.add_circle(sk, 8, 12, 2.5, role="hole")
    commands.add_circle(sk, 32, 12, 2.5, role="hole")
    solve(sk)
    return sk


def main() -> None:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return
    cmd = args[0]

    if cmd == "list":
        names = Sketch.list_names()
        print(
            "\n".join(names)
            if names
            else "(no sketches yet -- try: uv run sketch demo)"
        )
        return

    if cmd == "demo":
        sk = _demo()
        path = sk.save()
        print(f"Wrote {path}")
        print(f"Solve: {solve(sk).summary()}")
        return

    if cmd in ("show", "solve", "codegen"):
        if len(args) < 2:
            print(f"Usage: uv run sketch {cmd} <name>")
            sys.exit(1)
        sk = Sketch.load(args[1])
        report = solve(sk)
        if cmd == "show":
            print(json.dumps(sk.to_dict(), indent=2))
            print(f"\nSolve: {report.summary()}")
            return
        sk.save()
        if cmd == "solve":
            print(f"{args[1]}: {report.summary()}")
            return
        path = codegen.write_model(sk)
        print(f"Wrote {path}  ({report.summary()})")
        print(f"Preview it with:  uv run show {sk.name}")
        return

    print(f"Unknown command {cmd!r}")
    print(__doc__)
    sys.exit(1)


if __name__ == "__main__":
    main()
