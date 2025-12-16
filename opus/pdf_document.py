"PDF document interface."

import datetime
import io

import reportlab
import reportlab.rl_config
import reportlab.lib.colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph as PdfParagraph
from reportlab.platypus import ListItem as PdfListItem
from reportlab.platypus import (
    Spacer,
    PageBreak,
    NotAtTopPageBreak,
    HRFlowable,
    ListFlowable,
    SimpleDocTemplate,
)
from reportlab.platypus.tableofcontents import TableOfContents, SimpleIndex

from .base_document import *


__all__ = ["Document"]

NORMAL_FONT = "Helvetica"
NORMAL_FONT_SIZE = 12
NORMAL_LEADING = 18
NORMAL_SPACE_BEFORE = 6
NORMAL_SPACE_AFTER = 12
TITLE_FONT_SIZE = 24
TITLE_LEADING = 30
TITLE_SPACE_AFTER = 15
TITLE_PAGE_SPACER = 50
CODE_FONT = "Courier"
CODE_FONT_SIZE = 11
CODE_LEADING = 12
CODE_INDENT = 10
QUOTE_FONT = "Times-Roman"
QUOTE_FONT_SIZE = 14
QUOTE_LEADING = 16
QUOTE_SPACE_BEFORE = 0
QUOTE_SPACE_AFTER = 14
QUOTE_INDENT = 28
FOOTNOTE_INDENT = 10
REFERENCE_SPACE_BEFORE = 7
REFERENCE_INDENT = 10
EMDASH = "\u2014"
MAX_HEADING = 6


