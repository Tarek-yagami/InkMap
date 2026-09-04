"""Converts uploaded documents (PDF, DOCX, PPTX, HTML, ...) into plain markdown text.

Uses Docling for layout-aware parsing so multi-column reading order and tables survive
extraction, unlike naive PDF text extraction. OCR is disabled: research papers are
digital-native, not scans, and OCR models add real startup cost for no benefit here.
"""

from io import BytesIO

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.io import DocumentStream

_converter = DocumentConverter(
    format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=PdfPipelineOptions(do_ocr=False))}
)


def extract_text(data: bytes, filename: str) -> str:
    stream = DocumentStream(name=filename, stream=BytesIO(data))
    result = _converter.convert(stream)
    return result.document.export_to_markdown()
