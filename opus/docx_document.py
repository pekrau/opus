"DOCX document interface."

from contextlib import contextmanager
import datetime

import docx
import docx.oxml
import docx.shared
import docx.styles.style

from .constants import *


class Document:
    "DOCX document interface."

    def __init__(
        self,
        title=None,
        authors=None,
        version=None,
        language="sv-SE",
        page_break_level=1,
        section_numbers=True,
    ):
        self.title = title
        self.authors = authors
        self.version = version
        self.language = language
        self.page_break_level = page_break_level
        self.section_numbers = section_numbers

        self.docx = docx.Document()
        # Set the default document-wide language.
        # From https://stackoverflow.com/questions/36967416/how-can-i-set-the-language-in-text-with-python-docx
        if self.language:
            styles_element = self.docx.styles.element
            rpr_default = styles_element.xpath("./w:docDefaults/w:rPrDefault/w:rPr")[0]
            lang_default = rpr_default.xpath("w:lang")[0]
            lang_default.set(docx.oxml.shared.qn("w:val"), self.language)

        # Set to A4 page size. The section here is the docx class, not the Document one.
        section = self.docx.sections[0]
        section.page_height = docx.shared.Mm(297)
        section.page_width = docx.shared.Mm(210)
        section.left_margin = docx.shared.Mm(25.4)
        section.right_margin = docx.shared.Mm(25.4)
        section.top_margin = docx.shared.Mm(25.4)
        section.bottom_margin = docx.shared.Mm(25.4)
        section.header_distance = docx.shared.Mm(12.7)
        section.footer_distance = docx.shared.Mm(12.7)

        # Modify styles.
        style = self.docx.styles["Title"]
        style.font.color.rgb = docx.shared.RGBColor(0, 0, 0)

        for level in range(1, MAX_LEVEL + 1):
            style = self.docx.styles[f"Heading {level}"]
            style.paragraph_format.space_after = docx.shared.Pt(
                2 * (MAX_LEVEL + 1 - level)
            )
            style.font.color.rgb = docx.shared.RGBColor(0, 0, 0)

        style = self.docx.styles["Normal"]
        style.font.name = DOCX_NORMAL_FONT
        style.font.size = docx.shared.Pt(DOCX_NORMAL_FONT_SIZE)
        style.paragraph_format.line_spacing = docx.shared.Pt(DOCX_NORMAL_LINE_SPACING)

        # "Body Text": TOC entries and for index pages.
        style = self.docx.styles["Body Text"]
        style.font.name = DOCX_NORMAL_FONT
        style.paragraph_format.space_before = docx.shared.Pt(DOCX_TOC_SPACE_BEFORE)
        style.paragraph_format.space_after = docx.shared.Pt(DOCX_TOC_SPACE_AFTER)

        style = self.docx.styles["Quote"]
        style.paragraph_format.left_indent = docx.shared.Pt(DOCX_QUOTE_INDENT)
        style.paragraph_format.right_indent = docx.shared.Pt(DOCX_QUOTE_INDENT)

        style = self.docx.styles["macro"]
        style.font.name = DOCX_CODE_FONT
        style.font.size = docx.shared.Pt(DOCX_CODE_FONT_SIZE)
        style.paragraph_format.line_spacing = docx.shared.Pt(DOCX_CODE_LINE_SPACING)
        style.paragraph_format.left_indent = docx.shared.Pt(DOCX_CODE_INDENT)

        style = self.docx.styles.add_style(
            "Hyperlink", docx.enum.style.WD_STYLE_TYPE.CHARACTER, True
        )
        style.base_style = self.docx.styles["Normal"]
        style.unhide_when_used = True
        style.font.color.rgb = docx.shared.RGBColor(*DOCX_HYPERLINK_COLOR)
        style.font.underline = True

        # Set Dublin core metadata.
        if self.authors:
            self.docx.core_properties.author = ", ".join(self.authors)
        self.docx.core_properties.created = datetime.datetime.now(tz=datetime.UTC)
        # self.docx.core_properties.modified = self.book.modified
        if self.language:
            self.docx.core_properties.language = self.language

        # Display page number in the header.
        # https://stackoverflow.com/questions/56658872/add-page-number-using-python-docx
        paragraph = self.docx.sections[-1].header.paragraphs[0]
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

        if self.title:
            self.docx.add_heading(self.title, 0)
        if self.authors:
            self.docx.add_heading(", ".join(self.authors), 1)
        if self.version:
            self.docx.add_paragraph(self.version)
        self.section_counts = [0]

    def new_paragraph(self):
        self.paragraph = _Paragraph(self, style="Normal")
        return self.paragraph

    def new_section(self, title):
        return _Section(self, title)

    def new_page(self):
        self.docx.add_page_break()

    def write(self, filepath):
        self.docx.save(filepath)


class _Paragraph:

    def __init__(self, document, style="Normal"):
        self.paragraph = document.docx.add_paragraph(style=style)
        self._bold = 0
        self._italic = 0
        self._underline = 0

    def add(self, text):
        assert isinstance(text, str)
        self.set_font_style(self.paragraph.add_run(text.replace("\n", " ")))

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

    def set_font_style(self, run):
        if self._bold:
            run.bold = True
        if self._italic:
            run.italic = True
        if self._underline:
            run.underline = True

    def add_link(self, text, href):
        assert isinstance(text, str)
        # https://stackoverflow.com/questions/47666642/adding-an-hyperlink-in-msword-by-using-python-docx

        # This gets access to the document.xml.rels file and gets a new relation id value.
        part = self.paragraph.part
        r_id = part.relate_to(
            href, docx.opc.constants.RELATIONSHIP_TYPE.HYPERLINK, is_external=True
        )

        # Create the w:hyperlink tag and add needed values.
        hyperlink = docx.oxml.shared.OxmlElement("w:hyperlink")
        hyperlink.set(docx.oxml.shared.qn("r:id"), r_id)

        # Create a new run object (a wrapper over a 'w:r' element)
        new_run = docx.text.run.Run(docx.oxml.shared.OxmlElement("w:r"), self.paragraph)
        new_run.text = text
        new_run.style = "Hyperlink"
        self.set_font_style(new_run)

        # Join the XML elements together.
        hyperlink.append(new_run._element)
        self.paragraph._p.append(hyperlink)


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
        self.document.docx.add_heading(title, level=level)
        return self

    def __exit__(self, *exc):
        self.document.section_counts.pop()
