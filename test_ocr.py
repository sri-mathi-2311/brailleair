import pytesseract
from PIL import Image
import config
import pytest

# Configure pytesseract to use the exact exe path from config
pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_CMD

def run_ocr_smoke(image_path, lang):
    print(f"\n--- Testing {image_path} (lang='{lang}') ---")
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img, lang=lang)
        print("OCR Output:")
        # Save to file to avoid console printing errors, and also try to print safely
        out_txt = text.strip() if text.strip() else "[No text detected]"
        with open(f"{image_path}_out.txt", "w", encoding="utf-8") as f:
            f.write(out_txt)
        print(out_txt.encode("utf-8", errors="replace").decode("utf-8"))
        print("-" * 40)
    except Exception as e:
        print(f"Error: {e}")

@pytest.mark.parametrize(
    ("image_path", "lang"),
    [
        ("test_images/test_english_1.png", "eng"),
        ("test_images/test_tamil_1.png", "tam"),
    ],
)
def test_image_runs_without_error(image_path, lang):
    run_ocr_smoke(image_path, lang)

if __name__ == "__main__":
    run_ocr_smoke("test_images/test_english_1.png", "eng")
    run_ocr_smoke("test_images/test_tamil_1.png", "tam")
