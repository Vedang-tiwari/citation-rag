"""Document parsers for extracting page-by-page text from PDF, TXT, and DOCX files."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional
import pymupdf as fitz
import docx

from app.core.exceptions import DocumentParsingError, UnsupportedFileTypeError
from app.core.logging import get_logger
from app.models.schemas import PageContent

logger = get_logger(__name__)


class BaseParser(ABC):
    """Abstract base parser interface."""

    @abstractmethod
    def parse(self, file_path: Path, document_name: str) -> List[PageContent]:
        """
        Parse file into page-by-page text content.
        Preserves 1-indexed page numbers and records errors without silently discarding pages.
        """
        pass


class PDFParser(BaseParser):
    """PDF text extractor using PyMuPDF (fitz)."""

    def parse(self, file_path: Path, document_name: str) -> List[PageContent]:
        pages: List[PageContent] = []
        doc = None
        try:
            doc = fitz.open(str(file_path))
            total_pages = doc.page_count

            if total_pages == 0:
                logger.warning(f"PDF '{document_name}' contains 0 pages.")
                return [PageContent(page_number=1, text="", has_error=False)]

            for page_index in range(total_pages):
                page_num = page_index + 1
                try:
                    page = doc.load_page(page_index)
                    text = page.get_text("text") or ""
                    # Keep track of empty pages without crashing
                    pages.append(
                        PageContent(
                            page_number=page_num,
                            text=text.strip(),
                            has_error=False,
                            error_message=None,
                        )
                    )
                except Exception as page_exc:
                    logger.error(
                        f"Error extracting page {page_num} of '{document_name}': {page_exc}"
                    )
                    pages.append(
                        PageContent(
                            page_number=page_num,
                            text="",
                            has_error=True,
                            error_message=f"Page extraction failure: {str(page_exc)}",
                        )
                    )

            return pages

        except Exception as exc:
            logger.error(f"Failed to parse PDF document '{document_name}': {exc}")
            raise DocumentParsingError(filename=document_name, reason=str(exc))
        finally:
            if doc is not None:
                doc.close()


class TXTParser(BaseParser):
    """Plain text parser supporting UTF-8 and fallback encodings, with form-feed page splitting."""

    def parse(self, file_path: Path, document_name: str) -> List[PageContent]:
        raw_bytes = file_path.read_bytes()
        text: Optional[str] = None

        # Attempt decoding with UTF-8 first, fallback to common text encodings
        for encoding in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
            try:
                text = raw_bytes.decode(encoding)
                break
            except UnicodeDecodeError:
                continue

        if text is None:
            raise DocumentParsingError(
                filename=document_name,
                reason="Unable to decode text file with supported encodings (utf-8, latin-1, cp1252).",
            )

        # Check for form-feed characters (\x0c or \f) indicating page breaks
        raw_pages = text.split("\x0c")
        pages: List[PageContent] = []

        for idx, page_text in enumerate(raw_pages, start=1):
            pages.append(
                PageContent(
                    page_number=idx,
                    text=page_text.strip(),
                    has_error=False,
                    error_message=None,
                )
            )

        return pages if pages else [PageContent(page_number=1, text="", has_error=False)]


class DOCXParser(BaseParser):
    """DOCX text extractor using python-docx, preserving page breaks and paragraphs."""

    def parse(self, file_path: Path, document_name: str) -> List[PageContent]:
        try:
            doc = docx.Document(str(file_path))
            pages: List[PageContent] = []
            current_page_text: List[str] = []
            current_page_num = 1

            for paragraph in doc.paragraphs:
                # Check for explicit page breaks in paragraph runs or XML elements
                has_page_break = False
                for run in paragraph.runs:
                    # Check for page break element in run XML: <w:br w:type="page"/>
                    if "w:type=\"page\"" in run._element.xml:
                        has_page_break = True
                        break

                p_text = paragraph.text.strip()
                if p_text:
                    current_page_text.append(p_text)

                if has_page_break:
                    pages.append(
                        PageContent(
                            page_number=current_page_num,
                            text="\n\n".join(current_page_text).strip(),
                            has_error=False,
                        )
                    )
                    current_page_num += 1
                    current_page_text = []

            # Also extract tables
            for table in doc.tables:
                table_lines = []
                for row in table.rows:
                    row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                    if row_text:
                        table_lines.append(row_text)
                if table_lines:
                    current_page_text.append("\n".join(table_lines))

            # Append final or sole page
            pages.append(
                PageContent(
                    page_number=current_page_num,
                    text="\n\n".join(current_page_text).strip(),
                    has_error=False,
                )
            )

            return pages

        except Exception as exc:
            logger.error(f"Failed to parse DOCX document '{document_name}': {exc}")
            raise DocumentParsingError(filename=document_name, reason=str(exc))


class DocumentParser:
    """Dispatches document to the appropriate parser based on file extension."""

    def __init__(self) -> None:
        self._parsers = {
            ".pdf": PDFParser(),
            ".txt": TXTParser(),
            ".docx": DOCXParser(),
        }

    def parse_document(self, file_path: Path, filename: str) -> List[PageContent]:
        ext = file_path.suffix.lower()
        parser = self._parsers.get(ext)
        if not parser:
            raise UnsupportedFileTypeError(filename=filename, extension=ext)

        logger.info(f"Parsing '{filename}' using {parser.__class__.__name__}")
        return parser.parse(file_path=file_path, document_name=filename)
