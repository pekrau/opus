"Base document interface."

VERSION = "0.5.8"

from contextlib import contextmanager
from dataclasses import dataclass

import icecream
icecream.install()

class BaseDocument:

    def __init__(
        self,
        title=None,
        subtitle=None,
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
        footnotes_level=0,
        footnotes_title="Fotnoter",
    ):
        self.title = title
        self.subtitle = subtitle
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
        self.footnotes_level = footnotes_level
        self.footnotes_title = footnotes_title

        self.paragraphs_count = 0
        self.sections_counts = [0]
        self.footnotes = []

    def new_paragraph(self, text=None, thematic_break=False):
        """Create a new paragraph, add the text (if any) to it and return it.
        Optionally add a thematic break before it.
        """
        raise NotImplementedError

    def p(self, text=None, thematic_break=False):
        """Create a new paragraph, add the text (if any) to it and return it.
        Optionally add a thematic break before it.
        Syntactic sugar for 'new_paragraph'.
        """
        return self.new_paragraph(text=text, thematic_break=thematic_break)

    def new_quote(self, text=None):
        "Create a new quotation paragraph, add the text (if any) to it and return it."
        raise NotImplementedError

    def new_section(self, title, subtitle=None):
        "Add a new section, which is a context that increments the section level."
        raise NotImplementedError

    @property
    def section_level(self):
        return len(self.sections_counts) - 1

    def new_page(self):
        raise NotImplementedError

    def set_page_number(self, number):
        raise NotImplementedError

    def flush(self):
        pass

    @contextmanager
    def no_numbers(self):
        self.old_paragraph_numbers = self.paragraph_numbers
        self.paragraph_numbers = False
        self.old_section_numbers = self.section_numbers
        self.section_numbers = False
        try:
            yield self
        finally:
            self.paragraph_numbers = self.old_paragraph_numbers
            self.section_numbers = self.old_section_numbers

    def output_final(self):
        "Output footnotes, references and index."
        self.output_footnotes()
        if self.references:
            self.references.output(self)
        self.output_indexed()

    def output_footnotes(self):
        "Output the footnotes to the document."
        if not self.footnotes:
            return
        level = self.section_level
        if level != self.footnotes_level:
            return
        self.flush()
        with self.no_numbers():
            if level == 0:
                with self.new_section(self.footnotes_title):
                    self.output_footnotes_list()
            else:
                p = self.new_paragraph()
                with p.italic():
                    with p.bold():
                        p += self.footnotes_title
                self.output_footnotes_list()
            self.flush()

    def output_footnotes_list(self):
        "Output the list of footnotes to the document."
        for footnote in self.footnotes:
            p = self.new_paragraph()
            with p.bold():
               p += f"{footnote.number}."
            for item in footnote.items:
                match item.type:
                    case "add":
                        p.add(item.text)
                    case "raw":
                        p.raw(item.text)
                    case "indexed":
                        p.indexed(item.text, canonical=item.canonical)
                    case "link":
                        p.link(item.href, item.text)
                    case "reference":
                        p.reference(item.text)
        self.footnotes = []

    def output_indexed(self):
        raise NotImplementedError


class BaseSection:

    def __init__(self, document, title, subtitle=None):
        self.document = document
        self.title = title
        self.subtitle = subtitle
        self.document.sections_counts[-1] += 1

    def new_paragraph(self, text=None, thematic_break=False):
        """Create a new paragraph, add the text (if any) to it and return it.
        Optionally add a thematic break before it.
        """
        return self.document.new_paragraph(text=text, thematic_break=thematic_break)

    def p(self, text=None, thematic_break=False):
        """Create a new paragraph, add the text (if any) to it and return it.
        Optionally add a thematic break before it.
        Syntactic sugar for 'new_paragraph'.
        """
        return self.p(text=text, thematic_break=thematic_break)

    def new_quote(self, text=None):
        "Create a new quotation paragraph, add the text (if any) to it and return it."
        return self.document.new_quote(text=text)

    def number(self):
        return ".".join([str(n) for n in self.document.sections_counts[:-1]]) + "."

    def __enter__(self):
        raise NotImplementedError

    def __exit__(self, *exc):
        self.document.sections_counts.pop()

    def at_enter(self):
        self.document.sections_counts.append(0)
        level = self.document.section_level
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

    def add(self, text, raw=False):
        """Add the text to the paragraph.
        - Exchanges newlines for blanks.
        - Removes superfluous blanks.
        - Prepends a blank, if 'raw' is False.
        """
        raise NotImplementedError

    def raw(self, text):
        "Add the text without prepended blank to the paragraph."
        self.add(text, raw=True)

    def linebreak(self):
        raise NotImplementedError

    def emdash(self, raw=False):
        raise NotImplementedError

    def indexed(self, text, canonical=None, raw=False):
        raise NotImplementedError

    def link(self, href, text=None, raw=False):
        raise NotImplementedError

    def reference(self, name, raw=False):
        assert isinstance(name, str)
        if self.document.references:
            self.document.references.add(self, name, raw=raw)
        else:
            self.add(name, raw=raw)

    def new_footnote(self):
        footnote = Footnote(self, len(self.document.footnotes) + 1)
        with self.bold():
            with self.superscript():
                self.raw(str(footnote.number))
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
        self.items.append(FootnoteItem("add", text))

    def raw(self, text):
        assert isinstance(text, str)
        self.items.append(FootnoteItem("raw", text))

    def indexed(self, text, canonical=None):
        self.items.append(Footnote("indexed", text, canonical=canonical))

    def link(self, href, text=None):
        self.items.append(FootnoteItem("link", text=text or href, href=href))

    def reference(self, name):
        self.items.append(FootnoteItem("reference", name))


@dataclass
class FootnoteItem:

    type: str
    text: str
    canonical: str = None
    href: str = None
