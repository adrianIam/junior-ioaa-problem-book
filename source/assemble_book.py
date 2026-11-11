"""Assemble a topic-organized book from vector crops of the source papers.

The catalog supplies every source page and crop explicitly. This module adds
page furniture and navigation without retyping or rasterizing the paper.
"""

from __future__ import annotations

from pathlib import Path
import os
import tempfile

import pymupdf

from catalog import groups, paper_path


PAGE_WIDTH, PAGE_HEIGHT = pymupdf.paper_size("a4")
MARGIN = 54
TOP = 54
BOTTOM = PAGE_HEIGHT - 52
TEXT_WIDTH = PAGE_WIDTH - 2 * MARGIN
INK = (0.12, 0.16, 0.22)
MUTED = (0.38, 0.42, 0.48)
ACCENT = (0.12, 0.29, 0.42)
ROUND_NAMES = {
    "theory": "Theory",
    "data-analysis": "Data analysis",
    "sky-map": "Sky map",
    "telescope": "Telescope",
    "night": "Night observation",
    "planetarium": "Planetarium",
}


def wrap_text(text, width, font, size):
    """Wrap Unicode text using the same font metrics used for painting it."""
    lines = []
    for paragraph in str(text).split("\n"):
        line = ""
        for word in paragraph.split():
            candidate = f"{line} {word}" if line else word
            if font.text_length(candidate, fontsize=size) <= width:
                line = candidate
                continue
            if line:
                lines.append(line)
                line = ""
            while font.text_length(word, fontsize=size) > width:
                split = 1
                while (
                    split < len(word)
                    and font.text_length(word[: split + 1], fontsize=size) <= width
                ):
                    split += 1
                lines.append(word[:split])
                word = word[split:]
            line = word
        lines.append(line)
    return lines


