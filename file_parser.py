# file_parser.py

from docx import Document
import PyPDF2
import pytesseract
from PIL import Image, ImageEnhance
import io

# ✅ FIX FOR WINDOWS – Tesseract path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# -----------------------------
# DOCX TEXT EXTRACTION
# -----------------------------
def extract_text_from_docx(file):
    try:
        doc = Document(file)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text.strip()
    except Exception as e:
        return f"Error reading DOCX file: {str(e)}"


# -----------------------------
# PDF TEXT EXTRACTION
# -----------------------------
def extract_text_from_pdf(file):
    try:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

        # If PDF has no selectable text (scanned PDF)
        if not text.strip():
            return "⚠ This PDF appears to be scanned. Please upload image or use OCR version."

        return text.strip()

    except Exception as e:
        return f"Error reading PDF file: {str(e)}"


# -----------------------------
# IMAGE TEXT EXTRACTION (ENHANCED OCR)
# -----------------------------
def extract_text_from_image(file):
    try:
        # Reset file pointer
        file.seek(0)

        image = Image.open(file)

        # Convert to grayscale
        image = image.convert("L")

        # Increase contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2)

        # Optional: resize small images (improves OCR)
        width, height = image.size
        if width < 1000:
            image = image.resize((width * 2, height * 2))

        # OCR config for better accuracy
        custom_config = r'--oem 3 --psm 6'

        text = pytesseract.image_to_string(image, config=custom_config)

        if not text.strip():
            return "⚠ Could not extract readable text from image. Please upload clearer image."

        return text.strip()

    except Exception as e:
        return f"Error reading image file: {str(e)}"