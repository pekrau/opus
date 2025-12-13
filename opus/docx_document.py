"DOCX document interface."

import datetime

import docx
import docx.oxml
import docx.shared
import docx.styles.style

from .base_document import *

__all__ = ["Document"]

MAX_LEVEL = 6
HEADER_SPACE_BEFORE = 14
HEADER_SPACE_AFTER = 6
TOC_STYLE = "Normal Table"
NORMAL_FONT = "Helvetica"
NORMAL_FONT_SIZE = 12
NORMAL_LINE_SPACING = 18
QUOTE_FONT = "Times New Roman"
QUOTE_FONT_SIZE = 14
QUOTE_INDENT = 24
CODE_FONT = "Courier"
CODE_FONT_SIZE = 11
CODE_LINE_SPACING = 12
CODE_INDENT = 10
TITLE_PAGE_SPACER = 80
HYPERLINK_COLOR = (0x05, 0x63, 0xC1)
EMDASH = "\u2014"


class Document(BaseDocument):
    "DOCX document interface."

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.indexed = {}
        self.page_number = 1

        self.docx = self.get_docx()
        self.toc_table = None
        p = None
        if self.title:
            p = self.docx.add_heading(self.title, 0)
        if self.subtitle:
            p = self.docx.add_heading(self.subtitle, 1)
        if self.authors:
            p = self.docx.add_heading(", ".join(self.authors), 2)
        if self.version:
            p = self.docx.add_paragraph(self.version)
        if p:
            p.paragraph_format.space_after = docx.shared.Pt(TITLE_PAGE_SPACER)

    def initialize_toc(self):
        if not self.toc_level:
            return
        if self.toc_table:
            return
        self.page_number += 1
        self.docx.add_page_break()
        self.docx.add_heading(self.toc_title, 1)
        self.toc_table = self.docx.add_table(
            rows=0, cols=0, style=self.docx.styles[TOC_STYLE]
        )
        self.toc_table.add_column(docx.shared.Mm(140))
        self.toc_table.add_column(docx.shared.Mm(20))

    def get_docx(self):
        "Create, initialize and return a docx Document instance."
        result = docx.Document()

        # Set the default document-wide language.
        # From https://stackoverflow.com/questions/36967416/how-can-i-set-the-language-in-text-with-python-docx
        if self.language:
            styles_element = result.styles.element
            rpr_default = styles_element.xpath("./w:docDefaults/w:rPrDefault/w:rPr")[0]
            lang_default = rpr_default.xpath("w:lang")[0]
            lang_default.set(docx.oxml.shared.qn("w:val"), self.language)

        # Set to A4 page size. The section here is an instance of the docx Section class.
        section = result.sections[-1]
        section.page_height = docx.shared.Mm(297)
        section.page_width = docx.shared.Mm(210)
        section.left_margin = docx.shared.Mm(25.4)  # 1 inch
        section.right_margin = docx.shared.Mm(25.4)
        section.top_margin = docx.shared.Mm(25.4)
        section.bottom_margin = docx.shared.Mm(25.4)
        section.header_distance = docx.shared.Mm(12.7)  # 0.5 inch
        section.footer_distance = docx.shared.Mm(12.7)

        # Modify styles.
        style = result.styles["Title"]
        style.font.color.rgb = docx.shared.RGBColor(0, 0, 0)

        for level in range(1, MAX_LEVEL + 1):
            style = result.styles[f"Heading {level}"]
            style.paragraph_format.space_before = docx.shared.Pt(HEADER_SPACE_BEFORE)
            style.paragraph_format.space_after = docx.shared.Pt(HEADER_SPACE_AFTER)
            style.font.color.rgb = docx.shared.RGBColor(0, 0, 0)

        style = result.styles["Normal"]
        style.font.name = NORMAL_FONT
        style.font.size = docx.shared.Pt(NORMAL_FONT_SIZE)
        style.paragraph_format.line_spacing = docx.shared.Pt(NORMAL_LINE_SPACING)

        style = result.styles["Quote"]  # Quote blocks.
        style.font.name = QUOTE_FONT
        style.font.size = docx.shared.Pt(QUOTE_FONT_SIZE)
        style.font.italic = False
        style.paragraph_format.left_indent = docx.shared.Pt(QUOTE_INDENT)
        style.paragraph_format.right_indent = docx.shared.Pt(QUOTE_INDENT)

        style = result.styles["macro"]  # Code blocks.
        style.font.name = CODE_FONT
        style.font.size = docx.shared.Pt(CODE_FONT_SIZE)
        style.paragraph_format.line_spacing = docx.shared.Pt(CODE_LINE_SPACING)
        style.paragraph_format.left_indent = docx.shared.Pt(CODE_INDENT)

        style = result.styles.add_style(
            "Hyperlink", docx.enum.style.WD_STYLE_TYPE.CHARACTER, True
        )
        style.base_style = result.styles["Normal"]
        style.unhide_when_used = True
        style.font.color.rgb = docx.shared.RGBColor(*HYPERLINK_COLOR)
        style.font.underline = True

        # Set Dublin core metadata.
        if self.authors:
            result.core_properties.author = ", ".join(self.authors)
        result.core_properties.created = datetime.datetime.now(tz=datetime.UTC)
        if self.language:
            result.core_properties.language = self.language

        # Display page number in the header.
        # https://stackoverflow.com/questions/56658872/add-page-number-using-python-docx
        paragraph = result.sections[-1].header.paragraphs[0]
        paragraph.alignment = docx.enum.text.WD_ALIGN_PARAGRAPH.RIGHT
        run = paragraph.add_run()
        fldChar1 = docx.oxml.OxmlElement("w:fldChar")
        fldChar1.set(docx.oxml.ns.qn("w:fldCharType"), "begin")
        instrText = docx.oxml.OxmlElement("w:instrText")
        instrText.set(docx.oxml.ns.qn("xml:space"), "preserve")
        instrText.text = "PAGE"
        fldChar2 = docx.oxml.OxmlElement("w:fldChar")
        fldChar2.set(docx.oxml.ns.qn("w:fldCharType"), "end")
        run._r.append(fldChar1)
        run._r.append(instrText)
        run._r.append(fldChar2)

        return result

    def new_paragraph(self, text=None, thematic_break=False):
        """Create a new paragraph, add the text (if any) to it and return it.
        Optionally add a thematic break before it.
        """
        if thematic_break:
            p = self.docx.add_paragraph(EMDASH * 20, style="Normal")
            p.alignment = docx.enum.text.WD_ALIGN_PARAGRAPH.CENTER
        self.paragraphs_count += 1
        paragraph = Paragraph(self)
        if text:
            paragraph.add(text)
        return paragraph

    def new_quote(self, text=None):
        "Create a new quotation paragraph, add the text (if any) to it and return it."
        self.paragraphs_count += 1
        paragraph = Quote(self)
        if text:
            paragraph.add(text)
        return paragraph

    def new_section(self, title, subtitle=None):
        "Add a new section, which is a context that increments the section level."
        return Section(self, title, subtitle=subtitle)

    def new_page(self):
        self.page_number += 1
        self.docx.add_page_break()

    def set_page_number(self, number):
        self.page_number = number

    def write(self, filepath):
        self.output_final()
        self.docx.save(filepath)

    def output_indexed(self):
        if not self.indexed:
            return
        with self.no_numbers():
            with self.new_section(self.index_title):
                p = self.new_paragraph()
                for canonical, page_numbers in self.indexed.items():
                    numbers = ", ".join([str(n) for n in sorted(page_numbers)])
                    p.add(f"{canonical},\t{numbers}")
                    p.linebreak()