class CropBook:
    def __init__(self, problems, papers_dir):
        self.problems = problems
        self.papers_dir = Path(papers_dir)
        self.chapters = groups(problems)
        self.doc = pymupdf.open()
        self.sources = {}
        # Embedding these bundled fonts enables their complete Unicode maps.
        self.fonts = {
            "regular": pymupdf.Font("helv"),
            "bold": pymupdf.Font("hebo"),
            "italic": pymupdf.Font("heit"),
        }
        self.page = None
        self.y = TOP
        self.page_entries = 0
        self.problem_pages = {}
        self.solution_pages = {}
        self.locations = {}
        self.cross_links = []
        self.index_links = []
        self.bookmarks = []
        self.numbers = {}
        self.toc_specs = self.contents_specs()
        self.contents_pages = []

    def contents_specs(self):
        rows = []
        for chapter_index, (title, sections) in enumerate(self.chapters, 1):
            rows.append((1, f"{chapter_index}. {title}", f"chapter-{chapter_index}"))
            for section_index, (section_title, _) in enumerate(sections, 1):
                rows.append(
                    (2, section_title, f"section-{chapter_index}-{section_index}")
                )
            rows.append((2, f"Solutions to {title}", f"solutions-{chapter_index}"))
        rows.append((1, "Index by year", "year-index"))
        return rows

    def new_page(self):
        self.page = self.doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
        for style, font in self.fonts.items():
            self.page.insert_font(fontname=style, fontbuffer=font.buffer)
        self.y = TOP
        self.page_entries = 0
        return self.page

    def text(self, page, x, y, text, size=10, style="regular", color=INK):
        page.insert_text(
            (x, y), str(text), fontname=style, fontsize=size, color=color
        )

    def lines(self, page, x, y, text, width=TEXT_WIDTH, size=10, style="regular"):
        leading = size * 1.4
        rows = wrap_text(text, width, self.fonts[style], size)
        for row in rows:
            self.text(page, x, y + size, row, size, style)
            y += leading
        return y

    def source(self, segment):
        path = paper_path(self.papers_dir, segment["file"])
        if path not in self.sources:
            self.sources[path] = pymupdf.open(path)
        source = self.sources[path]
        page_number = segment["page"]
        if (
            not isinstance(page_number, int)
            or isinstance(page_number, bool)
            or not 0 <= page_number < len(source)
        ):
            raise ValueError(f"Invalid page in source segment {segment!r}")
        page = source[page_number]
        clip = pymupdf.Rect(segment.get("clip", page.rect)) & page.rect
        if clip.is_empty or clip.is_infinite:
            raise ValueError(f"Empty source crop in {segment!r}")
        return source, page_number, clip

    def crop_height(self, segment, max_height):
        _, _, clip = self.source(segment)
        scale = min(TEXT_WIDTH / clip.width, max_height / clip.height)
        return clip.height * scale

    def heading_height(self, problem, solution):
        number = self.numbers[problem["id"]]
        prefix = "Solution" if solution else "Problem"
        title = f"{prefix} {number}  {problem['title']}"
        title_lines = wrap_text(title, TEXT_WIDTH, self.fonts["bold"], 11)
        metadata = self.metadata(problem)
        meta_lines = wrap_text(metadata, TEXT_WIDTH, self.fonts["regular"], 8.5)
        return len(title_lines) * 15.4 + len(meta_lines) * 11.9 + 31

    def metadata(self, problem):
        details = [str(problem["year"])]
        if problem.get("host"):
            details.append(problem["host"])
        details.extend([ROUND_NAMES.get(problem["round"], problem["round"]), problem["label"]])
        if problem.get("points") is not None:
            points = problem["points"]
            unit = "point" if points == 1 else "points"
            details.append(f"{points:g} {unit}")
        return " | ".join(details)

    def header(self, problem, solution):
        identifier = problem["id"]
        page_number = self.page.number
        target = self.solution_pages if solution else self.problem_pages
        target[identifier] = page_number
        number = self.numbers[identifier]
        title = f"{'Solution' if solution else 'Problem'} {number}  {problem['title']}"
        self.y = self.lines(self.page, MARGIN, self.y, title, size=11, style="bold")
        self.y = self.lines(
            self.page, MARGIN, self.y + 3, self.metadata(problem), size=8.5
        )
        self.cross_links.append((page_number, identifier, solution, self.y + 11))
        self.y += 20
        self.page.draw_line(
            (MARGIN, self.y), (PAGE_WIDTH - MARGIN, self.y), color=ACCENT, width=0.6
        )
        self.y += 8

    def entry(self, problem, solution=False, section=None):
        segments = problem["solution"] if solution else problem["statement"]
        heading_height = self.heading_height(problem, solution) + 16
        section_height = 25 if section else 0
        remaining = BOTTOM - self.y - heading_height - section_height
        first_height = 54
        if segments:
            maximum = BOTTOM - TOP - heading_height - section_height
            if self.page_entries == 0:
                maximum = max(54, remaining)
            first_height = self.crop_height(segments[0], maximum)
        if self.y + section_height + heading_height + first_height > BOTTOM + 0.5:
            self.new_page()
        if section:
            title, key = section
            self.locations[key] = self.page.number
            self.bookmarks.append([2, title, self.page.number + 1])
            self.text(self.page, MARGIN, self.y + 12, title, 12, "bold", ACCENT)
            self.y += 25
        self.header(problem, solution)
        if not segments:
            note = problem.get("solution_note") or "An official solution is absent from the supplied source papers."
            self.note(note)
        else:
            for index, segment in enumerate(segments):
                self.place_crop(segment, first=index == 0)
            if solution and problem.get("solution_note"):
                self.note(problem["solution_note"])
        self.y += 19
        self.page_entries += 1

    def place_crop(self, segment, first=False):
        source, source_page, clip = self.source(segment)
        max_height = BOTTOM - TOP
        if first:
            max_height = max(1, BOTTOM - self.y)
        scale = min(TEXT_WIDTH / clip.width, max_height / clip.height)
        width, height = clip.width * scale, clip.height * scale
        if self.y + height > BOTTOM + 0.5:
            self.new_page()
        left = MARGIN + (TEXT_WIDTH - width) / 2
        target = pymupdf.Rect(left, self.y, left + width, self.y + height)
        self.page.show_pdf_page(
            target, source, source_page, clip=clip, keep_proportion=True
        )
        self.y += height + 8

    def note(self, text):
        lines = wrap_text(text, TEXT_WIDTH - 14, self.fonts["italic"], 9)
        for line in lines:
            if self.y + 15 > BOTTOM:
                self.new_page()
            self.text(self.page, MARGIN + 7, self.y + 10, line, 9, "italic", MUTED)
            self.y += 13
        self.y += 5

    def frontmatter(self):
        years = sorted({problem["year"] for problem in self.problems})
        span = str(years[0]) if len(years) == 1 else f"{years[0]}–{years[-1]}"
        page = self.new_page()
        self.text(page, MARGIN, 155, "JUNIOR IOAA", 18, "bold", ACCENT)
        self.text(page, MARGIN, 204, "Problems by Topic", 30, "bold")
        self.text(page, MARGIN, 243, span, 19, "regular", MUTED)
        page.draw_line((MARGIN, 270), (PAGE_WIDTH - MARGIN, 270), color=ACCENT, width=1.4)
        self.lines(
            page, MARGIN, 305,
            "A collection of individual problems and available official solutions from the junior competition.",
            width=TEXT_WIDTH - 65, size=12,
        )
        self.lines(
            page, MARGIN, 394,
            "Source-paper edition\nOriginal pages are reproduced as vector crops, preserving the diagrams, equations, and typography of the supplied papers.",
            width=TEXT_WIDTH - 65, size=10,
        )
        self.lines(
            page, MARGIN, 608,
            "This independent educational compilation is not affiliated with the competition organisers. Source-paper rights remain with their authors and organisers. Consult the repository notice for attribution and reuse information.",
            size=9,
        )
        self.locations["cover"] = 0
        y = 94
        pages = 1
        for level, title, _ in self.toc_specs:
            height = 18 * len(wrap_text(title, TEXT_WIDTH - 55 - (level - 1) * 14, self.fonts["regular"], 10.5)) + 4
            if y + height > BOTTOM:
                pages += 1
                y = 94
            y += height
        for _ in range(pages):
            self.contents_pages.append(self.new_page().number)

    def content(self):
        for chapter_index, (title, sections) in enumerate(self.chapters, 1):
            items = [problem for _, problems in sections for problem in problems]
            for index, problem in enumerate(items, 1):
                self.numbers[problem["id"]] = f"{chapter_index}.{index}"
            self.new_page()
            self.locations[f"chapter-{chapter_index}"] = self.page.number
            self.bookmarks.append([1, title, self.page.number + 1])
            self.y = self.lines(
                self.page, MARGIN, self.y, f"{chapter_index}. {title}", size=22, style="bold"
            ) + 19
            for section_index, (section_title, problems) in enumerate(sections, 1):
                key = f"section-{chapter_index}-{section_index}"
                for index, problem in enumerate(problems):
                    section = (section_title, key) if index == 0 else None
                    self.entry(problem, section=section)
            self.new_page()
            solution_title = f"Solutions to {title}"
            self.locations[f"solutions-{chapter_index}"] = self.page.number
            self.bookmarks.append([2, solution_title, self.page.number + 1])
            self.y = self.lines(
                self.page, MARGIN, self.y, solution_title, size=19, style="bold"
            ) + 16
            for problem in items:
                self.entry(problem, solution=True)

    def year_index(self):
        self.new_page()
        self.locations["year-index"] = self.page.number
        self.bookmarks.append([1, "Index by year", self.page.number + 1])
        self.text(self.page, MARGIN, self.y + 20, "Index by year", 22, "bold")
        self.y += 48
        years = sorted({problem["year"] for problem in self.problems})
        for year in years:
            if self.y + 70 > BOTTOM:
                self.new_page()
            self.text(self.page, MARGIN, self.y + 14, str(year), 14, "bold", ACCENT)
            self.y += 27
            entries = [problem for problem in self.problems if problem["year"] == year]
            for problem in entries:
                title = f"{self.numbers[problem['id']]}  {problem['label']}  {problem['title']}"
                rows = wrap_text(title, TEXT_WIDTH - 135, self.fonts["regular"], 9)
                height = max(1, len(rows)) * 13 + 7
                if self.y + height > BOTTOM:
                    self.new_page()
                row_y = self.y + 10
                self.y = self.lines(
                    self.page, MARGIN, self.y, title, width=TEXT_WIDTH - 135, size=9
                ) + 7
                identifier = problem["id"]
                for is_solution, x in ((False, PAGE_WIDTH - MARGIN - 120), (True, PAGE_WIDTH - MARGIN - 57)):
                    target = self.solution_pages if is_solution else self.problem_pages
                    text = f"{'sol.' if is_solution else 'prob.'} {target[identifier] + 1}"
                    self.text(self.page, x, row_y, text, 8.5, color=ACCENT)
                    width = self.fonts["regular"].text_length(text, fontsize=8.5)
                    self.index_links.append(
                        (self.page.number, pymupdf.Rect(x, row_y - 9, x + width, row_y + 3), target[identifier])
                    )
            self.y += 14

    def navigation(self):
        for source_page, identifier, is_solution, baseline in self.cross_links:
            targets = self.problem_pages if is_solution else self.solution_pages
            target = targets[identifier]
            label = "Problem" if is_solution else "Solution"
            text = f"{label} p. {target + 1}"
            width = self.fonts["regular"].text_length(text, fontsize=8.5)
            x = PAGE_WIDTH - MARGIN - width
            page = self.doc[source_page]
            self.text(page, x, baseline, text, 8.5, color=ACCENT)
            page.insert_link({
                "kind": pymupdf.LINK_GOTO,
                "from": pymupdf.Rect(x - 2, baseline - 9, PAGE_WIDTH - MARGIN + 2, baseline + 3),
                "page": target,
            })
        for source, rectangle, target in self.index_links:
            self.doc[source].insert_link({"kind": pymupdf.LINK_GOTO, "from": rectangle, "page": target})
        self.doc.set_toc(self.bookmarks)

    def contents(self):
        page_offset = 0
        page = self.doc[self.contents_pages[page_offset]]
        self.text(page, MARGIN, 73, "Contents", 22, "bold")
        y = 94
        for level, title, key in self.toc_specs:
            x = MARGIN + (level - 1) * 14
            rows = wrap_text(title, TEXT_WIDTH - 55 - (level - 1) * 14, self.fonts["regular"], 10.5)
            height = len(rows) * 18 + 4
            if y + height > BOTTOM:
                page_offset += 1
                page = self.doc[self.contents_pages[page_offset]]
                self.text(page, MARGIN, 73, "Contents (continued)", 22, "bold")
                y = 94
            for index, row in enumerate(rows):
                self.text(page, x, y + 11 + index * 18, row, 10.5)
            target = self.locations[key]
            number = str(target + 1)
            number_width = self.fonts["regular"].text_length(number, fontsize=10.5)
            self.text(page, PAGE_WIDTH - MARGIN - number_width, y + 11, number, 10.5)
            page.insert_link({
                "kind": pymupdf.LINK_GOTO,
                "from": pymupdf.Rect(x, y, PAGE_WIDTH - MARGIN, y + height),
                "page": target,
            })
            y += height

    def furniture(self):
        for number in range(1, len(self.doc)):
            page = self.doc[number]
            self.text(page, MARGIN, 30, "JUNIOR IOAA  ·  PROBLEMS BY TOPIC", 7, color=MUTED)
            page.draw_line(
                (MARGIN, PAGE_HEIGHT - 37),
                (PAGE_WIDTH - MARGIN, PAGE_HEIGHT - 37),
                color=(0.77, 0.80, 0.82), width=0.35,
            )
            text = str(number + 1)
            width = self.fonts["regular"].text_length(text, fontsize=8)
            self.text(page, (PAGE_WIDTH - width) / 2, PAGE_HEIGHT - 22, text, 8, color=MUTED)

    def close(self):
        for source in self.sources.values():
            source.close()
        self.doc.close()


def build_crop(problems, papers_dir, output):
    """Write the complete source-paper edition and return its output path."""
    if not problems:
        raise ValueError("The problem catalog is empty.")
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    book = CropBook(problems, papers_dir)
    temporary = None
    try:
        book.frontmatter()
        book.content()
        book.year_index()
        book.contents()
        book.navigation()
        book.furniture()
        book.doc.set_metadata({
            "title": "Junior IOAA Problems by Topic, source-paper edition",
            "author": "Junior IOAA Problem Book contributors",
            "subject": "Junior astronomy and astrophysics problems with official solutions",
        })
        descriptor, name = tempfile.mkstemp(prefix=f".{output.stem}-", suffix=".pdf", dir=output.parent)
        os.close(descriptor)
        temporary = Path(name)
        book.doc.save(temporary, garbage=4, deflate=True)
        os.replace(temporary, output)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
        book.close()
    return output
