"""Build the editable LaTeX edition and its cropped vector figures."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

import pymupdf

from catalog import ROUNDS, groups, paper_path


LATEX_DIR = Path(__file__).resolve().parent
IDENTIFIER = re.compile(r"[A-Za-z0-9_-]+\Z")
ROUND_ORDER = {round_code: index for index, round_code in enumerate(ROUNDS)}
SPECIALS = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
    "−": r"\ensuremath{-}",
    "°": r"\ensuremath{^\circ}",
    "±": r"\ensuremath{\pm}",
    "×": r"\ensuremath{\times}",
    "·": r"\ensuremath{\cdot}",
    "≤": r"\ensuremath{\leq}",
    "≥": r"\ensuremath{\geq}",
    "≈": r"\ensuremath{\approx}",
    "∞": r"\ensuremath{\infty}",
    "→": r"\ensuremath{\rightarrow}",
    "–": "--",
    "—": "---",
    "ț": r"\textcommabelow{t}",
    "Ț": r"\textcommabelow{T}",
    "ș": r"\textcommabelow{s}",
    "Ș": r"\textcommabelow{S}",
}
GREEK = {
    "α": "alpha", "β": "beta", "γ": "gamma", "δ": "delta", "ε": "epsilon",
    "ζ": "zeta", "η": "eta", "θ": "theta", "ι": "iota", "κ": "kappa",
    "λ": "lambda", "μ": "mu", "ν": "nu", "ξ": "xi", "π": "pi",
    "ρ": "rho", "σ": "sigma", "ς": "varsigma", "τ": "tau", "υ": "upsilon",
    "φ": "phi", "χ": "chi", "ψ": "psi", "ω": "omega", "ϕ": "varphi",
    "ϵ": "varepsilon", "ϑ": "vartheta", "Γ": "Gamma", "Δ": "Delta",
    "Θ": "Theta", "Λ": "Lambda", "Ξ": "Xi", "Π": "Pi", "Σ": "Sigma",
    "Υ": "Upsilon", "Φ": "Phi", "Ψ": "Psi", "Ω": "Omega",
}
SPECIALS.update({
    character: "\\ensuremath{\\" + command + "}"
    for character, command in GREEK.items()
})


def escape_tex(value: object) -> str:
    """Quote plain catalogue text without changing authored LaTeX fragments."""
    return "".join(SPECIALS.get(character, character) for character in str(value))


def _numbered_groups(problems: list[dict]) -> tuple[list, dict[str, str]]:
    grouped = groups(problems)
    numbers = {}
    for chapter, (_, sections) in enumerate(grouped, 1):
        sequence = 0
        for _, items in sections:
            for problem in items:
                sequence += 1
                numbers[problem["id"]] = f"{chapter}.{sequence}"
    return grouped, numbers


def _copy_fragment(kind: str, problem_id: str, stage: Path) -> None:
    if not IDENTIFIER.fullmatch(problem_id):
        raise ValueError(f"Invalid problem identifier {problem_id!r}")
    source = LATEX_DIR / kind / f"{problem_id}.tex"
    if not source.is_file():
        raise FileNotFoundError(f"Missing {kind} transcription: {source}")
    destination = stage / kind / source.name
    destination.parent.mkdir(exist_ok=True)
    shutil.copyfile(source, destination)


def _extract_figure(name: str, segment: dict, papers_dir: Path, stage: Path) -> None:
    if Path(name).name != name or not name.endswith(".pdf"):
        raise ValueError(f"Invalid figure filename {name!r}")
    source = paper_path(papers_dir, segment["file"])
    with pymupdf.open(source) as document:
        page = document.load_page(segment["page"])
        clip = pymupdf.Rect(segment.get("clip", page.rect))
        if clip.is_empty or clip.is_infinite or not page.rect.contains(clip):
            raise ValueError(f"Figure crop lies outside its source page: {name}")
        with pymupdf.open() as figure:
            target = figure.new_page(width=clip.width, height=clip.height)
            target.show_pdf_page(target.rect, document, page.number, clip=clip)
            figure.save(stage / "images" / name, garbage=4, deflate=True)


def _chapter_source(grouped: list, numbers: dict[str, str], stage: Path) -> str:
    lines = []
    for chapter_title, sections in grouped:
        lines.append(r"\chapter{" + escape_tex(chapter_title) + "}")
        for round_heading, items in sections:
            lines.append(r"\section*{" + escape_tex(round_heading) + "}")
            for problem in items:
                problem_id = problem["id"]
                _copy_fragment("problems", problem_id, stage)
                arguments = [
                    numbers[problem_id],
                    problem_id,
                    problem["title"],
                    problem["year"],
                    problem["host"],
                    round_heading,
                    problem["label"],
                    "" if problem.get("points") is None else problem["points"],
                ]
                lines.append(
                    r"\problemhead"
                    + "".join(
                        "{" + (str(argument) if index == 1 else escape_tex(argument)) + "}"
                        for index, argument in enumerate(arguments)
                    )
                )
                lines.append("% source id: " + problem_id)
                lines.append(r"\input{problems/" + problem_id + "}")
        lines.append(r"\clearpage\section*{Solutions}")
        for _, items in sections:
            for problem in items:
                problem_id = problem["id"]
                arguments = [numbers[problem_id], problem_id, problem["title"]]
                lines.append(
                    r"\solutionhead"
                    + "".join(
                        "{" + (str(argument) if index == 1 else escape_tex(argument)) + "}"
                        for index, argument in enumerate(arguments)
                    )
                )
                lines.append("% source id: " + problem_id)
                if problem.get("solution_note"):
                    lines.append(
                        r"\editorialnote{"
                        + escape_tex(problem["solution_note"])
                        + "}"
                    )
                if problem.get("solution"):
                    _copy_fragment("solutions", problem_id, stage)
                    lines.append(r"\input{solutions/" + problem_id + "}")
                elif not problem.get("solution_note"):
                    raise ValueError(f"Missing explanation for absent solution {problem_id}")
    return "\n\n".join(lines) + "\n"


def _year_index(problems: list[dict], numbers: dict[str, str]) -> str:
    lines = [
        r"\chapter*{Index by year}",
        r"\addcontentsline{toc}{chapter}{Index by year}",
        r"\begin{longtable}{@{}rllp{0.44\linewidth}r@{}}",
        r"\toprule Year & Round & Label & Problem & Page\\\midrule",
        r"\endhead",
    ]
    for problem in sorted(
        problems,
        key=lambda item: (item["year"], ROUND_ORDER[item["round"]], item["id"]),
    ):
        problem_id = problem["id"]
        title = escape_tex(numbers[problem_id] + " " + problem["title"])
        cells = [
            str(problem["year"]),
            escape_tex(problem["round"]),
            escape_tex(problem["label"]),
            r"\hyperref[prob:" + problem_id + "]{" + title + "}",
            r"\pageref{prob:" + problem_id + "}",
        ]
        lines.append(" & ".join(cells) + r"\\")
    lines.extend([r"\bottomrule", r"\end{longtable}"])
    return "\n".join(lines) + "\n"


def build_latex(
    problems: list[dict], figures: dict, papers_dir: Path, output: Path
) -> Path:
    """Stage editable sources, compile them, and replace output after success."""
    if not problems:
        raise ValueError("Cannot build a book without problems")
    papers_dir = Path(papers_dir).resolve()
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = output.parent / f"{output.stem}-latex"
    stage.mkdir(parents=True, exist_ok=True)
    (stage / "images").mkdir(exist_ok=True)
    grouped, numbers = _numbered_groups(problems)
    (stage / "chapters.tex").write_text(
        _chapter_source(grouped, numbers, stage), encoding="utf-8"
    )
    (stage / "year-index.tex").write_text(
        _year_index(problems, numbers), encoding="utf-8"
    )
    for name, segment in figures.items():
        _extract_figure(name, segment, papers_dir, stage)
    (stage / "figures.json").write_text(
        json.dumps(figures, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    years = sorted({problem["year"] for problem in problems})
    year_range = str(years[0]) if len(years) == 1 else f"{years[0]}--{years[-1]}"
    master = (LATEX_DIR / "book.tex").read_text(encoding="utf-8")
    (stage / "book.tex").write_text(
        master.replace("@@YEAR_RANGE@@", year_range), encoding="utf-8"
    )
    command = ["latexmk", "-pdf", "-halt-on-error", "-file-line-error", "book.tex"]
    result = subprocess.run(
        command, cwd=stage, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    (stage / "build.log").write_text(result.stdout, encoding="utf-8")
    if result.returncode:
        tail = "\n".join(result.stdout.splitlines()[-35:])
        raise RuntimeError(f"LaTeX build failed. See {stage / 'build.log'}\n{tail}")
    log = (stage / "book.log").read_text(encoding="utf-8", errors="replace")
    if re.search(r"undefined references|multiply defined|Missing character:", log):
        raise RuntimeError(f"LaTeX reported unresolved content. See {stage / 'book.log'}")
    with tempfile.NamedTemporaryFile(dir=output.parent, delete=False) as temporary:
        temporary_path = Path(temporary.name)
    try:
        shutil.copyfile(stage / "book.pdf", temporary_path)
        os.replace(temporary_path, output)
    finally:
        temporary_path.unlink(missing_ok=True)
    return output
