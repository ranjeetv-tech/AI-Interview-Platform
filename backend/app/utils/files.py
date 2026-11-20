from pathlib import Path
from uuid import uuid4
from pypdf import PdfReader
from docx import Document

ALLOWED = {".pdf", ".docx"}

def safe_filename(name: str) -> str:
    suffix = Path(name).suffix.lower()
    return f"{uuid4().hex}{suffix}"

def extract_text(path: str) -> str:
    suffix = Path(path).suffix.lower()
    if suffix == ".pdf":
        reader = PdfReader(path)
        return "\n".join((p.extract_text() or "") for p in reader.pages).strip()
    if suffix == ".docx":
        doc = Document(path)
        return "\n".join(p.text for p in doc.paragraphs).strip()
    raise ValueError("Unsupported file type")
