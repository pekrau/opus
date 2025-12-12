"PDF document interface."

import datetime
import io

import reportlab
import reportlab.rl_config
import reportlab.lib.colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph as PdfParagraph
from reportlab.platypus import (
    Spacer,
    PageBreak,
    NotAtTopPageBreak,
    SimpleDocTemplate,
    LayoutError,
)
from reportlab.platypus.tableofcontents import TableOfContents, SimpleIndex

from .base_document import *


__all__ = ["Document"]

NORMAL_FONT = "Helvetica"
NORMAL_FONT_SIZE = 12
NORMAL_LEADING = 18
NORMAL_SPACE_BEFORE = 6
NORMAL_SPACE_AFTER = 6
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
QUOTE_LEADING = 14
QUOTE_SPACE_BEFORE = 8
QUOTE_SPACE_AFTER = 14
QUOTE_INDENT = 28
FOOTNOTE_INDENT = 10
REFERENCE_SPACE_BEFORE = 7
REFERENCE_INDENT = 10


class Document(BaseDocument):
    "PDF document interface."

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.stylesheet = getSampleStyleSheet()
        # self.stylesheet.list()

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

        self.paragraph = None
        self.index = SimpleIndex(style=self.stylesheet["Normal"], headers=False)
        self.any_indexed = False
        self.flowables = []
        self.toc = None

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
        self.flowables.append(Spacer(0, TITLE_PAGE_SPACER))

    def setup_toc(self):
        if not self.toc_level:
            return
        if self.toc is not None:
            return
        self.flush()
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

    def new_paragraph(self):
        self.flush()
        self.paragraphs_count += 1
        self.paragraph = Paragraph(self)
        return self.paragraph

    def new_quote(self):
        self.flush()
        self.paragraphs_count += 1
        self.paragraph = Quote(self)
        return self.paragraph

    def new_section(self, title):
        self.setup_toc()
        self.flush()
        return Section(self, title)

    def new_page(self):
        self.flush()
        self.flowables.append(NotAtTopPageBreak())

    def set_page_number(self, number):
        "Not needed for PDF."
        pass

    def flush(self):
        if self.paragraph:
            self.paragraph.output()
            self.paragraph = None

    def write(self, filepath):
        self.flush()
        self.output_footnotes()
        if self.references and self.references.used:
            self.references.write(self)
        output = io.BytesIO()
        kwargs = dict(
            title=self.title,
            author=", ".join(self.authors) or None,
            creator=f"opus {VERSION}",
            lang=self.language,
        )
        if self.toc_level:
            pdfdoc = TocDocTemplate(output, self.toc_level, **kwargs)
        else:
            pdfdoc = SimpleDocTemplate(output, **kwargs)
        if self.any_indexed:
            self.new_page()
            self.flowables.append(
                PdfParagraph(self.index_title, style=self.stylesheet["Heading1"])
            )
            self.flowables.append(self.index)
            if self.toc_level:
                pdfdoc.multiBuild(
                    self.flowables,
                    onLaterPages=self.write_page_number,
                    canvasmaker=self.index.getCanvasMaker(),
                )
            else:
                pdfdoc.build(
                    self.flowables,
                    onLaterPages=self.write_page_number,
                    canvasmaker=self.index.getCanvasMaker(),
                )
        else:
            if self.toc_level:
                pdfdoc.multiBuild(self.flowables, onLaterPages=self.write_page_number)
            else:
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
        title, level = self.at_enter()
        self.document.flowables.append(
            PdfParagraph(title, style=self.document.stylesheet[f"Heading{level}"])
        )
        return self.document


class Paragraph(BaseParagraph):

    STYLESHEETNAME = "Normal"

    def __init__(self, document):
        super().__init__(document)
        self.contents = []

    def add(self, text, prepend_blank=True):
        assert isinstance(text, str)
        if prepend_blank:
            self.contents.append(" ")
        self.contents.append(text)

    def linebreak(self):
        self.contents.append("<br/>")

    def add_indexed(self, text, canonical=None, prepend_blank=True):
        if canonical:
            canonical = canonical.replace(",", ",,")
        if prepend_blank:
            self.contents.append(" ")
        with self.underline():
            self.contents.append(f'<index item="{canonical or text}">{text}</index>')
        self.document.any_indexed = True

    def add_link(self, text, href, prepend_blank=True):
        assert isinstance(text, str)
        if prepend_blank:
            self.contents.append(" ")
        self.contents.append(
            f'<link href="{href}" underline="true" color="blue">{text}</link>'
        )

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

    @contextmanager
    def subscript(self):
        try:
            self.contents.append("<sub>")
            yield self
        finally:
            self.contents.append("</sub>")

    @contextmanager
    def superscript(self):
        try:
            self.contents.append("<super>")
            yield self
        finally:
            self.contents.append("</super>")

    def output(self):
        if not self.contents:
            return
        if self.document.paragraph_numbers:
            self.contents.insert(0, f"({self.document.paragraphs_count}) ")
        self.document.flowables.append(
            PdfParagraph(
                "".join(self.contents),
                style=self.document.stylesheet[self.STYLESHEETNAME],
            )
        )
        self.contents = []


class Quote(Paragraph):

    STYLESHEETNAME = "Quote"
