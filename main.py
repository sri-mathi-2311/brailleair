# main.py
# Entry point for the BarileAir Braille conversion system
# Day 9 — Full pipeline dry run + Latency benchmark

import argparse
import time
from pipeline import build_graph, BrailleState

def main():
    parser = argparse.ArgumentParser(description="BarileAir: OCR → Braille via BLE")
    parser.add_argument("--mode", default="FILE", help="Capture mode (FILE, WEBCAM, BLE)")
    parser.add_argument("--image", default="", help="Path to input image")
    args = parser.parse_args()

    # We can inject capture_mode into the state if we extend BrailleState.
    # For now, capture_node in pipeline.py defaults to FILE.

    app = build_graph().compile()

    init_state: BrailleState = {
        "image_path": args.image,
        "cleaned_image": None,
        "raw_text": "",
        "lang": "",
        "final_text": "",
        "vibration_seq": [],
        "retry_count": 0,
        "error": "",
    }

    print(f"\n==================================================")
    print(f"  BarileAir Full Pipeline Run")
    print(f"  Mode: {args.mode}")
    print(f"  Image: {args.image or 'auto-cycle'}")
    print(f"==================================================\n")

    start = time.time()
    
    result = app.invoke(init_state)

    elapsed = time.time() - start

    print(f"\n==================================================")
    print(f"  Total: {elapsed:.2f}s")
    print(f"==================================================\n")

if __name__ == "__main__":
    main()
