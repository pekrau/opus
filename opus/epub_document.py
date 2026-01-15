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
        self._paragraph = None
        self.filename = None

        self.book = epub.EpubBook()
        self.stylesheet = epub.EpubItem(
            uid="stylesheet",
            file_name="style/stylesheet.css",
            media_type="text/css",
            content=STYLESHEET,
        )
        self.book.add_item(self.stylesheet)
        self.book.add_metadata("DC", "date", datetime.date.today().isoformat())
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
        self.flush()

    def paragraph(self, text=None, thematic_break=False):
        """Create a new paragraph, add the text (if any) to it and return it.
        Optionally add a thematic break before it.
        """
        self.flush()
        if thematic_break:
            self.thematic_break()
        self._paragraph = Paragraph(self)
        if text:
            self._paragraph.add(text)
        return self._paragraph

    def thematic_break(self):
        self.flush()
        self.buffer.append('<hr style="margin-top: 40px;"/>')

    def quote(self, text=None):
        "Create a new quotation paragraph, add the text (if any) to it and return it."
        self.flush()
        self._paragraph = Quote(self)
        if text:
            self._paragraph.add(text)
        return self._paragraph

    def section(self, title, subtitle=None):
        "Add a new section, which is a context that increments the section level."
        return Section(self, title, subtitle=subtitle)

    def pagebreak(self):
        self.flush()
        self.buffer.append('<br style="page-break-after: always;"/>')

    def ordered_list(self):
        self.flush()
        return List(self, ordered=True)

    def unordered_list(self):
        self.flush()
        return List(self, ordered=False)

    def flush(self):
        "Flush out any pending output."
        if self._paragraph:
            self._paragraph.output()
            self._paragraph = None

    @property
    def location(self):
        return (self.paragraphs_count, self.filename)

    def output_indexed_location(self, paragraph, location):
        number, filename = location
        paragraph.raw(f', <a href="{filename}#{number}">{number}</a>')

    def write(self, filepath):
        self.flush()
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
        contents = [f"<h1>{self.toc_title}</h1>", "<p>"]
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
        self.document.flush()
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
        self.document.flush()
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
        - Exchange newlines for blanks.
        - Remove superfluous blanks.
        - Prepend a blank, if 'raw' is False.
        - Return the paragraph.
        """
        assert isinstance(text, str)
        if not raw:
            self.contents.append(" ")
        self.contents.append(text)
        return self

    def linebreak(self):
        "Add a line break. Return the paragraph."
        self.contents.append("<br/>")
        return self

    def emdash(self, raw=False):
        "Add an emdash character. Return the paragraph."
        if not raw:
            self.contents.append(" ")
        self.contents.append(EMDASH)
        return self

    def indexed(self, text, canonical=None, raw=False):
        "Add an indexed term, optionally with its canonical term. Return the paragraph."
        if not raw:
            self.contents.append(" ")
        with self.underline():
            self.raw(text)
        self.document.add_indexed(canonical or text)
        return self

    def link(self, href, text=None, raw=False):
        "Add a hyperlink, optionally with a text to display. Return the paragraph."
        if not raw:
            self.contents.append(" ")
        self.contents.append(f'<a href="{href}">{text or href}</a>')
        return self

    def comment(self, text):
        pass

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
        self.document.buffer.append(
            f'<{self.TAG} id=f"{self.document.paragraphs_count}">'
        )
        if self.document.paragraph_numbers:
            self.document.buffer.append(f"({self.document.paragraphs_count})")
        self.document.buffer.append("".join(self.contents))
        self.document.buffer.append(f"</{self.TAG}>")
        self.contents = []


class Quote(Paragraph):

    TAG = "blockquote"


class List(BaseList):
    "List class; a context manager."

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

    def item(self):
        return ListItem(self)


class ListItem(BaseListItem):
    "List item class; a context manager."

    def __enter__(self):
        self.list.document.buffer.append("<li>")
        self._paragraph = None
        return self

    def __exit__(self, *exc):
        self.flush()
        self.list.document.buffer.append("</li>")

    def paragraph(self, text=None):
        self.flush()
        self._paragraph = Paragraph(self.list.document)
        if text:
            self._paragraph.add(text)
        return self._paragraph

    def quote(self, text=None):
        self.flush()
        self._paragraph = Quote(self.list.document)
        if text:
            self._paragraph.add(text)
        return self._paragraph

    def ordered_list(self):
        self.flush()
        return List(self.list.document, ordered=True)

    def unordered_list(self):
        self.flush()
        return List(self.list.document, ordered=False)

    def flush(self):
        "Flush out any pending output for this list item."
        if self._paragraph:
            self._paragraph.output()
            self._paragraph = None
