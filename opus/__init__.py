"opus: Text defined in Python for output to PDF, DOCX and EPUB."

from .base_document import VERSION as __version__
from .references import References, DefaultReferenceFormatter


def get_document(format, **kwargs):
    "Get the document object for the given format."
    match format:
        case "docx":
            from .docx_document import Document
        case "pdf":
            from .pdf_document import Document
        case "epub":
            from .epub_document import Document
        case _:
            raise NotImplementedError
    return Document(**kwargs)
