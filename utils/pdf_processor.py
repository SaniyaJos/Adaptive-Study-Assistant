import fitz  # PyMuPDF
import re
from typing import Dict, List, Any

def extract_text_from_pdf(pdf_file) -> Dict[str, Any]:
    """
    Extracts raw text from an uploaded PDF file (bytes stream) or a file path.
    """
    pages_text = []
    
    if hasattr(pdf_file, "read"):
        pdf_bytes = pdf_file.read()
        if hasattr(pdf_file, "seek"):
            pdf_file.seek(0)
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    else:
        doc = fitz.open(pdf_file)
        
    page_count = len(doc)
    
    for page in doc:
        text = page.get_text()
        text = re.sub(r'[ \t]+', ' ', text)
        pages_text.append(text)
        
    full_text = "\n".join(pages_text)
    
    return {
        "full_text": full_text,
        "pages": pages_text,
        "page_count": page_count,
        "char_count": len(full_text)
    }

def chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """
    Splits text into overlapping chunks, attempting to respect logical boundaries (sentence ends or newlines).
    """
    if not text:
        return []
        
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = min(start + chunk_size, text_len)
        
        if end < text_len:
            boundary_found = False
            # Look backward up to 150 characters to align chunk ends with sentences or paragraphs
            for i in range(end, max(start, end - 150), -1):
                if text[i] in ['.', '\n']:
                    end = i + 1
                    boundary_found = True
                    break
            
            if not boundary_found:
                for i in range(end, max(start, end - 150), -1):
                    if text[i] == ' ':
                        end = i
                        break
                        
        chunks.append(text[start:end].strip())
        
        start = end - chunk_overlap
        if start >= text_len - chunk_overlap:
            break
            
    return [c for c in chunks if c]

