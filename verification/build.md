# Integrated build verification

The final catalog contains all 64 individual problems from 2022–2025 and 72
figure recipes. There are 58 entries with supplied official solution material,
including two 2022 variant keys, and six entries with explicit absence notes.
Each year has a source and transcription review record in this directory.

## Build results

Both editions were rebuilt from the final catalogs and transcriptions with
the root build command. The 30 source PDFs were checked against the pinned
Git blob checksums. The sources were initially materialized through an
authenticated GitHub connection. The fetch script's verified-cache path was
exercised on all 30 files. Its live GitHub CLI download path requires the
user's authenticated CLI session.

| Edition | Pages | Problem headings | Solution headings | Valid internal links |
|---|---:|---:|---:|---:|
| Editable LaTeX | 117 | 64 | 64 | 402 |
| Source crops | 170 | 64 | 64 | 286 |

Every expected problem and solution identifier occurs in the LaTeX auxiliary
labels. Each problem's header links to its matching solution and each
solution's header links back to its problem. All internal destinations in both
PDFs point to valid pages. The final LaTeX log has no undefined references,
multiply defined labels, missing characters, or overfull boxes.

The final visual review sampled 23 LaTeX pages and 15 crop-edition pages,
including both covers and contents, all chapter starts, source-variant notes,
sky charts, equations, photographs, telescope material, and year indexes.
The year records describe additional source, crop, and manuscript checks.

## Input and failure checks

The catalog validator checked source-page and crop bounds, source checksums,
unique problem identifiers, supported topics and rounds, required statement
and solution fragments, explanations for missing solutions, and the complete
set of figure references.

Separate rejection checks exercised source-path escapes, duplicate problem
identifiers, an unknown round, an unexplained absent solution, a changed source
checksum, and a crop extending outside its PDF page. Each was rejected.

Python compilation and the Git whitespace check passed.
