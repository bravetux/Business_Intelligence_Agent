# Business Intelligence Agent
# Copyright (C) 2026  B. Vignesh Kumar (Bravetux) <ic19939@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

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
