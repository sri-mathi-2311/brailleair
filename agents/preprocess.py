# agents/preprocess.py
# Day 5 — PreprocessAgent: Full OpenCV Pipeline
# Grayscale -> Denoise -> Deskew -> Threshold (Otsu) -> Resize to 300 DPI

import cv2
import numpy as np
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 1. Grayscale
# ---------------------------------------------------------------------------
def _grayscale(img: np.ndarray) -> np.ndarray:
    """Convert BGR image to grayscale."""
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img  # already grayscale

    # Day 10 Fix: Apply CLAHE to resolve noisy background / poor contrast
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    
    # Denoise with modest median blur
    gray = cv2.medianBlur(gray, 3)

    logger.info("[PREPROCESS] Grayscale applied with CLAHE and Median Blur")
    return gray


# ---------------------------------------------------------------------------
# 2. Denoise
# ---------------------------------------------------------------------------
def _denoise(gray: np.ndarray, h: int = 10) -> np.ndarray:
    """
    Apply fast non-local means denoising.
    h=10 is a good starting value. Increase for very noisy phone photos.
    """
    denoised = cv2.fastNlMeansDenoising(gray, h=h)
    logger.info(f"[PREPROCESS] Denoised (h={h})")
    return denoised


# ---------------------------------------------------------------------------
# 3. Deskew up to +/-15 degrees
# ---------------------------------------------------------------------------
def _deskew(denoised: np.ndarray, max_angle: float = 15.0) -> np.ndarray:
    """
    Detect skew angle from contours and correct it.
    Only deskew if angle > 1 degree to avoid unnecessary transforms.
    """
    # Find contours
    coords = np.column_stack(np.where(denoised > 0))

    if len(coords) < 10:
        logger.info("[PREPROCESS] Deskew skipped — too few points")
        return denoised

    # Get the minimum area rectangle around all foreground pixels
    rect = cv2.minAreaRect(coords)
    angle = rect[-1]

    # Normalize the angle
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    # Only deskew if angle > 1 degree and within +/-15 degrees
    if abs(angle) < 1.0:
        logger.info(f"[PREPROCESS] Deskew skipped — angle {angle:.2f} deg < 1 deg")
        return denoised

    if abs(angle) > max_angle:
        logger.warning(f"[PREPROCESS] Skew angle {angle:.2f} deg exceeds +/-{max_angle} deg, clamping")
        angle = max_angle if angle > 0 else -max_angle

    h, w = denoised.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(denoised, M, (w, h),
                              flags=cv2.INTER_CUBIC,
                              borderMode=cv2.BORDER_REPLICATE)
    logger.info(f"[PREPROCESS] Deskewed by {angle:.2f} degrees")
    return rotated


# ---------------------------------------------------------------------------
# 4. Threshold (Otsu)
# ---------------------------------------------------------------------------
def _threshold(image: np.ndarray) -> np.ndarray:
    """
    Apply Otsu's automatic thresholding.
    Otsu auto-selects the threshold — no manual tuning needed.
    """
    _, thresh = cv2.threshold(image, 0, 255,
                               cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    logger.info("[PREPROCESS] Otsu threshold applied")
    return thresh


# ---------------------------------------------------------------------------
# 5. Resize to 300 DPI
# ---------------------------------------------------------------------------
def _resize_300dpi(thresh: np.ndarray, current_dpi: int = 96) -> np.ndarray:
    """
    Resize image to approximate 300 DPI from assumed current DPI.
    Default assumes screen capture at 96 DPI.
    """
    scale = 300 / current_dpi
    resized = cv2.resize(thresh, None, fx=scale, fy=scale,
                          interpolation=cv2.INTER_CUBIC)
    logger.info(f"[PREPROCESS] Resized to 300 DPI (scale={scale:.2f}x, "
                f"size={resized.shape[1]}x{resized.shape[0]})")
    return resized


# ---------------------------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------------------------
def preprocess(image_path: str, save_output: bool = True) -> np.ndarray:
    """
    Run the full preprocessing pipeline on an image file.

    Pipeline: Grayscale -> Denoise -> Deskew -> Threshold -> Resize 300DPI

    Args:
        image_path: Path to the input image.
        save_output: If True, save the preprocessed image for visual QA.

    Returns:
        Preprocessed image as numpy array.
    """
    print(f"[PREPROCESS] Processing: {image_path}")

    # Load image
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Could not load image: {image_path}")

    # Pipeline steps
    gray = _grayscale(img)
    denoised = _denoise(gray)
    deskewed = _deskew(denoised)
    thresh = _threshold(deskewed)
    resized = _resize_300dpi(thresh)

    # Save preprocessed output for visual QA
    if save_output:
        os.makedirs("preprocessed", exist_ok=True)
        basename = os.path.splitext(os.path.basename(image_path))[0]
        output_path = os.path.join("preprocessed", f"{basename}_preprocessed.png")
        cv2.imwrite(output_path, resized)
        print(f"[PREPROCESS] Saved: {output_path}")

    return resized


def run(state: dict) -> dict:
    """
    Entry point for the pipeline node.
    Reads image_path from state, runs preprocessing, updates cleaned_image.
    """
    image_path = state.get("image_path", "")

    if not image_path:
        state["error"] = "No image_path in state"
        logger.error(state["error"])
        return state

    try:
        cleaned = preprocess(image_path)
        state["cleaned_image"] = cleaned
        state["error"] = ""
    except Exception as e:
        state["error"] = str(e)
        logger.error(f"[PREPROCESS] Error: {e}")

    return state


# ---------------------------------------------------------------------------
# Standalone test — run on all test images
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import glob
    logging.basicConfig(level=logging.INFO)

    test_images = sorted(glob.glob("test_images/*.png")) + sorted(glob.glob("test_images/*.jpg"))
    print(f"\n=== PreprocessAgent — Processing {len(test_images)} images ===\n")

    for img_path in test_images:
        try:
            result = preprocess(img_path)
            print(f"  OK  {img_path} -> {result.shape}")
        except Exception as e:
            print(f"  FAIL {img_path} -> {e}")

    print(f"\n=== Done. Check preprocessed/ folder for visual QA ===\n")
