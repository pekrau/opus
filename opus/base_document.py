"Base document interface."

from contextlib import contextmanager
from dataclasses import dataclass

from .references import DefaultReferenceFormatter
from .constants import EMDASH


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

    def paragraph(self, text=None, thematic_break=False):
        """Create a new paragraph, add the text (if any) to it and return it.
        Optionally add a thematic break before it.
        """
        raise NotImplementedError

    def p(self, text=None, thematic_break=False):
        "Syntactic sugar for 'paragraph'."
        return self.paragraph(text=text, thematic_break=thematic_break)

    def quote(self, text=None):
        "Create a new quotation paragraph, add the text (if any) to it and return it."
        raise NotImplementedError

    def section(self, title, subtitle=None):
        "Create a new section, which is a context that increments the section level."
        raise NotImplementedError

    @property
    def section_level(self):
        return len(self.sections_counts) - 1

    def pagebreak(self):
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

    def ordered_list(self):
        raise NotImplementedError

    def unordered_list(self):
        raise NotImplementedError

    def flush(self):
        "Flush out any pending output."
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
        self.flush()
        assert self.section_level == 0
        if not self.footnotes:
            return
        with self.no_numbers():
            with self.section(title, **pages):
                self.output_footnotes_list()

    def output_footnotes_list(self):
        for footnote in self.footnotes:
            p = self.paragraph()
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
        self.flush()

    def output_references(self, title="References", formatter=None, **pages):
        self.flush()
        if self.references is None:
            raise ValueError("No references instance provided.")
        if not self.references.used:
            return
        if formatter is None:
            formatter = DefaultReferenceFormatter()
        self.set_page(**pages)
        with self.no_numbers():
            with self.section(title):
                for item in self.references:
                    formatter.add_full(self, item)
            self.flush()

    def output_indexed(self, title="Index", **pages):
        self.flush()
        if not self.indexed:
            return
        self.set_page(**pages)
        with self.no_numbers():
            with self.section(title):
                p = self.paragraph()
                items = sorted(self.indexed.items(), key=lambda i: i[0].casefold())
                for canonical, locations in items:
                    p.add(canonical)
                    for location in sorted(locations):
                        self.output_indexed_location(p, location)
                    p.linebreak()
                self.flush()

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
            self.document.pagebreak()

    def __exit__(self, *exc):
        self.document.sections_counts.pop()
        return self

    def __exit__(self, *exc):
        self.document.sections_counts.pop()

    def set_page(self, **pages):
        self.document.set_page(**pages)

    def paragraph(self, text=None, thematic_break=False):
        """Create a new paragraph, add the text (if any) to it and return it.
        Optionally add a thematic break before it.
        """
        return self.document.paragraph(text=text, thematic_break=thematic_break)

    def p(self, text=None, thematic_break=False):
        "Syntactic sugar for 'paragraph'."
        return self.paragraph(text=text, thematic_break=thematic_break)

    def quote(self, text=None):
        "Create a new quotation paragraph, add the text (if any) to it and return it."
        return self.document.quote(text=text)

    def ordered_list(self):
        return self.document.ordered_list()

    def unordered_list(self):
        return self.document.unordered_list()

    def section(self, title, subtitle=None):
        "Create a new subsection, which is a context that increments the section level."
        return self.document.section(title, subtitle=subtitle)

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
        return self.add(text)

    def add(self, text, raw=False):
        """Add the text to the paragraph.
        - Exchange newlines for blanks.
        - Remove superfluous blanks.
        - Prepend a blank, if 'raw' is False.
        - Return the paragraph.
        """
        raise NotImplementedError

    def raw(self, text):
        """Add the text without prepended blank to the paragraph.
        Return the paragraph.
        """
        return self.add(text, raw=True)

    def linebreak(self):
        "Add a line break. Return the paragraph."
        raise NotImplementedError

    def emdash(self, raw=False):
        "Add an emdash character. Return the paragraph."
        raise NotImplementedError

    def period(self):
        "Add a period, with no blank prepended."
        return self.raw(".")

    def indexed(self, text, canonical=None, raw=False):
        "Add an indexed term, optionally with its canonical term. Return the paragraph."
        raise NotImplementedError

    def link(self, href, text=None, raw=False):
        "Add a hyperlink, optionally with a text to display. Return the paragraph."
        raise NotImplementedError

    def reference(self, name, raw=False):
        "Add a reference. Return the paragraph."
        assert isinstance(name, str)
        if self.document.references:
            self.document.references.add(self, name, raw=raw)
        else:
            self.add(name, raw=raw)
        return self

    def footnote(self, text=None):
        "Add a footnot and return it."
        footnote = Footnote(self, len(self.document.footnotes) + 1)
        with self.bold():
            with self.superscript():
                self.raw(str(footnote.number))
        self.document.footnotes.append(footnote)
        if text:
            footnote.add(text)
        return footnote

    def comment(self, text):
        raise NotImplementedError

    def set_page(self, **pages):
        self.document.set_page(**pages)

    # @contextmanager
    def bold(self):
        raise NotImplementedError

    def in_bold(self, text):
        "Add the text in bold. Return the paragraph."
        self.add(" ")
        with self.bold():
            self.add(text)
        return self

    # @contextmanager
    def italic(self):
        raise NotImplementedError

    def in_italic(self, text):
        "Add the text in italic. Return the paragraph."
        self.add(" ")
        with self.italic():
            self.raw(text)
        return self

    # @contextmanager
    def underline(self):
        raise NotImplementedError

    def in_underline(self, text):
        "Add the text in underlined. Return the paragraph."
        self.add(" ")
        with self.underline():
            self.raw(text)
        return self

    # @contextmanager
    def subscript(self):
        raise NotImplementedError

    def in_subscript(self, text):
        "Add the text in subscript. Return the paragraph."
        self.add(" ")
        with self.subscript():
            self.raw(text)
        return self

    # @contextmanager
    def superscript(self):
        raise NotImplementedError

    def in_superscript(self, text):
        "Add the text in superscript. Return the paragraph."
        self.add(" ")
        with self.superscript():
            self.raw(text)
        return self


class Footnote:

    def __init__(self, document, number):
        self.document = document
        self.number = number
        self.items = []

    def __iadd__(self, text):
        return self.add(text)

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

    def period(self):
        return self.raw(".")

    def in_subscript(self, text):
        self.items.append(FootnoteItem("subscript", text))
        return self

    def in_superscript(self, text):
        self.items.append(FootnoteItem("superscript", text))
        return self


@dataclass
class FootnoteItem:

    type: str
    text: str
    canonical: str = None
    href: str = None


class BaseList:
    "Base list class; a context manager."

    def __init__(self, document, ordered=False):
        self.document = document
        self.ordered = ordered

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        pass

    def item(self):
        "Return a new item in the list, which is a context manager."
        raise NotImplementedError

    def add_items(self, *texts):
        for text in texts:
            with self.item() as i:
                i.p(text)


class BaseListItem:
    "Base list item class; a context manager."

    def __init__(self, list):
        self.list = list

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        pass

    def paragraph(self, text=None):
        raise NotImplementedError

    def p(self, text=None):
        "Syntactic sugar for 'paragraph'."
        return self.paragraph(text=text)

    def quote(self, text=None):
        raise NotImplementedError

    def ordered_list(self):
        raise NotImplementedError

    def unordered_list(self):
        raise NotImplementedError
