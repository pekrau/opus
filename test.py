"Test of opus."


def add(doc):
    p = doc.new_paragraph()
    p.add("This is text in the first paragraph.")

    p.add(
        """This is the first sentence in the document.
    Newlines in this text are handled as ordinary whitespace. """
    )

    p = doc.new_paragraph()
    p.add("First sentence in new paragraph.")
    with p.bold():
        p.add("This is bold text.")
    with p.italic():
        p.add(" And italic text. ")
        with p.bold():
            p.add("Bold and italic at the same time.")
        p.add(" ")
        with p.underline():
            p.add("Underlined and italic.")
    p.add(" Normal again. ")

    p.add_link("First link.", href="http://somewhere.com/")
    p.add(" Ordinary text.")

    p = doc.new_paragraph()
    p.add("First sentence in a new paragraph.")
    with p.italic():
        p.add_link("Second link.", href="http://somewhere.com/")

    q = doc.new_quote()
    q.add("This is a quote from a sage. More text. More text. More text. More text. More text. More text. More text. More text. More text. More text. More text.")
    q.linebreak()
    q.linebreak()
    q.add("The name of the")
    q.add_indexed("Mr Sage", canonical="Sage, Mr", append_blank=False)
    q.add(".")

    p = doc.new_paragraph()
    p.add("And a sentence after the quote.")

    with doc.new_section("Title for top-level section"):
        p = doc.new_paragraph()
        p.add("First sentence in the top-level section.")
        p.add("Here is another mention of")
        p.add_indexed("Sage",  canonical="Sage, Mr", append_blank=False)
        p.add(".")
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
        p.add_indexed("Sage",  canonical="Sage, Mr", append_blank=False)
        p.add(".")


if __name__ == "__main__":
    import opus

    kwargs = dict(
        title="Testing opus",
        authors=["Per Kraulis"],
        version="version 1",
    )

    document = opus.get_document("docx", **kwargs)
    add(document)
    document.write("test.docx")

    document = opus.get_document("pdf", **kwargs)
    add(document)
    document.write("test.pdf")
