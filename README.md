# Junior IOAA Problem Book

Junior IOAA problems and official solutions from 2022–2025, organized by topic.
The project produces two complementary editions.

- The LaTeX edition contains editable statements, official reasoning, inline
  point values, and vector figures.
- The crop edition reproduces the source question and solution spans as vector
  PDF content.

Both editions group theory problems by subject and collect observation tasks
in a final chapter grouped by round. Each chapter is followed by its solutions.
The books include a table of contents, an index by year, and links between each
problem and its solution.

The editorial catalogs record each original label, year, host, point value,
topic, and source crop. Figures are extracted from explicit crop recipes.
Missing official solutions and mismatched source variants carry explanatory
notes. Verification records are kept in [verification/](verification/).

## Build

Use Python 3.10 or later, PyMuPDF, and a TeX installation with latexmk,
pdfLaTeX, Latin Modern, and the standard packages used by [latex/book.tex](latex/book.tex).

    python -m pip install -r requirements.txt

The input papers live outside this repository. The pinned source archive is
the Junior Past Papers 2022-2025 directory of
[adrianIam/stars](https://github.com/adrianIam/stars/tree/main/Junior%20Past%20Papers%202022-2025).
Downloading from that archive currently requires repository access and an
authenticated [GitHub CLI](https://cli.github.com/).

    gh auth login
    python fetch_papers.py --dest ../junior-papers
    python build.py --validate-only
    python build.py

The fetcher verifies every input against its pinned Git blob checksum. It
reuses verified local inputs, so a build can run offline after fetching.

The outputs are build/junior-ioaa-problem-book.pdf and
build/junior-ioaa-problem-book-crops.pdf. The LaTeX build also stages editable
master files and extracted figures beside the output. Generated files are
ignored by Git.

To build one edition or use a different archive location, run

    python build.py --edition latex --papers-dir /path/to/junior-papers
    python build.py --edition crop --papers-dir /path/to/junior-papers

IOAA_JUNIOR_PAPERS_DIR also selects the source archive.

## Edit or extend

- data/YYYY.json contains the problem catalog and source crop spans.
- data/figures-YYYY.json contains figure crop recipes.
- [data/papers.json](data/papers.json) pins the papers to a revision and checksums.
- [latex/problems/](latex/problems/) and [latex/solutions/](latex/solutions/)
  contain the editable transcriptions.
- [catalog.py](catalog.py) validates inputs and defines chapter and round order.
- [latex/build_book.py](latex/build_book.py) and
  [source/assemble_book.py](source/assemble_book.py) build the editions.

To add another year, register its source papers, add a yearly catalog and
transcriptions, record figure recipes, and write a verification record.
Validate, build both editions, and inspect the new pages and links.

## Attribution

This project follows the topic-book approach of
[ioanazelko/ioaa-problem-book](https://github.com/ioanazelko/ioaa-problem-book).
Its build software and layout were written independently. See
[NOTICE.md](NOTICE.md) for source attribution and content rights.
