"Base document interface."

VERSION = "0.5.0"

from contextlib import contextmanager
from dataclasses import dataclass


class BaseDocument:

    def __init__(
        self,
        title=None,
        authors=None,
        version=None,
        language="sv-SE",
        page_break_level=1,
        section_numbers=False,
        paragraph_numbers=False,
        toc_level=0,
        toc_title="Innehåll",
        index_title="Index",
        references=None,
        references_title="Referenser",
        footnotes_title="Fotnoter",
    ):
        self.title = title
        self.authors = authors
        self.version = version
        self.language = language
        self.page_break_level = page_break_level
        self.section_numbers = section_numbers
        self.paragraph_numbers = paragraph_numbers
        self.toc_level = toc_level
        self.toc_title = toc_title
        self.index_title = index_title
        self.references = references
        self.references_title = references_title
        self.footnotes_title = footnotes_title

        self.paragraphs_count = 0
        self.sections_counts = [0]
        self.footnotes = []

    def __call__(self, text=None):
        "Create a new paragraph, add the text to it and return it."
        p = self.new_paragraph()
        if text:
            p.add(text)
        return p

    def new_paragraph(self):
        raise NotImplementedError

    def new_quote(self):
        raise NotImplementedError

    def new_section(self, title):
        raise NotImplementedError

    def new_page(self):
        raise NotImplementedError

    def set_page_number(self, number):
        raise NotImplementedError

    def write(self, filepath):
        raise NotImplementedError

    def output_footnotes(self):
        if not self.footnotes:
            return
        p = self.new_paragraph()
        with p.italic():
            with p.bold():
                p += self.footnotes_title
        for footnote in self.footnotes:
            p = self.new_paragraph()
            with p.bold():
                p += f"{footnote.number}. "
            for item in footnote.items:
                match item.type:
                    case "text":
                        p.add(item.text)
                    case "indexed":
                        p.add_indexed(item.text, canonical=item.canonical, prepend_blank=item.prepend_blank)
                    case "link":
                        p.add_link(item.text, item.href, prepend_blank=item.prepend_blank)
                    case "reference":
                        p.add_reference(item.text)
        self.footnotes = []


class BaseSection:

    def __init__(self, document, title):
        self.document = document
        self.title = title
        self.document.sections_counts[-1] += 1

    def __call__(self, text=None):
        "Create a new paragraph, add the text to it and return it."
        p = self.new_paragraph()
        if text:
            p.add(text)
        return p

    def new_paragraph(self):
        return self.document.new_paragraph()

    def number(self):
        return ".".join([str(n) for n in self.document.sections_counts[:-1]]) + "."

    def __enter__(self):
        raise NotImplementedError

    def __exit__(self, *exc):
        self.document.sections_counts.pop()

    def at_enter(self):
        self.document.sections_counts.append(0)
        level = len(self.document.sections_counts) - 1
        if level <= self.document.page_break_level:
            self.document.new_page()
        if self.document.section_numbers:
            title = [self.number()]
        else:
            title = []
        if self.title:
            title.append(self.title)
        return " ".join(title), level

    def __exit__(self, *exc):
        self.document.output_footnotes()
        self.document.sections_counts.pop()


class BaseParagraph:

    def __init__(self, document):
        self.document = document

    def __iadd__(self, text):
        self.add(text)
        return self

    def add(self, text, prepend_blank=True):
        raise NotImplementedError

    def linebreak(self):
        raise NotImplementedError

    def add_indexed(self, text, canonical=None, prepend_blank=True):
        raise NotImplementedError

    def add_link(self, text, href, prepend_blank=True):
        raise NotImplementedError

    def add_reference(self, name, prepend_blank=True):
        assert isinstance(name, str)
        if self.document.references:
            self.document.references.add(self, name)
        else:
            self.add(name, prepend_blank=prepend_blank)

    def new_footnote(self):
        footnote = Footnote(self, len(self.document.footnotes) + 1)
        with self.bold():
            with self.superscript():
                self.add(str(footnote.number), prepend_blank=False)
        self.document.footnotes.append(footnote)
        return footnote

    # @contextmanager
    def bold(self):
        raise NotImplementedError

    # @contextmanager
    def italic(self):
        raise NotImplementedError

    # @contextmanager
    def underline(self):
        raise NotImplementedError

    # @contextmanager
    def subscript(self):
        raise NotImplementedError

    # @contextmanager
    def superscript(self):
        raise NotImplementedError


class Footnote:

    def __init__(self, document, number):
        self.document = document
        self.number = number
        self.items = []

    def __iadd__(self, text):
        self.add(text)
        return self

    def add(self, text):
        assert isinstance(text, str)
        self.items.append(FootnoteItem("text", text))

    def add_indexed(self, text, canonical=None, prepend_blank=True):
        self.items.append(Footnote("indexed", text, canonical=canonical, prepend_blank=prepend_blank))

    def add_link(self, text, href, prepend_blank=True):
        self.items.append(FootnoteItem("link", text, href=href, prepend_blank=prepend_blank))

    def add_reference(self, name):
        self.items.append(FootnoteItem("reference", name))


@dataclass
class FootnoteItem:

    type: str
    text: str
    canonical: str = None
    href: str = None
    prepend_blank: bool = True
