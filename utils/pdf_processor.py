import fitz  # PyMuPDF
import re
from typing import Dict, List, Any

def extract_text_from_pdf(pdf_file) -> Dict[str, Any]:
    """
    Extracts raw text from an uploaded PDF file (bytes stream) or a file path.
    
    Args:
        pdf_file: File-like object (BytesIO) from streamlit uploader or string file path.
        
    Returns:
        Dict: A structured dictionary containing full text, raw pages, page count, and character count.
    """
    pages_text = []
    
    # Check if the input is a stream (Streamlit uploader) or a file path
    if hasattr(pdf_file, "read"):
        pdf_bytes = pdf_file.read()
        # Reset the stream cursor if seekable
        if hasattr(pdf_file, "seek"):
            pdf_file.seek(0)
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    else:
        doc = fitz.open(pdf_file)
        
    page_count = len(doc)
    
    for page in doc:
        text = page.get_text()
        # Clean extra white spaces while preserving line breaks
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
    
    Args:
        text: The source document text.
        chunk_size: Target character length of each chunk.
        chunk_overlap: Overlap length between consecutive chunks.
        
    Returns:
        List[str]: List of text chunks.
    """
    if not text:
        return []
        
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        # Determine initial slice boundary
        end = min(start + chunk_size, text_len)
        
        # If we are not at the end of the text, look for a logical break point
        if end < text_len:
            boundary_found = False
            # Check backwards up to 150 characters for sentence ends or newlines
            for i in range(end, max(start, end - 150), -1):
                if text[i] in ['.', '\n']:
                    end = i + 1  # Include the punctuation or newline character
                    boundary_found = True
                    break
            
            # Fallback to word boundaries (spaces) if no sentence or paragraph boundary was found
            if not boundary_found:
                for i in range(end, max(start, end - 150), -1):
                    if text[i] == ' ':
                        end = i
                        break
                        
        chunks.append(text[start:end].strip())
        
        # Move sliding window start position
        start = end - chunk_overlap
        if start >= text_len - chunk_overlap:
            break
            
    return [c for c in chunks if c]
