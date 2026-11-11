# Editable LaTeX edition

The LaTeX book groups the Junior IOAA problems by topic, with an observation
chapter grouped by round. Each chapter is followed by its official solutions.
Problems and solutions link to each other, and the book ends with an index by
year.

Edit a problem in `problems/<id>.tex` or its solution in `solutions/<id>.tex`.
These files contain document bodies. Use LaTeX mathematical notation and keep
the official numerical values, part labels, and point values. Record source
variants and missing material in the corresponding `data/<year>.json` entry.
Editorial notes appear in both editions.

Figures are described in `data/figures-<year>.json`. Each entry identifies a
source PDF, a zero-based page number, and an optional crop rectangle in PDF
points. The builder extracts these regions as vector PDFs. Include them with
`\ioaafig{filename.pdf}` or `\ioaafig[0.75]{filename.pdf}`. The figure macro
preserves aspect ratio and caps the height at 82% of the text area.

The root build command stages a complete editable project alongside the chosen
output PDF, under `<output-stem>-latex/`. This directory contains `book.tex`,
the generated chapter and index files, the transcriptions, the cropped figures,
and the compilation logs. Run `latexmk` -pdf -halt-on-error -file-line-error
`book.tex` inside it to compile a staged copy directly. Apply lasting edits to the
repository fragments and catalogue before rebuilding.

The build requires Python with PyMuPDF and a TeX installation containing
`latexmk`, `pdfLaTeX`, Latin Modern, AMS mathematics, `booktabs`, `longtable`,
`graphicx`, `geometry`, `xcolor`, and `hyperref`.
