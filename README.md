# Junior IOAA Problem Book

A collection of 66 Junior International Olympiad on Astronomy and Astrophysics
(IOAA) problems from 2022–2025, with official solution material for 63 entries.
Use it to practise for the competition, explore astronomy problems, or find
questions for lessons and study groups.

## Read the book

### Latest edition — Version 2

**[Download junior-ioaa-problem-book-2.pdf (Version 2)](https://raw.githubusercontent.com/adrianIam/junior-ioaa-problem-book/main/junior-ioaa-problem-book-2.pdf)**

You can also [preview the PDF on GitHub](junior-ioaa-problem-book-2.pdf).
No software installation or setup is needed to read it. Once downloaded, you
can use it offline in your usual PDF reader.

An [alternative PDF preserving source layouts where available (Version 2)](https://raw.githubusercontent.com/adrianIam/junior-ioaa-problem-book/main/junior-ioaa-problem-book-unformatted-2.pdf)
is also available. You can [preview the alternative PDF on GitHub](junior-ioaa-problem-book-unformatted-2.pdf).

### Previous edition — Version 1 (archived)

The original editions remain available for reference:

- [Version 1 — typeset PDF](archive/v1/junior-ioaa-problem-book.pdf)
- [Version 1 — unformatted PDF](archive/v1/junior-ioaa-problem-book-unformatted.pdf)

## How to use it

- **Practise by topic:** theory problems are grouped by subject, so you can
  focus on one area at a time.
- **Try observation tasks:** these appear in the final chapter, grouped by
  competition round.
- **Check your work:** solutions follow each chapter, with links between
  problems and their solutions.
- **Find a particular year's questions:** use the index by year or the table
  of contents.

Try a problem before opening its solution, then compare your approach with
the official reasoning.

## What's included

| Year | Problems | Entries with official solution material |
|---|---:|---:|
| 2022 | 15 | 13 |
| 2023 | 18 | 17 |
| 2024 | 17 | 17 |
| 2025 | 16 | 16 |
| **Total** | **66** | **63** |

### Notes for readers

Some original papers are incomplete or have different versions. The book
includes notes wherever this affects a problem or its solution.

- Two 2022 answer keys refer to different versions of their questions. The
  supplied reasoning is included, with the mismatch clearly identified.
- Official solutions are unavailable for the two 2022 night-observation tasks
  and the 2023 cloudy-sky telescope task.
- The separate blank sky map and constellation-code table for 2022 Q13 are
  missing from the question file. The available annotated solution maps are
  included.
- The 2023 collection includes the solar and cloudy-sky telescope alternatives
  and the planned lunar and stellar night-observation variants. The first
  classroom key gives example identifications. The solar key depends on the
  sunspots visible during the examination.
- The 2024 sky-map problems use the 72-point paper that matches the official
  answer key. Notes identify the separately issued 75-point version.
- The 2022 multiple-choice section is worth 100 points overall, but the papers
  do not specify points for individual questions.

## Corrections and contributions

Found a typo, a broken link, or something that is unclear?
[Open an issue](https://github.com/adrianIam/junior-ioaa-problem-book/issues)
and include the year, problem number, and PDF page if possible.

If you would like to edit the book or add another year, the technical details
are below.

<details>
<summary>For contributors: build and edit the book</summary>

### Build the PDFs

The project produces two editions: a typeset edition with editable text and
figures, and an edition assembled from the original question and solution pages.

Use Python 3.10 or later, PyMuPDF, and a TeX installation with latexmk,
pdfLaTeX, Latin Modern, and the standard packages used by [latex/book.tex](latex/book.tex).

```sh
python -m pip install -r requirements.txt
```

The input papers live outside this repository. The pinned source archive is
the Junior Past Papers 2022-2025 directory of
[adrianIam/stars](https://github.com/adrianIam/stars/tree/main/Junior%20Past%20Papers%202022-2025).
Downloading from that archive requires repository access and an authenticated
[GitHub CLI](https://cli.github.com/).

```sh
gh auth login
python fetch_papers.py --dest ../junior-papers
python build.py --validate-only
python build.py
```

The fetcher checks each input against its pinned Git blob checksum and reuses
verified local files. After fetching, builds can run offline.

Build outputs are `build/junior-ioaa-problem-book.pdf` and
`build/junior-ioaa-problem-book-crops.pdf`. The typeset build also places editable
master files and extracted figures beside the output. The `build/` outputs are
ignored by Git; the reading links above point to the PDFs published at the
repository root.

To build one edition or use a different archive location:

```sh
python build.py --edition latex --papers-dir /path/to/junior-papers
python build.py --edition crop --papers-dir /path/to/junior-papers
```

The `IOAA_JUNIOR_PAPERS_DIR` environment variable also selects the source archive.

### Edit or extend

- `data/YYYY.json` contains the problem catalog and source crop spans.
- `data/figures-YYYY.json` contains figure crop recipes.
- [data/papers.json](data/papers.json) pins the papers to a revision and checksums.
- [latex/problems/](latex/problems/) and [latex/solutions/](latex/solutions/)
  contain the editable transcriptions.
- [catalog.py](catalog.py) validates inputs and defines chapter and round order.
- [latex/build_book.py](latex/build_book.py) and
  [source/assemble_book.py](source/assemble_book.py) build the editions.
- [verification/](verification/) records checks against the original papers.

To add another year, register its source papers, add a yearly catalog and
transcriptions, record figure recipes, and write a verification record.
Validate, build both editions, and inspect the new pages and links. Preserve
official wording and clearly note missing solutions or different source versions.

</details>

## Attribution

This project follows the topic-book approach of
[ioanazelko/ioaa-problem-book](https://github.com/ioanazelko/ioaa-problem-book).
Its build software and layout were written independently. See
[NOTICE.md](NOTICE.md) for source attribution and content rights.