class Document(BaseDocument):
    "PDF document interface."

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.paragraph = None
        self.indexed = {}
        self.flowables = []
        self.toc = None

        self.stylesheet = getSampleStyleSheet()

        # These modifications will affect subsquent styles inheriting from Normal.
        self.stylesheet["Normal"].fontName = NORMAL_FONT
        self.stylesheet["Normal"].fontSize = NORMAL_FONT_SIZE
        self.stylesheet["Normal"].leading = NORMAL_LEADING

        self.stylesheet["Title"].fontSize = TITLE_FONT_SIZE
        self.stylesheet["Title"].leading = TITLE_LEADING
        self.stylesheet["Title"].alignment = 0  # Left
        self.stylesheet["Title"].spaceAfter = TITLE_SPACE_AFTER

        self.stylesheet["Code"].fontName = CODE_FONT
        self.stylesheet["Code"].fontSize = CODE_FONT_SIZE
        self.stylesheet["Code"].leading = CODE_LEADING
        self.stylesheet["Code"].leftIndent = CODE_INDENT

        self.stylesheet["OrderedList"].fontName = NORMAL_FONT
        self.stylesheet["OrderedList"].fontSize = NORMAL_FONT_SIZE
        self.stylesheet["OrderedList"].bulletFormat = "%s. "

        self.stylesheet["UnorderedList"].fontName = NORMAL_FONT
        self.stylesheet["UnorderedList"].fontSize = NORMAL_FONT_SIZE
        self.stylesheet["UnorderedList"].bulletType = "bullet"
        self.stylesheet["UnorderedList"].bulletFont = NORMAL_FONT_SIZE

        self.stylesheet.add(
            ParagraphStyle(
                name="Subtitle",
                parent=self.stylesheet["Heading1"],
            )
        )
        self.stylesheet.add(
            ParagraphStyle(
                name="Authors",
                parent=self.stylesheet["Heading2"],
            )
        )
        for level in range(1, MAX_HEADING+1):
            self.stylesheet.add(
                ParagraphStyle(
                    name=f"SectionSubtitle{level}",
                    parent=self.stylesheet[f"Heading{level}"],
                )
            )
        self.stylesheet.add(
            ParagraphStyle(
                name="Contents",
                parent=self.stylesheet["Heading1"],
            )
        )
        self.stylesheet.add(
            ParagraphStyle(
                name="Quote",
                parent=self.stylesheet["Normal"],
                fontName=QUOTE_FONT,
                fontSize=QUOTE_FONT_SIZE,
                leading=QUOTE_LEADING,
                spaceBefore=QUOTE_SPACE_BEFORE,
                spaceAfter=QUOTE_SPACE_AFTER,
                leftIndent=QUOTE_INDENT,
                rightIndent=QUOTE_INDENT,
            )
        )
        self.stylesheet.add(
            ParagraphStyle(
                name="Footnote",
                parent=self.stylesheet["Normal"],
                firstLineIndent=0,
                leftIndent=FOOTNOTE_INDENT,
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
                spaceBefore=REFERENCE_SPACE_BEFORE,
                firstLineIndent=0,
                leftIndent=REFERENCE_INDENT,
            )
        )

        # Placed here to avoid affecting previously defined styles.
        self.stylesheet["Normal"].spaceBefore = NORMAL_SPACE_BEFORE
        self.stylesheet["Normal"].spaceAfter = NORMAL_SPACE_AFTER

        if self.title:
            self.flowables.append(
                PdfParagraph(self.title, style=self.stylesheet["Title"])
            )
        if self.subtitle:
            self.flowables.append(
                PdfParagraph(self.subtitle, style=self.stylesheet["Subtitle"])
            )
        if self.authors:
            self.flowables.append(
                PdfParagraph(", ".join(self.authors), style=self.stylesheet["Authors"])
            )
        if self.version:
            self.flowables.append(
                PdfParagraph(self.version, style=self.stylesheet["Normal"])
            )
        self.flowables.append(
            HRFlowable(width="100%", color=reportlab.lib.colors.black, spaceAfter=10)
        )
        self.flowables.append(Spacer(0, TITLE_PAGE_SPACER))

    def setup_toc(self):
        if not self.toc_level:
            return
        if self.toc is not None:
            return
        self.paragraph_flush()
        self.flowables.append(PageBreak())
        self.flowables.append(
            PdfParagraph(self.toc_title, style=self.stylesheet["Contents"])
        )
        level_styles = []
        for level in range(0, self.toc_level + 1):
            style = ParagraphStyle(
                name=f"TOC level {level}",
                fontName=NORMAL_FONT,
                fontSize=NORMAL_FONT_SIZE,
                leftIndent=20 * (level - 1),
                rightIndent=30,
                firstLineIndent=0,
            )
            level_styles.append(style)
        self.toc = TableOfContents(
            dotsMinLevel=-1,
            levelStyles=level_styles,
        )
        self.flowables.append(self.toc)

    def new_paragraph(self, text=None, thematic_break=False):
        """Create a new paragraph, add the text (if any) to it and return it.
        Optionally add a thematic break before it.
        """
        self.paragraph_flush()
        if thematic_break:
            self.flowables.append(
                HRFlowable(width="60%", color=reportlab.lib.colors.black, spaceAfter=10)
            )
        self.paragraph = Paragraph(self)
        if text:
            self.paragraph.add(text)
        return self.paragraph

    def new_quote(self, text=None):
        "Create a new quotation paragraph, add the text (if any) to it and return it."
        self.paragraph_flush()
        self.paragraph = Quote(self)
        if text:
            self.paragraph.add(text)
        return self.paragraph

    def new_section(self, title, subtitle=None):
        "Add a new section, which is a context that increments the section level."
        self.setup_toc()
        self.paragraph_flush()
        return Section(self, title, subtitle=subtitle)

    def new_page(self):
        self.paragraph_flush()
        self.flowables.append(NotAtTopPageBreak())

    def new_list(self, ordered=False):
        self.paragraph_flush()
        return List(self, ordered=ordered)

    def paragraph_flush(self):
        "Flush out the current paragraph."
        if self.paragraph:
            self.paragraph.output()
            self.paragraph = None

    def write(self, filepath):
        self.paragraph_flush()
        output = io.BytesIO()
        kwargs = dict(
            title=self.title,
            author=", ".join(self.authors) or None,
            creator=f"opus {VERSION}",
            lang=self.language,
        )
        if self.toc_level:
            pdfdoc = TocDocTemplate(output, self.toc_level, **kwargs)
            pdfdoc.multiBuild(self.flowables, onLaterPages=self.write_page_number)
        else:
            pdfdoc = SimpleDocTemplate(output, **kwargs)
            pdfdoc.build(self.flowables, onLaterPages=self.write_page_number)
        with open(filepath, "wb") as outfile:
            outfile.write(output.getvalue())

    def write_page_number(self, canvas, pdfdoc):
        "Output page number onto the current canvas."
        width, height = reportlab.rl_config.defaultPageSize
        canvas.saveState()
        canvas.setFont(NORMAL_FONT, NORMAL_FONT_SIZE)
        canvas.drawString(width - 84, height - 56, str(pdfdoc.page))
        canvas.restoreState()


class TocDocTemplate(SimpleDocTemplate):

    def __init__(self, filename, toc_level, **kwargs):
        super().__init__(filename, **kwargs)
        self.toc_level = toc_level

    def afterFlowable(self, flowable):
        "Registers TOC entries."
        if flowable.__class__.__name__ != "Paragraph":
            return
        stylename = flowable.style.name
        if not stylename.startswith("Heading"):
            return
        text = flowable.getPlainText()
        for level in range(1, self.toc_level + 1):
            if stylename == f"Heading{level}":
                self.notify("TOCEntry", (level, text, self.page))
                break


