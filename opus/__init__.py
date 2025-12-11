"Opus: Text defined in Python for output to different formats."

from .base_document import VERSION as __version__
from .references import References


def get_document(format, **kwargs):
    "Get the document object for the given format."
    match format:
        case "docx":
            from .docx_document import Document
        case "pdf":
            from .pdf_document import Document
        case _:
            raise NotImplementedError
    return Document(**kwargs)
