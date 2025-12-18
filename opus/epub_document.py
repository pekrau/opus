"EPUB document interface."

import datetime

from ebooklib import epub

from .base_document import *

__all__ = ["Document"]

MAX_LEVEL = 6
EMDASH = "\u2014"
STYLESHEET = """
body {
  color: black;
  background-color: white;
  font-family: Arial, Helvetica, sans-serif;
}
blockquote {
  font-family: "Times New Roman", serif;
}
"""


class Document(BaseDocument):
    "EPUB document interface."

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.buffer = []
        self.chapters = []  # Title page and level 1 sections.
        self.indexed = {}
        self.paragraph = None
        self.filename = None

        self.book = epub.EpubBook()
        self.stylesheet = epub.EpubItem(
            uid="stylesheet",
            file_name="style/stylesheet.css",
            media_type="text/css",
            content=STYLESHEET,
        )
        self.book.add_item(self.stylesheet)
        if self.identifier:
            self.book.add_metadata("DC", "identifier", self.identifier)
        if self.title:
            self.book.set_title(self.title)
            self.buffer.append(f"<h1>{self.title}</h1>")
        if self.subtitle:
            self.book.add_metadata("DC", "description", self.subtitle)
            self.buffer.append(f"<h2>{self.subtitle}</h2>")
        if self.authors:
            self.buffer.append("<h3>")
            for pos, author in enumerate(self.authors):
                self.book.add_author(author)
                if pos >= 1:
                    self.buffer.append("<br/>")
                self.buffer.append(author)
            self.buffer.append("</h3>")
        if self.version:
            self.book.add_metadata("DC", "hasVersion", self.version)
            self.buffer.append(f"<p>{self.version}</p>")
        self.buffer.append("<hr/>")
        if self.language:
            self.book.set_language(self.language)
        self.book.add_metadata("DC", "creator", f"opus {VERSION}")
        self.filename = "title_page.xhtml"
        title_page = epub.EpubHtml(
            uid="title_page",
            title=self.title_page_title,
            file_name=self.filename,
            lang=self.language,
        )
        title_page.add_item(self.stylesheet)
        self.chapters.append(title_page)
        self.paragraph_flush()

    def new_paragraph(self, text=None, thematic_break=False):
        """Create a new paragraph, add the text (if any) to it and return it.
        Optionally add a thematic break before it.
        """
        self.paragraph_flush()
        if thematic_break:
            self.thematic_break()
        self.paragraph = Paragraph(self)
        if text:
            self.paragraph.add(text)
        return self.paragraph

    def thematic_break(self):
        self.paragraph_flush()
        self.buffer.append('<hr style="margin-top: 40px;"/>')

    def new_quote(self, text=None):
        "Create a new quotation paragraph, add the text (if any) to it and return it."
        self.paragraph_flush()
        self.paragraph = Quote(self)
        if text:
            self.paragraph.add(text)
        return self.paragraph

    def new_section(self, title, subtitle=None):
        "Add a new section, which is a context that increments the section level."
        return Section(self, title, subtitle=subtitle)

    def new_page(self):
        self.paragraph_flush()
        self.buffer.append('<br style="page-break-after: always;"/>')

    def new_list(self, ordered=False):
        self.paragraph_flush()
        return List(self, ordered=ordered)

    def paragraph_flush(self):
        "Output the current paragraph, if any."
        if self.paragraph:
            self.paragraph.output()
            self.paragraph = None

    @property
    def location(self):
        return (self.paragraphs_count, self.filename)

    def output_indexed_location(self, paragraph, location):
        number, filename = location
        paragraph.raw(f', <a href="{filename}#{number}">{number}</a>')

    def write(self, filepath):
        self.paragraph_flush()
        if self.buffer:
            self.chapters[-1].content = "\n".join(self.buffer)
        self.filename = "nav.xhtml"
        nav = epub.EpubHtml(
            uid="nav",
            title=self.toc_title,
            file_name=self.filename,
            lang=self.language,
        )
        nav.add_item(self.stylesheet)
        contents = [
            f'<h1>{self.toc_title}</h1>',
            '<p>'
        ]
        for ch in self.chapters[1:]:
            contents.append(f'<a href="{ch.file_name}">{ch.title}</a><br/>')
        contents.append("</ul></p>")
        nav.content = "\n".join(contents)
        self.chapters.insert(1, nav)
        for ch in self.chapters:
            self.book.add_item(ch)
        self.book.toc = self.chapters
        self.book.spine = self.chapters
        self.book.add_item(epub.EpubNcx())
        epub.write_epub(filepath, self.book)


