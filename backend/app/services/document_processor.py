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
        
        text = ""
        if 'pdf' in file_type:
            text = DocumentProcessor._extract_from_pdf(file_stream)
        elif 'docx' in file_type or 'word' in file_type:
            text = DocumentProcessor._extract_from_docx(file_stream)
        elif 'xlsx' in file_type or 'excel' in file_type or 'spreadsheet' in file_type:
            text = DocumentProcessor._extract_from_xlsx(file_stream)
        elif 'text' in file_type or 'md' in file_type or 'txt' in file_type:
            text = file_stream.read().decode('utf-8', errors='ignore')
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
            
        # Sanitize: Remove null bytes which cause PostgreSQL errors
        if text:
            text = text.replace('\x00', '')
            
        return text

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
            
            rows = list(ws.rows)
            if not rows:
                continue
                
            # Determine max columns to handle inconsistent rows
            max_cols = 0
            for row in rows:
                max_cols = max(max_cols, len(row))
            
            # Helper to format row
            def format_row(row_cells):
                cells = [str(cell.value).strip().replace('\n', ' ') if cell.value is not None else "" for cell in row_cells]
                # Pad to max cols if needed (though usually not strict for markdown, it helps alignment)
                return "| " + " | ".join(cells) + " |"

            # Header
            header_row = rows[0]
            text.append(format_row(header_row))
            
            # Separator
            separator = "| " + " | ".join(["---"] * len(header_row)) + " |"
            text.append(separator)
            
            # Data
            for row in rows[1:]:
                # skip empty rows
                if all(cell.value is None for cell in row):
                    continue
                text.append(format_row(row))
                
            text.append("\n") # Spacing between sheets
            
        return "\n".join(text)
