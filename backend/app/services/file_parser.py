from app.models.schemas import FileFormat
import json
import csv
import io
from typing import Tuple, Optional


class FileParser:
    @staticmethod
    def parse(content: bytes, file_format: FileFormat, filename: str) -> Tuple[str, Optional[dict]]:
        if file_format == FileFormat.TEXT:
            return FileParser._parse_text(content)
        elif file_format == FileFormat.CSV:
            return FileParser._parse_csv(content)
        elif file_format == FileFormat.JSON:
            return FileParser._parse_json(content)
        elif file_format == FileFormat.PDF:
            return FileParser._parse_pdf(content)
        else:
            raise ValueError(f"Unsupported file format: {file_format}")

    @staticmethod
    def _parse_text(content: bytes) -> Tuple[str, None]:
        try:
            text = content.decode('utf-8')
        except UnicodeDecodeError:
            text = content.decode('latin-1')
        return text, None

    @staticmethod
    def _parse_csv(content: bytes) -> Tuple[str, Optional[dict]]:
        try:
            text = content.decode('utf-8')
        except UnicodeDecodeError:
            text = content.decode('latin-1')

        reader = csv.reader(io.StringIO(text))
        rows = list(reader)

        if not rows:
            return "", None

        headers = rows[0] if rows else []
        data_rows = rows[1:] if len(rows) > 1 else []

        extracted_content = []
        for row in data_rows:
            row_text = ' '.join(str(cell) for cell in row if cell)
            if row_text:
                extracted_content.append(row_text)

        metadata = {
            "columns": headers,
            "row_count": len(data_rows)
        }

        return '\n'.join(extracted_content), metadata

    @staticmethod
    def _parse_json(content: bytes) -> Tuple[str, Optional[dict]]:
        try:
            text = content.decode('utf-8')
        except UnicodeDecodeError:
            text = content.decode('latin-1')

        data = json.loads(text)

        extracted_content = FileParser._extract_from_json(data)
        metadata = {"keys": list(data.keys()) if isinstance(data, dict) else None}

        return extracted_content, metadata

    @staticmethod
    def _extract_from_json(data) -> str:
        if isinstance(data, str):
            return data
        elif isinstance(data, (int, float, bool)):
            return str(data)
        elif isinstance(data, list):
            return ' '.join(FileParser._extract_from_json(item) for item in data)
        elif isinstance(data, dict):
            values = []
            for value in data.values():
                extracted = FileParser._extract_from_json(value)
                if extracted:
                    values.append(extracted)
            return ' '.join(values)
        return ""

    @staticmethod
    def _parse_pdf(content: bytes) -> Tuple[str, Optional[dict]]:
        try:
            import pdfplumber
        except ImportError:
            raise ImportError("pdfplumber is required for PDF parsing. Install with: pip install pdfplumber")

        text_parts = []
        metadata = {}

        with pdfplumber.open(io.BytesIO(content)) as pdf:
            metadata["page_count"] = len(pdf.pages)
            if pdf.metadata:
                metadata.update({
                    "title": pdf.metadata.get("Title", ""),
                    "author": pdf.metadata.get("Author", ""),
                })

            for page_num, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

        return '\n'.join(text_parts), metadata

    @staticmethod
    def detect_format(filename: str, content: Optional[bytes] = None) -> FileFormat:
        extension = filename.lower().split('.')[-1]

        format_mapping = {
            'txt': FileFormat.TEXT,
            'csv': FileFormat.CSV,
            'json': FileFormat.JSON,
            'pdf': FileFormat.PDF,
        }

        if extension in format_mapping:
            return format_mapping[extension]

        if content and extension not in format_mapping:
            if content.startswith(b'%PDF'):
                return FileFormat.PDF
            try:
                json.loads(content.decode('utf-8'))
                return FileFormat.JSON
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass

            if b',' in content and b'\n' in content:
                return FileFormat.CSV

        return FileFormat.TEXT
