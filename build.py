#!/usr/bin/env python3
"""Validate the catalog and build the Junior IOAA problem book."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

from catalog import ROOT, load_catalog, validate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--edition", choices=("latex", "crop", "all"), default="all")
    parser.add_argument(
        "--papers-dir",
        type=Path,
        default=Path(os.environ.get("IOAA_JUNIOR_PAPERS_DIR", ROOT.parent / "junior-papers")),
    )
    parser.add_argument("--output-dir", type=Path, default=ROOT / "build")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    try:
        problems, figures = load_catalog()
        counts = validate(problems, figures, args.papers_dir)
        print(
            f"Validated {counts['problems']} problems, {counts['solutions']} entries with official solution material, "
            f"and {counts['figures']} figures."
        )
        if args.validate_only:
            return 0
        args.output_dir.mkdir(parents=True, exist_ok=True)
        if args.edition in ("crop", "all"):
            from source.assemble_book import build_crop

            output = args.output_dir / "junior-ioaa-problem-book-crops.pdf"
            build_crop(problems, args.papers_dir, output)
            print(f"Built {output}")
        if args.edition in ("latex", "all"):
            from latex.build_book import build_latex

            output = args.output_dir / "junior-ioaa-problem-book.pdf"
            build_latex(problems, figures, args.papers_dir, output)
            print(f"Built {output}")
    except (KeyError, ValueError, OSError, RuntimeError) as error:
        print(f"Build failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
