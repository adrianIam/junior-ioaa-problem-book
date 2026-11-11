"""Load and validate the editorial catalog used by both book editions."""

from __future__ import annotations

from collections import Counter
from contextlib import ExitStack
import hashlib
import json
from pathlib import Path
import re

import pymupdf


ROOT = Path(__file__).resolve().parent
TOPICS = {
    "celestial-sphere": "The Celestial Sphere",
    "time-and-calendars": "Time and Calendars",
    "solar-system": "The Solar System",
    "orbital-mechanics": "Orbital Mechanics",
    "light-and-telescopes": "Light and Telescopes",
    "sun-and-stars": "The Sun and Stars",
    "stellar-evolution": "Stellar Evolution",
    "galaxies-and-cosmology": "Galaxies and Cosmology",
    "observation": "Observational Problems",
}
ROUNDS = {
    "theory": "Theory problems",
    "data-analysis": "Data-analysis problems",
    "planetarium": "Planetarium",
    "sky-map": "Sky maps and charts",
    "telescope": "Telescope",
    "night": "Night observation",
}


def paper_path(papers_dir: Path, relative: str) -> Path:
    root = Path(papers_dir).resolve()
    path = (root / relative).resolve()
    if Path(relative).is_absolute() or not path.is_relative_to(root):
        raise ValueError(f"Source path escapes the paper archive: {relative}")
    return path


def git_blob_sha(path: Path) -> str:
    digest = hashlib.sha1(f"blob {path.stat().st_size}\0".encode())
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_catalog() -> tuple[list[dict], dict]:
    problems = []
    figures = {}
    for path in sorted((ROOT / "data").glob("[0-9][0-9][0-9][0-9].json")):
        edition = json.loads(path.read_text())
        for entry in edition["problems"]:
            problems.append({**entry, "year": edition["year"], "host": edition["host"]})
    for path in sorted((ROOT / "data").glob("figures-*.json")):
        entries = json.loads(path.read_text())
        overlap = figures.keys() & entries.keys()
        if overlap:
            raise ValueError(f"Duplicate figure names in {path.name}: {sorted(overlap)}")
        figures.update(entries)
    return problems, figures


def groups(problems: list[dict]) -> list[tuple[str, list[tuple[str, list[dict]]]]]:
    chapters = []
    for topic, title in TOPICS.items():
        sections = []
        for round_code, heading in ROUNDS.items():
            items = sorted(
                (p for p in problems if p["topic"] == topic and p["round"] == round_code),
                key=lambda p: (p["year"], p["id"]),
            )
            if items:
                sections.append((heading, items))
        if sections:
            chapters.append((title, sections))
    return chapters


def validate(problems: list[dict], figures: dict, papers_dir: Path) -> dict:
    if not problems:
        raise ValueError("No yearly problem catalogs were found.")
    ids = [p["id"] for p in problems]
    repeated = [key for key, count in Counter(ids).items() if count > 1]
    if repeated:
        raise ValueError(f"Duplicate problem identifiers: {repeated}")
    papers = json.loads((ROOT / "data" / "papers.json").read_text())
    known_papers = {p["file"]: p for p in papers["papers"]}
    source_years = {int(Path(p["file"]).parts[0]) for p in papers["papers"]}
    catalog_years = {p["year"] for p in problems}
    if source_years != catalog_years:
        raise ValueError(
            f"Source years and catalog years differ: {sorted(source_years)} / "
            f"{sorted(catalog_years)}"
        )
    with ExitStack() as stack:
        documents = {}

        def check_segment(segment: dict, owner: str) -> None:
            relative = segment["file"]
            if relative not in known_papers:
                raise ValueError(f"{owner} refers to an unregistered source paper: {relative}")
            if relative not in documents:
                path = paper_path(papers_dir, relative)
                if not path.is_file():
                    raise ValueError(f"Source paper missing: {path}. Run fetch_papers.py.")
                if git_blob_sha(path) != known_papers[relative]["sha"]:
                    raise ValueError(f"Source paper checksum mismatch: {relative}")
                documents[relative] = stack.enter_context(pymupdf.open(path))
            document = documents[relative]
            page = segment["page"]
            if not isinstance(page, int) or isinstance(page, bool) or not 0 <= page < len(document):
                raise ValueError(f"Invalid source page for {owner}: {page}")
            bounds = document[page].rect
            rectangle = pymupdf.Rect(segment.get("clip", bounds))
            if rectangle.is_empty or rectangle.is_infinite or not bounds.contains(rectangle):
                raise ValueError(f"Invalid source crop for {owner}: {list(rectangle)}")

        referenced = set()
        for problem in problems:
            identifier = problem["id"]
            if not re.fullmatch(r"\d{4}_[A-Z-]+_[A-Za-z0-9]+", identifier):
                raise ValueError(f"Invalid problem identifier: {identifier}")
            if problem["topic"] not in TOPICS or problem["round"] not in ROUNDS:
                raise ValueError(f"Unknown topic or round for {identifier}")
            if (problem["topic"] == "observation") != (
                problem["round"] not in ("theory", "data-analysis")
            ):
                raise ValueError(f"Observation round and topic disagree for {identifier}")
            points = problem["points"]
            if points is not None and (
                not isinstance(points, (int, float)) or isinstance(points, bool) or points < 0
            ):
                raise ValueError(f"Invalid point value for {identifier}: {points}")
            if not problem["statement"]:
                raise ValueError(f"No statement source for {identifier}")
            if not problem.get("solution") and not problem.get("solution_note"):
                raise ValueError(f"Missing explanation for absent solution of {identifier}")
            for kind, folder in (("statement", "problems"), ("solution", "solutions")):
                segments = problem.get(kind)
                if not segments:
                    continue
                for segment in segments:
                    check_segment(segment, identifier)
                path = ROOT / "latex" / folder / f"{identifier}.tex"
                if not path.is_file() or not path.read_text().strip():
                    raise ValueError(f"Missing LaTeX transcription: {path}")
                text = re.sub(r"(?<!\\)%.*", "", path.read_text())
                referenced.update(re.findall(r"\\ioaafig(?:\[[^\]]+\])?\{([^}]+)\}", text))
        absent = referenced - figures.keys()
        if absent:
            raise ValueError(f"Missing figure recipes: {sorted(absent)}")
        unused = figures.keys() - referenced
        if unused:
            raise ValueError(f"Unreferenced figure recipes: {sorted(unused)}")
        for name, segment in figures.items():
            if Path(name).name != name or not name.endswith(".pdf"):
                raise ValueError(f"Invalid figure filename: {name}")
            check_segment(segment, name)
    return {
        "problems": len(problems),
        "solutions": sum(bool(p.get("solution")) for p in problems),
        "figures": len(figures),
        "years": sorted({p["year"] for p in problems}),
    }
