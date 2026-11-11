#!/usr/bin/env python3
"""Fetch the pinned source papers using an authenticated GitHub CLI session."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import tempfile
from urllib.parse import quote

from catalog import ROOT, git_blob_sha, paper_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", type=Path, default=ROOT.parent / "junior-papers")
    args = parser.parse_args()
    manifest = json.loads((ROOT / "data" / "papers.json").read_text())
    for record in manifest["papers"]:
        destination = paper_path(args.dest, record["file"])
        if destination.is_file() and git_blob_sha(destination) == record["sha"]:
            print(f"Verified {record['file']}")
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        endpoint = (
            f"repos/{manifest['repository']}/contents/{quote(record['path'], safe='/')}"
            f"?ref={manifest['revision']}"
        )
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as target:
                temporary = Path(target.name)
                subprocess.run(
                    ["gh", "api", "-H", "Accept: application/vnd.github.raw+json", endpoint],
                    stdout=target,
                    check=True,
                )
            if git_blob_sha(temporary) != record["sha"]:
                raise ValueError(f"Checksum mismatch for {record['file']}")
            temporary.replace(destination)
            print(f"Downloaded {record['file']}")
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
