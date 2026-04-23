import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def parse_document(file_path: Path) -> str:
    """Return clean text from PDF, DOCX, or PPTX. Tries docling first, falls back to unstructured."""
    try:
        from docling.document_converter import DocumentConverter
        converter = DocumentConverter()
        result = converter.convert(str(file_path))
        text = result.document.export_to_markdown()
        logger.info("doc_parser: docling succeeded for %s", file_path.name)
        return text
    except Exception as e:
        logger.warning("doc_parser: docling failed (%s), falling back to unstructured", e)

    try:
        from unstructured.partition.auto import partition
        elements = partition(filename=str(file_path))
        text = "\n\n".join(str(el) for el in elements if str(el).strip())
        logger.info("doc_parser: unstructured succeeded for %s", file_path.name)
        return text
    except Exception as e:
        raise RuntimeError(f"Both docling and unstructured failed for {file_path.name}: {e}") from e
