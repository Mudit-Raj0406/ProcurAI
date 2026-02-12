import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from services import docling_extractor

pdf_path = r"c:\Users\Mudit\Desktop\ISP\Indian Institute of Technology Kharagpur Mail - LLM-driven intelligent procurement assistant.pdf"
text = docling_extractor.extract_content_from_doc(pdf_path)
if text:
    print(text)
else:
    print("Extraction failed")
