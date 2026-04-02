# parsing.py
import os
from pypdf import PdfReader
from pptx import Presentation

import re
try:
    import pdfplumber
except ImportError:
    pdfplumber = None

def clean_text(text: str) -> str:
    """
    Clean text extracted from PDF/PPT.
    1. Merge broken lines (e.g. "Net\nwork" -> "Network").
    2. Fix vertical text (e.g. "N\ne\nt" -> "Net").
    3. Remove excessive whitespace.
    """
    if not text:
        return ""
    
    encoded_text = text.encode("utf-8", "ignore").decode("utf-8")
    
    # Debugging: Log raw length
    raw_len = len(encoded_text)
    
    # Simplified Cleaning:
    # Replace newlines with spaces to keep word boundaries
    text = encoded_text.strip().replace('\n', ' ')
    
    # Remove excessive spaces
    text = re.sub(r' +', ' ', text)
    
    clean_len = len(text)
    # print(f"[DEBUG] Cleaned: {raw_len} -> {clean_len} chars")
    
    return text

def parse_pdf(filepath: str, user_config: dict = None) -> list[str]:
    """
    Parse PDF and return a list of cleaned text blocks.
    Strategy: Use pdfplumber primarily (better layout handling). Fallback to pypdf.
    """
    blocks = []
    print(f"[DEBUG] Parsing PDF: {filepath}")
    
    # Method 1: pdfplumber (Primary)
    if pdfplumber:
        print("[INFO] Using pdfplumber as primary parser...")
        try:
            with pdfplumber.open(filepath) as pdf:
                print(f"[DEBUG] Total Pages (pdfplumber): {len(pdf.pages)}")
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text() or ""
                    # print(f"[DEBUG] pdfplumber Page {i} Raw: {text[:50]!r}")
                    cleaned = clean_text(text)
                    if cleaned:
                        # print(f"[DEBUG] pdfplumber Page {i} Cleaned (First 100): {cleaned[:100]!r}")
                        blocks.append(cleaned)
        except Exception as e:
            print(f"[ERROR] pdfplumber parsing failed: {e}")
    else:
        print("[WARN] pdfplumber not installed. Skipping.")

    # Quality Check 1: pdfplumber
    total_len = sum(len(b) for b in blocks)
    if len(blocks) > 0 and total_len >= 500:
        print(f"[DEBUG] pdfplumber successful. Extracted {len(blocks)} blocks, total chars: {total_len}")
        return blocks
    else:
        print(f"[INFO] pdfplumber result insufficient (blocks={len(blocks)}, chars={total_len}). Continuing to fallback...")
        # Keep blocks, maybe pypdf will add more

    # Method 2: pypdf (Fallback)
    if not blocks:
        print("[INFO] Falling back to pypdf...")
        try:
            reader = PdfReader(filepath)
            print(f"[DEBUG] Total Pages (pypdf): {len(reader.pages)}")
            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                cleaned = clean_text(text)
                if cleaned:
                    blocks.append(cleaned)
        except Exception as e:
            print(f"[ERROR] pypdf parsing failed: {e}")

    # Quality Check 2: pypdf & Final OCR Decision
    total_len = sum(len(b) for b in blocks)
    logger.info(f"[DEBUG] Total text length from extractors: {total_len}")
    
    if total_len < 1000: # Increased threshold to be safer
        logger.warning(f"[WARN] Text extraction yielded only {total_len} chars (< 1000). Attempting OCR...")
        # Pass user_config to OCR to let it decide between cloud VLM and local Tesseract
        ocr_blocks = parse_pdf_ocr(filepath, user_config=user_config) 
        blocks.extend(ocr_blocks)
        total_len = sum(len(b) for b in blocks)
        logger.info(f"[DEBUG] Total text length after OCR: {total_len}")

    print(f"[DEBUG] Final Extracted {len(blocks)} non-empty blocks.")
    return blocks

import logging
logger = logging.getLogger(__name__)

def parse_pdf_ocr(filepath: str, user_config: dict = None) -> list[str]:
    """
    Convert PDF pages to images and use OCR.
    If cloud API is configured, use the cloud VLM.
    Otherwise, fallback to local Tesseract OCR (0 VRAM).
    """
    import fitz  # pymupdf
    from core.llm_factory import get_llm_service
    
    blocks = []
    
    use_cloud_vlm = False
    llm = None
    if user_config and user_config.get("llm_provider") == "cloud":
        use_cloud_vlm = True
        llm = get_llm_service(user_config)
        logger.info("[OCR] Using Cloud VLM for OCR.")
    else:
        logger.info("[OCR] Using local Tesseract for OCR.")
        try:
            import pytesseract
            from PIL import Image
        except ImportError:
            logger.error("[OCR] pytesseract or Pillow not installed. Cannot perform local OCR.")
            return []

    try:
        doc = fitz.open(filepath)
        logger.info(f"[OCR] Processing {len(doc)} pages for {filepath}...")
        
        max_pages = 20
        
        for i, page in enumerate(doc):
            if i >= max_pages:
                logger.warning(f"[OCR] Limit reached ({max_pages} pages). Stopping for performance.")
                break
                
            logger.debug(f"[OCR] Rendering page {i}...")
            pix = page.get_pixmap(dpi=150)
            
            text = ""
            if use_cloud_vlm and llm:
                img_bytes = pix.tobytes("png")
                # Need to implement ocr_image in CloudAPIService if not exists, or pass image as base64 to chat
                # Assuming ocr_image is implemented or we fallback to string extraction
                try:
                    text = llm.ocr_image(img_bytes) 
                except AttributeError:
                    logger.warning("[OCR] Cloud provider doesn't support ocr_image yet. Skipping page.")
            else:
                # Local Tesseract
                from PIL import Image
                import io
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                # Specify languages if needed: lang='chi_sim+eng'
                # Note: User needs to have tesseract installed on Windows and in PATH
                try:
                    # In python, tesseract might need to be explicitly pointed to the exe on Windows
                    # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
                    text = pytesseract.image_to_string(img, lang='chi_sim+eng')
                except Exception as eval_e:
                    logger.error(f"[OCR] Tesseract failed on page {i}: {eval_e}. Is Tesseract installed on your system?")
                    text = ""

            # Remove markdown code blocks if LLM outputs them (mostly for cloud VLM)
            text = text.replace("```", "")
            
            cleaned = clean_text(text)
            
            if cleaned:
                blocks.append(cleaned)
            else:
                logger.warning(f"[OCR] Page {i} yielded empty text after cleaning.")
                
    except Exception as e:
        logger.error(f"[OCR] Pipeline failed: {e}", exc_info=True)
        
    return blocks

def parse_ppt(filepath: str) -> list[str]:
    """
    Parse PPTX and return a list of text blocks (slides).
    """
    blocks = []
    try:
        prs = Presentation(filepath)
        for slide in prs.slides:
            text_runs = []
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    text_runs.append(shape.text)
            
            full_text = "\n".join(text_runs).strip()
            if full_text:
                blocks.append(full_text)
    except Exception as e:
        print(f"Error parsing PPT {filepath}: {e}")
        return []
    return blocks

def parse_file(filepath: str, file_type: str, user_config: dict = None) -> list[str]:
    if file_type.lower() == 'pdf':
        return parse_pdf(filepath, user_config=user_config)
    elif file_type.lower() in ['ppt', 'pptx']:
        return parse_ppt(filepath)
    else:
        return []
