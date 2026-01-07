import io
from typing import Optional
import fitz  # pymupdf
import docx
import openpyxl

class DocumentProcessor:
    @staticmethod
    def extract_text(file_stream: io.BytesIO, file_type: str) -> str:
        """
        Extracts text from various file formats.
        """
        file_type = file_type.lower()
        
        if 'pdf' in file_type:
            return DocumentProcessor._extract_from_pdf(file_stream)
        elif 'docx' in file_type or 'word' in file_type:
            return DocumentProcessor._extract_from_docx(file_stream)
        elif 'xlsx' in file_type or 'excel' in file_type or 'spreadsheet' in file_type:
            return DocumentProcessor._extract_from_xlsx(file_stream)
        elif 'text' in file_type or 'md' in file_type:
            return file_stream.read().decode('utf-8', errors='ignore')
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    @staticmethod
    def _extract_from_pdf(stream: io.BytesIO) -> str:
        text = ""
        with fitz.open(stream=stream, filetype="pdf") as doc:
            for page in doc:
                text += page.get_text() + "\n"
        return text

    @staticmethod
    def _extract_from_docx(stream: io.BytesIO) -> str:
        doc = docx.Document(stream)
        return "\n".join([para.text for para in doc.paragraphs])

    @staticmethod
    def _extract_from_xlsx(stream: io.BytesIO) -> str:
        wb = openpyxl.load_workbook(stream, data_only=True)
        text = []
        for sheet in wb.sheetnames:
            ws = wb[sheet]
            text.append(f"Sheet: {sheet}")
            for row in ws.rows:
                row_text = " | ".join([str(cell.value) for cell in row if cell.value is not None])
                if row_text:
                    text.append(row_text)
        return "\n".join(text)
