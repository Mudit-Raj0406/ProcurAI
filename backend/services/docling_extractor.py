def extract_content_from_doc(file_path: str) -> str:
    """
    Uses Docling to convert a document (PDF, etc.) to Markdown.
    Falls back to pypdf for plain text extraction if Docling fails.
    """
    # 1. Try Docling
    try:
        from docling.document_converter import DocumentConverter
        converter = DocumentConverter()
        result = converter.convert(file_path)
        text = result.document.export_to_markdown()
        if text and len(text.strip()) > 0:
            return text
    except Exception as e:
        print(f"Docling Conversion Error: {e}. Falling back to pypdf.")

    # 2. Fallback to pypdf
    try:
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        
        if text and len(text.strip()) > 0:
            print("Successfully extracted text using pypdf fallback.")
            return text
    except Exception as e:
        print(f"pypdf Extraction Error: {e}")
    
    return None
