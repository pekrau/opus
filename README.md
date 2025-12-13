# Opus

Text defined in Python for output to different formats.

```python
"Test of opus, showing usage of current features."


def add(doc):
    p = doc.p("This is text in the first paragraph.")
    p += """This is the second sentence in the document.
    Newlines in this text are handled as ordinary whitespace."""

    p = doc.new_paragraph()
    p += "First sentence in new paragraph."
    with p.bold():
        p += "This is bold text."
    with p.italic():
        p.add(" And italic text. ")
        with p.bold():
            p.add("Bold and italic at the same time.")
        p.add(" ")
        with p.underline():
            p.add("Underlined and italic.")
    p.add(" Normal again. ")

    p.link("http://somewhere.com/", "First link.")
    p.add(" Ordinary text.")

    p = doc.p("First sentence in a new paragraph.")
    with p.italic():
        p.link("http://somewhere.com/", "Second link.")

    q = doc.new_quote("""This is a quote from a sage.
        Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed
        do eiusmod tempor incididunt ut labore et dolore magna
        aliqua. Ut enim ad minim veniam, quis nostrud exercitation
        ullamco laboris nisi ut aliquip ex ea commodo consequat.""")
    q.linebreak()
    q.linebreak()
    q.add("The name of the")
    q.indexed("Mr Sage", canonical="Sage, Mr")
    q.raw(".")

    p = doc.new_paragraph()
    p.add("And a sentence after the quote.")

    with doc.new_section("Title for top-level section"):
        p = doc.new_paragraph()
        p.add("First sentence in the top-level section.")
        p.add("Here is another mention of")
        p.indexed("Sage", canonical="Sage, Mr")
        p.raw(".")
        with doc.new_section("Second-level section"):
            p = doc.new_paragraph()
            p.add("First sentence in the second-level section.")
            with doc.new_section("A third-level section"):
                p = doc.new_paragraph()
                p.add("First sentence in the third-level section.")
            with doc.new_section("Another third-level section"):
                p = doc.new_paragraph()
                p.add("First sentence in the third-level section.")
        with doc.new_section("Another second-level section"):
            p = doc.new_paragraph()
            p.add("First sentence in the second second-level section.")
            with doc.new_section("A third-level section"):
                p = doc.new_paragraph()
                p.add("First sentence in the third-level section.")

    with doc.new_section("Title for a second top-level section"):
        p = doc.new_paragraph()
        p.add(
            """First sentence in the second top-level section.
            This should appear on a new page."""
        )
        p.add("Here is yet another mention of")
        p.indexed("Sage", canonical="Sage, Mr")
        p.raw(".")


if __name__ == "__main__":
    import opus

    kwargs = dict(
        title="Testing opus",
        authors=["Per Kraulis"],
        version=f"Version {opus.__version__}",
        page_break_level=1,
        section_numbers=True,
        paragraph_numbers=True,
        toc_level=2,
        toc_title="Contents",
    )

    document = opus.get_document("docx", **kwargs)
    add(document)
    document.write("test.docx")

    document = opus.get_document("pdf", **kwargs)
    add(document)
    document.write("test.pdf")
```