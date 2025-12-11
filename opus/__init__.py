"Opus: Text defined in Python for output to different formats."

from .base_document import VERSION as __version__
from .references import References
from .docx_document import Document as DocxDocument
from .pdf_document import Document as PdfDocument


def get_document(format, **kwargs):
    "Get the document object for the given format."
    match format:
        case "docx":
            return DocxDocument(**kwargs)
        case "pdf":
            return PdfDocument(**kwargs)
        case _:
            raise NotImplementedError
