# Editing the Junior IOAA book

Compare statements, answers, equations, units, points, and figures against the
source PDFs before changing scientific content. Preserve the official wording
and mark genuine source errors or variant questions visibly. Use editorial
titles only where the papers have none.

Keep one catalog record and one statement fragment per numbered problem.
Official solutions belong in their matching solution fragments. Record missing
solutions explicitly and identify source variants. Preserve identifiers so
problem and solution links stay stable.

The yearly catalogs in `data/` specify zero-based PDF pages and optional crop
rectangles in PDF points. Crop rectangles must include the complete question or
solution and its figures. Figure manifests specify reproducible vector crops.
Original papers and generated editions remain outside the tracked source tree.

After editing, run `python build.py --validate-only`, build the affected
editions, and inspect the affected pages. Check links and source variants.
Changes to the builders should also be checked with a small fixture covering
missing solutions, tall crops, and problem/solution links.
