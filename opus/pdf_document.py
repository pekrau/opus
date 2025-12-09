"PDF document interface."

from contextlib import contextmanager
import datetime
import io

import reportlab
import reportlab.rl_config
import reportlab.lib.colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    Paragraph,
    Spacer,
    NotAtTopPageBreak,
    SimpleDocTemplate,
    LayoutError,
)
from reportlab.platypus.tableofcontents import TableOfContents, SimpleIndex

from .constants import *


class Document:
    "PDF document interface."

    def __init__(
        self,
        title=None,
        authors=None,
        version=None,
        language="sv-SE",
        page_break_level=1,
        section_numbers=True,
        paragraph_numbers=True,
    ):
        self.title = title
        self.authors = authors
        self.version = version
        self.language = language
        self.page_break_level = page_break_level
        self.section_numbers = section_numbers
        self.paragraph_numbers = paragraph_numbers

        self.stylesheet = getSampleStyleSheet()
        # self.stylesheet.list()

        # These modifications will affect subsquent styles inheriting from Normal.
        self.stylesheet["Normal"].fontName = PDF_NORMAL_FONT
        self.stylesheet["Normal"].fontSize = PDF_NORMAL_FONT_SIZE
        self.stylesheet["Normal"].leading = PDF_NORMAL_LEADING

        self.stylesheet["Title"].fontSize = PDF_TITLE_FONT_SIZE
        self.stylesheet["Title"].leading = PDF_TITLE_LEADING
        self.stylesheet["Title"].alignment = 0  # Left
        self.stylesheet["Title"].spaceAfter = PDF_TITLE_SPACE_AFTER

        self.stylesheet["Code"].fontName = PDF_CODE_FONT
        self.stylesheet["Code"].fontSize = PDF_CODE_FONT_SIZE
        self.stylesheet["Code"].leading = PDF_CODE_LEADING
        self.stylesheet["Code"].leftIndent = PDF_CODE_INDENT

        self.stylesheet["OrderedList"].fontName = PDF_NORMAL_FONT
        self.stylesheet["OrderedList"].fontSize = PDF_NORMAL_FONT_SIZE
        self.stylesheet["OrderedList"].bulletFormat = "%s. "

        self.stylesheet["UnorderedList"].fontName = PDF_NORMAL_FONT
        self.stylesheet["UnorderedList"].fontSize = PDF_NORMAL_FONT_SIZE
        self.stylesheet["UnorderedList"].bulletType = "bullet"
        self.stylesheet["UnorderedList"].bulletFont = PDF_NORMAL_FONT_SIZE

        self.stylesheet.add(
            ParagraphStyle(
                name="Index",
                parent=self.stylesheet["Normal"],
            )
        )
        self.stylesheet.add(
            ParagraphStyle(
                name="Quote",
                parent=self.stylesheet["Normal"],
                fontName=PDF_QUOTE_FONT,
                fontSize=PDF_QUOTE_FONT_SIZE,
                leading=PDF_QUOTE_LEADING,
                spaceBefore=PDF_QUOTE_SPACE_BEFORE,
                spaceAfter=PDF_QUOTE_SPACE_AFTER,
                leftIndent=PDF_QUOTE_INDENT,
                rightIndent=PDF_QUOTE_INDENT,
            )
        )
        self.stylesheet.add(
            ParagraphStyle(
                name="Footnote",
                parent=self.stylesheet["Normal"],
                leftIndent=PDF_FOOTNOTE_INDENT,
                firstLineIndent=-PDF_FOOTNOTE_INDENT,
            )
        )
        self.stylesheet.add(
            ParagraphStyle(
                name="Footnote subsequent",
                parent=self.stylesheet["Footnote"],
                firstLineIndent=0,
            )
        )
        self.stylesheet.add(
            ParagraphStyle(
                name="Reference",
                parent=self.stylesheet["Normal"],
                spaceBefore=PDF_REFERENCE_SPACE_BEFORE,
                leftIndent=PDF_REFERENCE_INDENT,
                firstLineIndent=-PDF_REFERENCE_INDENT,
            )
        )

        # Placed here to avoid affecting previously defined styles.
        self.stylesheet["Normal"].spaceBefore = PDF_NORMAL_SPACE_BEFORE
        self.stylesheet["Normal"].spaceAfter = PDF_NORMAL_SPACE_AFTER

        self.paragraph = None
        self.paragraphs_count = 0
        self.section_counts = [0]
        self.index = SimpleIndex(style=self.stylesheet["Index"], headers=False)
        self.any_indexed = False
        self.flowables = []

        if self.title:
            self.flowables.append(Paragraph(self.title, style=self.stylesheet["Title"]))
        if self.authors:
            self.flowables.append(
                Paragraph(", ".join(self.authors), style=self.stylesheet["Heading2"])
            )
        if self.version:
            self.flowables.append(
                Paragraph(self.version, style=self.stylesheet["Normal"])
            )
        self.flowables.append(Spacer(0, PDF_TITLE_PAGE_SPACER))

    def new_paragraph(self):
        if self.paragraph:
            self.paragraph.output()
        self.paragraphs_count += 1
        self.paragraph = _Paragraph(self)
        return self.paragraph

    def new_quote(self):
        if self.paragraph:
            self.paragraph.output()
        self.paragraphs_count += 1
        self.paragraph = _Quote(self)
        return self.paragraph

    def new_section(self, title):
        if self.paragraph:
            self.paragraph.output()
            self.paragraph = None
        return _Section(self, title)

    def new_page(self):
        if self.paragraph:
            self.paragraph.output()
            self.paragraph = None
        self.flowables.append(NotAtTopPageBreak())

    def display_page_number(self, canvas, pdfdoc):
        "Output page number onto the current canvas."
        width, height = reportlab.rl_config.defaultPageSize
        canvas.saveState()
        canvas.setFont(PDF_NORMAL_FONT, PDF_NORMAL_FONT_SIZE)
        canvas.drawString(width - 84, height - 56, str(pdfdoc.page))
        canvas.restoreState()

    def write(self, filepath):
        self.new_paragraph()
        output = io.BytesIO()
        pdfdoc = SimpleDocTemplate(
            output,
            title=self.title,
            author=", ".join(self.authors) or None,
            creator=f"opus {VERSION}",
            lang=self.language,
        )
        if self.any_indexed:
            self.new_page()
            self.flowables.append(Paragraph("Index", style=self.stylesheet["Heading1"]))
            self.flowables.append(self.index)
            pdfdoc.build(
                self.flowables,
                onLaterPages=self.display_page_number,
                canvasmaker=self.index.getCanvasMaker(),
            )
        else:
            pdfdoc.build(self.flowables, onLaterPages=self.display_page_number)
        with open(filepath, "wb") as outfile:
            outfile.write(output.getvalue())


