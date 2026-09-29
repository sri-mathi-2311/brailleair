
import sys
import os
from pipeline import build_graph
import cv2
import config

def _safe_preview(text: str) -> str:
    """Return a console-safe preview for Windows terminals."""
    if not text:
        return ""
    try:
        # Check if current stdout can handle it
        text.encode(sys.stdout.encoding or "utf-8")
        return text
    except Exception:
        # Fallback to ASCII representation
        return "".join(c if ord(c) < 128 else f"\\u{ord(c):04x}" for c in text)

def test_pipeline(image_path, label):
    print(f"\n{'='*20} Testing {label}: {image_path} {'='*20}")
    if not os.path.exists(image_path):
        print(f"Error: Test image not found at {image_path}")
        return False

    graph = build_graph()
    
    initial_state = {
        "image_path": image_path,
        "retry_count": 0,
        "error": ""
    }
    
    # Ensure CAMERA_MODE is FILE for testing
    config.CAMERA_MODE = 'FILE'
    
    try:
        app = graph.compile()
        final_state = app.invoke(initial_state)
        
        if final_state.get("error"):
            print(f"Pipeline Error: {final_state['error']}")
            return False
        
        print(f"Detected Lang: {final_state.get('lang')}")
        final_text = final_state.get('final_text', '')
        print(f"Final Text: {_safe_preview(final_text)}")
        
        seq = final_state.get("vibration_seq", [])
        print(f"Generated {len(seq)} Braille patterns.")
        
        # Print a few patterns as a sample
        if seq:
            print("Sample patterns (first 5):")
            for item in seq[:5]:
                char_preview = _safe_preview(item['char'])
                print(f"  '{char_preview}' -> {item['dots']}")
        
        return True
    except Exception as e:
        print(f"Exception during pipeline execution: {e}")
        return False

if __name__ == "__main__":
    tests = [
        ("test_images/test_english_1.png", "English"),
        ("test_images/test_tamil_1.png", "Tamil"),
    ]
    
    results = []
    for img_path, label in tests:
        success = test_pipeline(img_path, label)
        results.append((label, success))
    
    print(f"\n{'='*20} Test Summary {'='*20}")
    for label, success in results:
        status = "PASSED" if success else "FAILED"
        print(f"{label}: {status}")
