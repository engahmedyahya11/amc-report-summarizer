
import pdfplumber
import re

class PDFProcessor:

    def extract_text(self, pdf_path: str) -> str:
        full_text = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        for row in table:
                            if row:
                                clean_row = [str(cell).strip() if cell else "" for cell in row]
                                full_text.append(" | ".join(clean_row))
                text = page.extract_text()
                if text:
                    full_text.append(text)
        combined = "\n".join(full_text)
        return self._clean_text(combined)

    def _clean_text(self, text: str) -> str:
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'[ \t]{2,}', ' ', text)
        text = re.sub(r'[^\S\n]+', ' ', text)
        return text.strip()

    def get_metadata(self, pdf_path: str) -> dict:
        with pdfplumber.open(pdf_path) as pdf:
            page_count = len(pdf.pages)
            all_text   = " ".join(p.extract_text() or "" for p in pdf.pages)
            word_count = len(all_text.split())
        return {"pages": page_count, "words": word_count}

    def chunk_text(self, text: str, max_chars: int = 4000) -> list:
        if len(text) <= max_chars:
            return [text]
        chunks, current = [], ""
        for paragraph in text.split("\n\n"):
            if len(current) + len(paragraph) < max_chars:
                current += paragraph + "\n\n"
            else:
                if current:
                    chunks.append(current.strip())
                current = paragraph + "\n\n"
        if current:
            chunks.append(current.strip())
        return chunks
