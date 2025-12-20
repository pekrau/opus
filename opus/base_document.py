"Base document interface."

import icecream

icecream.install()

VERSION = "0.7.6"

from contextlib import contextmanager
from dataclasses import dataclass

from .references import DefaultReferenceFormatter

EMDASH = "\u2014"


class BaseDocument:

    def __init__(
        self,
        identifier=None,
        title=None,
        subtitle=None,
        authors=None,
        version=None,
        language="sv-SE",
        title_page_title="Title page",
        section_numbers=False,
        paragraph_numbers=False,
        toc_level=0,
        toc_title="Contents",
        references=None,
    ):
        self.identifier = identifier
        self.title = title
        self.subtitle = subtitle
        self.authors = authors
        self.version = version
        self.language = language
        self.title_page_title = title_page_title
        self.section_numbers = section_numbers
        self.paragraph_numbers = paragraph_numbers
        self.toc_level = toc_level
        self.toc_title = toc_title
        self.references = references

        self.paragraphs_count = 0
        self.sections_counts = [0]
        self.footnotes = []
        self.page = dict(pdf=1, docx=1, epub=1)

    def new_paragraph(self, text=None, thematic_break=False):
        """Create a new paragraph, add the text (if any) to it and return it.
        Optionally add a thematic break before it.
        """
        raise NotImplementedError

    def p(self, text=None, thematic_break=False):
        "Syntactic sugar for 'new_paragraph'."
        return self.new_paragraph(text=text, thematic_break=thematic_break)

    def new_quote(self, text=None):
        "Create a new quotation paragraph, add the text (if any) to it and return it."
        raise NotImplementedError

    def new_section(self, title, subtitle=None):
        "Create a new section, which is a context that increments the section level."
        raise NotImplementedError

    @property
    def section_level(self):
        return len(self.sections_counts) - 1

    def new_page(self):
        "New page, for formats that support this notion."
        raise NotImplementedError

    def set_page(self, **pages):
        for format, number in pages.items():
            if format not in self.page:
                raise ValueError(f"no such format '{format}' for set_page.")
            if number is not None:
                self.page[format] = number

    def increment_page(self, format):
        try:
            self.page[format] += 1
        except KeyError:
            pass

    def new_list(self, ordered=False):
        raise NotImplementedError

    def paragraph_flush(self):
        "Flush out the current paragraph."
        pass

    @property
    def location(self):
        return self.paragraphs_count

    def add_indexed(self, canonical):
        self.indexed.setdefault(canonical or text, set()).add(self.location)

    @contextmanager
    def no_numbers(self):
        "Within this context, do not output section or paragraph numbers."
        self.old_paragraph_numbers = self.paragraph_numbers
        self.paragraph_numbers = False
        self.old_section_numbers = self.section_numbers
        self.section_numbers = False
        try:
            yield self
        finally:
            self.paragraph_numbers = self.old_paragraph_numbers
            self.section_numbers = self.old_section_numbers

    def output_footnotes(self, title="Footnotes", **pages):
        "Output the footnotes to the document."
        self.paragraph_flush()
        assert self.section_level == 0
        if not self.footnotes:
            return
        with self.no_numbers():
            with self.new_section(title, **pages):
                self.output_footnotes_list()

    def output_footnotes_list(self):
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
                    case "superscript":
                        with p.superscript():
                            p.add(item.text)
                    case "subscript":
                        with p.subscript():
                            p.add(item.text)
                    case _:
                        raise NotImplementedError
        self.footnotes = []
        self.paragraph_flush()

    def output_references(self, title="References", formatter=None, **pages):
        self.paragraph_flush()
        if self.references is None:
            raise ValueError("No references instance provided.")
        if not self.references.used:
            return
        if formatter is None:
            formatter = DefaultReferenceFormatter()
        self.set_page(**pages)
        with self.no_numbers():
            with self.new_section(title):
                for item in self.references:
                    formatter.add_full(self, item)
            self.paragraph_flush()

    def output_indexed(self, title="Index", **pages):
        self.paragraph_flush()
        if not self.indexed:
            return
        self.set_page(**pages)
        with self.no_numbers():
            with self.new_section(title):
                p = self.new_paragraph()
                items = sorted(self.indexed.items(), key=lambda i: i[0].casefold())
                for canonical, locations in items:
                    p.add(canonical)
                    for location in sorted(locations):
                        self.output_indexed_location(p, location)
                    p.linebreak()
                self.paragraph_flush()

    def output_indexed_location(self, paragraph, location):
        paragraph.raw(f", {location}")


