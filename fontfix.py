"""Make OCP's font stack use the system libfontconfig.

``cadquery-ocp`` (pulled in by ``build123d`` / ``ocp_vscode``) bundles an old
``libfontconfig`` (1.12.x) that cannot parse a modern system's fontconfig
2.15+ config files. OCCT therefore floods stderr with ``invalid constant`` /
``xsi:nil`` warnings on every font operation -- e.g. every ``Text`` in a model.

Loading the *system* ``libfontconfig`` with ``RTLD_GLOBAL`` before any
OCP-backed module is imported makes OCCT's font calls bind to the
config-compatible system library instead, so the warnings disappear while font
lookup keeps working.

Import this module for its side effect *before* importing ``build123d``,
``ocp_vscode`` or ``ocp_tessellate``. Set ``OCP_FONTFIX=0`` to opt out.
"""

from __future__ import annotations

import ctypes
import os
import sys
from ctypes.util import find_library


def preload_system_fontconfig() -> bool:
    """Load the system libfontconfig into the global symbol scope.

    Returns True if a system library was loaded. No-op off Linux, when opted
    out, or when no system libfontconfig can be found (OCP then falls back to
    its bundled copy, i.e. the pre-existing behaviour).
    """
    if sys.platform != "linux" or os.environ.get("OCP_FONTFIX") == "0":
        return False

    candidates = [
        "/usr/lib/libfontconfig.so.1",
        "/usr/lib64/libfontconfig.so.1",
        "/usr/lib/x86_64-linux-gnu/libfontconfig.so.1",
        "/lib/x86_64-linux-gnu/libfontconfig.so.1",
    ]
    resolved = find_library("fontconfig")
    if resolved:
        candidates.append(resolved)

    for path in candidates:
        try:
            ctypes.CDLL(path, mode=os.RTLD_GLOBAL | os.RTLD_NOW)
            return True
        except OSError:
            continue
    return False


preload_system_fontconfig()
