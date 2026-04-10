# agents/ocr.py
# Day 6 — OCRAgent: English + Confidence Filtering
# Primary OCR -> Confidence filter -> Retry logic -> Post-clean

import re
import sys
import os
import logging
import pytesseract
from pytesseract import Output
import numpy as np

# Ensure project root is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import TESSERACT_CMD

# Configure Tesseract path
pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

logger = logging.getLogger(__name__)

# Max retries from config (image spec says MAX_RETRY=2)
MAX_RETRY = 2
CONFIDENCE_THRESHOLD = 60


# ---------------------------------------------------------------------------
# 1. Primary OCR call
#    --psm 6: uniform block of text
#    --oem 3: LSTM engine (best for printed text)
# ---------------------------------------------------------------------------
def _ocr_extract(image: np.ndarray, lang: str = "eng",
                 psm: int = 6) -> str:
    """
    Run Tesseract OCR on a preprocessed image array.

    Args:
        image: Preprocessed grayscale/binary numpy array.
        lang: Tesseract language code ('eng' or 'tam').
        psm: Page segmentation mode (6=uniform block, 3=auto-detect).

    Returns:
        Raw OCR text string.
    """
    config = f"--psm {psm} --oem 3"
    raw = pytesseract.image_to_string(image, lang=lang, config=config)
    logger.info(f"[OCR] Raw extraction (psm={psm}, lang={lang}): "
                f"{len(raw.split())} words")
    return raw


# ---------------------------------------------------------------------------
# 2. Confidence filter
#    Drop words with confidence < 60. Rejoin remaining into clean string.
# ---------------------------------------------------------------------------
def _confidence_filter(image: np.ndarray, lang: str = "eng",
                       psm: int = 6,
                       threshold: int = CONFIDENCE_THRESHOLD) -> str:
    """
    Extract words with confidence scores, drop low-confidence words.

    Args:
        image: Preprocessed image array.
        lang: Language code.
        psm: Page segmentation mode.
        threshold: Minimum confidence to keep (0-100).

    Returns:
        Filtered text string with only high-confidence words.
    """
    config = f"--psm {psm} --oem 3"
    data = pytesseract.image_to_data(image, lang=lang, config=config,
                                      output_type=Output.DICT)

    words = []
    total = 0
    kept = 0
    for w, c in zip(data['text'], data['conf']):
        if w.strip():
            total += 1
            if int(c) >= threshold:
                words.append(w)
                kept += 1

    filtered = ' '.join(words)
    logger.info(f"[OCR] Confidence filter: kept {kept}/{total} words "
                f"(threshold={threshold})")
    return filtered


# ---------------------------------------------------------------------------
# 4. Post-clean
#    Strip chars not in Braille map. Collapse multiple spaces/newlines.
# ---------------------------------------------------------------------------
def _post_clean(text: str) -> str:
    """
    Clean OCR output:
    - Strip characters not in the Braille map (keep alphanumeric + basic punct)
    - Collapse multiple spaces and newlines
    """
    # Keep only word chars, whitespace, and basic punctuation
    clean = re.sub(r"[^\w\s.,!?'\-:;()\"/]", "", text)
    # Collapse multiple whitespace into single space
    clean = re.sub(r"\s+", " ", clean).strip()
    logger.info(f"[OCR] Post-clean: {len(clean)} chars")
    return clean


# ---------------------------------------------------------------------------
# 3. Main run function with retry logic
# ---------------------------------------------------------------------------
def run(state: dict) -> dict:
    """
    OCRAgent entry point for the pipeline.

    Retry logic:
    - First attempt: --psm 6 (uniform block of text)
    - If filtered text is empty and retry_count < MAX_RETRY:
        increment retry_count, graph routes back to PreprocessAgent
    - On retry: use --psm 3 (auto-detect page layout)

    Args:
        state: BrailleState dict with cleaned_image.

    Returns:
        Updated state with raw_text set.
    """
    image = state.get("cleaned_image")
    retry_count = state.get("retry_count", 0)

    if image is None:
        state["error"] = "No cleaned_image in state"
        logger.error(state["error"])
        return state

    # Choose PSM based on retry attempt
    # First try: psm 6 (uniform block). On retry: psm 3 (auto-detect layout)
    psm = 6 if retry_count == 0 else 3
    lang = state.get("lang", "") or "tam+eng"

    print(f"[OCR] Attempt {retry_count + 1} (psm={psm}, lang={lang})")

    # Step 1: Primary OCR extraction
    raw = _ocr_extract(image, lang=lang, psm=psm)

    # Step 2: Confidence filter
    filtered = _confidence_filter(image, lang=lang, psm=psm)

    # Step 3: Retry logic — if filtered is empty
    if not filtered.strip():
        state["retry_count"] = retry_count + 1
        state["raw_text"] = ""
        if retry_count + 1 < MAX_RETRY:
            print(f"[OCR] Empty result, retry_count={retry_count + 1} "
                  f"-> routing back to preprocess")
        else:
            print(f"[OCR] Empty result after {MAX_RETRY} attempts, "
                  f"proceeding with raw text")
            # Fallback: use raw text even without confidence filtering
            state["raw_text"] = _post_clean(raw)
        return state

    # Step 4: Post-clean
    cleaned = _post_clean(filtered)
    state["raw_text"] = cleaned
    print(f"[OCR] Result: '{cleaned[:80]}{'...' if len(cleaned) > 80 else ''}'")

    return state


# ---------------------------------------------------------------------------
# 5. Standalone test + benchmark
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import cv2
    import glob

    logging.basicConfig(level=logging.INFO)

    print("\n=== OCRAgent — Standalone Test ===\n")

    # Test on all preprocessed images
    preprocessed = sorted(glob.glob("preprocessed/*_preprocessed.png"))
    if not preprocessed:
        print("No preprocessed images found. Run agents/preprocess.py first.")
    else:
        for img_path in preprocessed:
            print(f"\n--- {img_path} ---")
            img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
            state = {
                "cleaned_image": img,
                "raw_text": "",
                "retry_count": 0,
                "lang": "eng",
                "error": "",
            }
            result = run(state)
            print(f"  raw_text: {result['raw_text'][:100]}")
            print(f"  error:    {result['error']}")

    # -----------------------------------------------------------------------
    # Benchmark: word-level match rate
    # -----------------------------------------------------------------------
    print("\n\n=== OCR Benchmark — Word Match Rate ===\n")

    # Expected text for our English test images (from generation)
    benchmarks = {
        "preprocessed/test_english_1_preprocessed.png": (
            "The quick brown fox jumps over the lazy dog "
            "This is a sample English text for OCR testing "
            "Tesseract optical character recognition system"
        ),
    }

    for img_path, expected in benchmarks.items():
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            print(f"  SKIP {img_path} (not found)")
            continue

        state = {
            "cleaned_image": img,
            "raw_text": "",
            "retry_count": 0,
            "lang": "eng",
            "error": "",
        }
        result = run(state)
        ocr_text = result["raw_text"]

        # Word-level comparison
        expected_words = set(expected.lower().split())
        ocr_words = set(ocr_text.lower().split())

        if expected_words:
            matched = expected_words & ocr_words
            match_rate = len(matched) / len(expected_words) * 100
            print(f"  {img_path}")
            print(f"  Expected words : {len(expected_words)}")
            print(f"  OCR words      : {len(ocr_words)}")
            print(f"  Matched        : {len(matched)}")
            print(f"  Match rate     : {match_rate:.1f}%")
            print(f"  Target         : >85%")
            print(f"  Status         : {'PASS' if match_rate > 85 else 'FAIL'}")
