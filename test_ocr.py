import pytesseract
from PIL import Image
import config

# Configure pytesseract to use the exact exe path from config
pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_CMD

def test_image(image_path, lang):
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

if __name__ == "__main__":
    test_image("test_images/test_english_1.png", "eng")
    test_image("test_images/test_tamil_1.png", "tam")
