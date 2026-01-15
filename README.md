# opus

Text defined in Python for output to PDF, DOCX and EPUB.

```python
"Test of opus, showing usage of current features."

import opus


def add(doc):
    p = doc.p("This is text in the first paragraph.")
    p += """This is the second sentence in the document.
    Newlines in this text are handled as ordinary whitespace."""

    p = doc.paragraph("First sentence in a paragraph.")
    with p.bold():
        p += "This is bold text."
    with p.italic():
        p.add(" And italic text.")
        with p.bold():
            p.add("Bold and italic at the same time.")
        p.add(" ")
        with p.underline():
            p.raw("Underlined and italic.")
    p.add("Normal again.")
    p.in_italic("More in italic.").in_underline("And underlined.")
    p.link("http://somewhere.com/", "First link.")
    p.add(" Ordinary text.")

    p = doc.p("First sentence in a new paragraph.")
    with p.italic():
        p.link("http://somewhere.com/", "Second link.")
    p.comment("This is a comment.")  # Only DOCX.

    q = doc.quote(
        """This is a quote from a sage.
        Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed
        do eiusmod tempor incididunt ut labore et dolore magna
        aliqua. Ut enim ad minim veniam, quis nostrud exercitation
        ullamco laboris nisi ut aliquip ex ea commodo consequat."""
    )
    q.linebreak().linebreak()
    q.add("The name of the").indexed("Mr Sage", canonical="Sage, Mr").period()
    p = doc.paragraph()
    p.add("A sentence after the quote.")

    with doc.section("Title for top-level section") as section1:
        section1.set_page(docx=3)
        p = section1.paragraph()
        p.add("First sentence in the top-level section.")
        p.add("Here is another mention of")
        p.indexed("Sage", canonical="Sage, Mr").period()
        p.add("And here is a reference to an important book:")
        p.reference("Darwin 1859").period()
        with section1.section("Second-level section") as section2:
            p = section2.paragraph()
            p.add("First sentence in the second-level section.")
            with section2.section("A third-level section") as section3:
                p = section3.paragraph()
                p.add("First sentence in the third-level section.")
            with section2.section("Another third-level section") as section3:
                p = section3.paragraph()
                p.add("First sentence in the other third-level section.")
        with section1.section("Another second-level section") as section2:
            p = section2.paragraph()
            p.add("First sentence in the second second-level section.")
            f = p.footnote("This is a footnote.")
            with section2.section("A third-level section") as section3:
                p = section3.paragraph()
                p.add("First sentence in the third-level section.")
        section1.output_footnotes()

    with doc.section("Title for a second top-level section") as section:
        section.set_page(docx=4)
        p = section.paragraph()
        p.add(
            """First sentence in the second top-level section.
            This should appear on a new page."""
        )
        p.add("Here is yet another mention of")
        p.indexed("Sage", canonical="Sage, Mr").period()

        with section.ordered_list() as l:
            with l.item() as i:
                i.p("First item in an ordered list.")
            with l.item() as i:
                i.p("Second item in an ordered list.")
            with l.item() as i:
                i.p("Third item.")
                with i.unordered_list() as l2:
                    with l2.item() as i2:
                        i2.p("First item in an unordered sublist")
                    with l2.item() as i2:
                        i2.p("Second item in an unordered  sublist")
            with l.item() as i:
                i.p("Fourth item in an ordered list.")

        with section.unordered_list() as l:
            with l.item() as i:
                i.p("First item in an unordered list.")
            with l.item() as i:
                i.p("Second item in an unordered list.")
            with l.item() as i:
                i.p("Third item in an unordered list.")

    doc.output_references(docx=5)
    doc.output_indexed(docx=6)


if __name__ == "__main__":
    kwargs = dict(
        identifier="https://github.com/pekrau/opus",
        title="Testing opus",
        authors=["Per Kraulis"],
        version=f"Version {opus.__version__}",
        section_numbers=True,
        paragraph_numbers=True,
        toc_level=2,
        toc_title="Contents",
        references=opus.References("~/references"),
    )

    for format in ["docx", "pdf", "epub"]:
        document = opus.get_document(format, **kwargs)
        add(document)
        document.write(f"test.{format}")
        print(f"wrote {format}")
```