class _Paragraph:

    STYLESHEETNAME = "Normal"

    def __init__(self, document):
        self.document = document
        self.contents = []

    def add(self, text, append_blank=True):
        assert isinstance(text, str)
        self.contents.append(text)
        if append_blank and text[-1] != " ":
            self.contents.append(" ")

    def linebreak(self):
        self.contents.append("<br/>")

    def add_indexed(self, text, canonical=None, append_blank=True):
        if canonical:
            canonical = canonical.replace(",", ",,")
        with self.underline():
            self.add(f'<index item="{canonical or text}">{text}</index>', append_blank=append_blank)
        self.document.any_indexed = True

    def add_link(self, text, href, append_blank=True):
        assert isinstance(text, str)
        self.contents.append(
            f'<link href="{href}" underline="true" color="blue">{text}</link>'
        )
        if append_blank:
            self.contents.append(" ")

    @contextmanager
    def bold(self):
        self.contents.append("<b>")
        try:
            yield self
        finally:
            self.contents.append("</b>")

    @contextmanager
    def italic(self):
        self.contents.append("<i>")
        try:
            yield self
        finally:
            self.contents.append("</i>")

    @contextmanager
    def underline(self):
        self.contents.append("<u>")
        try:
            yield self
        finally:
            self.contents.append("</u>")

    def output(self):
        if not self.contents:
            return
        if self.document.paragraph_numbers:
            self.contents.insert(0, f"<b>{self.document.paragraphs_count}.</b> ")
        self.document.flowables.append(
            Paragraph(
                "".join(self.contents),
                style=self.document.stylesheet[self.STYLESHEETNAME],
            )
        )


class _Quote(_Paragraph):

    STYLESHEETNAME = "Quote"


class _Section:

    def __init__(self, document, title):
        self.document = document
        self.title = title
        self.document.section_counts[-1] += 1

    def number(self):
        return ".".join([str(n) for n in self.document.section_counts[:-1]]) + "."

    def __enter__(self):
        self.document.section_counts.append(0)
        level = len(self.document.section_counts) - 1
        if level <= self.document.page_break_level:
            self.document.new_page()
        if self.document.section_numbers:
            title = [self.number()]
        else:
            title = []
        if self.title:
            title.append(self.title)
        title = " ".join(title)
        self.document.flowables.append(
            Paragraph(title, style=self.document.stylesheet[f"Heading{level}"])
        )
        return self

    def __exit__(self, *exc):
        self.document.section_counts.pop()
