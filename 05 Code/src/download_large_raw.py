"""Re-download the large raw files that are NOT stored in the Git repository, then verify
each against the SHA-256 recorded in data/raw/source_manifest.csv.

    python src/download_large_raw.py            # IMD rainfall 1950-2025 (required by the pipeline)
    python src/download_large_raw.py --optional # also geoBoundaries ADM2/ADM3 (not used by the pipeline)
"""
from __future__ import annotations

import argparse
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import RAW, ROOT, SRC, sha256  # noqa: E402

IMD_URL = "https://www.imdpune.gov.in/cmpg/Griddata/RF25.php"
GEOBOUNDARIES = {
    "boundaries/geoboundaries/geoBoundaries-IND-ADM2-all.zip":
        "https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/IND/ADM2/geoBoundaries-IND-ADM2-all.zip",
    "boundaries/geoboundaries/geoBoundaries-IND-ADM3-all.zip":
        "https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/IND/ADM3/geoBoundaries-IND-ADM3-all.zip",
}


def fetch(url: str, out: Path, data: dict | None = None) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    body = urllib.parse.urlencode(data).encode() if data else None
    with urllib.request.urlopen(urllib.request.Request(url, data=body), timeout=900) as r, open(out, "wb") as f:
        f.write(r.read())


def verify(path: Path, expected: dict) -> str:
    key = str(path.relative_to(ROOT))
    if key not in expected:
        return "not in manifest"
    return "ok" if sha256(path) == expected[key] else "HASH MISMATCH (source file changed since the manifest was built)"


def main(optional: bool) -> None:
    man = pd.read_csv(SRC["manifest"]).dropna(subset=["sha256"])
    expected = dict(zip(man.local_path, man.sha256))
    jobs = [(SRC["imd_dir"] / f"ind{y}_rfp25.nc", IMD_URL, {"RF25": y}) for y in range(1950, 2026)]
    if optional:
        jobs += [(RAW / p, u, None) for p, u in GEOBOUNDARIES.items()]
    for out, url, data in jobs:
        if out.exists() and verify(out, expected) == "ok":
            continue
        print(f"downloading {out.relative_to(ROOT)}", flush=True)
        fetch(url, out, data)
        print(f"  {verify(out, expected)}", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--optional", action="store_true")
    main(ap.parse_args().optional)
