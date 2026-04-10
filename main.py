# main.py
# Entry point for the BarileAir Braille conversion system

import argparse
from pipeline import run_pipeline


def main():
    parser = argparse.ArgumentParser(description="BarileAir: OCR → Braille via BLE")
    parser.add_argument("image", help="Path to input image (English or Tamil text)")
    args = parser.parse_args()
    run_pipeline(args.image)


if __name__ == "__main__":
    main()