class Section(BaseSection):

    def __enter__(self):
        # The superclass '__enter__' method is wholly superceded.
        self.document.paragraph_flush()
        self.document.sections_counts.append(0)
        if self.level <= 1:
            if self.document.buffer:
                self.document.chapters[-1].content = "\n".join(self.document.buffer)
                self.document.buffer = []
            self.document.filename = f"{self.number(delimiter='_')}section.xhtml"
            chapter = epub.EpubHtml(
                title=self.title,
                file_name=self.document.filename,
                lang=self.document.language,
            )
            chapter.add_item(self.document.stylesheet)
            self.document.chapters.append(chapter)
        self.document.buffer.append(f"<h{self.level}>{self.title}</h{self.level}>")
        if self.subtitle:
            self.document.buffer.append(
                f"<h{self.level+1}>{self.subtitle}</h{self.level+1}>"
            )
        return self

    def output_footnotes(self, title="Footnotes"):
        "Output the footnotes to the section."
        if not self.document.footnotes:
            return
        with self.document.no_numbers():
            self.document.thematic_break()
            self.document.buffer.append(f"<h{self.level+1}>{title}</h{self.level+1}>")
            self.document.output_footnotes_list()


class Paragraph(BaseParagraph):

    TAG = "p"

    def __init__(self, document):
        super().__init__(document)
        self.contents = []

    def add(self, text, raw=False):
        """Add the text to the paragraph.
        - Exchanges newlines for blanks.
        - Removes superfluous blanks.
        - Prepends a blank, if 'raw' is False.
        """
        assert isinstance(text, str)
        if not raw:
            self.contents.append(" ")
        self.contents.append(text)

    def linebreak(self):
        self.contents.append("<br/>")

    def emdash(self, raw=False):
        if not raw:
            self.contents.append(" ")
        self.contents.append(EMDASH)

    def indexed(self, text, canonical=None, raw=False):
        if not raw:
            self.contents.append(" ")
        with self.underline():
            self.raw(text)
        self.document.add_indexed(canonical or text)

    def link(self, href, text=None, raw=False):
        if not raw:
            self.contents.append(" ")
        self.contents.append(f'<a href="{href}">{text or href}</a>')

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
            self.contents.append("<sup>")
            yield self
        finally:
            self.contents.append("</sup>")

    def output(self):
        if not self.contents:
            return
        self.document.buffer.append(f'<{self.TAG} id=f"{self.document.paragraphs_count}">')
        if self.document.paragraph_numbers:
            self.document.buffer.append(f"({self.document.paragraphs_count})")
        self.document.buffer.append("".join(self.contents))
        self.document.buffer.append(f"</{self.TAG}>")
        self.contents = []


class Quote(Paragraph):

    TAG = "blockquote"


class List(BaseList):

    def __enter__(self):
        if self.ordered:
            self.document.buffer.append("<ol>")
        else:
            self.document.buffer.append("<ul>")
        return self

    def __exit__(self, *exc):
        if self.ordered:
            self.document.buffer.append("</ol>")
        else:
            self.document.buffer.append("</ul>")

    def new_item(self):
        return ListItem(self)


class ListItem(BaseListItem):

    def __enter__(self):
        self.list.document.buffer.append("<li>")
        self.paragraph = None
        return self

    def __exit__(self, *exc):
        self.paragraph_flush()
        self.list.document.buffer.append("</li>")

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
        return List(self.list.document, ordered=ordered)

    def paragraph_flush(self):
        "Flush out the current paragraph of this list item."
        if self.paragraph:
            self.paragraph.output()
            self.paragraph = None
