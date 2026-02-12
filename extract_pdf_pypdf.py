import sys
from pypdf import PdfReader

# Reconfigure stdout to use utf-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

pdf_path = r"c:\Users\Mudit\Desktop\ISP\Indian Institute of Technology Kharagpur Mail - LLM-driven intelligent procurement assistant.pdf"

try:
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    print(text)
except Exception as e:
    print(f"Error: {e}")