class BaseSection:

    def __init__(self, document, title, subtitle=None):
        self.document = document
        self._title = title
        self.subtitle = subtitle
        self.document.sections_counts[-1] += 1

    def __enter__(self):
        self.document.sections_counts.append(0)
        if self.level <= 1:
            self.document.new_page()

    def __exit__(self, *exc):
        self.document.sections_counts.pop()
        return self

    def __exit__(self, *exc):
        self.document.sections_counts.pop()

    def set_page(self, **pages):
        self.document.set_page(**pages)

    def new_paragraph(self, text=None, thematic_break=False):
        """Create a new paragraph, add the text (if any) to it and return it.
        Optionally add a thematic break before it.
        """
        return self.document.new_paragraph(text=text, thematic_break=thematic_break)

    def p(self, text=None, thematic_break=False):
        "Syntactic sugar for 'new_paragraph'."
        return self.new_paragraph(text=text, thematic_break=thematic_break)

    def new_quote(self, text=None):
        "Create a new quotation paragraph, add the text (if any) to it and return it."
        return self.document.new_quote(text=text)

    def new_list(self, ordered=False):
        return self.document.new_list(ordered=ordered)

    def new_section(self, title, subtitle=None):
        "Create a new subsection, which is a context that increments the section level."
        return self.document.new_section(title, subtitle=subtitle)

    @property
    def level(self):
        return self.document.section_level

    def number(self, delimiter="."):
        return (
            delimiter.join([str(n) for n in self.document.sections_counts[:-1]])
            + delimiter
        )

    @property
    def title(self):
        if self.document.section_numbers:
            return f"{self.number()} {self._title}"
        else:
            return self._title

    def output_footnotes(self, title="Footnotes"):
        "Output the footnotes to the section."
        raise NotImplementedError


class BaseParagraph:

    def __init__(self, document):
        self.document = document
        self.document.paragraphs_count += 1

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

    def set_page(self, **pages):
        self.document.set_page(**pages)

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
        return self

    def raw(self, text):
        assert isinstance(text, str)
        self.items.append(FootnoteItem("raw", text))
        return self

    def indexed(self, text, canonical=None):
        self.items.append(Footnote("indexed", text, canonical=canonical))
        return self

    def link(self, href, text=None):
        self.items.append(FootnoteItem("link", text=text or href, href=href))
        return self

    def reference(self, name):
        self.items.append(FootnoteItem("reference", name))
        return self

    def emdash(self):
        self.items.append(FootnoteItem("add", EMDASH))
        return self

    def superscript(self, text):
        self.items.append(FootnoteItem("superscript", text))
        return self

    def subscript(self, text):
        self.items.append(FootnoteItem("subscript", text))
        return self



@dataclass
class FootnoteItem:

    type: str
    text: str
    canonical: str = None
    href: str = None


class BaseList:

    def __init__(self, document, ordered=False):
        self.document = document
        self.ordered = ordered

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        pass

    def new_item(self):
        raise NotImplementedError

    def add_items(self, *texts):
        for text in texts:
            with self.new_item() as i:
                i.p(text)


class BaseListItem:

    def __init__(self, list):
        self.list = list

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        pass

    def new_paragraph(self, text=None):
        raise NotImplementedError

    def p(self, text=None):
        return self.new_paragraph(text=text)

    def new_quote(self, text=None):
        raise NotImplementedError

    def new_list(self, ordered=False):
        raise NotImplementedError
