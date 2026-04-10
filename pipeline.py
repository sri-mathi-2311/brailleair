# pipeline.py
# Orchestrates the full OCR → Braille conversion pipeline

def run_pipeline(image_path: str):
    """
    Main pipeline: takes an image path, runs OCR, detects language,
    converts to Braille, and sends via BLE.
    """
    pass


if __name__ == "__main__":
    run_pipeline("test_images/sample.jpg")
