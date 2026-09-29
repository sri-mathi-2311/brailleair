# agents/capture.py
# Day 4 — CaptureAgent: Webcam + File Mode
# Supports FILE, WEBCAM, and BLE (stub) capture modes

import os
import cv2
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

# Track file index across invocations (cycles through test_images/)
_file_index = 0


# ---------------------------------------------------------------------------
# 1. FILE mode — cycle through test_images/ on each invocation
# ---------------------------------------------------------------------------
def _capture_file(state: dict) -> dict:
    """
    Load images from test_images/ directory, cycling through them
    on each invocation.
    """
    global _file_index

    # If image_path is already provided via state, use it directly
    if state.get("image_path"):
        selected = state["image_path"]
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"[{timestamp}] FILE capture: {selected} (provided via --image)")
        print(f"[CAPTURE-FILE] [{timestamp}] Loaded provided image: {selected}")
        return state

    image_dir = Path("test_images")
    extensions = ("*.png", "*.jpg", "*.jpeg", "*.bmp", "*.tiff")
    images = []
    for ext in extensions:
        images.extend(sorted(image_dir.glob(ext)))

    if not images:
        state["error"] = "No images found in test_images/"
        logger.error(state["error"])
        return state

    # Cycle through images
    idx = _file_index % len(images)
    selected = str(images[idx])
    _file_index += 1

    state["image_path"] = selected
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"[{timestamp}] FILE capture: {selected} (index {idx}/{len(images)})")
    print(f"[CAPTURE-FILE] [{timestamp}] Loaded: {selected}")

    return state


# ---------------------------------------------------------------------------
# 2. WEBCAM mode — live preview with cv2.imshow(), press SPACE to capture
# ---------------------------------------------------------------------------
def _capture_webcam(state: dict) -> dict:
    """
    Open webcam, show live preview window.
    Press SPACE to capture a frame, ESC to cancel.
    Saves captured frame to a temp file.
    """
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        state["error"] = "Could not open webcam"
        logger.error(state["error"])
        return state

    print("[CAPTURE-WEBCAM] Live preview — press SPACE to capture, ESC to cancel")

    captured = False
    while True:
        ret, frame = cap.read()
        if not ret:
            state["error"] = "Failed to read frame from webcam"
            logger.error(state["error"])
            break

        cv2.imshow("BarileAir — Press SPACE to capture", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == 32:  # SPACE
            # Save the captured frame
            output_path = os.path.join("test_images", "brailleair_capture.jpg")
            cv2.imwrite(output_path, frame)
            state["image_path"] = output_path
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"[{timestamp}] WEBCAM capture saved: {output_path}")
            print(f"[CAPTURE-WEBCAM] [{timestamp}] Saved: {output_path}")
            captured = True
            break
        elif key == 27:  # ESC
            print("[CAPTURE-WEBCAM] Cancelled by user")
            state["error"] = "Webcam capture cancelled"
            break

    cap.release()
    cv2.destroyAllWindows()

    return state


# ---------------------------------------------------------------------------
# 3. URL mode — fetch from ESP32 camera URL
# ---------------------------------------------------------------------------
def _capture_url(state: dict) -> dict:
    """
    Fetch an image from the ESP32 camera URL defined in config.
    Saves it to a temp file.
    """
    import requests
    import config

    url = config.ESP32_CAMERA_URL
    print(f"[CAPTURE-URL] Fetching from {url}...")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        output_path = os.path.join("web_uploads", "esp32_capture.jpg")
        os.makedirs("web_uploads", exist_ok=True)
        
        with open(output_path, "wb") as f:
            f.write(response.content)
            
        state["image_path"] = output_path
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"[{timestamp}] URL capture saved: {output_path}")
        print(f"[CAPTURE-URL] [{timestamp}] Saved: {output_path}")
        
    except Exception as e:
        state["error"] = f"Failed to capture from ESP32: {str(e)}"
        logger.error(state["error"])
        print(f"[CAPTURE-URL] Error: {state['error']}")

    return state


# ---------------------------------------------------------------------------
# 4. BLE mode stub — raises NotImplementedError (real BLE in Day 11)
# ---------------------------------------------------------------------------
def _capture_ble(state: dict) -> dict:
    """
    BLE capture stub — not implemented until Day 11.
    Raises NotImplementedError.
    """
    if True:  # BLE mode placeholder
        raise NotImplementedError(
            "BLE capture mode is a stub — real BLE implemented Day 11. "
            "Use FILE or WEBCAM mode instead."
        )
    # Future: return ble_client.receive_image()
    return state


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def run(mode: str = "FILE", state: dict = None) -> dict:
    """
    Run the CaptureAgent in the specified mode.

    Args:
        mode: 'FILE', 'WEBCAM', or 'BLE'
        state: BrailleState dict (created if None)

    Returns:
        Updated state with image_path set.
    """
    if state is None:
        state = {
            "image_path": "",
            "cleaned_image": None,
            "raw_text": "",
            "lang": "",
            "final_text": "",
            "vibration_seq": [],
            "retry_count": 0,
            "error": "",
        }

    mode = mode.upper()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[CAPTURE] [{timestamp}] Mode: {mode}")

    if mode == "FILE":
        return _capture_file(state)
    elif mode == "WEBCAM":
        return _capture_webcam(state)
    elif mode == "URL":
        return _capture_url(state)
    elif mode == "BLE":
        return _capture_ble(state)
    else:
        state["error"] = f"Unknown capture mode: {mode}"
        logger.error(state["error"])
        return state


# ---------------------------------------------------------------------------
# 4. Standalone test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)

    mode = sys.argv[1] if len(sys.argv) > 1 else "FILE"
    print(f"\n=== CaptureAgent standalone test (mode={mode}) ===\n")

    result = run(mode=mode)

    print(f"\n--- Result ---")
    print(f"  image_path : {result.get('image_path', '')}")
    print(f"  error      : {result.get('error', '')}")

    # Run FILE mode 3 times to demonstrate cycling
    if mode == "FILE":
        print(f"\n--- Cycling test (3 more invocations) ---")
        for i in range(3):
            result = run(mode="FILE")
            print(f"  [{i+1}] image_path: {result.get('image_path', '')}")