class Section(BaseSection):

    def __enter__(self):
        super().__enter__()
        self.document.flowables.append(
            PdfParagraph(self.title, style=self.document.stylesheet[f"Heading{self.level}"])
        )
        if self.subtitle:
            self.document.flowables.append(
                PdfParagraph(
                    self.subtitle, style=self.document.stylesheet[f"SectionSubtitle{self.level+1}"]
                )
            )
        return self


class Paragraph(BaseParagraph):

    STYLESHEETNAME = "Normal"

    def __init__(self, document):
        super().__init__(document)
        self.buffer = []

    def add(self, text, raw=False):
        """Add the text to the paragraph.
        - Exchanges newlines for blanks.
        - Removes superfluous blanks.
        - Prepends a blank, if 'raw' is False.
        """
        assert isinstance(text, str)
        if not raw:
            self.buffer.append(" ")
        self.buffer.append(text)  # No cleanup needed; reportlab does that.

    def linebreak(self):
        self.buffer.append("<br/>")

    def emdash(self, raw=False):
        if not raw:
            self.buffer.append(" ")
        self.buffer.append(EMDASH)

    def indexed(self, text, canonical=None, raw=False):
        if not raw:
            self.buffer.append(" ")
        with self.underline():
            self.buffer.append(text)
        self.document.add_indexed(canonical or text, self.location)

    def link(self, href, text=None, raw=False):
        if not raw:
            self.buffer.append(" ")
        self.buffer.append(
            f'<link href="{href}" underline="true" color="blue">{text or href}</link>'
        )

    @contextmanager
    def bold(self):
        self.buffer.append("<b>")
        try:
            yield self
        finally:
            self.buffer.append("</b>")

    @contextmanager
    def italic(self):
        self.buffer.append("<i>")
        try:
            yield self
        finally:
            self.buffer.append("</i>")

    @contextmanager
    def underline(self):
        self.buffer.append("<u>")
        try:
            yield self
        finally:
            self.buffer.append("</u>")

    @contextmanager
    def subscript(self):
        try:
            self.buffer.append("<sub>")
            yield self
        finally:
            self.buffer.append("</sub>")

    @contextmanager
    def superscript(self):
        try:
            self.buffer.append("<super>")
            yield self
        finally:
            self.buffer.append("</super>")

    def output(self, flowables=None):
        if not self.buffer:
            return
        if self.document.paragraph_numbers:
            self.buffer.insert(0, f"({self.document.paragraphs_count}) ")
        if flowables is None:
            flowables = self.document.flowables
        flowables.append(
            PdfParagraph(
                "".join(self.buffer),
                style=self.document.stylesheet[self.STYLESHEETNAME],
            )
        )
        self.buffer = []


class Quote(Paragraph):

    STYLESHEETNAME = "Quote"


class List(BaseList):

    def __init__(self, document, ordered=False, parent=None):
        super().__init__(document, ordered=ordered)
        self.parent = parent

    def __enter__(self):
        self.flowables = []
        return self

    def __exit__(self, *exc):
        if self.ordered:
            style = self.document.stylesheet["OrderedList"]
        else:
            style = self.document.stylesheet["UnorderedList"]
        if self.parent is None:
            self.document.flowables.append(ListFlowable(self.flowables, style=style))
        else:
            self.parent.flowables.append(ListFlowable(self.flowables, style=style))

    def new_item(self):
        return ListItem(self)


class ListItem(BaseListItem):

    def __enter__(self):
        self.flowables = []
        self.paragraph = None
        return self

    def __exit__(self, *exc):
        self.paragraph_flush()
        self.list.flowables.append(PdfListItem(self.flowables))

    def new_paragraph(self, text=None):
        self.paragraph_flush()
        self.paragraph = Paragraph(self.list.document)
        if text:
            self.paragraph.add(text)
        return self.paragraph

    def new_quote(self, text=None):
        self.paragraph_flush()
        self.paragraph = Quote(self.list.document)
        if text:
            self.paragraph.add(text)
        return self.paragraph

    def new_list(self, ordered=False):
        self.paragraph_flush()
        return List(self.list.document, ordered=ordered, parent=self)

    def paragraph_flush(self):
        "Flush out the current paragraph of this list item."
        if self.paragraph:
            self.paragraph.output(flowables=self.flowables)
            self.paragraph = None
