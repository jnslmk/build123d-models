"""Repack upstream build123d 0.11.1 for lazy browser-only sklearn installation.

Run from the repository root with ``python website/browser-wheels/build_wheel.py``.
The upstream wheel, including its Apache-2.0 license, is fetched and SHA-256
verified; only the two DBSCAN call sites and the sklearn requirement are changed.
"""

from __future__ import annotations

import base64
import csv
import hashlib
import io
import urllib.request
import zipfile
from pathlib import Path

WHEEL = "build123d-0.11.1-py3-none-any.whl"
URL = "https://files.pythonhosted.org/packages/py3/b/build123d/" + WHEEL
UPSTREAM_SHA256 = "4e95fa7ccbdc83e624313be492e7c4f5f0eb2ea1df36130eb718bb0c25a89e10"
BROWSER_SHA256 = "fa97b4aa763d72591ea2206cc52bf24314e273de740544abf4aa34a41f4336fa"
DESTINATION = Path(__file__).with_name(WHEEL)
MODULE = "build123d/brep_from_stl.py"
DIST_INFO = "build123d-0.11.1.dist-info/"


def replace_once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise ValueError(f"Expected exactly one occurrence of {old!r}")
    return text.replace(old, new)


def main() -> None:
    upstream = urllib.request.urlopen(URL).read()
    if hashlib.sha256(upstream).hexdigest() != UPSTREAM_SHA256:
        raise ValueError("Upstream build123d wheel SHA-256 mismatch")
    with zipfile.ZipFile(io.BytesIO(upstream)) as source:
        files = {
            item.filename: source.read(item.filename) for item in source.infolist()
        }
        module = files[MODULE].decode()
        import_line = (
            "from sklearn.cluster import DBSCAN  # type: ignore[import-untyped]\n"
        )
        module = replace_once(module, import_line, "")
        for signature in (
            "    labels = DBSCAN(eps=eps, min_samples=min_samples)"
            ".fit(_point_rows(points)).labels_\n",
            "    labels = (\n        DBSCAN(eps=eps, min_samples=min_samples, "
            'metric="cosine")\n',
        ):
            module = replace_once(
                module,
                signature,
                "    from sklearn.cluster import DBSCAN  "
                "# type: ignore[import-untyped]\n\n" + signature,
            )
        files[MODULE] = module.encode()
        metadata = files[DIST_INFO + "METADATA"].decode()
        requirement = "Requires-Dist: scikit-learn<2,>=1.5\n"
        files[DIST_INFO + "METADATA"] = replace_once(metadata, requirement, "").encode()
        record = DIST_INFO + "RECORD"
        rows = []
        for name, content in files.items():
            if name == record:
                rows.append((name, "", ""))
            else:
                digest = (
                    base64.urlsafe_b64encode(hashlib.sha256(content).digest())
                    .decode()
                    .rstrip("=")
                )
                rows.append((name, "sha256=" + digest, str(len(content))))
        output = io.StringIO(newline="")
        csv.writer(output, lineterminator="\n").writerows(rows)
        files[record] = output.getvalue().encode()
        result = io.BytesIO()
        with zipfile.ZipFile(result, "w") as wheel:
            for item in source.infolist():
                wheel.writestr(item, files[item.filename])
    data = result.getvalue()
    if hashlib.sha256(data).hexdigest() != BROWSER_SHA256:
        raise ValueError("Browser build123d wheel SHA-256 mismatch")
    DESTINATION.write_bytes(data)
    print(f"{DESTINATION}: {len(data)} bytes, SHA-256 {BROWSER_SHA256}")


if __name__ == "__main__":
    main()