class Section(BaseSection):

    def __init__(self, document, title, subtitle=None):
        super().__init__(document, title, subtitle=subtitle)
        self.document.initialize_toc()

    def __enter__(self):
        title, level = self.at_enter()
        self.document.docx.add_heading(title, level=level)
        if self.subtitle:
            self.document.docx.add_heading(self.subtitle, level=level+1)
        if level <= self.document.toc_level:
            cells = self.document.toc_table.add_row().cells
            cells[0].text = title
            cells[0].paragraphs[0].paragraph_format.space_before = docx.shared.Mm(1)
            cells[0].paragraphs[0].paragraph_format.space_after = docx.shared.Mm(1)
            cells[0].paragraphs[0].paragraph_format.left_indent = docx.shared.Mm(3*(level-1))
            cells[1].text = str(self.document.page_number)
            cells[1].paragraphs[0].alignment = docx.enum.text.WD_ALIGN_PARAGRAPH.RIGHT
            cells[1].paragraphs[0].paragraph_format.space_before = docx.shared.Mm(1)
            cells[1].paragraphs[0].paragraph_format.space_after = docx.shared.Mm(1)
        return self.document


class Paragraph(BaseParagraph):

    STYLESHEETNAME = "Normal"

    def __init__(self, document):
        super().__init__(document)
        self.paragraph = document.docx.add_paragraph(style=self.STYLESHEETNAME)
        self.line_started = False
        self._bold = 0
        self._italic = 0
        self._underline = 0
        self._subscript = 0
        self._superscript = 0
        if document.paragraph_numbers:
            self.add(f"({document.paragraphs_count})")

    def add(self, text, raw=False):
        """Add the text to the paragraph.
        - Exchanges newlines for blanks.
        - Removes superfluous blanks.
        - Prepends a blank, if 'raw' is False.
        """
        assert isinstance(text, str)
        lines = list(text.split())
        if raw or not self.line_started:
            result = []
        else:
            result = [" "]
        if not lines:
            return
        for line in lines[:-1]:
            result.append(line)
            result.append(" ")
        result.append(lines[-1])
        self.set_font_style(self.paragraph.add_run("".join(result)))
        self.line_started = True

    def linebreak(self):
        self.paragraph.add_run("\n")
        self.line_started = False

    def emdash(self, raw=False):
        if not raw and self.line_started:
            self.set_font_style(self.paragraph.add_run(" "))
        self.set_font_style(self.paragraph.add_run(EMDASH))
        self.line_started = True

    def indexed(self, text, canonical=None, raw=False):
        if not raw and self.line_started:
            self.set_font_style(self.paragraph.add_run(" "))
        with self.underline():
            self.raw(text)
        self.line_started = True
        self.document.indexed.setdefault(canonical or text, set()).add(
            self.document.page_number
        )

    def link(self, href, text=None, raw=False):
        if not raw and self.line_started:
            self.set_font_style(self.paragraph.add_run(" "))

        # https://github.com/python-openxml/python-docx/issues/74#issuecomment-261169410
        # This works in 'writethatbook', but not here??

        # This gets access to the document.xml.rels file and gets a new relation id value
        part = self.paragraph.part
        r_id = part.relate_to(
            href, docx.opc.constants.RELATIONSHIP_TYPE.HYPERLINK, is_external=True
        )

        # Create the w:hyperlink tag and add needed values
        hyperlink = docx.oxml.shared.OxmlElement("w:hyperlink")
        hyperlink.set(docx.oxml.shared.qn("r:id"), r_id)

        # Create a w:r element and a new w:rPr element and join together
        new_run = docx.oxml.shared.OxmlElement("w:r")
        rPr = docx.oxml.shared.OxmlElement("w:rPr")
        new_run.append(rPr)

        # Style and add text to the w:r element
        new_run.text = text or href
        new_run.style = "Hyperlink"
        hyperlink.append(new_run)

        self.paragraph._p.append(hyperlink)
        self.line_started = True

    @contextmanager
    def bold(self):
        try:
            self._bold += 1
            yield self
        finally:
            self._bold -= 1

    @contextmanager
    def italic(self):
        try:
            self._italic += 1
            yield self
        finally:
            self._italic -= 1

    @contextmanager
    def underline(self):
        try:
            self._underline += 1
            yield self
        finally:
            self._underline -= 1

    @contextmanager
    def subscript(self):
        try:
            self._subscript += 1
            yield self
        finally:
            self._subscript -= 1

    @contextmanager
    def superscript(self):
        try:
            self._superscript += 1
            yield self
        finally:
            self._superscript -= 1

    def set_font_style(self, run):
        if self._bold:
            run.font.bold = True
        if self._italic:
            run.font.italic = True
        if self._underline:
            run.font.underline = True
        if self._subscript:
            run.font.subscript = True
        if self._superscript:
            run.font.superscript = True


class Quote(Paragraph):

    STYLESHEETNAME = "Quote"
