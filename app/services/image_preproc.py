# app/services/image_preproc.py
from PIL import Image
import pytesseract
import io

MAX_DIMENSION = 1600          # tune based on token-cost testing
OCR_TRIGGER_DIMENSION = 2400   # only OCR very high-res photos

def preprocess_image(raw_bytes: bytes) -> dict:
    img = Image.open(io.BytesIO(raw_bytes))
    orig_w, orig_h = img.size

    ocr_text = None
    if max(orig_w, orig_h) > OCR_TRIGGER_DIMENSION:
        # high-quality photo: extract text before downscaling to avoid losing readability
        ocr_text = pytesseract.image_to_string(img).strip() or None

    if max(orig_w, orig_h) > MAX_DIMENSION:
        ratio = MAX_DIMENSION / max(orig_w, orig_h)
        img = img.resize((int(orig_w * ratio), int(orig_h * ratio)), Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return {
        "image_bytes": buf.getvalue(),
        "ocr_text": ocr_text,
        "original_size": (orig_w, orig_h),
        "final_size": img.size,
    }